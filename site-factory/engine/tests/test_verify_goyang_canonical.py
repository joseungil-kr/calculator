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


class CapabilitiesAPI(API):
    def __init__(self):
        super().__init__()
        self.subdomain={"enabled":True,"previews_enabled":True,"private":SECRET}
        self.deployment_id="11111111-2222-4333-8444-555555555555"
        self.deployments={"deployments":[{"id":self.deployment_id,"author_email":SECRET,"annotations":{"secret":SECRET}}]}
        self.info={"page":1,"per_page":1,"count":1,"total_count":10,"total_pages":10}
        self.endpoint_fault=None

    def __call__(self,method,path):
        if "/workers/scripts/" not in path:return super().__call__(method,path)
        self.calls.append((method,path))
        if self.endpoint_fault:raise self.endpoint_fault
        if path==f"/accounts/{ACCOUNT}/workers/scripts/{qa.WORKER}/subdomain":return {"success":True,"result":self.subdomain}
        if path==f"/accounts/{ACCOUNT}/workers/scripts/{qa.WORKER}/deployments?page=1&per_page=1":return {"success":True,"result":self.deployments,"result_info":self.info}
        raise AssertionError("Unexpected capability endpoint")


class CapabilityTests(unittest.TestCase):
    def test_get_only_exact_target_filters_everything_except_observed_flags_and_id(self):
        for enabled in (True,False):
            api=CapabilitiesAPI();api.subdomain['previews_enabled']=enabled
            result=qa.check_preview_capabilities(api,ACCOUNT)
            self.assertEqual(result,{"state":"goyang_preview_capabilities_observed","hostname":qa.HOSTNAME,
                "worker":qa.WORKER,"previews_enabled":enabled,"deployment_id":api.deployment_id,"mutations_performed":False})
            self.assertEqual(len(api.calls),4);self.assertTrue(all(method=='GET' for method,_ in api.calls))
            for secret in (SECRET,ACCOUNT,ZONE,'author_email','annotations','private'):
                self.assertNotIn(secret,json.dumps(result))

    def test_missing_unknown_or_non_boolean_flag_is_never_false(self):
        for value in (None,0,1,'false',{},[]):
            api=CapabilitiesAPI();api.subdomain['previews_enabled']=value
            with self.assertRaises(qa.PreflightError):qa.check_preview_capabilities(api,ACCOUNT)
        api=CapabilitiesAPI();del api.subdomain['previews_enabled']
        with self.assertRaises(qa.PreflightError):qa.check_preview_capabilities(api,ACCOUNT)

    def test_missing_invalid_or_non_first_deployment_blocks(self):
        for rows in (None,[],[{}],[{'id':SECRET}],[{'id':None}],[{'id':'a'*32}],[{'id':'11111111-2222-4333-8444-555555555555'}]*2):
            api=CapabilitiesAPI();api.deployments['deployments']=rows
            with self.assertRaises(qa.PreflightError):qa.check_preview_capabilities(api,ACCOUNT)
        for info in ({'page':2},{'page':True},{'count':0},{'per_page':50}):
            api=CapabilitiesAPI();api.info=info
            with self.assertRaises(qa.PreflightError):qa.check_preview_capabilities(api,ACCOUNT)

    def test_401_403_redirect_and_unknown_failures_never_infer_disabled(self):
        for fault in (HTTPError('https://'+SECRET,401,SECRET,{'Set-Cookie':SECRET},io.BytesIO(SECRET.encode())),
                      HTTPError('https://'+SECRET,403,SECRET,{'Set-Cookie':SECRET},io.BytesIO(SECRET.encode())),
                      HTTPError('https://'+SECRET,302,SECRET,{'Location':'https://'+SECRET},None),RuntimeError(SECRET)):
            api=CapabilitiesAPI();api.endpoint_fault=fault
            with self.assertRaises(qa.PreflightError) as error:qa.check_preview_capabilities(api,ACCOUNT)
            self.assertNotIn(SECRET,str(error.exception));self.assertEqual(len(api.calls),3)

    def test_malformed_api_body_and_api_failure_are_blocked_without_raw_messages(self):
        api=CapabilitiesAPI()
        for payload in ({'success':False,'result':{'previews_enabled':False},'errors':[SECRET]},
                        {'success':True,'result':{'enabled':True,'previews_enabled':False},'errors':[SECRET]},
                        {'success':True,'result':[]},None):
            def transport(method,path):
                if '/workers/scripts/' in path:return payload
                return api(method,path)
            with self.assertRaises(qa.PreflightError) as error:qa.check_preview_capabilities(transport,ACCOUNT)
            self.assertNotIn(SECRET,str(error.exception))

    def test_cli_reports_known_false_distinct_from_blocked_unknown_and_never_logs_credentials(self):
        for denied in (False,True):
            api=CapabilitiesAPI();api.subdomain['previews_enabled']=False
            if denied:api.endpoint_fault=HTTPError('https://'+SECRET,403,SECRET,{'Set-Cookie':SECRET},None)
            class Opener:
                def open(self,request,timeout):
                    self_method=request.get_method();self_path=urlsplit(request.full_url).path.removeprefix('/client/v4')
                    if urlsplit(request.full_url).query:self_path+='?'+urlsplit(request.full_url).query
                    self_payload=api(self_method,self_path)
                    return Response(request.full_url,json.dumps(self_payload),header='')
            with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{'CLOUDFLARE_API_TOKEN':SECRET,'CLOUDFLARE_ACCOUNT_ID':ACCOUNT},clear=True),patch.object(qa,'build_opener',return_value=Opener()):
                report=Path(directory)/'report.json';stdout=io.StringIO()
                with redirect_stdout(stdout):code=qa.main(['preview-capabilities','--report',str(report)])
                result=json.loads(report.read_text());self.assertNotIn(SECRET,report.read_text()+stdout.getvalue())
                self.assertNotIn(ACCOUNT,report.read_text()+stdout.getvalue())
                self.assertEqual(code,1 if denied else 0)
                if denied:
                    self.assertEqual(result['state'],'goyang_preview_capabilities_blocked')
                    self.assertEqual(result['httpStatus'],403);self.assertIsNone(result['previews_enabled']);self.assertIsNone(result['deployment_id'])
                else:self.assertIs(result['previews_enabled'],False)

    def test_read_only_workflow_has_no_upload_deploy_or_shared_deployment_lock(self):
        text=(ROOT/'.github/workflows/goyang-staging-qa.yml').read_text()
        self.assertIn("permissions:\n  contents: read",text)
        self.assertIn("github.ref == 'refs/heads/main'",text)
        self.assertIn("[GOYANG-PREVIEW-INSPECT]",text)
        self.assertIn("['admin', 'maintain', 'write']",text)
        self.assertLess(text.index('Authorize repository writer'),text.index('CLOUDFLARE_API_TOKEN'))
        self.assertLess(text.index('Require exact registered Goyang inspection scope'),text.index('CLOUDFLARE_API_TOKEN'))
        self.assertIn('verify_goyang_canonical.py http --report goyang-preview-verification.json',text)
        self.assertIn('verify_goyang_canonical.py preview-capabilities --report goyang-preview-capabilities.json',text)
        for forbidden in ('npx ','wrangler@','versions upload','domain_attach','dns_records','workers/routes','issues: write','schedule:','concurrency:'):
            self.assertNotIn(forbidden,text)

    def test_inspection_scope_requires_registered_identity_review_and_unique_headers(self):
        text=(ROOT/'.github/workflows/goyang-staging-qa.yml').read_text()
        code=re.search(r"python3 - <<'PYTHON'\n(.*?)\n          PYTHON",text,re.S).group(1)
        code='\n'.join(line[10:] for line in code.splitlines());compile(code,'inspection-scope','exec')
        registry=json.loads((ROOT/'.github/site-factory-sites.json').read_text())
        revision=registry['sites']['goyang-flower-v2']['coverageDeployment']['previewRevision']
        scope='goyang-flower-v2-dong-coverage-20261003'
        body=f'SITE_KEY: goyang-flower-v2\nLAUNCH_KEY: {scope}\nSCOPE_KEY: {scope}\nEXPECTED_REVISION: {revision}'
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'control/.github';path.mkdir(parents=True);(path/'site-factory-sites.json').write_text(json.dumps(registry));cwd=Path.cwd()
            try:
                os.chdir(directory)
                env={'SCOPE_KEY':'','REVISION':'','ISSUE_BODY':body,'EVENT_NAME':'issues','GITHUB_REPOSITORY':'joseungil-kr/fwith-site-factory'}
                with patch.dict(os.environ,env,clear=True),redirect_stdout(io.StringIO()):
                    exec(code,{})
                    for bad in [body.replace('SITE_KEY: goyang','SITE_KEY: seongnam'),body.replace(scope,'other'),body.replace(revision,'f'*40),body+'\nSCOPE_KEY: '+scope]:
                        os.environ['ISSUE_BODY']=bad
                        with self.assertRaises(SystemExit):exec(code,{})
                    os.environ['ISSUE_BODY']=body;os.environ['GITHUB_REPOSITORY']='other/repo'
                    with self.assertRaises(SystemExit):exec(code,{})
            finally:os.chdir(cwd)


class UploadPreflightAPI(CapabilitiesAPI):
    def __init__(self):
        super().__init__();self.service={'default_environment':{'script':{'tags':[]}}};self.settings={'bindings':[],'observability':{'enabled':False}}
    def __call__(self,method,path):
        if path==f'/accounts/{ACCOUNT}/workers/services/{qa.WORKER}':
            self.calls.append((method,path));return {'success':True,'result':self.service}
        if path==f'/accounts/{ACCOUNT}/workers/scripts/{qa.WORKER}/settings':
            self.calls.append((method,path));return {'success':True,'result':self.settings}
        return super().__call__(method,path)


class UploadPreflightTests(unittest.TestCase):
    def test_get_only_preflight_proves_no_tag_patch_or_shared_runtime_resources(self):
        api=UploadPreflightAPI();result=qa.check_version_upload_preflight(api,ACCOUNT)
        self.assertEqual(len(api.calls),6);self.assertTrue(all(method=='GET' for method,_ in api.calls))
        self.assertTrue(result['assets_only']);self.assertTrue(result['grouping_tags_unchanged'])
        self.assertEqual(qa.compare_upload_boundary(result,result)['state'],'goyang_version_upload_boundary_preserved')
        self.assertNotIn(SECRET,json.dumps(result));self.assertNotIn('observability',json.dumps(result))

    def test_tags_bindings_unknown_or_disabled_block_before_upload(self):
        for tags in (['cf:service:old'],['ordinary-tag'],{},'unknown'):
            api=UploadPreflightAPI();api.service['default_environment']['script']['tags']=tags
            with self.assertRaises(qa.PreflightError):qa.check_version_upload_preflight(api,ACCOUNT)
        for bindings in (None,{},[{'type':'kv_namespace','name':'SECRET'}],[{'type':'secret_text','name':'SECRET'}]):
            api=UploadPreflightAPI();api.settings['bindings']=bindings
            with self.assertRaises(qa.PreflightError):qa.check_version_upload_preflight(api,ACCOUNT)
        api=UploadPreflightAPI();del api.service['default_environment']['script']['tags']
        with self.assertRaises(qa.PreflightError):qa.check_version_upload_preflight(api,ACCOUNT)
        api=UploadPreflightAPI();api.subdomain['previews_enabled']=False
        with self.assertRaises(qa.PreflightError):qa.check_version_upload_preflight(api,ACCOUNT)
        self.assertEqual(len(api.calls),4)

    def test_changed_active_deployment_binding_settings_or_unknown_results_never_pass(self):
        before=qa.check_version_upload_preflight(UploadPreflightAPI(),ACCOUNT)
        for key,value in [('deployment_id','new'),('hostname','other'),('worker','other'),('settings_sha256','a'*64),('previews_enabled',False),('state','failed')]:
            with self.assertRaises(qa.PreflightError):qa.compare_upload_boundary(before,{**before,key:value})
        with self.assertRaises(qa.PreflightError):qa.compare_upload_boundary(before,{})


if __name__ == "__main__":
    unittest.main()
