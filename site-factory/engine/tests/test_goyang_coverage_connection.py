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
    # Test approval states are disposable fixtures, not an assertion that the
    # real registry must stay at its initial pre-preview state forever.
    value.update(productionEnabled=False, launchMode='staging', approvedRevision='', approvalEvidenceUrl='')
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

    def test_closed_registry_fixture_preserves_original_gates(self):
        value = site();value['coverageDeployment']['enabled'] = False
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


SYNTHETIC_BEACON = (b'<script type="module" src="' + qa.GOYANG_CF_BEACON_SRC
    + b'" integrity="sha512-synthetic" data-cf-beacon=\'{"token":"public-test-fixture"}\' crossorigin="anonymous"></script>\n')


class ManagedBeaconTests(unittest.TestCase):
    def test_exact_bytes_or_one_fully_pinned_suffix_only(self):
        artifact=b'<html><body><h1>Fixture</h1></body></html>'
        live=artifact.replace(b'</body>',SYNTHETIC_BEACON+b'</body>')
        with patch.object(qa,'GOYANG_CF_BEACON_SHA256',hashlib.sha256(SYNTHETIC_BEACON).hexdigest()):
            self.assertTrue(qa.goyang_artifact_matches(artifact.decode(),artifact))
            self.assertTrue(qa.goyang_artifact_matches(live.decode(),artifact,True))
            self.assertFalse(qa.goyang_artifact_matches(live.decode(),artifact,False))

    def test_changed_source_attributes_inline_duplicate_or_location_is_rejected(self):
        artifact=b'<html><body><h1>Fixture</h1></body></html>'
        variants=[SYNTHETIC_BEACON.replace(b'static.cloudflareinsights.com',b'attacker.example'),
            SYNTHETIC_BEACON.replace(b'type="module"',b'type="text/javascript"'),
            SYNTHETIC_BEACON.replace(b'public-test-fixture',b'other-token'),
            SYNTHETIC_BEACON.replace(b'integrity="sha512-synthetic"',b'integrity="changed"'),
            SYNTHETIC_BEACON.replace(b'crossorigin="anonymous"',b'crossorigin="use-credentials"'),
            SYNTHETIC_BEACON.replace(b'></script>',b'>alert(1)</script>'),
            SYNTHETIC_BEACON.replace(b' crossorigin=',b' onload="alert(1)" crossorigin='),
            SYNTHETIC_BEACON*2,SYNTHETIC_BEACON+b'<script>alert(1)</script>',b'<script>alert(1)</script>']
        with patch.object(qa,'GOYANG_CF_BEACON_SHA256',hashlib.sha256(SYNTHETIC_BEACON).hexdigest()):
            for injected in variants:
                self.assertFalse(qa.goyang_artifact_matches(artifact.replace(b'</body>',injected+b'</body>').decode(),artifact,True))
            for live in [SYNTHETIC_BEACON+artifact,artifact+SYNTHETIC_BEACON,
                         artifact.replace(b'<h1>',SYNTHETIC_BEACON+b'<h1>')]:
                self.assertFalse(qa.goyang_artifact_matches(live.decode(),artifact,True))

    def test_known_beacon_never_hides_body_cta_image_or_metadata_changes(self):
        artifact=b'<html><body><h1>Fixture</h1><a href="https://fwith.co.kr">Order</a><img src="/proof.jpg"></body></html>'
        live=artifact.replace(b'</body>',SYNTHETIC_BEACON+b'</body>')
        with patch.object(qa,'GOYANG_CF_BEACON_SHA256',hashlib.sha256(SYNTHETIC_BEACON).hexdigest()):
            for old,new in [(b'Fixture',b'Changed'),(b'https://fwith.co.kr',b'https://attacker.example'),
                            (b'/proof.jpg',b'/wrong.jpg'),(b'<body>',b'<body><meta name="robots" content="index">')]:
                self.assertFalse(qa.goyang_artifact_matches(live.replace(old,new).decode(),artifact,True))


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

    def test_complete_pages_and_404_accept_only_pinned_managed_suffix(self):
        for phase in ('preview','production'):
            self.phase=phase;self.write(self.root,'site-config.json',{'siteKey':qa.GOYANG_SITE,'productionApproved':phase=='production','region':'고양'})
            if phase=='production':(self.root/'production-indexing.enabled').write_text('SYNTHETIC')
            self.build()
            for path,(status,body,headers) in list(self.responses.items()):
                if not path.endswith('/'):
                    continue
                artifact='<html><body>'+body+'</body></html>'
                file=self.root/'dist'/path.lstrip('/')/'index.html' if status==200 else self.root/'dist/404.html'
                file.write_text(artifact)
                self.responses[path]=(status,artifact.replace('</body>',SYNTHETIC_BEACON.decode()+'</body>'),headers)
            with patch.object(qa,'GOYANG_CF_BEACON_SHA256',hashlib.sha256(SYNTHETIC_BEACON).hexdigest()):
                self.assertIn(self.verify()['pipelineState'],('preview_verified','live_verified'))
                path='/regions/unpublished/';status,body,headers=self.responses[path]
                self.responses[path]=(status,body.replace('public-test-fixture','unapproved'),headers)
                with self.assertRaisesRegex(ValueError,'404'):self.verify()

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

    def test_production_ready_source_only_allowed_in_isolated_noindex_version_mode(self):
        self.write(self.root,'site-config.json',{'siteKey':qa.GOYANG_SITE,'productionApproved':True})
        with self.assertRaisesRegex(ValueError,'indexing'):self.verify(False)
        result=qa.verify_goyang_coverage(self.root,self.base,qa.GOYANG_ORIGIN,REVISION,self.digest(),'preview',version_preview=True)
        self.assertEqual(result['pipelineState'],'goyang_source_validated')
        path='/regions/';status,body,headers=self.responses[path]
        self.responses[path]=(status,body.replace('noindex,nofollow,noarchive','index,follow'),headers)
        with self.assertRaises((AssertionError,ValueError)):
            qa.verify_goyang_coverage(self.root,self.base,qa.GOYANG_ORIGIN,REVISION,self.digest(),'preview',self.fetch,version_preview=True)

    def test_provider_header_only_on_confirmed_live_version_keeps_html_meta_strict(self):
        for path,(status,body,headers) in list(self.responses.items()):
            self.responses[path]=(status,body,{'X-Robots-Tag':'noindex'})
        # A provider response must never weaken canonical, legacy or offline QA.
        with self.assertRaisesRegex(ValueError,'header'):self.verify()
        with self.assertRaisesRegex(ValueError,'confirmed live'):
            qa.verify_goyang_coverage(self.root,self.base,qa.GOYANG_ORIGIN,REVISION,self.digest(),'preview',version_preview=True,version_headers=True)
        run=lambda:qa.verify_goyang_coverage(self.root,self.base,qa.GOYANG_ORIGIN,REVISION,self.digest(),'preview',self.fetch,version_preview=True,version_headers=True)
        self.assertEqual(run()['pipelineState'],'preview_verified')
        for path in ('/','/regions/unpublished/','/sitemap-0.xml'):
            original=self.responses[path]
            for header in ('','index','noindex,index','noindex,follow'):
                self.responses[path]=(original[0],original[1],{'X-Robots-Tag':header})
                with self.subTest(path=path,header=header),self.assertRaises(ValueError):run()
            self.responses[path]=original
        original=self.responses['/'];self.responses['/']=(200,original[1].replace('noindex,nofollow,noarchive','noindex'),original[2])
        with self.assertRaises(ValueError):run()

    def test_probe_never_enters_production_artifact_and_canonical_must_return_exact_404(self):
        path='/_site-factory/version-probe/123.txt'
        missing=(self.root/'dist/404.html').read_bytes()
        qa.verify_goyang_probe_absent(self.root,path,lambda p:(404,missing,{}))
        for status,body in [(200,missing),(403,b'blocked'),(404,b'foreign 404')]:
            with self.assertRaises((ValueError,PermissionError)):
                qa.verify_goyang_probe_absent(self.root,path,lambda p:(status,body,{}))
        self.phase='production';self.write(self.root,'site-config.json',{'siteKey':qa.GOYANG_SITE,'productionApproved':True})
        (self.root/'production-indexing.enabled').write_text('SYNTHETIC');self.build()
        p=self.root/'dist'/path.lstrip('/');p.parent.mkdir(parents=True);p.write_text('synthetic')
        with self.assertRaisesRegex(ValueError,'probe'):self.verify(False)


class VersionPreviewTests(unittest.TestCase):
    def upload(self):
        return {'type':'version-upload','version':1,'worker_name':'goyang-flower-guide-qa',
            'version_id':'11111111-2222-4333-8444-555555555555',
            'preview_url':'https://11111111-goyang-flower-guide-qa.joseungil.workers.dev','worker_name_overridden':False}

    def parse(self,rows):return qa.read_goyang_version_upload('\n'.join(json.dumps(row) for row in rows))

    def test_actual_official_single_upload_record_with_session_filters_nonpublic_fields(self):
        row=self.upload();row.update(worker_tag='PRIVATE',bundle_size={'raw_bytes':1})
        result=self.parse([{'type':'wrangler-session','argv':['PRIVATE']},row])
        self.assertEqual(result,{'versionId':row['version_id'],'previewUrl':row['preview_url']})
        self.assertNotIn('PRIVATE',json.dumps(result))

    def test_failed_missing_stale_duplicate_alias_foreign_or_deployment_id_results_block(self):
        row=self.upload()
        for rows in [[],[{'type':'wrangler-session'}],[row,row],[row,{'type':'command-failed'}],
                     [row,{'type':'version-deploy'}],[row,{'type':'deploy'}],[row,{'type':'preview'}]]:
            with self.subTest(rows=rows),self.assertRaises(ValueError):self.parse(rows)
        for k,v in [('version_id',None),('version_id','different-deployment-id'),('preview_url',None),
            ('preview_url',row['preview_url']+'/'),('preview_url',row['preview_url']+'?secret=x'),
            ('preview_url',row['preview_url'].replace('11111111','22222222')),
            ('preview_url','https://goyang.fwith.kr'),('preview_url','https://11111111-goyang-flower-guide-qa.attacker.workers.dev'),
            ('preview_alias_url',row['preview_url']),('worker_name','other'),('worker_name_overridden',True),('wrangler_environment','production')]:
            with self.subTest(k=k,v=v),self.assertRaises(ValueError):self.parse([{**row,k:v}])

    def test_live_preview_requires_explicit_version_path_and_uses_approved_public_reference(self):
        live=site('production');live['coverageDeployment']['previewRevision']='c'*40
        args=(live,REPO,'c'*40,qa.GOYANG_SCOPE,qa.GOYANG_SCOPE,'preview')
        with self.assertRaises(ValueError):qa.resolve_goyang_coverage_target(*args)
        target=qa.resolve_goyang_coverage_target(*args,version_preview=True)
        self.assertEqual(target['revision'],'c'*40)
        self.assertEqual(qa.goyang_public_reference(live),{'revision':REVISION,'manifest_sha256':'b'*64,'phase':'production'})
        live['approvalEvidenceUrl']=''
        with self.assertRaises(ValueError):qa.goyang_public_reference(live)
        preview=site();preview['coverageDeployment']['previewRevision']='d'*40
        self.assertEqual(qa.goyang_public_reference(preview)['revision'],qa.GOYANG_PUBLIC_BOOTSTRAP)

    def test_all_static_assets_require_exact_status_bytes_mime_and_version_noindex(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist=Path(tmp)/'dist';dist.mkdir();(dist/'photo.jpg').write_bytes(b'jpeg-fixture');(dist/'style.css').write_bytes(b'css-fixture');(dist/'index.html').write_text('HTML tested elsewhere');(dist/'_headers').write_text('rules')
            responses={'/photo.jpg':(200,b'jpeg-fixture',{'Content-Type':'image/jpeg','X-Robots-Tag':'noindex,nofollow,noarchive'}),'/style.css':(200,b'css-fixture',{'Content-Type':'text/css','X-Robots-Tag':'noindex,nofollow,noarchive'})}
            self.assertEqual(qa.verify_goyang_assets(tmp,responses.__getitem__,True),2)
            original=responses['/photo.jpg']
            for replacement in [(403,b'jpeg-fixture',original[2]),(200,b'changed',original[2]),(200,original[1],{'Content-Type':'image/png','X-Robots-Tag':'noindex,nofollow,noarchive'}),(200,original[1],{'Content-Type':'image/jpeg'})]:
                responses['/photo.jpg']=replacement
                with self.assertRaises((ValueError,PermissionError)):qa.verify_goyang_assets(tmp,responses.__getitem__,True)
            responses['/photo.jpg']=original

    def test_provider_asset_noindex_header_does_not_allow_missing_or_index_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            dist=Path(tmp)/'dist';dist.mkdir();(dist/'proof.txt').write_bytes(b'proof')
            fetch=lambda path:(200,b'proof',{'X-Robots-Tag':'noindex'})
            with self.assertRaises(ValueError):qa.verify_goyang_assets(tmp,fetch,True)
            self.assertEqual(qa.verify_goyang_assets(tmp,fetch,True,version_headers=True),1)
            for header in ('','index','noindex,index','noindex,follow'):
                with self.assertRaises(ValueError):qa.verify_goyang_assets(tmp,lambda p:(200,b'proof',{'X-Robots-Tag':header}),True,version_headers=True)

    def test_workflow_only_goyang_uses_upload_and_always_checks_public_boundary(self):
        import yaml
        data=yaml.safe_load((ROOT/'.github/workflows/site-staging-deploy.yml').read_text())
        steps=data['jobs']['preview']['steps'];byid={step.get('id'):step for step in steps}
        self.assertEqual(byid['deploy']['if'],"steps.target.outputs.goyang_coverage != 'true'")
        upload=byid['version_upload'];self.assertEqual(upload['if'],"steps.target.outputs.goyang_coverage == 'true'")
        self.assertIn('versions upload -c "$CONFIG" --strict --keep-vars',upload['run'])
        self.assertIn('test ! -e "$WRANGLER_OUTPUT_FILE_PATH"',upload['run'])
        for forbidden in ('versions deploy','triggers deploy','--preview-alias','--env ','--secrets-file','--experimental-provision'):
            self.assertNotIn(forbidden,upload['run'])
        after=[step for step in steps if 'after every upload attempt' in step.get('name','') or 'after upload attempt' in step.get('name','')]
        self.assertEqual(len(after),2)
        self.assertTrue(all('always()' in step['if'] and "steps.version_upload.outcome != 'skipped'" in step['if'] for step in after))
        marker=next(step for step in steps if 'Record one Goyang' in step.get('name',''))
        self.assertIn('GITHUB_RUN_ATTEMPT',marker['with']['script']);self.assertIn('GOYANG_VERSION_UPLOAD_STARTED:',marker['with']['script'])
        artifacts=next(step for step in steps if step.get('uses','').startswith('actions/upload-artifact'))['with']['path']
        self.assertNotIn('ndjson',artifacts);self.assertNotIn('upload.log',artifacts)


class WorkflowContractTests(unittest.TestCase):
    def test_existing_workflow_inline_python_compiles_and_binding_runs_after_closed_scope_gate(self):
        for filename in ['site-staging-deploy.yml','site-production-deploy.yml']:
            text=(ROOT/'.github/workflows'/filename).read_text()
            for block in re.findall(r"python3 - <<'PYTHON'\n(.*?)\n          PYTHON",text,re.S):
                compile('\n'.join(line[10:] for line in block.splitlines()),filename,'exec')
            guard='verify_goyang_canonical.py version-upload-preflight' if filename=='site-staging-deploy.yml' else 'verify_goyang_canonical.py binding'
            self.assertEqual(text.count(guard),2)
            self.assertLess(text.index('resolve_goyang_coverage_target'),text.index(guard))
            self.assertIn('--validate-only',text);self.assertIn('git -C target archive',text)
            self.assertNotIn('schedule:',text);self.assertNotIn('goyang_domain_attach.py',text)

    def test_exact_staging_resolver_closed_or_scope_selected_and_legacy_suwon_unchanged(self):
        text=(ROOT/'.github/workflows/site-staging-deploy.yml').read_text()
        block=re.search(r"- name: Resolve isolated preview target.*?python3 - <<'PYTHON'\n(.*?)\n          PYTHON",text,re.S).group(1)
        code='\n'.join(line[10:] for line in block.splitlines())
        with tempfile.TemporaryDirectory() as directory:
            tmp=Path(directory);(tmp/'control/.github').mkdir(parents=True)
            registry=json.loads((ROOT/'.github/site-factory-sites.json').read_text())
            registry['sites'][qa.GOYANG_SITE]['coverageDeployment']['enabled']=False
            (tmp/'control/.github/site-factory-sites.json').write_text(json.dumps(registry))
            cwd=Path.cwd()
            try:
                os.chdir(tmp)
                env={'SITE_KEY':qa.GOYANG_SITE,'REVISION':REVISION,'ISSUE_BODY':'','GITHUB_REPOSITORY':REPO,'GITHUB_OUTPUT':str(tmp/'outputs'),'GITHUB_RUN_ID':'12345',
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
