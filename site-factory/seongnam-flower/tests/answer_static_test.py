from pathlib import Path
import importlib.util, unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('qa_static',ROOT/'scripts/qa_static.py')
qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)
page={'url':'/test/','firstAnswer':'확인 후 주문하세요.','contentMarkdown':'확인 후 주문하세요.\n\n## 주문 정보\n\n전화로 확인하세요.'}
expected=[{'type':'h2','text':'주문 정보'},{'type':'p','text':'전화로 확인하세요.'}]
hero='<section class="detail-hero"><div><h1>안내</h1><p>확인 후 주문하세요.</p></div></section>'
body='<div class="content-card markdown-content"><h2>주문 정보</h2><p>전화로 확인하세요.</p></div>'
class AnswerGateTests(unittest.TestCase):
    def check(self,html):qa.check_rendered_answer(qa.Document(html),page,expected)
    def test_single_answer_passes(self):self.check(hero+body)
    def test_duplicate_body_lead_fails(self):
        with self.assertRaises(AssertionError):self.check(hero+body.replace('<h2>','<p>확인 후 주문하세요.</p><h2>'))
    def test_removing_hero_fails(self):
        with self.assertRaises(AssertionError):self.check(body)
    def test_changed_hero_fails(self):
        with self.assertRaises(AssertionError):self.check(hero.replace('확인 후 주문하세요.','바뀐 안내')+body)
    def test_missing_or_changed_later_paragraph_fails(self):
        for html in [body.replace('<p>전화로 확인하세요.</p>',''),body.replace('전화로','온라인으로')]:
            with self.assertRaises(AssertionError):self.check(hero+html)
    def test_block_order_or_type_change_fails(self):
        for html in [body.replace('<h2>주문 정보</h2><p>전화로 확인하세요.</p>','<p>전화로 확인하세요.</p><h2>주문 정보</h2>'),body.replace('h2','h3')]:
            with self.assertRaises(AssertionError):self.check(hero+html)
    def test_formatted_later_blocks_are_parsed_without_losing_text(self):
        self.check(hero+body.replace('전화로 확인하세요.','<a href="tel:18440644">전화로</a> <strong>확인하세요.</strong>'))
    def test_outside_markdown_paragraphs_are_not_body_blocks(self):
        self.check(hero+body+'<section class="source-card"><h2>출처</h2><p>출처 안내</p></section>')
if __name__=='__main__':unittest.main()
