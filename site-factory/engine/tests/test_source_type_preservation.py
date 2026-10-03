"""Preserve independently reviewed source classification through every renderer."""
import json
import unittest
import test_engine as f
import test_regional_service as region_fixture
TYPES=['official','facility','education','professional','business','reference']

def emitted_sources(data,renderer):
    if renderer=='structured-json-v12':return json.loads((data/'pages.json').read_text())[0]['sources']
    file=next((data.parent/'content/articles').glob('*.md'))
    return json.loads(next(line[len('sources: '):] for line in file.read_text().splitlines() if line.startswith('sources: ')))

class SourceTypeTests(unittest.TestCase):
    bytes=f.SnapshotTests.bytes
    render=f.SnapshotTests.render
    assert_rejected_unchanged=f.SnapshotTests.assert_rejected_unchanged
    def setUp(self):f.SnapshotTests.setUp(self)
    def test_all_six_types_preserved_in_nonregional_markdown_and_structured(self):
        for renderer in ['markdown-v1','structured-json-v12']:
            with self.subTest(renderer=renderer):
                self.setUp();self.registry['sites']['test']['snapshotRenderer']=renderer
                body=f.payload(SOURCES='\n'.join('https://example.com/'+t for t in TYPES),**{'SOURCE-NAMES':'\n'.join('Test '+t for t in TYPES),'SOURCE-TYPES':'\n'.join(TYPES)})
                validated=f.snap.validate_content(f.snap.parse_payload(body));self.render(body)
                self.assertEqual(emitted_sources(self.root/'site/src/data',renderer),validated['sources'])
                self.assertEqual(self.render(body)['changedFiles'],[])
    def test_unknown_source_types_rejected_atomically(self):
        for renderer in ['markdown-v1','structured-json-v12']:
            for typ in ['unknown','vendor','Business','operator_confirmed','official,business']:
                with self.subTest(renderer=renderer,typ=typ):
                    self.setUp();self.registry['sites']['test']['snapshotRenderer']=renderer
                    self.assert_rejected_unchanged(f.payload(**{'SOURCE-TYPES':typ}))
    def test_absent_optional_types_still_default_to_reference(self):
        for renderer in ['markdown-v1','structured-json-v12']:
            self.setUp();self.registry['sites']['test']['snapshotRenderer']=renderer;self.render(f.payload(**{'SOURCE-TYPES':''}));self.assertEqual(emitted_sources(self.root/'site/src/data',renderer)[0]['type'],'reference')
    def test_existing_nonbusiness_payload_bytes_are_unchanged_against_baseline(self):
        # Existing old snapshots are not rewritten; this asserts new unchanged-type output too.
        for renderer in ['markdown-v1','structured-json-v12']:
            self.setUp();self.registry['sites']['test']['snapshotRenderer']=renderer;body=f.payload(**{'SOURCE-TYPES':'official'});self.render(body);before=self.bytes();self.assertEqual(self.render(body)['changedFiles'],[]);self.assertEqual(self.bytes(),before)

class RegionalSourceTypeTests(unittest.TestCase):
    bytes=f.SnapshotTests.bytes
    render=f.SnapshotTests.render
    assert_rejected_unchanged=f.SnapshotTests.assert_rejected_unchanged
    save=region_fixture.RegionalTests.save
    body=region_fixture.RegionalTests.body
    def setUp(self):region_fixture.RegionalTests.setUp(self)
    def test_all_six_types_preserved_in_both_regional_renderers(self):
        for renderer in ['markdown-v1','structured-json-v12']:
            self.setUp();self.registry['sites']['test']['snapshotRenderer']=renderer
            urls=['https://www.ansan.go.kr/stat/']+['https://example.com/'+t for t in TYPES[1:]]
            body=self.body(SOURCES='\n'.join(urls),**{'SOURCE-NAMES':'\n'.join('Test '+t for t in TYPES),'SOURCE-TYPES':'\n'.join(TYPES)})
            expected=f.snap.validate_content(f.snap.parse_payload(body))['sources'];self.render(body);self.assertEqual(emitted_sources(self.data,renderer),expected)
    def test_unknown_regional_source_type_is_rejected_before_writes(self):
        self.assert_rejected_unchanged(self.body().replace('official\nbusiness\n---END-SOURCE-TYPES---','official\nunknown\n---END-SOURCE-TYPES---'))
