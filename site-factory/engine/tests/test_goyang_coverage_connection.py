"""Disposable synthetic contract fixtures; never content/approval or release evidence."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ENGINE = Path(__file__).resolve().parents[1]
ROOT = ENGINE.parents[1]
sys.path.insert(0, str(ENGINE))
spec = importlib.util.spec_from_file_location('coverage_live', ENGINE / 'verify_live.py')
qa = importlib.util.module_from_spec(spec); spec.loader.exec_module(qa)
REVISION = 'a' * 40
REPO = 'joseungil-kr/fwith-site-factory'
EVIDENCE = 'https://github.com/joseungil-kr/fwith-site-factory/issues/1#issuecomment-1'


def site(phase='preview'):
    value = copy.deepcopy(json.loads((ROOT / '.github/site-factory-sites.json').read_text())['sites'][qa.GOYANG_SITE])
    value['coverageDeployment'].update(enabled=True, previewRevision=REVISION,
        previewManifestSha256='b'*64, previewApprovalEvidenceUrl=EVIDENCE, productionManifestSha256='b'*64)
    if phase == 'production':
        value.update(productionEnabled=True, launchMode='live', approvedRevision=REVISION, approvalEvidenceUrl=EVIDENCE)
    return value


class ResolverTests(unittest.TestCase):
    def resolve(self, value, phase='preview', **kw):
        args = dict(repository=REPO, revision=REVISION, launch_key=qa.GOYANG_SCOPE, scope_key=qa.GOYANG_SCOPE, phase=phase)
        args.update(kw)
        return qa.resolve_goyang_coverage_target(value, **args)

    def test_committed_registry_is_closed_and_preserves_original_gates(self):
        value = json.loads((ROOT / '.github/site-factory-sites.json').read_text())['sites'][qa.GOYANG_SITE]
        self.assertFalse(value['productionEnabled']); self.assertTrue(value['growthPaused'])
        self.assertFalse(value['autoDeploySnapshots']); self.assertFalse(value['coverageDeployment']['enabled'])
        self.assertEqual(value['approvedRevision'], '')
        with self.assertRaisesRegex(ValueError, 'closed'): self.resolve(value)

    def test_exact_preview_and_production_select_existing_bound_worker_and_canonical(self):
        for phase in ('preview', 'production'):
            resolved = self.resolve(site(phase), phase)
            self.assertEqual(resolved['worker'], 'goyang-flower-guide-qa')
            self.assertEqual(resolved['url'], qa.GOYANG_ORIGIN)
            self.assertEqual(resolved['config'], 'wrangler.staging.jsonc')
            self.assertEqual(resolved['isolated'], 'true')

    def test_missing_wrong_canary_scope_revision_repository_or_evidence_fail(self):
        for change in ({'scope_key':''}, {'launch_key':'goyang-flower-v2-launch'}, {'scope_key':'other'},
                       {'revision':'c'*40}, {'repository':'other/repo'}, {'phase':'automatic'}):
            with self.subTest(change=change), self.assertRaises(ValueError): self.resolve(site(), **change)
        for key, value in [('previewApprovalEvidenceUrl','https://attacker.example/review'),
                           ('previewApprovalEvidenceUrl','https://github.com/other/repo/issues/1'),
                           ('previewManifestSha256',''), ('canonicalOrigin','https://other.fwith.kr'),
                           ('worker','goyang-flower-prod-disabled'), ('wranglerConfig','wrangler.jsonc'),
                           ('scopeKey','old'), ('enabled',False)]:
            candidate=site();candidate['coverageDeployment'][key]=value
            with self.subTest(key=key), self.assertRaises(ValueError):self.resolve(candidate)

    def test_production_gate_and_paused_snapshot_policy_cannot_be_bypassed(self):
        for key,value in [('growthPaused',False),('autoDeploySnapshots',True),('requireRevisionApproval',False),
                          ('requireSnapshotApproval',False),('branch','main'),('siteUrl','https://other.fwith.kr'),
                          ('indexnowKey','unapproved-change')]:
            candidate=site();candidate[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.resolve(candidate)
        with self.assertRaises(ValueError):self.resolve(site(), 'production')
        with self.assertRaises(ValueError):self.resolve(site('production'), 'preview')


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'candidate';self.base=Path(self.temp.name)/'fixed-canary'
        self.phase='preview';self.responses={};self.calls=[]
        self.old={'pageKey':'synthetic-canary','snapshotId':qa.GOYANG_CANARY,'snapshotHash':qa.GOYANG_CANARY_HASH,
            'approvalVerified':True,'status':'approved','category':'funeral','pageType':'funeral-facility',
            'routeType':'category','url':'/funeral/ilsan-paik-funeral-wreath/','slug':'ilsan-paik-funeral-wreath',
            'sources':[{'name':'SYNTHETIC SOURCE','url':'https://example.com/source','type':'facility','verifiedAt':'2026-10-03'}]}
        self.region={**self.old,'pageKey':'synthetic-dong','snapshotId':'synthetic-region','snapshotHash':'c'*64,
            'category':'regions','pageType':'regional-service','url':'/regions/synthetic-dong/','slug':'synthetic-dong'}
        self.manifest={'siteKey':qa.GOYANG_SITE,'snapshotMode':'git-frozen','pages':[self.old,self.region],
            'snapshotLedger':{qa.GOYANG_CANARY:{'pageKey':'synthetic-canary','snapshotHash':qa.GOYANG_CANARY_HASH}}}
        self.arch={'pages':[self.old,{**self.region,'pageRole':'REGION_SERVICE_LANDING','parentHub':'/regions/','localizationPolicy':'local-required'}],
            'hubs':[{'category':'funeral','url':'/funeral/','children':1},{'category':'regions','url':'/regions/','children':1},
                    {'category':'gift','url':'/gift/','children':0}]}
        for r in (self.root,self.base):
            (r/'src/data').mkdir(parents=True);(r/'public/images').mkdir(parents=True)
            (r/'public/images/proof.jpg').write_bytes(b'SYNTHETIC IMAGE')
            self.write(r,'products.json',[{'sourceUrl':'https://example.com/SOURCE_ONLY','price':100}])
            self.write(r,'business-truth.json',{'onlineOrderUrl':'https://fwith.co.kr','phoneHref':'tel:18440644','brand':'SYNTHETIC','phone':'1844-0644'})
        self.write(self.base,'pages.json',[self.old])
        self.write(self.base,'publish-manifest.json',{**self.manifest,'pages':[self.old]})
        self.write(self.root,'pages.json',[self.old,self.region])
        self.write(self.root,'publish-manifest.json',self.manifest)
        self.write(self.root,'page-map.json',{'pages':self.manifest['pages']})
        self.write(self.root,'architecture.json',self.arch)
        self.write(self.root,'site-config.json',{'siteKey':qa.GOYANG_SITE,'productionApproved':False,'region':'고양'})
        self.write(self.root,'region-coverage.json',{'siteKey':qa.GOYANG_SITE,'scopeKey':qa.GOYANG_SCOPE,'unitBasis':'legal',
            'units':[{'pageKey':'synthetic-dong','slug':'synthetic-dong','url':'/regions/synthetic-dong/'},
                     {'pageKey':'unpublished','slug':'unpublished','url':'/regions/unpublished/'}]})
        (self.root/'wrangler.jsonc').write_text(json.dumps({'name':'goyang-flower-prod-disabled'}))
        (self.root/'wrangler.staging.jsonc').write_text(json.dumps({'name':'goyang-flower-guide-qa','workers_dev':True,'assets':{'directory':'./dist/'}}))
        for name in ['wrangler.jsonc','wrangler.staging.jsonc']:
            (self.base/name).write_bytes((self.root/name).read_bytes())
        self.build()

    def write(self,root,name,value): (root/'src/data'/name).write_text(json.dumps(value,ensure_ascii=False))
    def digest(self):return hashlib.sha256((self.root/'src/data/publish-manifest.json').read_bytes()).hexdigest()
    def build(self):
        paths={'/':None, '/funeral/':None, '/regions/':None, self.old['url']:qa.GOYANG_CANARY,self.region['url']:'synthetic-region'}
        headers={'X-Robots-Tag':'noindex, nofollow, noarchive'} if self.phase=='preview' else {}
        for path,snapshot in paths.items():
            robots='noindex,nofollow,noarchive' if self.phase=='preview' else ('noindex,follow' if path in ['/funeral/','/regions/'] else 'index,follow')
            html=f'<meta name="robots" content="{robots}"><meta name="site-factory-revision" content="{REVISION}"><link rel="canonical" href="{qa.GOYANG_ORIGIN+path}"><h1>SYNTHETIC</h1><script type="application/ld+json">{{}}</script>'
            if snapshot:html+=f'<article data-snapshot-id="{snapshot}">SYNTHETIC BODY <a href="https://example.com/source">Source</a></article>'
            p=self.root/'dist'/path.lstrip('/')/'index.html';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(html)
            self.responses[path]=(200,html,headers.copy())
        not_found_robots='noindex,follow' if self.phase=='production' else 'noindex,nofollow,noarchive'
        nf=(f'<meta name="robots" content="{not_found_robots}"><meta name="site-factory-revision" content="{REVISION}">'
            '<h1>페이지를 찾을 수 없습니다</h1>')
        (self.root/'dist/404.html').write_text(nf)
        for path in ['/site-factory-live-qa-definitely-not-found/','/gift/','/regions/unpublished/']:
            self.responses[path]=(404,nf,headers.copy())
        robots='User-agent: *\nDisallow: /\n' if self.phase=='preview' else f'User-agent: *\nAllow: /\nSitemap: {qa.GOYANG_ORIGIN}/sitemap-index.xml\n'
        self.responses['/robots.txt']=(200,robots,{})
        def xml(tag,child,urls):return f'<{tag} xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<{child}><loc>{u}</loc></{child}>' for u in urls)+f'</{tag}>'
        self.responses['/sitemap-index.xml']=(200,xml('sitemapindex','sitemap',[qa.GOYANG_ORIGIN+'/sitemap-0.xml']),headers.copy())
        self.responses['/sitemap-0.xml']=(200,xml('urlset','url',[qa.GOYANG_ORIGIN+p for p in ['/',self.old['url'],self.region['url']]]),headers.copy())
        for route in ['/robots.txt','/sitemap-index.xml','/sitemap-0.xml']:
            (self.root/'dist'/route.lstrip('/')).write_text(self.responses[route][1])
        (self.root/'dist/_headers').write_text('/*\n'+('  X-Robots-Tag: noindex, nofollow, noarchive\n' if self.phase=='preview' else '  X-Content-Type-Options: nosniff\n'))

    def fetch(self,path):self.calls.append(path);return self.responses[path]
    def verify(self,fetch=True):return qa.verify_goyang_coverage(self.root,self.base,qa.GOYANG_ORIGIN,REVISION,self.digest(),self.phase,self.fetch if fetch else None)
    def test_complete_preview_and_production_route_set_artifact_parity(self):
        self.assertEqual(self.verify()['pipelineState'],'preview_verified')
        self.assertIn('/regions/',self.calls);self.assertIn('/regions/unpublished/',self.calls)
        self.phase='production';self.write(self.root,'site-config.json',{'siteKey':qa.GOYANG_SITE,'productionApproved':True,'region':'고양'})
        (self.root/'production-indexing.enabled').write_text('SYNTHETIC');self.build()
        self.assertEqual(self.verify()['pipelineState'],'live_verified')

    def test_preflight_is_offline_and_changed_source_canary_products_images_fail(self):
        self.assertEqual(self.verify(False)['pipelineState'],'goyang_source_validated');self.assertEqual(self.calls,[])
        for relative in ['src/data/products.json','src/data/business-truth.json','public/images/proof.jpg']:
            p=self.root/relative;original=p.read_bytes();p.write_bytes(b'CHANGED')
            with self.subTest(file=relative),self.assertRaises(ValueError):self.verify(False)
            p.write_bytes(original)
        self.write(self.root,'pages.json',[{**self.old,'contentMarkdown':'SYNTHETIC CHANGED BODY'},self.region])
        with self.assertRaisesRegex(ValueError,'canary'):self.verify(False)

    def test_wrong_manifest_digest_scope_parent_source_or_approval_fails(self):
        with self.assertRaisesRegex(ValueError,'digest'):qa.validate_goyang_coverage_source(self.root,self.base,'0'*64,self.phase)
        original=(self.root/'src/data/pages.json').read_bytes()
        for change in [{'approvalVerified':False},{'sources':[]},{'url':'/regions/../escape/'}]:
            self.write(self.root,'pages.json',[self.old,{**self.region,**change}])
            with self.subTest(change=change),self.assertRaises(ValueError):self.verify(False)
        (self.root/'src/data/pages.json').write_bytes(original)
        self.arch['pages'][1]['parentHub']='/wrong/';self.write(self.root,'architecture.json',self.arch)
        with self.assertRaisesRegex(ValueError,'invalid page'):self.verify(False)

    def test_live_body_source_cta_canonical_revision_snapshot_and_duplicate_fail(self):
        p=self.region['url'];original=self.responses[p]
        for old,new in [('SYNTHETIC BODY','WRONG BODY'),('https://example.com/source','https://wrong.example/source'),
                        (qa.GOYANG_ORIGIN,'https://workers.dev'),(REVISION,'d'*40),('synthetic-region','wrong-snapshot')]:
            self.responses[p]=(200,original[1].replace(old,new),original[2])
            with self.subTest(change=old),self.assertRaises((ValueError,AssertionError)):self.verify()
        self.responses[p]=(200,original[1]+'<article data-snapshot-id="synthetic-region"></article>',original[2])
        with self.assertRaisesRegex(ValueError,'snapshot'):self.verify()

    def test_headers_thin_hubs_sitemaps_404_and_phantom_routes_fail(self):
        original=copy.deepcopy(self.responses)
        for path, replacement in [('/regions/',(200,self.responses['/regions/'][1],{})),
            ('/sitemap-0.xml',(200,self.responses['/sitemap-0.xml'][1].replace('</urlset>',f'<url><loc>{qa.GOYANG_ORIGIN}/regions/</loc></url></urlset>'),self.responses['/sitemap-0.xml'][2])),
            ('/regions/unpublished/',(200,self.responses['/regions/'][1],{})),
            ('/gift/',(404,self.responses['/gift/'][1],{}))]:
            self.responses=copy.deepcopy(original);self.responses[path]=replacement
            with self.subTest(path=path),self.assertRaises(ValueError):self.verify()
        self.responses=original
        p=self.root/'dist/regions/phantom/index.html';p.parent.mkdir(parents=True);p.write_text('PHANTOM')
        with self.assertRaisesRegex(ValueError,'route set'):self.verify(False)

    def test_http403_and_redirect_status_never_become_success(self):
        self.responses[self.region['url']]=(403,'SECRET RESPONSE',{})
        with self.assertRaises(PermissionError) as error:self.verify()
        self.assertNotIn('SECRET',str(error.exception))
        self.responses[self.region['url']]=(302,'',{'Location':'https://other.example'})
        with self.assertRaises(ValueError):self.verify()

    def test_production_thin_hub_stale_header_and_sitemap_extra_url_fail(self):
        self.phase='production';self.write(self.root,'site-config.json',{'siteKey':qa.GOYANG_SITE,'productionApproved':True,'region':'고양'})
        (self.root/'production-indexing.enabled').write_text('SYNTHETIC');self.build()
        original=copy.deepcopy(self.responses)
        for path in ['/', '/regions/', '/sitemap-index.xml', '/sitemap-0.xml']:
            self.responses=copy.deepcopy(original);status,html,_=self.responses[path]
            self.responses[path]=(status,html,{'X-Robots-Tag':'noindex'})
            with self.subTest(path=path),self.assertRaises(ValueError):self.verify()
        self.responses=copy.deepcopy(original);status,html,headers=self.responses['/regions/']
        self.responses['/regions/']=(status,html.replace('noindex,follow','index,follow'),headers)
        with self.assertRaises((ValueError,AssertionError)):self.verify()

    def test_existing_cli_offline_validation_needs_exact_scope_registry_and_digest(self):
        registry={'sites':{qa.GOYANG_SITE:site()}}
        registry['sites'][qa.GOYANG_SITE]['coverageDeployment']['previewManifestSha256']=self.digest()
        p=self.root/'trusted-registry.json';p.write_text(json.dumps(registry))
        command=[sys.executable,'-B',str(ENGINE/'verify_live.py'),'--site-key',qa.GOYANG_SITE,'--root',str(self.root),
                 '--baseline-root',str(self.base),'--registry',str(p),'--origin',qa.GOYANG_ORIGIN,'--revision',REVISION,
                 '--launch-key',qa.GOYANG_SCOPE,'--scope-key',qa.GOYANG_SCOPE,'--phase','preview','--validate-only',
                 '--report',str(self.root/'report.json')]
        result=subprocess.run(command,text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads((self.root/'report.json').read_text())['pipelineState'],'goyang_source_validated')
        registry['sites'][qa.GOYANG_SITE]['coverageDeployment']['enabled']=False;p.write_text(json.dumps(registry))
        self.assertNotEqual(subprocess.run(command,text=True,capture_output=True).returncode,0)

    def test_legacy_wrong_404_metadata_is_rejected_before_deploy_and_fixed_404_passes(self):
        file=self.root/'dist/404.html';original=file.read_text()
        self.assertEqual(self.verify(False)['pipelineState'],'goyang_source_validated')
        self.assertEqual(self.verify()['pipelineState'],'preview_verified')
        for extra in [f'<link rel="canonical" href="{qa.GOYANG_ORIGIN}/">',
                      '<script type="application/ld+json">{"@type":"Florist"}</script>']:
            file.write_text(original+extra)
            with self.subTest(extra=extra),self.assertRaises(ValueError):self.verify(False)
        for old,new in [('noindex,nofollow,noarchive','index,follow'),(REVISION,'d'*40)]:
            file.write_text(original.replace(old,new))
            with self.subTest(change=old),self.assertRaises(ValueError):self.verify(False)
        file.write_text(original)
        headers=self.root/'dist/_headers';headers.write_text('/*\n  X-Content-Type-Options: nosniff\n')
        with self.assertRaisesRegex(ValueError,'header'):self.verify(False)

    def test_unapproved_standalone_html_htm_xhtml_artifacts_fail_before_http(self):
        for name in ['unapproved.html','unapproved.htm','UNAPPROVED.HTML','unapproved.xhtml']:
            path=self.root/'dist'/name;path.write_text('<h1>UNAPPROVED SYNTHETIC</h1>')
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,'standalone HTML'):self.verify(False)
            with self.assertRaisesRegex(ValueError,'standalone HTML'):self.verify()
            path.unlink()

    def test_unexpected_wrangler_bindings_migrations_or_other_config_changes_fail_before_http(self):
        for name in ['wrangler.jsonc','wrangler.staging.jsonc']:
            path=self.root/name;original=path.read_bytes()
            for key,value in [('routes',['https://other.example/*']),('migrations',[{'tag':'unapproved'}]),
                              ('kv_namespaces',[{'binding':'UNAPPROVED','id':'synthetic'}]),('workers_dev',False)]:
                config=json.loads(original);config[key]=value;path.write_text(json.dumps(config))
                with self.subTest(file=name,key=key),self.assertRaisesRegex(ValueError,'fixed authorized baseline'):self.verify(False)
            path.write_bytes(original)


class WorkflowContractTests(unittest.TestCase):
    def test_existing_workflow_inline_python_compiles_and_binding_runs_after_closed_scope_gate(self):
        for filename in ['site-staging-deploy.yml','site-production-deploy.yml']:
            text=(ROOT/'.github/workflows'/filename).read_text()
            for block in re.findall(r"python3 - <<'PYTHON'\n(.*?)\n          PYTHON",text,re.S):
                compile('\n'.join(line[10:] for line in block.splitlines()),filename,'exec')
            self.assertEqual(text.count('verify_goyang_canonical.py binding'),2)
            self.assertLess(text.index('resolve_goyang_coverage_target'),text.index('verify_goyang_canonical.py binding'))
            self.assertIn('--validate-only',text);self.assertIn('git -C target archive',text)
            self.assertNotIn('schedule:',text);self.assertNotIn('goyang_domain_attach.py',text)

    def test_exact_staging_resolver_closed_or_scope_selected_and_legacy_suwon_unchanged(self):
        text=(ROOT/'.github/workflows/site-staging-deploy.yml').read_text()
        block=re.search(r"- name: Resolve isolated preview target.*?python3 - <<'PYTHON'\n(.*?)\n          PYTHON",text,re.S).group(1)
        code='\n'.join(line[10:] for line in block.splitlines())
        with tempfile.TemporaryDirectory() as directory:
            tmp=Path(directory);(tmp/'control/.github').mkdir(parents=True)
            registry=json.loads((ROOT/'.github/site-factory-sites.json').read_text())
            (tmp/'control/.github/site-factory-sites.json').write_text(json.dumps(registry))
            cwd=Path.cwd()
            try:
                os.chdir(tmp)
                env={'SITE_KEY':qa.GOYANG_SITE,'REVISION':REVISION,'ISSUE_BODY':'','GITHUB_REPOSITORY':REPO,'GITHUB_OUTPUT':str(tmp/'outputs'),
                    'LAUNCH_KEY':qa.GOYANG_SCOPE,'SCOPE_KEY':qa.GOYANG_SCOPE}
                with patch.dict(os.environ,env,clear=True):
                    with self.assertRaisesRegex(ValueError,'closed'):exec(code,{})
                    registry['sites'][qa.GOYANG_SITE]=site();(tmp/'control/.github/site-factory-sites.json').write_text(json.dumps(registry))
                    with self.assertRaises(SystemExit) as exit_code:exec(code,{})
                    self.assertEqual(exit_code.exception.code,0)
                    self.assertIn('url='+qa.GOYANG_ORIGIN,(tmp/'outputs').read_text())
                    os.environ['SITE_KEY']='suwon-flower-test';exec(code,{})
                    self.assertIn('url=https://suwon-flower-guide-qa.joseungil.workers.dev',(tmp/'outputs').read_text())
            finally:os.chdir(cwd)

    def test_production_issue_scope_and_shared_lock_reject_whitespace_normalization_gap(self):
        text=(ROOT/'.github/workflows/site-production-deploy.yml').read_text()
        self.assertIn("contains(github.event.issue.body, 'SITE_KEY: goyang-flower-v2')",text)
        block=re.search(r"- name: Resolve approved production target.*?python3 - <<'PYTHON'\n(.*?)\n          PYTHON",text,re.S).group(1)
        code='\n'.join(line[10:] for line in block.splitlines())
        with tempfile.TemporaryDirectory() as directory:
            tmp=Path(directory);(tmp/'control/.github').mkdir(parents=True)
            (tmp/'control/.github/site-factory-sites.json').write_text(json.dumps({'sites':{qa.GOYANG_SITE:site('production')}}))
            cwd=Path.cwd()
            try:
                os.chdir(tmp)
                env={'SITE_KEY':'','REVISION':REVISION,'GITHUB_REPOSITORY':REPO,'GITHUB_OUTPUT':str(tmp/'out'),
                     'LAUNCH_KEY':qa.GOYANG_SCOPE,'SCOPE_KEY':qa.GOYANG_SCOPE}
                with patch.dict(os.environ,env,clear=True):
                    for header in ['SITE_KEY:  goyang-flower-v2','SITE_KEY: \tgoyang-flower-v2','SITE_KEY: goyang-flower-v2 ']:
                        os.environ['ISSUE_BODY']=header
                        with self.subTest(header=header),self.assertRaisesRegex(SystemExit,'shared deployment lock'):exec(code,{})
                    os.environ['ISSUE_BODY']='SITE_KEY: goyang-flower-v2'
                    with self.assertRaises(SystemExit) as result:exec(code,{})
                    self.assertEqual(result.exception.code,0)
                    self.assertIn('worker=goyang-flower-guide-qa',(tmp/'out').read_text())
                    os.environ['SITE_KEY']=qa.GOYANG_SITE;os.environ['ISSUE_BODY']=''
                    with self.assertRaises(SystemExit) as result:exec(code,{})
                    self.assertEqual(result.exception.code,0)
            finally:os.chdir(cwd)


if __name__ == '__main__':unittest.main()
