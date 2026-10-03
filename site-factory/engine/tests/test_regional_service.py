"""Synthetic local contract fixtures; none are customer copy or Queue writes."""
import copy,hashlib,json,base64,unittest
import test_engine as f

class RegionalTests(unittest.TestCase):
    bytes=f.SnapshotTests.bytes
    render=f.SnapshotTests.render
    assert_rejected_unchanged=f.SnapshotTests.assert_rejected_unchanged
    # Inherit no baseline test methods: those run under the separate SnapshotTests class.
    def setUp(self):
        f.SnapshotTests.setUp(self)
        self.registry['sites']['test'].update(allowedCategories=['regions'],allowedPageTypes=['regional-service'],categoryPageTypes={'regions':['regional-service']},regionalService={'enabled':True,'scopeKey':'test-maintenance'})
        self.data=self.root/'site/src/data'
        image=self.root/'site/public/images/test.png';image.parent.mkdir(parents=True);image.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9ZlS8AAAAASUVORK5CYII='))
        self.coverage={'schemaVersion':2,'siteKey':'test','scopeKey':'test-maintenance','unitBasis':'legal-dong-plus-eup-myeon','countIsPageQuota':False,'officialSourceUrls':['https://www.ansan.go.kr/stat/'],'units':[{'unitKey':'sa'},{'unitKey':'seonbu'}],'representatives':[{'pageKey':'test-page-01','slug':'sa','url':'/regions/sa/','unitKeys':['sa'],'intentKey':'ansan|local|sa','primaryKeyword':'안산 사동 꽃배달','status':'approved','routeMode':'regional','queryEvidence':'Explicit coverage task and official source'},{'pageKey':'launch14','slug':'existing','url':'/places/existing/','unitKeys':['seonbu'],'intentKey':'reserved-seonbu','primaryKeyword':'선부동 꽃배달','status':'reserved','routeMode':'existing'}]}
        self.policy={'siteKey':'test','scopeKey':'test-maintenance','enabled':True,'officialHosts':['www.ansan.go.kr'],'visualBindings':[{'pageKey':'test-page-01','image':'/images/test.png','alt':'Test source image','sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'sourceUrl':'https://fwith.co.kr/','status':'approved','purchaseMode':'consultation-only','productKeys':[],'assetType':'brand','verifiedAt':'2026-10-03','width':1,'height':1,'type':'image/png'}]}
        self.save()
    def save(self):
        for name,obj in [('region-coverage',self.coverage),('region-policy',self.policy)]: (self.data/(name+'.json')).write_text(json.dumps(obj))
    def body(self,**changes):
        values=dict(CATEGORY='regions',SLUG='sa',PAGE_TYPE='regional-service',PAGE_ROLE='REGION_SERVICE_LANDING',PARENT_HUB='/regions/',INTENT_KEY='ansan|local|sa',PRIMARY_KEYWORD='안산 사동 꽃배달',TITLE='안산 사동 꽃배달 | TEST',H1='안산 사동 꽃배달 TEST',QUERY_CLASS='local-commercial',VISUAL_INTENT='flower_delivery',ASSET_SLOT='SPLIT_VISUAL',SOURCES='https://www.ansan.go.kr/stat/\nhttps://fwith.co.kr/',**{'SOURCE-NAMES':'Municipal\nBusiness','SOURCE-TYPES':'official\nbusiness','CARD-SUMMARY':'Useful synthetic fixture summary','FIRST-ANSWER':'Synthetic direct answer'})
        values.update(changes);body=f.payload(**values);proof=f.snap.frozen_hashes(f.snap.validate_content(f.snap.parse_payload(body)))[1]
        return f.payload(**values,APPROVAL_STATUS='approved',APPROVED_SNAPSHOT_HASH=proof)
    def test_existing_publisher_headers_suffice_for_both_renderers(self):
        for renderer in ['structured-json-v12','markdown-v1']:
            with self.subTest(renderer=renderer):
                self.setUp();self.registry['sites']['test']['snapshotRenderer']=renderer
                result=self.render(self.body());self.assertTrue(result['approvalVerified']);self.assertEqual(result['url'],'/regions/sa/')
                self.assertEqual(self.render(self.body())['changedFiles'],[])
                row=json.loads((self.data/'publish-manifest.json').read_text())['pages'][0];self.assertEqual(row['scopeKey'],'test-maintenance');self.assertEqual(row['ogImage'],'/images/test.png')
                if renderer=='markdown-v1':self.assertIn('"type": "business"',(self.root/'site/src/content/articles/test-page-01.md').read_text())
    def test_region_rejections_are_atomic(self):
        tests=[('registry disabled',lambda:self.registry['sites']['test']['regionalService'].update(enabled=False)),('policy disabled',lambda:self.policy.update(enabled=False)),('scope mismatch',lambda:self.policy.update(scopeKey='wrong')),('candidate',lambda:self.coverage['representatives'][0].update(status='candidate')),('duplicate canonical',lambda:self.coverage['representatives'].append({**self.coverage['representatives'][0],'pageKey':'different','url':'/regions/different/','intentKey':'different'})),('untrusted source',lambda:self.coverage['officialSourceUrls'].append('https://evil.example/')),('unverified asset',lambda:self.policy['visualBindings'][0].update(sha256='0'*64))]
        for name,mutate in tests:
            with self.subTest(name=name):
                self.setUp();mutate();self.save();self.assert_rejected_unchanged(self.body())
    def test_supplied_optional_metadata_cannot_override_registered_source(self):
        for changes in [{'REGION_SCOPE_KEY':'wrong'},{'OG_IMAGE':'/images/evil.png'},{'SOURCES':'https://fwith.co.kr/','SOURCE-TYPES':'business'},{'CATEGORY':'places','PARENT_HUB':'/places/'},{'PAGE_TYPE':'general-guide'}]:
            with self.subTest(changes=changes):self.assert_rejected_unchanged(self.body(**changes))
    def test_missing_frozen_approval_cannot_use_legacy_trusted_writer_exception(self):
        self.registry['sites']['test']['snapshotRenderer']='markdown-v1';body=self.body().replace('APPROVAL_STATUS: approved','APPROVAL_STATUS: pending');self.assert_rejected_unchanged(body)


    def test_consultation_only_is_not_a_missing_catalog_fallback(self):
        self.assert_rejected_unchanged(self.body(CONTENT='꽃다발을 주문할 수 있습니다. '+('지역 주문 안내를 확인합니다. '*30)))
        self.assert_rejected_unchanged(self.body(CONTENT='가격은 50,000원입니다. '+('지역 주문 안내를 확인합니다. '*30)))
        self.policy['visualBindings'][0]['purchaseMode']='catalog';self.save()
        self.assert_rejected_unchanged(self.body())
    def test_catalog_intent_requires_existing_exact_key_and_family(self):
        (self.data/'products.json').write_text(json.dumps([{'key':'bouquet-test','family':'bouquet','sourceUrl':'https://fwith.co.kr/test'}]))
        self.policy['visualBindings'][0].update(purchaseMode='catalog',productKeys=['bouquet-test']);self.save()
        content='꽃다발 TEST ONLY. '+('Synthetic test input, not customer content. '*20)
        result=self.render(self.body(CONTENT=content));self.assertTrue(result['approvalVerified'])
        page=json.loads((self.data/'pages.json').read_text())[0]
        self.assertEqual(page['regionalProductFamilies'],['bouquet']);self.assertEqual(page['regionalProductKeys'],['bouquet-test'])

    def test_common_korean_claims_and_consultation_notices(self):
        for text in ['가격은 5만원입니다.', '가격은 5.5만 원입니다.', '오늘 도착을 보장합니다.', '전 지역 배송을 보장합니다.', '꽃 다발을 주문할 수 있습니다.', '꽃 바구니를 주문하세요.', '무료 배송입니다.']:
            with self.subTest(text=text):self.assert_rejected_unchanged(self.body(CONTENT=text+' Synthetic local fixture. '*30))
        for text in ['주소와 희망 시간을 알려 주시면 서비스 가능 여부를 상담합니다.', '배송 가능 여부와 추가비용은 상담 후 확인하세요.', '당일 배송을 보장하지 않습니다.', '도착을 보장할 수 없습니다.', '무료 배송이 아닙니다.']:
            with self.subTest(text=text):
                self.assertEqual(f.snap.regional_customer_claims(text),(set(),False))

    def test_empty_representative_membership_is_atomic(self):
        self.coverage['representatives'][0]['unitKeys']=[];self.save()
        self.assert_rejected_unchanged(self.body())
