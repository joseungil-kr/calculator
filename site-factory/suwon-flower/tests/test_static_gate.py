"""Run after production build: SITE_INDEXABLE=true python3 -m unittest discover -s tests."""
import importlib.util, tempfile, shutil, os, unittest, json, re
from pathlib import Path
spec=importlib.util.spec_from_file_location('gate',Path(__file__).parents[1]/'scripts/qa_static.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
class StaticGateTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  for folder in ['dist','src/data']:shutil.copytree(folder,self.root/folder)
  (self.root/'public').symlink_to(Path('public').resolve(),target_is_directory=True)
 def tearDown(self):self.temp.cleanup()
 def mutate(self,find,replace):
  f=self.root/'dist/index.html';s=f.read_text();assert find in s;f.write_text(s.replace(find,replace,1))
 def test_duplicate_h1_rejected(self):
  self.mutate('</h1>','</h1><h1>Second</h1>')
  with self.assertRaisesRegex(AssertionError,'one H1'):gate.check(self.root)
 def test_internal_404_rejected(self):
  self.mutate('href="/funeral/"','href="/missing/"')
  with self.assertRaisesRegex(AssertionError,'Broken internal'):gate.check(self.root)
 def test_canonical_drift_rejected(self):
  self.mutate('rel="canonical" href="https://suwon.fwith.kr/"','rel="canonical" href="https://wrong.example/"')
  with self.assertRaisesRegex(AssertionError,'Canonical'):gate.check(self.root)
 def test_production_noindex_rejected(self):
  self.mutate('content="index,follow"','content="noindex,follow"')
  with self.assertRaisesRegex(AssertionError,'Wrong robots'):gate.check(self.root)
 def test_rendered_internal_catalog_copy_rejected(self):
  self.mutate('</h1>','</h1><p>실제 Product Catalog 기준으로</p>')
  with self.assertRaisesRegex(AssertionError,'customer copy'):gate.check(self.root)
 def page_file(self,page_type=None,intent=None):
  pages=json.loads((self.root/'src/data/pages.json').read_text())
  p=next(p for p in pages if (page_type is None or p['pageType']==page_type) and (intent is None or p['visualIntent']==intent))
  return self.root/'dist'/p['url'].strip('/')/'index.html'
 def replace_next_target(self,file,target):
  text=file.read_text();text,n=re.subn(r'(data-journey="next-step"[^>]*>.*?<a[^>]*href=")[^"]+',lambda m:m[1]+target,text,count=1,flags=re.S)
  assert n==1;file.write_text(text)
 def test_hospital_next_step_cannot_be_wreath_order(self):
  self.replace_next_target(self.page_file('hospital-visit'),'/order/suwon-wreath-order/')
  with self.assertRaisesRegex(AssertionError,'Gift intent leads to wreath'):gate.check(self.root)
 def test_sibling_school_is_reading_not_purchase_step(self):
  self.replace_next_target(self.page_file('school-event'),'/school/skku-natural-campus-graduation-flowers/')
  with self.assertRaisesRegex(AssertionError,'Invalid next-step destination'):gate.check(self.root)
 def test_home_cannot_revert_to_all_wreath_images(self):
  file=self.root/'dist/index.html';text=file.read_text().replace('data-product-family="bouquet"','data-product-family="congrats"').replace('data-product-family="basket"','data-product-family="congrats"');file.write_text(text)
  with self.assertRaisesRegex(AssertionError,'Home hero omits|catalog family mismatch'):gate.check(self.root)
 def test_real_product_photo_cannot_be_reassigned_to_another_sku(self):
  # Mutate the visible product, not the new social-image metadata.
  self.mutate('src="/images/products/bouquet-happiness.jpg"','src="/images/products/congrats-basic.jpg"')
  with self.assertRaisesRegex(AssertionError,'catalog image mismatch'):gate.check(self.root)
 def test_rendered_sku_price_cannot_drift_from_catalog(self):
  file=self.root/'dist/index.html';text=file.read_text();assert '50,000원' in text;file.write_text(text.replace('50,000원','49,000원'))
  with self.assertRaisesRegex(AssertionError,'catalog price mismatch'):gate.check(self.root)
 def test_performance_body_cannot_order_unrelated_wreath(self):
  file=self.page_file(intent='performance_venue');file.write_text(file.read_text().replace('</article>','<p>축하화환 상품을 선택해 주문하세요.</p></article>',1))
  with self.assertRaisesRegex(AssertionError,'Performance.*mismatch'):gate.check(self.root)
 def test_message_examples_must_actually_render(self):
  file=self.page_file('message-guide');text=file.read_text();text,n=re.subn(r'“[^”]+”','문구 예시',text)
  assert n>0;file.write_text(text)
  with self.assertRaisesRegex(AssertionError,'Missing rendered .* examples'):gate.check(self.root)
if __name__=='__main__':unittest.main()
