"""Run after production build: SITE_INDEXABLE=true python3 -m unittest discover -s tests."""
import importlib.util, tempfile, shutil, os, unittest
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
if __name__=='__main__':unittest.main()
