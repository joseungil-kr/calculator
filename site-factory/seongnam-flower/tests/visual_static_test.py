"""Both visual paths stay strict; these HTML fixtures are not publish approvals."""
from pathlib import Path
import copy, importlib.util, json, unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('qa_static',ROOT/'scripts/qa_static.py')
qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)
products=json.loads((ROOT/'src/data/products.json').read_text())
asset=json.loads((ROOT/'src/data/editorial-assets.json').read_text())['openingWreath']
page={'pageType':'business-opening','url':'/business/local-visual-test/','visualIntent':'congrats_wreath','assetSlot':'REAL_PROOF'}
real_html='<div class="detail-product" data-product-family="congrats" data-product-key="congrats-basic"><img src="/images/products/seongnam-official-20261002/C200.jpg" alt="축하 3단 화환" width="540" height="540"><small>꽃이랑 공식 상품 이미지</small><small>사진 속 리본 문구는 예시입니다.</small></div>'
art_html=f'<figure class="detail-product editorial-hero"><img src="{asset["img"]}" alt="설명용" width="1000" height="1000"><figcaption>{asset["caption"]}</figcaption></figure>'

class VisualGateTests(unittest.TestCase):
    def check(self,html,record=page,catalog=products):
        qa.check_opening_visual(qa.Document(html),record,catalog,ROOT)
    def test_verified_real_product_passes(self):self.check(real_html)
    def test_editorial_cannot_replace_real_proof(self):
        with self.assertRaises(AssertionError):self.check(art_html)
    def test_ribbon_disclosure_is_required_on_hero(self):
        with self.assertRaises(AssertionError):self.check(real_html.replace('사진 속 리본 문구는 예시입니다.',''))
    def test_original_aspect_ratio_is_required(self):
        with self.assertRaises(AssertionError):self.check(real_html.replace('height="540"','height="300"'))
    def test_real_product_cannot_be_mislabeled_as_wide(self):
        with self.assertRaises(AssertionError):self.check(real_html,{**page,'assetSlot':'HERO_WIDE'})
    def test_official_sku_is_required(self):
        bad=copy.deepcopy(products)
        next(p for p in bad if p['key']=='congrats-basic')['officialSku']='UNVERIFIED'
        with self.assertRaises(AssertionError):self.check(real_html,catalog=bad)
    def test_modified_asset_bytes_are_rejected(self):
        with patch.object(qa.hashlib,'sha256') as digest:
            digest.return_value.hexdigest.return_value='0'*64
            with self.assertRaisesRegex(AssertionError,'image hash mismatch'):self.check(real_html)
    def test_legacy_editorial_caption_still_passes(self):
        self.check(art_html,{'pageType':'business-opening','url':page['url']})
    def test_legacy_editorial_caption_cannot_be_removed(self):
        with self.assertRaises(AssertionError):self.check(art_html.replace(asset['caption'],''),{'pageType':'business-opening','url':page['url']})

if __name__=='__main__':unittest.main()
