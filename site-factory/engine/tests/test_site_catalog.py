"""Synthetic local fixtures only; no Catalog, approval, or Queue writes."""
import copy
import hashlib
import json
import unittest
import test_engine as f
import test_regional_service as region_fixture

class SiteCatalogTests(unittest.TestCase):
    bytes = f.SnapshotTests.bytes
    render = f.SnapshotTests.render
    assert_rejected_unchanged = f.SnapshotTests.assert_rejected_unchanged
    save = region_fixture.RegionalTests.save
    def body(self, **changes):
        return region_fixture.RegionalTests.body(self, SITE_KEY='ansan-flower-test', **changes)
    def setUp(self):
        region_fixture.RegionalTests.setUp(self)
        self.registry['sites']['ansan-flower-test'] = self.registry['sites'].pop('test')
        self.coverage['siteKey'] = self.policy['siteKey'] = 'ansan-flower-test'
        self.save()
        for name in ['publish-manifest', 'page-map', 'architecture']:
            file=self.data/(name+'.json');data=json.loads(file.read_text());data['siteKey']='ansan-flower-test';file.write_text(json.dumps(data))
        self.catalog_file=self.data/'site-catalog.json'
        self.legacy=[{'key':'wreath-test','family':'funeral','sourceUrl':'https://fwith.co.kr/'}]
        (self.data/'products.json').write_text(json.dumps(self.legacy))
        (self.data/'business-truth.json').write_text(json.dumps({'brandKey':'flower-fwith','truthKey':'flower-fwith-v1','onlineOrderUrl':'https://fwith.co.kr'}))
        # Minimal JPEG header fixture tests format/dimensions/hash validation; not a real product asset.
        self.image_bytes=bytes.fromhex('ffd8ffc0000b080001000101011100ffd9')
        self.product={'productKey':'bouquet-g108','sku':'G108','catalogRecordId':'recAAAAAAAAAAAAAA','catalogStatus':'draft','brandKey':'flower-fwith','category':'flower_bouquet','family':'bouquet','name':'SYNTHETIC TEST ONLY','price':1,'priceKind':'public_sale','currency':'KRW','priceNotice':'Test only','sourceUrl':'https://fwith.co.kr/shop/item.php?it_id=G108','sourceImageUrl':'https://fwith.co.kr/data/item/flower379/G108/thumb-1_500x500.jpg','onlineOrderUrl':'https://fwith.co.kr','sourceLevel':'official_business_source','assetType':'real_product','verifiedAt':'2026-10-03T00:00:00Z','availability':'public_listing_orderable_stock_unconfirmed','image':'/images/products/bouquet-g108.jpg','imageSha256':hashlib.sha256(self.image_bytes).hexdigest(),'imageWidth':1,'imageHeight':1,'imageType':'image/jpeg','imageAlt':'Synthetic fixture'}
        self.image=self.root/'site/public/images/products/bouquet-g108.jpg';self.image.parent.mkdir(parents=True);self.image.write_bytes(self.image_bytes)
        self.catalog={'schemaVersion':1,'siteKey':'ansan-flower-test','brandKey':'flower-fwith','truthKey':'flower-fwith-v1','status':'candidate','enabled':False,'products':[self.product],'pageBindings':[]}
        self.evidence={'schemaVersion':1,'siteKey':'ansan-flower-test','brandKey':'flower-fwith','truthKey':'flower-fwith-v1','sourceLevel':'official_business_source','verifiedAt':'2026-10-03','catalogBaseId':'appOthiezu3SqH2Nu','catalogTableId':'tbl7qSHi0lTDjPE5A','products':copy.deepcopy(self.catalog['products'])}
        (self.data/'site-catalog-evidence.json').write_text(json.dumps(self.evidence))
        self.write_catalog()
    def write_catalog(self):self.catalog_file.write_text(json.dumps(self.catalog))
    def products(self):return f.snap.site_catalog_products(self.root/'site','ansan-flower-test')
    def test_absent_definition_is_unchanged_for_other_cities(self):
        self.catalog_file.unlink();self.assertEqual(self.products(),self.legacy)
    def test_disabled_does_not_promote_global_draft_or_expose_gift(self):
        self.assertEqual(self.products(),self.legacy);self.assertEqual(self.catalog['products'][0]['catalogStatus'],'draft')
    def test_enabled_uses_only_this_sites_exact_products(self):
        self.catalog['enabled']=True;self.catalog['status']='approved';self.write_catalog();self.assertEqual(self.products(),self.legacy+[self.product])
        with self.assertRaises(f.snap.SnapshotError):f.snap.site_catalog_products(self.root/'site','another-city')
    def test_bad_source_inputs_fail_even_disabled(self):
        cases=[('family','orchid'),('productKey','bouquet-happiness'),('price',None),('price',0),('priceKind','cost'),('image','/images/products/wrong.jpg'),('imageWidth',2),('imageType','image/png'),('imageSha256','0'*64),('sourceUrl','https://fwith.co.kr/shop/item.php?it_id=G105'),('sourceImageUrl','https://fwith.co.kr/data/item/flower379/G105/thumb-1_500x500.jpg'),('availability','in_stock_guaranteed'),('onlineOrderUrl','https://fwith.co.kr/shop/item.php?it_id=G108')]
        for field,value in cases:
            with self.subTest(field=field,value=value):
                self.setUp();self.catalog['products'][0][field]=value;self.write_catalog()
                with self.assertRaises(f.snap.SnapshotError):self.products()
    def test_bad_image_bytes_fail(self):
        self.image.write_bytes(b'not an image')
        with self.assertRaises(f.snap.SnapshotError):self.products()
    def test_snapshot_rendering_respects_local_enable_and_exact_family_atomically(self):
        self.policy['visualBindings'][0].update(purchaseMode='catalog',productKeys=['bouquet-g108']);self.save()
        body=self.body(CONTENT='꽃다발 SYNTHETIC TEST ONLY. '+('Test fixture, not customer content. '*20))
        self.assert_rejected_unchanged(body)
        self.catalog['enabled']=True;self.catalog['status']='approved';self.write_catalog()
        result=self.render(body);self.assertTrue(result['approvalVerified'])
        row=json.loads((self.data/'pages.json').read_text())[0];self.assertEqual(row['regionalProductKeys'],['bouquet-g108']);self.assertEqual(row['regionalProductFamilies'],['bouquet'])
    def test_disabled_catalog_cannot_be_bypassed_with_a_frozen_payload(self):
        self.policy['visualBindings'][0].update(purchaseMode='catalog',productKeys=['bouquet-g108']);self.save()
        self.assert_rejected_unchanged(self.body(CONTENT='꽃다발 fixture. '+('Synthetic fixture only. '*30)))
    def test_unknown_selected_key_is_atomic(self):
        self.catalog['enabled']=True;self.catalog['pageBindings']=[{'pageKey':'test-page-01','status':'approved','productKeys':['unknown']}];self.write_catalog()
        self.policy['visualBindings'][0].update(purchaseMode='catalog',productKeys=['bouquet-g108']);self.save();self.assert_rejected_unchanged(self.body())

    def test_exact_tuple_rejects_positive_price_name_and_record_drift(self):
        for field,value in [('price',2),('name','invented'),('catalogRecordId','recBBBBBBBBBBBBBB')]:
            with self.subTest(field=field):
                self.setUp();self.catalog['products'][0][field]=value;self.write_catalog()
                with self.assertRaisesRegex(f.snap.SnapshotError,'tuple drift'):self.products()
    def test_enabled_alone_cannot_publish_candidate_home_catalog(self):
        self.catalog['enabled']=True;self.write_catalog()
        with self.assertRaisesRegex(f.snap.SnapshotError,'requires reviewed source'):self.products()
    def test_another_city_cannot_relabel_the_same_brand_evidence(self):
        self.catalog.update(siteKey='goyang-flower-v2',enabled=True,status='approved');self.evidence['siteKey']='goyang-flower-v2';self.write_catalog();(self.data/'site-catalog-evidence.json').write_text(json.dumps(self.evidence))
        with self.assertRaisesRegex(f.snap.SnapshotError,'site-local scope'):f.snap.site_catalog_products(self.root/'site','goyang-flower-v2')
    def test_missing_evidence_cannot_fall_back_to_presentation(self):
        (self.data/'site-catalog-evidence.json').unlink()
        with self.assertRaisesRegex(f.snap.SnapshotError,'evidence'):self.products()

    def test_schema_version_bool_and_string_rejected_but_numeric_one_equivalent(self):
        for key in ['definition','evidence']:
            for value in [True,False,'1']:
                with self.subTest(key=key,value=value):
                    self.setUp()
                    if key=='definition':self.catalog['schemaVersion']=value;self.write_catalog()
                    else:self.evidence['schemaVersion']=value;(self.data/'site-catalog-evidence.json').write_text(json.dumps(self.evidence))
                    with self.assertRaises(f.snap.SnapshotError):self.products()
        self.setUp();self.catalog['schemaVersion']=1.0;self.evidence['schemaVersion']=1.0;self.write_catalog();(self.data/'site-catalog-evidence.json').write_text(json.dumps(self.evidence));self.assertEqual(self.products(),self.legacy)
