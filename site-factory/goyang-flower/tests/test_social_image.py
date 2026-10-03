from pathlib import Path
import copy,importlib.util,json,unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('social_qa',ROOT/'scripts/qa_static.py');qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)
products=json.loads((ROOT/'src/data/products.json').read_text());proof=json.loads((ROOT/'src/data/social-image-provenance.json').read_text())
product=products[0];image='https://goyang.fwith.kr'+product['img'];record=proof['products'][0]
truth=json.loads((ROOT/'src/data/business-truth.json').read_text())
values={'og:image':image,'og:image:secure_url':image,'og:image:alt':'꽃이랑 '+product['name'],'og:image:type':record['image']['type'],
    'og:image:width':str(record['image']['dimensions'][0]),'og:image:height':str(record['image']['dimensions'][1]),'twitter:image':image,'twitter:image:alt':'꽃이랑 '+product['name']}
def html(values):return ''.join('<meta property="'+key+'" content="'+value+'">'for key,value in values.items())
class SocialGateTests(unittest.TestCase):
    def check(self,text):qa.check_social_image(qa.Document(text),'/', 'https://goyang.fwith.kr',products,proof,'꽃이랑')
    def test_valid_metadata_and_actual_assets(self):
        self.check(html(values));qa.check_social_provenance(ROOT,products,proof)
    def test_missing_and_duplicate_metadata(self):
        for key in values:
            with self.assertRaises(AssertionError):self.check(html({k:v for k,v in values.items() if k!=key}))
        with self.assertRaises(AssertionError):self.check(html(values)+html({'og:image':image}))
    def test_wrong_image_origin_or_missing_path(self):
        for bad in ['http://goyang.fwith.kr'+product['img'],'https://other.example'+product['img'],'https://goyang.fwith.kr/missing.jpg',image+'?crop=1']:
            with self.assertRaises(AssertionError):self.check(html({**values,'og:image':bad}))
    def test_wrong_alt_mime_dimensions_or_twitter(self):
        for key,value in [('og:image:alt',''),('twitter:image:alt','Other'),('og:image:type','image/png'),('og:image:width','1200'),('og:image:height','630'),('twitter:image','https://other.example/a.jpg')]:
            with self.assertRaises(AssertionError):self.check(html({**values,key:value}))
    def test_changed_asset_proof_fails(self):
        for key,value in [('dimensions',[1200,630]),('type','image/png'),('sha256','0'*64)]:
            altered=copy.deepcopy(proof);altered['products'][0]['image'][key]=value
            with self.assertRaises(AssertionError):qa.check_social_provenance(ROOT,products,altered)
    def test_empty_fake_duplicate_or_wrong_destination_banner_fails(self):
        banner='<aside data-order-banner="inline" aria-label="꽃이랑 고양 주문 안내"><a href="tel:18440644">전화</a><a href="https://fwith.co.kr">온라인</a></aside>'
        qa.check_purchase_banner(qa.Document(banner),'/',truth)
        for bad in ['',banner+banner,banner.replace('tel:18440644','tel:000'),banner.replace('https://fwith.co.kr','https://other.example'),banner.replace('꽃이랑','다른 브랜드'),'<aside data-order-banner="inline" aria-label="꽃이랑"><img src="fake-buttons.jpg"></aside>']:
            with self.assertRaises(AssertionError):qa.check_purchase_banner(qa.Document(bad),'/',truth)
if __name__=='__main__':unittest.main()
