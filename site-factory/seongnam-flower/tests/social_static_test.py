from pathlib import Path
import importlib.util,json,unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('qa_static',ROOT/'scripts/qa_static.py');qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)
products=json.loads((ROOT/'src/data/products.json').read_text());proof=json.loads((ROOT/'src/data/catalog-provenance.json').read_text());p=products[0]
image='https://seongnam.fwith.kr'+p['img']
values={'og:image':image,'og:image:secure_url':image,'og:image:alt':'꽃이랑 '+p['name'],'og:image:type':'image/jpeg','og:image:width':'500','og:image:height':'500','twitter:image':image,'twitter:image:alt':'꽃이랑 '+p['name']}
def html(values):return ''.join('<meta property="'+key+'" content="'+value+'">'for key,value in values.items())
class SocialGateTests(unittest.TestCase):
    def check(self,text):qa.check_social_image(qa.Document(text),'/', 'https://seongnam.fwith.kr',products,proof,'꽃이랑')
    def test_valid(self):self.check(html(values))
    def test_missing(self):
        for key in values:
            with self.assertRaises(AssertionError):self.check(html({k:v for k,v in values.items() if k!=key}))
    def test_duplicate(self):
        with self.assertRaises(AssertionError):self.check(html(values)+html({'og:image':image}))
    def test_wrong_image(self):
        for bad in ['http://seongnam.fwith.kr'+p['img'],'https://other.example'+p['img'],'https://seongnam.fwith.kr/missing.jpg',image+'?crop=1']:
            with self.assertRaises(AssertionError):self.check(html({**values,'og:image':bad}))
    def test_wrong_alt_type_dimensions_or_twitter(self):
        for key,value in [('og:image:alt',''),('twitter:image:alt','다른상품'),('og:image:type','image/png'),('og:image:width','1200'),('og:image:height','630'),('twitter:image','https://other.example/a.jpg')]:
            with self.assertRaises(AssertionError):self.check(html({**values,key:value}))
if __name__=='__main__':unittest.main()
