import copy
import importlib.util
from pathlib import Path
import unittest

path=Path(__file__).resolve().parents[1]/'scripts/qa_static.py'
spec=importlib.util.spec_from_file_location('qa_static',path)
qa=importlib.util.module_from_spec(spec);spec.loader.exec_module(qa)
TRUTH={'onlineOrderUrl':'https://fwith.co.kr','phoneHref':'tel:18440644'}
PRODUCT={'key':'test-only','family':'funeral','name':'Synthetic product','price':100,
         'img':'/synthetic.jpg','orderUrl':'https://fwith.co.kr/shop/item.php?it_id=TEST',
         'sourceUrl':'https://fwith.co.kr/shop/item.php?it_id=TEST'}

def product_document(href):
    return qa.Document('<article data-product-key="test-only" data-product-family="funeral">'
        '<img src="/synthetic.jpg" alt="Synthetic product"><strong>100원</strong>'
        f'<a href="{href}">상품 확인·주문</a></article>'
        '<a class="btn" href="tel:18440644">전화주문</a>')

class OrderCtaTest(unittest.TestCase):
    def test_home_order_destination_preserves_catalog_source_metadata(self):
        before=copy.deepcopy(PRODUCT);doc=product_document(TRUTH['onlineOrderUrl'])
        qa.check_rendered_catalog(doc,'/test/',[PRODUCT],TRUTH['onlineOrderUrl'])
        qa.check_order_ctas(doc,'/test/',TRUTH)
        self.assertEqual(PRODUCT,before)

    def test_sku_product_card_destination_is_rejected(self):
        doc=product_document(PRODUCT['orderUrl'])
        with self.assertRaisesRegex(AssertionError,'product CTA mismatch'):
            qa.check_rendered_catalog(doc,'/test/',[PRODUCT],TRUTH['onlineOrderUrl'])

    def test_sku_footer_mobile_and_detail_action_destinations_are_rejected(self):
        for template in ['<footer><a href="{url}">온라인 주문</a></footer>',
                         '<div class="mobile-bar"><a href="{url}">온라인 주문</a></div>',
                         '<a class="btn dark" href="{url}">상품 확인·주문</a>']:
            with self.subTest(template=template):
                doc=qa.Document('<a class="btn" href="https://fwith.co.kr">온라인 주문</a>'
                    '<a class="btn" href="tel:18440644">전화주문</a>'+template.format(url=PRODUCT['orderUrl']))
                with self.assertRaisesRegex(AssertionError,'contradicts Business Truth'):
                    qa.check_order_ctas(doc,'/test/',TRUTH)

    def test_official_product_source_link_and_internal_navigation_are_preserved(self):
        doc=qa.Document('<a class="btn" href="https://fwith.co.kr">온라인 주문</a>'
            '<a class="btn" href="tel:18440644">전화주문</a>'
            '<a class="btn light" href="#deogyang">덕양구</a>'
            f'<section class="source-card"><a href="{PRODUCT["sourceUrl"]}" rel="nofollow">공식 상품 출처</a></section>')
        qa.check_order_ctas(doc,'/test/',TRUTH)
        self.assertIn(PRODUCT['sourceUrl'],doc.links)
        self.assertNotIn(PRODUCT['sourceUrl'],doc.cta_links)

    def test_wrong_phone_cta_is_rejected(self):
        doc=qa.Document('<a class="btn" href="https://fwith.co.kr">온라인 주문</a>'
            '<a class="btn" href="tel:18440644">전화주문</a>'
            '<footer><a href="tel:000">잘못된 전화주문</a></footer>')
        with self.assertRaisesRegex(AssertionError,'contradicts Business Truth'):
            qa.check_order_ctas(doc,'/test/',TRUTH)

if __name__=='__main__':unittest.main()
