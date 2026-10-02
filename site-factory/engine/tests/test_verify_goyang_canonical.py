from contextlib import redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.parse import urlsplit

ENGINE = Path(__file__).resolve().parents[1]
ROOT = ENGINE.parents[1]
sys.path.insert(0, str(ENGINE))
spec = importlib.util.spec_from_file_location("verify_goyang_canonical", ENGINE / "verify_goyang_canonical.py")
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)
ACCOUNT, ZONE, SECRET = "a" * 32, "b" * 32, "never-log-cookies-token-or-body"


class API:
    def __init__(self):
        self.calls = []
        self.zone = {"id": ZONE, "name": "fwith.kr", "status": "active", "account": {"id": ACCOUNT}}
        self.domains = [{"hostname": qa.HOSTNAME, "service": qa.WORKER, "environment": "production", "zone_id": ZONE}]
        self.fault = None

    def __call__(self, method, path):
        self.calls.append((method, path))
        if self.fault:
            raise self.fault
        if urlsplit(path).path == "/zones":
            return {"success": True, "result": [self.zone], "result_info": {"page": 1, "per_page": 50, "count": 1, "total_count": 1, "total_pages": 1}}
        if urlsplit(path).path == f"/accounts/{ACCOUNT}/workers/domains":
            return {"success": True, "result": self.domains}
        raise AssertionError("Unexpected API endpoint")


def html(path):
    snapshot = f'<article data-snapshot-id="{qa.SNAPSHOT}"></article>' if path == qa.DETAIL else ""
    link = f'<a href="{qa.DETAIL}">detail</a>' if path == qa.HUB else ""
    return (f'<meta name="robots" content="noindex,nofollow,noarchive">'
            f'<meta name="site-factory-revision" content="{qa.REVISION}">'
            f'<link rel="canonical" href="{qa.ORIGIN + path}">' + snapshot + link)


class Response(io.BytesIO):
    def __init__(self, url, text, header="noindex, nofollow, noarchive", status=200):
        super().__init__(text.encode())
        self.url, self.status, self.headers = url, status, {"X-Robots-Tag": header}

    def geturl(self):
        return self.url


class HTTP:
    def __init__(self):
        self.calls, self.changed, self.headers = [], {}, {}
        self.error_path = None
        self.redirect = None

    def __call__(self, request, timeout):
        url = request if isinstance(request, str) else request.full_url
        path = urlsplit(url).path
        self.calls.append((request, timeout))
        if path == self.error_path:
            raise HTTPError(url, 403, SECRET, {"Set-Cookie": SECRET, "CF-RAY": "1234567890abcdef-ICN", "Content-Type": "text/plain"}, io.BytesIO(SECRET.encode()))
        body = "User-agent: *\nDisallow: /\n" if path == "/robots.txt" else html(path)
        if path in ("/sitemap-index.xml", "/sitemap-0.xml"):
            tag = "sitemapindex" if path == "/sitemap-index.xml" else "urlset"
            urls = [qa.ORIGIN + "/sitemap-0.xml"] if tag == "sitemapindex" else [qa.ORIGIN + "/", qa.ORIGIN + qa.DETAIL]
            entry = 'sitemap' if tag == 'sitemapindex' else 'url'
            body = f'<{tag} xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<{entry}><loc>{url}</loc></{entry}>' for url in urls) + f'</{tag}>'
        return Response(self.redirect or url, self.changed.get(path, body), self.headers.get(path, "noindex"))


class CanonicalTests(unittest.TestCase):
    def test_binding_is_exact_read_only_and_uses_no_dns_or_routes(self):
        api = API()
        self.assertEqual(qa.check_binding(api, ACCOUNT)["state"], "goyang_binding_verified")
        self.assertEqual(len(api.calls), 2)
        self.assertTrue(all(method == "GET" for method, _ in api.calls))
        self.assertIn("hostname=goyang.fwith.kr", api.calls[1][1])
        self.assertNotIn(ACCOUNT, json.dumps(qa.check_binding(api, ACCOUNT)))
        self.assertNotIn(ZONE, json.dumps(qa.check_binding(api, ACCOUNT)))

    def test_wrong_missing_multiple_binding_stops(self):
        for rows in ([], [{}], [API().domains[0], API().domains[0]],
                     [{**API().domains[0], "service": SECRET}],
                     [{**API().domains[0], "zone_id": "c" * 32}],
                     [{**API().domains[0], "hostname": "other.fwith.kr"}],
                     [{**API().domains[0], "environment": "staging"}]):
            api = API()
            api.domains = rows
            with self.assertRaises(qa.PreflightError):
                qa.check_binding(api, ACCOUNT)

    def test_denied_binding_read_is_not_empty_success(self):
        api = API()
        api.fault = HTTPError("https://" + SECRET, 403, SECRET, {}, None)
        with self.assertRaises(qa.PreflightError) as raised:
            qa.check_binding(api, ACCOUNT)
        self.assertEqual(raised.exception.status, 403)
        self.assertNotIn(SECRET, str(raised.exception))

    def test_home_detail_hub_canonical_noindex_revision_and_snapshot(self):
        http = HTTP()
        self.assertEqual(qa.verify_http(http, lambda _: None)["state"], "goyang_canonical_noindex_verified")
        self.assertTrue(all(timeout == 15 for _, timeout in http.calls))
        for request, _ in http.calls:
            if not isinstance(request, str):
                self.assertEqual(request.get_header("User-agent"), "SiteFactory-StagingQA/3.0")
                self.assertIsNone(request.get_header("Authorization"))

    def test_workersdev_canonical_or_duplicate_canonical_fails_each_route(self):
        for path in ("/", qa.DETAIL, qa.HUB):
            for value in (html(path).replace(qa.ORIGIN, "https://goyang-flower-guide-qa.joseungil.workers.dev"),
                          html(path) + f'<link rel="canonical" href="{qa.ORIGIN + path}">'):
                http = HTTP()
                http.changed[path] = value
                self.assertEqual(qa.verify_http(http, lambda _: None)["state"], "goyang_canonical_qa_failed")

    def test_detail_snapshot_revision_meta_and_header_fail(self):
        for value in (html(qa.DETAIL).replace(qa.SNAPSHOT, "wrong-snapshot"),
                      html(qa.DETAIL).replace(qa.REVISION, "f" * 40),
                      html(qa.DETAIL).replace("noindex", "index")):
            http = HTTP()
            http.changed[qa.DETAIL] = value
            self.assertEqual(qa.verify_http(http, lambda _: None)["state"], "goyang_canonical_qa_failed")
        http = HTTP()
        http.headers[qa.DETAIL] = "index"
        self.assertEqual(qa.verify_http(http, lambda _: None)["state"], "goyang_canonical_qa_failed")

    def test_robots_gate_and_base_retries_are_reused(self):
        http, delays, stdout = HTTP(), [], io.StringIO()
        http.changed["/robots.txt"] = "User-agent: *\nAllow: /\n"
        with redirect_stdout(stdout):
            result = qa.verify_http(http, delays.append)
        self.assertEqual(result["state"], "preview_verification_failed")
        self.assertEqual(result["attempts"], 12)
        self.assertEqual(delays, [5] * 11)

    def test_exact_sitemap_index_child_and_noindex_headers_pass(self):
        http = HTTP()
        result = qa.verify_http(http, lambda _: None)
        self.assertEqual(result["sitemap"]["urls"], sorted([qa.ORIGIN + "/", qa.ORIGIN + qa.DETAIL]))
        self.assertTrue(result["sitemap"]["noindexHeaderVerified"])
        self.assertEqual([urlsplit(request.full_url).path for request, _ in http.calls[-2:]], ["/sitemap-index.xml", "/sitemap-0.xml"])

    def test_sitemap_foreign_hosts_thin_hubs_duplicates_or_wrong_child_fail(self):
        for path, tag, urls in (
            ("/sitemap-index.xml", "sitemapindex", [qa.ORIGIN + "/other.xml"]),
            ("/sitemap-index.xml", "sitemapindex", ["https://other.fwith.kr/sitemap-0.xml"]),
            ("/sitemap-0.xml", "urlset", [qa.ORIGIN + "/", qa.ORIGIN + qa.DETAIL, qa.ORIGIN + qa.HUB]),
            ("/sitemap-0.xml", "urlset", [qa.ORIGIN + "/", "https://goyang-flower-guide-qa.joseungil.workers.dev" + qa.DETAIL]),
            ("/sitemap-0.xml", "urlset", [qa.ORIGIN + "/", qa.ORIGIN + "/", qa.ORIGIN + qa.DETAIL]),
            ("/sitemap-0.xml", "urlset", [qa.ORIGIN + "/"]),
        ):
            with self.subTest(path=path, urls=urls):
                http = HTTP()
                entry = 'sitemap' if tag == 'sitemapindex' else 'url'
                http.changed[path] = f'<{tag} xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<{entry}><loc>{url}</loc></{entry}>' for url in urls) + f'</{tag}>'
                self.assertEqual(qa.verify_http(http, lambda _: None)["state"], "goyang_canonical_qa_failed")

    def test_sitemap_http_failure_has_safe_exact_path_diagnostics(self):
        for path in ("/sitemap-index.xml", "/sitemap-0.xml"):
            http = HTTP()
            http.error_path = path
            result = qa.verify_http(http, lambda _: None)
            self.assertEqual(result["lastFailure"]["url"], qa.ORIGIN + path)
            self.assertEqual(result["lastFailure"]["status"], 403)
            self.assertNotIn(SECRET, json.dumps(result))

    def test_sitemap_malformed_unsafe_or_indexable_response_fails(self):
        for text in ('not xml', '<!DOCTYPE xml><urlset/>', 'x' * (1024 * 1024 + 1)):
            http = HTTP()
            http.changed["/sitemap-0.xml"] = text
            self.assertEqual(qa.verify_http(http, lambda _: None)["state"], "goyang_canonical_qa_failed")
        http = HTTP()
        http.headers["/sitemap-0.xml"] = "index"
        self.assertEqual(qa.verify_http(http, lambda _: None)["state"], "goyang_canonical_qa_failed")

    def test_hub_link_and_https_redirect_fail(self):
        http = HTTP()
        http.changed[qa.HUB] = html(qa.HUB).replace(qa.DETAIL, "/wrong/")
        self.assertEqual(qa.verify_http(http, lambda _: None)["state"], "goyang_canonical_qa_failed")
        http = HTTP()
        http.redirect = "https://goyang-flower-guide-qa.joseungil.workers.dev/"
        self.assertEqual(qa.verify_http(http, lambda _: None)["state"], "goyang_canonical_qa_failed")

    def test_http403_report_excludes_body_cookies_and_tokens(self):
        http = HTTP()
        http.error_path = qa.DETAIL
        result = qa.verify_http(http, lambda _: None)
        self.assertEqual(result["lastFailure"]["status"], 403)
        self.assertEqual(result["lastFailure"]["url"], qa.ORIGIN + qa.DETAIL)
        self.assertNotIn(SECRET, json.dumps(result))

    def test_fixed_workflow_reuses_config_and_commands_without_routes_flags(self):
        text = (ROOT / ".github/workflows/goyang-canonical-noindex-deploy.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("SITE_URL: https://goyang.fwith.kr", text)
        self.assertIn("SITE_INDEXABLE: 'false'", text)
        self.assertIn("ref: " + qa.REVISION, text)
        self.assertIn("27a45b8e99151c34b966f0a59a96110b91395fad", text)
        self.assertIn("git -C target archive " + qa.REVISION + ":site-factory/goyang-flower | tar -xf - -C goyang-build", text)
        self.assertEqual(text.count("working-directory: goyang-build"), 2)
        self.assertIn("npx --yes wrangler@4.146.0 deploy -c wrangler.staging.jsonc", text)
        self.assertIn("staging['workers_dev'] is True", text)
        self.assertIn("'route' not in staging and 'routes' not in staging", text)
        self.assertIn("site-staging-${{ github.repository }}", text)
        self.assertEqual(text.count("verify_goyang_canonical.py binding"), 2)
        for forbidden in ("wrangler@latest", "custom_domain", "--route", "--domain", "dns_records", "workers/routes", "schedule:", "issues: write"):
            self.assertNotIn(forbidden, text)
        source = text.partition("python3 - <<'PYTHON'\n")[2].partition("\n          PYTHON")[0]
        compile("\n".join(line[10:] for line in source.splitlines()), "fixed-source-gate", "exec")

    def test_legacy_goyang_guard_does_not_change_suwon_path(self):
        text = (ROOT / ".github/workflows/site-staging-deploy.yml").read_text(encoding="utf-8")
        block = re.search(r"- name: Resolve isolated preview target.*?python3 - <<'PYTHON'\n(.*?)\n          PYTHON", text, re.S).group(1)
        code = "\n".join(line[10:] for line in block.splitlines())
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            (temp / "control/.github").mkdir(parents=True)
            (temp / "control/.github/site-factory-sites.json").write_bytes((ROOT / ".github/site-factory-sites.json").read_bytes())
            previous = Path.cwd()
            try:
                os.chdir(temp)
                with patch.dict(os.environ, {"SITE_KEY": "goyang-flower-v2", "REVISION": qa.REVISION,
                                             "ISSUE_BODY": "", "GITHUB_REPOSITORY": "joseungil-kr/fwith-site-factory", "GITHUB_OUTPUT": str(temp / "outputs")}, clear=True):
                    with self.assertRaisesRegex(SystemExit, "legacy staging would revert"):
                        exec(code, {})
                    os.environ["SITE_KEY"] = "suwon-flower-test"
                    exec(code, {})
                    self.assertIn("url=https://suwon-flower-guide-qa.joseungil.workers.dev", (temp / "outputs").read_text(encoding="utf-8"))
            finally:
                os.chdir(previous)


if __name__ == "__main__":
    unittest.main()
