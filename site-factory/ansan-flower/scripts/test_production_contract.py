import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import textwrap
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlparse

WORKFLOW = Path(__file__).resolve().parents[3] / '.github/workflows/ansan-cloudflare-production-deploy.yml'
SOURCE = textwrap.dedent(WORKFLOW.read_text().split("python3 - <<'PY'\n", 1)[1].split('\n          PY', 1)[0])
REVISION = 'a' * 40
META = f'<meta name="site-factory-revision" content="{REVISION}"><meta name="robots" content="index,follow">'
BUSINESS = {'phone':'1844-0644','phoneHref':'tel:18440644','onlineOrderUrl':'https://fwith.co.kr'}
CTA = '<figure class="content-order-banner" data-order-banner="1"><figcaption>꽃 주문 안내</figcaption><a href="tel:18440644">전화 주문 1844-0644</a><a href="https://fwith.co.kr" rel="noopener">온라인 주문</a></figure>'

class Response(io.BytesIO):
    def __init__(self, status, content):
        super().__init__(content.encode())
        self.status = status

class ProductionContractTest(unittest.TestCase):
    def execute_gate(self, article=None, home=None, robots=None, status=200):
        documents = {'/':META if home is None else home, '/robots.txt':'User-agent: *\nAllow: /\n' if robots is None else robots, '/안산꽃배달/':META+CTA if article is None else article}
        def request(req, timeout):
            return Response(status, documents[unquote(urlparse(req.full_url).path)])
        cwd = Path.cwd()
        with tempfile.TemporaryDirectory(prefix='production-cta-contract-') as directory:
            root = Path(directory); (root/'src/data').mkdir(parents=True)
            (root/'src/data/business-truth.json').write_text(json.dumps(BUSINESS))
            try:
                os.chdir(root)
                with patch.dict(os.environ, {'EXPECTED_REVISION':REVISION}), patch('urllib.request.urlopen', request), patch('time.sleep'), contextlib.redirect_stdout(io.StringIO()):
                    exec(compile(SOURCE, str(WORKFLOW), 'exec'), {'__name__':'__main__'})
            finally:
                os.chdir(cwd)

    def test_current_accessible_cta_passes(self):
        self.execute_gate()

    def test_every_injected_cta_is_checked(self):
        self.execute_gate(article=META+CTA+CTA.replace('data-order-banner="1"','data-order-banner="2"'))
        with self.assertRaises(SystemExit):
            self.execute_gate(article=META+CTA+CTA.replace('tel:18440644','tel:00000000'))

    def test_contact_and_order_contract_failures(self):
        mutations = {
            'wrong phone':CTA.replace('tel:18440644','tel:18441234'),
            'wrong online URL':CTA.replace('https://fwith.co.kr','https://example.com'),
            'empty telephone label':CTA.replace('전화 주문 1844-0644',''),
            'empty online label':CTA.replace('>온라인 주문<','><'),
            'missing CTA':'<p>본문만 있습니다.</p>',
            'old image':CTA.replace('</figcaption>','</figcaption><img src="/images/banners/order-banner-01.webp" alt="주문">'),
            'lowest price claim':CTA.replace('꽃 주문 안내','근조화환 생화 최저가'),
        }
        for name, article in mutations.items():
            with self.subTest(name=name), self.assertRaises(SystemExit): self.execute_gate(article=META+article)

    def test_stale_representative_article_fails_even_with_current_home(self):
        with self.assertRaises(SystemExit): self.execute_gate(article=(META+CTA).replace(REVISION,'b'*40))

    def test_existing_home_robots_and_http_checks_still_fail_closed(self):
        for kwargs in [
            {'home':META.replace(REVISION,'b'*40)},
            {'home':META.replace('index,follow','noindex,nofollow')},
            {'article':(META+CTA).replace('index,follow','noindex,nofollow')},
            {'article':(META+CTA).replace('index,follow','noindex,follow')},
            {'robots':'User-agent: *\nDisallow: /\n'},
            {'status':404},
        ]:
            with self.subTest(kwargs=kwargs), self.assertRaises(SystemExit): self.execute_gate(**kwargs)

if __name__ == '__main__': unittest.main()
