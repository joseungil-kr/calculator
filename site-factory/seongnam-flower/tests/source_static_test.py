from pathlib import Path
from html import escape
import copy, importlib.util, unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('qa_static',ROOT/'scripts/qa_static.py')
qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)
sources=[{'name':'시설 <안내> & 위치','url':'https://example.org/map?a=1&b=2','type':'facility','verifiedAt':'2026-10-02'},
         {'name':'꽃이랑 공식몰','url':'https://fwith.co.kr/','type':'business','verifiedAt':'2026-10-02'}]
page={'url':'/test/','sources':sources,'source':sources[0]}
def cards(rows):
    return ''.join(f'<section class="source-card" data-source-type="{s["type"]}"><h2>{escape(s["name"])}</h2><a href="{escape(s["url"],quote=True)}" rel="nofollow" aria-label="{escape(s["name"],quote=True)} 확인">출처 확인 →</a><small>출처 유형: {qa.SOURCE_TYPE_LABELS[s["type"]]} · 확인일 <time datetime="{s["verifiedAt"]}">{s["verifiedAt"]}</time></small></section>' for s in rows)
class SourceGateTests(unittest.TestCase):
    def check(self,html,record=page):qa.check_rendered_sources(qa.Document(html),record)
    def test_full_ordered_array_passes(self):self.check(cards(sources))
    def test_escaped_names_and_query_strings_round_trip(self):
        doc=qa.Document(cards(sources));self.assertEqual(''.join(doc.source_cards[0]['name']),sources[0]['name']);self.check(cards(sources))
    def test_missing_later_source_fails_even_if_url_exists_elsewhere(self):
        with self.assertRaisesRegex(AssertionError,'count mismatch'):self.check(cards(sources[:1])+'<a href="https://fwith.co.kr/">주문</a>')
    def test_reordered_sources_fail(self):
        with self.assertRaises(AssertionError):self.check(cards(sources[::-1]))
    def test_each_wrong_field_fails(self):
        for field,value in [('name','다른 이름'),('url','https://example.org/wrong'),('type','official'),('verifiedAt','2026-10-01')]:
            wrong=copy.deepcopy(sources);wrong[1][field]=value
            with self.subTest(field=field),self.assertRaises(AssertionError):self.check(cards(wrong))
    def test_duplicate_or_extra_source_fails(self):
        with self.assertRaises(AssertionError):self.check(cards(sources+sources[:1]))
    def test_unsafe_source_fails(self):
        bad=copy.deepcopy(sources);bad[0]['url']='javascript:alert(1)'
        with self.assertRaises(AssertionError):self.check(cards(bad),{'url':'/test/','sources':bad})
    def test_missing_visible_type_or_date_fails(self):
        for html in [cards(sources).replace('출처 유형: 시설',''),cards(sources).replace('>2026-10-02</time>','></time>')]:
            with self.assertRaises(AssertionError):self.check(html)
    def test_legacy_primary_only_passes(self):self.check(cards(sources[:1]),{'url':'/legacy/','source':sources[0]})
    def test_exact_href_preserved_despite_root_slash_equivalence(self):
        self.assertEqual(qa.urlparse('https://fwith.co.kr').netloc,qa.urlparse('https://fwith.co.kr/').netloc)
        with self.assertRaises(AssertionError):self.check(cards(sources).replace('href="https://fwith.co.kr/"','href="https://fwith.co.kr"'))
if __name__=='__main__':unittest.main()
