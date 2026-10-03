import importlib.util
from pathlib import Path
import unittest

path=Path(__file__).resolve().parents[1]/'scripts/qa_static.py'
spec=importlib.util.spec_from_file_location('qa_static',path)
qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)

class RobotsPolicyTest(unittest.TestCase):
    def test_isolation_and_thin_hubs_are_distinct(self):
        arch={'hubs':[{'url':'/funeral/','children':1},{'url':'/regions/','children':2},{'url':'/gift/','children':3}]}
        for url in ['/','/funeral/','/regions/','/gift/','/regions/example/']:
            self.assertEqual(qa.expected_robots(False,url,arch),'noindex,nofollow,noarchive')
        self.assertEqual(qa.expected_robots(True,'/funeral/',arch),'noindex,follow')
        self.assertEqual(qa.expected_robots(True,'/regions/',arch),'noindex,follow')
        self.assertEqual(qa.expected_robots(True,'/gift/',arch),'index,follow')
        self.assertEqual(qa.expected_robots(True,'/regions/example/',arch),'index,follow')

    def test_fragment_targets_are_observed_in_rendered_html(self):
        doc=qa.Document('<section id="deogyang"><a href="/regions/#deogyang">구</a></section>')
        self.assertEqual(doc.ids,{'deogyang'})
        self.assertEqual(doc.links,['/regions/#deogyang'])

if __name__=='__main__':unittest.main()
