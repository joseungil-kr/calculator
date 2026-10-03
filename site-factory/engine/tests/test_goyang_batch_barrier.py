"""Synthetic integrity fixtures only; no customer content or approval evidence."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import render_snapshot as snapshot_renderer
from batch_barrier import GOYANG_GATES, GOYANG_SCOPE, GOYANG_SITE, GOYANG_TARGET, check, identity
from render_snapshot import frozen_hashes, parse_payload, validate_content
from test_engine import payload

BASE, FINAL = 'a' * 40, 'f' * 40
ROOT = GOYANG_TARGET['root']


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


class MemoryGit:
    def __init__(self, documents, history):
        self.documents, self.history = documents, history

    def read(self, revision, path):
        return self.documents[(revision, path)]

    def ancestor(self, older, newer):
        return older in self.history and newer in self.history and self.history.index(older) <= self.history.index(newer)


def source_rows(p, order):
    storage, _ = frozen_hashes(p)
    e = {'pageKey': p['PAGE_KEY'], 'snapshotId': p['SNAPSHOT_ID'], 'snapshotHash': storage,
         'approvalVerified': True, 'draftKey': p['DRAFT_KEY'], 'sourceRecordId': p['SOURCE_RECORD_ID'],
         'publishQueueRecordId': p['PUBLISH_QUEUE_RECORD_ID'], 'slug': p['SLUG'], 'category': p['CATEGORY'],
         'routeType': p['ROUTE_TYPE'], 'url': p['url'], 'title': p['TITLE'], 'primaryKeyword': p['PRIMARY_KEYWORD'],
         'pageType': p['PAGE_TYPE'], 'status': 'approved', 'file': 'src/data/pages.json'}
    page = {**e, 'order': order, 'h1': p['H1'], 'description': p['DESCRIPTION'], 'cardSummary': p['CARD-SUMMARY'],
            'firstAnswer': p['FIRST-ANSWER'], 'contentMarkdown': p['CONTENT'], 'sections': [], 'faq': [],
            'sources': p['sources'], 'source': p['sources'][0], 'relatedKeys': p['relatedKeys'],
            'queryClass': p['QUERY_CLASS'], 'visualIntent': p['VISUAL_INTENT'], 'assetSlot': p['ASSET_SLOT']}
    arch = {**e, 'pageRole': p['PAGE_ROLE'], 'parentHub': p['PARENT_HUB'], 'intentKey': p['INTENT_KEY'],
            'contentRole': p['CONTENT_ROLE'], 'localizationPolicy': p['LOCALIZATION_POLICY'],
            'sitemapIndexable': True, 'status': 'primary'}
    return e, page, arch


def make_body(i, **changes):
    args = {'SITE_KEY': GOYANG_SITE, 'PAGE_KEY': f'region-{i}', 'INTENT_KEY': f'goyang|flower-delivery|local-order|dong-{i}',
            'TARGET_REPO': GOYANG_TARGET['repo'], 'TARGET_BRANCH': GOYANG_TARGET['branch'], 'TARGET_ROOT': ROOT,
            'SLUG': f'dong-{i}', 'CATEGORY': 'regions', 'PAGE_TYPE': 'regional-service',
            'PAGE_ROLE': 'REGION_SERVICE_LANDING', 'STRUCTURE_TYPE': 'REGION_SERVICE_LANDING', 'PARENT_HUB': '/regions/',
            'QUERY_CLASS': 'local-commercial', 'VISUAL_INTENT': 'flower_delivery', 'ASSET_SLOT': 'REAL_PROOF',
            'PRIMARY_KEYWORD': f'합성{i}동 꽃배달', 'TITLE': f'합성{i}동 꽃배달 | 테스트 전용 원문',
            'H1': '합성 검증 예시', 'FIRST-ANSWER': '합성 테스트의 직접 답변입니다.',
            'CARD-SUMMARY': '합성 fixture 전용 카드 요약입니다.',
            'SNAPSHOT_ID': f'fixture-snapshot-{i}', 'PUBLISH_QUEUE_RECORD_ID': f'rec{i:014d}'}
    args.update(changes)
    body = payload(**args)
    _, reviewed = frozen_hashes(validate_content(parse_payload(body)))
    return payload(**args, APPROVAL_STATUS='approved', APPROVED_SNAPSHOT_HASH=reviewed)


def fixture(count=3):
    documents, history, bodies = {}, [BASE], {}
    units = [{'pageKey': f'region-{i}', 'unitKey': f'fixture-unit-{i}', 'name': f'합성{i}동', 'slug': f'dong-{i}',
              'url': f'/regions/dong-{i}/'} for i in range(count + 1)]
    coverage = {'siteKey': GOYANG_SITE, 'scopeKey': GOYANG_SCOPE, 'unitBasis': 'legal', 'units': units,
                'administrativeCrosswalk': [{'name': '합성행정동', 'unitKey': 'admin-0'}]}
    coverage_raw = encode(coverage)
    registry = {'sites': {GOYANG_SITE: {**GOYANG_TARGET, 'snapshotRenderer': 'structured-json-v12', 'allowedCategories': ['regions'],
                'allowedPageTypes': ['regional-service'],
                'administrativeCoverage': {'enabled': True, 'regionKey': 'goyang', 'unitBasis': 'legal'},
                'categoryPageTypes': {'regions': ['regional-service']}, 'productionEnabled': True, 'growthPaused': True,
                'autoDeploySnapshots': False, 'requireRevisionApproval': True, 'requireSnapshotApproval': True}}}
    documents[(BASE, '.github/site-factory-sites.json')] = encode(registry)
    documents[(BASE, 'site-factory/engine/render_snapshot.py')] = Path(snapshot_renderer.__file__).read_bytes()
    documents[(BASE, ROOT + '/src/data/region-coverage.json')] = coverage_raw
    documents[(FINAL, ROOT + '/src/data/region-coverage.json')] = coverage_raw
    tables = {'publish-manifest': [], 'pages': [], 'architecture': [], 'page-map': []}
    ledger = {}

    def add(body):
        p = validate_content(parse_payload(body)); e, page, arch = source_rows(p, len(tables['pages']) + 1)
        tables['publish-manifest'].append(e); tables['page-map'].append(e)
        tables['pages'].append(page); tables['architecture'].append(arch)
        ledger[p['SNAPSHOT_ID']] = {k: e[k] for k in ('pageKey', 'snapshotHash', 'publishQueueRecordId')}
        return p

    def checkpoint(revision):
        for name, rows in tables.items():
            if name == 'pages': doc = rows
            else:
                doc = {'siteKey': GOYANG_SITE, 'pages': rows}
                if name == 'publish-manifest': doc['snapshotLedger'] = ledger
                if name == 'architecture':
                    doc['hubs'] = [{'url': f'/{c}/', 'category': c, 'children': sum(p['category'] == c for p in tables['pages']),
                                    'indexable': False} for c in ('funeral', 'regions', 'gift')]
            documents[(revision, ROOT + '/src/data/' + name + '.json')] = encode(doc)

    add(make_body(900, PAGE_KEY='existing-canary', CATEGORY='funeral', PAGE_TYPE='funeral-facility',
                  PAGE_ROLE='PLACE_LANDING', PARENT_HUB='/funeral/'))
    add(make_body(0)); checkpoint(BASE)
    batch = {'schemaVersion': 2, 'contractType': 'goyang-all-remaining-legal-dongs', 'batchId': 'synthetic-goyang',
             'siteKey': GOYANG_SITE, 'scopeKey': GOYANG_SCOPE, 'baselineSourceSha': BASE,
             'baselineManifestSha256': hashlib.sha256(documents[(BASE, ROOT + '/src/data/publish-manifest.json')]).hexdigest(),
             'coverageSha256': hashlib.sha256(coverage_raw).hexdigest(),
             'ruleRevision': BASE, 'templateRevision': BASE, 'registryRevision': BASE,
             'members': [{'pageKey': f'region-{i}', 'intentKey': f'goyang|flower-delivery|local-order|dong-{i}'} for i in range(1, count + 1)]}
    batch['membershipHash'] = identity(batch)
    items = []
    with tempfile.TemporaryDirectory(prefix='goyang-barrier-test-') as directory:
        workspace = Path(directory); data = workspace / ROOT / 'src/data'; data.mkdir(parents=True)
        for name in tables:
            (data / (name + '.json')).write_bytes(documents[(BASE, ROOT + '/src/data/' + name + '.json')])
        for i, member in enumerate(batch['members'], 1):
            body = make_body(i); p = validate_content(parse_payload(body)); commit = f'{i:040x}'; history.append(commit)
            snapshot_renderer.render(body, registry, workspace)
            for name in tables:
                documents[(commit, ROOT + '/src/data/' + name + '.json')] = (data / (name + '.json')).read_bytes()
            storage, reviewed = frozen_hashes(p)
            items.append({**member, 'ruleRevision': BASE, 'templateRevision': BASE, 'registryRevision': BASE,
                          'draftRevision': 'fixture-r1', 'writerRunId': 'fixture-writer', 'payload': body,
                          'reviewDigest': reviewed, 'snapshotHash': storage, 'queueRecordId': p['PUBLISH_QUEUE_RECORD_ID'],
                          'issueUrl': f'https://github.com/{GOYANG_TARGET["repo"]}/issues/{i}', 'snapshotId': p['SNAPSHOT_ID'],
                          'commitSha': commit, 'reviewSourceSha': BASE,
                          'reviewerApproval': {'status': 'approved', 'reviewer': 'fixture-independent-reviewer',
                                               'evidenceUrl': 'https://example.com/fixture-not-real-approval', 'draftRevision': 'fixture-r1',
                                               'reviewDigest': reviewed, 'membershipHash': batch['membershipHash']}})
        history.append(FINAL)
        for name in tables:
            documents[(FINAL, ROOT + '/src/data/' + name + '.json')] = (data / (name + '.json')).read_bytes()
    final_pages = json.loads(documents[(FINAL, ROOT + '/src/data/pages.json')])
    paths = ['/', '/funeral/', '/regions/'] + [p['url'] for p in final_pages]
    qa = {'sourceSha': FINAL, 'manifestSha256': hashlib.sha256(documents[(FINAL, ROOT + '/src/data/publish-manifest.json')]).hexdigest(),
          'state': 'passed', 'environment': 'staging', 'noindex': True, 'reviewer': 'fixture-independent-qa',
          'evidenceUrl': 'https://example.com/fixture-not-real-qa', 'gates': sorted(GOYANG_GATES),
          'routes': [{'url': url, 'state': 'passed', 'noindex': True} for url in paths],
          'notFoundRoutes': [{'url': url, 'state': 'passed', 'status': 404, 'canonicalAbsent': True}
                             for url in ('/gift/', '/site-factory-live-qa-definitely-not-found/')],
          'aliasCoverageSha256': batch['coverageSha256'],
          'discoverableNames': sorted({r['name'] for r in units + coverage['administrativeCrosswalk']})}
    return batch, {'batchId': batch['batchId'], 'membershipHash': batch['membershipHash'], 'finalSourceSha': FINAL,
                   'items': items, 'qa': qa}, MemoryGit(documents, history)


class GoyangBarrierTests(unittest.TestCase):
    def setUp(self):
        self.batch, self.evidence, self.git = fixture()

    def check(self):
        return check(self.batch, self.evidence, self.git)

    def mutate_doc(self, revision, name, mutator):
        path = (revision, ROOT + '/src/data/' + name + '.json')
        doc = json.loads(self.git.documents[path]); mutator(doc); self.git.documents[path] = encode(doc)

    def test_scoped_dynamic_membership_and_read_only(self):
        before = copy.deepcopy((self.batch, self.evidence, self.git.documents))
        r = self.check()
        self.assertEqual((r['baselineDetailCount'], r['newDetailCount'], r['detailCount'], r['qaRouteCount']), (2, 3, 5, 8))
        self.assertEqual(r['notFoundRouteCount'], 2)
        self.assertFalse(r['productionApproved']); self.assertFalse(r['indexNowAllowed'])
        self.assertEqual(before, (self.batch, self.evidence, self.git.documents))
        self.assertEqual(r, self.check())

    def test_current_size_is_membership_derived_not_quota(self):
        b, e, g = fixture(52)
        r = check(b, e, g)
        self.assertEqual((r['newDetailCount'], r['detailCount'], r['qaRouteCount']), (52, 54, 57))
        b['members'].reverse(); self.assertEqual(identity(b), b['membershipHash'])
        check(b, e, g)

    def test_changed_scope_identity_and_gates_rejected(self):
        mutations = [lambda b,e:b.update(siteKey='other'), lambda b,e:b.update(scopeKey='other'),
            lambda b,e:b.update(contractType='generic'), lambda b,e:b.update(baselineManifestSha256='0'*64),
            lambda b,e:b.update(coverageSha256='0'*64), lambda b,e:b['members'].pop(),
            lambda b,e:b['members'][0].update(intentKey='wrong'), lambda b,e:e['items'].pop(),
            lambda b,e:e['items'].reverse(), lambda b,e:e['items'][0].update(commitSha=FINAL),
            lambda b,e:e['items'][0].update(reviewSourceSha=FINAL),
            lambda b,e:e['items'][0].update(draftRevision='other'),
            lambda b,e:e['items'][0]['reviewerApproval'].update(reviewer='fixture-writer'),
            lambda b,e:e['items'][0]['reviewerApproval'].update(status='pending'),
            lambda b,e:e['items'][0].update(snapshotHash='0'*64),
            lambda b,e:e['items'][0].update(queueRecordId='recZZZZZZZZZZZZZZ'),
            lambda b,e:e['items'][0].update(issueUrl='https://github.com/other/repo/issues/1'),
            lambda b,e:e['qa']['gates'].remove('aliases'), lambda b,e:e['qa']['routes'].pop(),
            lambda b,e:e['qa']['notFoundRoutes'].pop(), lambda b,e:e['qa']['notFoundRoutes'][0].update(status=200),
            lambda b,e:e['qa']['notFoundRoutes'][0].update(canonicalAbsent=False),
            lambda b,e:e['qa']['discoverableNames'].pop(), lambda b,e:e['qa'].update(noindex=False),
            lambda b,e:e['qa'].update(reviewer='fixture-writer'), lambda b,e:e['qa'].update(sourceSha=BASE)]
        for i, mutate in enumerate(mutations):
            with self.subTest(i=i):
                b,e=copy.deepcopy((self.batch,self.evidence));mutate(b,e)
                with self.assertRaises(ValueError):check(b,e,self.git)

    def test_rehash_does_not_authorize_shrunken_or_extra_membership(self):
        for remove in (True, False):
            b,e,g=fixture()
            if remove:b['members'].pop()
            else:b['members'].append({'pageKey':'extra','intentKey':'extra'})
            b['membershipHash']=identity(b);e['membershipHash']=b['membershipHash']
            with self.assertRaisesRegex(ValueError,'every remaining'):check(b,e,g)

    def test_raw_coverage_drift_fails(self):
        self.git.documents[(FINAL, ROOT+'/src/data/region-coverage.json')]+=b'\n'
        with self.assertRaisesRegex(ValueError,'Coverage bytes'):self.check()

    def test_baseline_body_preserved(self):
        self.mutate_doc(FINAL,'pages',lambda d:d[0].update(contentMarkdown='tampered old body'))
        with self.assertRaisesRegex(ValueError,'baseline frozen'):self.check()

    def test_new_body_tamper_with_unchanged_claimed_hash_fails(self):
        self.mutate_doc(FINAL,'pages',lambda d:d[-1].update(contentMarkdown='tampered new body'))
        with self.assertRaisesRegex(ValueError,'pinned renderer|checkpoint changed'):self.check()

    def test_missing_or_extra_final_rows_fails(self):
        for remove in (True,False):
            b,e,g=fixture(); key=(FINAL,ROOT+'/src/data/publish-manifest.json');d=json.loads(g.documents[key])
            if remove:d['pages'].pop()
            else:d['pages'].append({**d['pages'][-1],'pageKey':'extra','url':'/regions/extra/','snapshotId':'extra','publishQueueRecordId':'extra'})
            g.documents[key]=encode(d)
            with self.assertRaises(ValueError):check(b,e,g)

    def test_snapshot_flags_stay_closed(self):
        path=(BASE,'.github/site-factory-sites.json');d=json.loads(self.git.documents[path]);d['sites'][GOYANG_SITE]['autoDeploySnapshots']=True
        self.git.documents[path]=encode(d)
        with self.assertRaisesRegex(ValueError,'no intermediate'):self.check()

    def test_reapproved_future_link_fails(self):
        item=self.evidence['items'][0];body=make_body(1,**{'RELATED-PAGE-KEYS':'region-3'})
        p=validate_content(parse_payload(body));s,r=frozen_hashes(p)
        item.update(payload=body,snapshotHash=s,reviewDigest=r);item['reviewerApproval']['reviewDigest']=r
        with self.assertRaisesRegex(ValueError,'future/unapproved'):self.check()

    def test_empty_hub_cannot_count_as_normal_route(self):
        self.evidence['qa']['routes'].append({'url':'/gift/','state':'passed','noindex':True})
        with self.assertRaisesRegex(ValueError,'Every final rendered'):self.check()

    def test_whole_ledger_preserved_at_every_checkpoint(self):
        first = self.evidence['items'][0]['commitSha']
        def deleted(doc): del doc['snapshotLedger']['fixture-snapshot-900']
        def changed(doc): doc['snapshotLedger']['fixture-snapshot-900']['snapshotHash'] = '0' * 64
        def extra(doc): doc['snapshotLedger']['unreviewed-extra'] = {'pageKey': 'extra'}
        for mutation in (deleted, changed, extra):
            with self.subTest(mutation=mutation.__name__):
                self.batch, self.evidence, self.git = fixture()
                self.mutate_doc(first, 'publish-manifest', mutation)
                # Later checkpoints/final retain the original ledger: repair cannot erase history.
                with self.assertRaisesRegex(ValueError, 'pinned renderer'):
                    self.check()

    def change_first_member_everywhere(self, filename, field, value):
        key = self.evidence['items'][0]['pageKey']
        for sha in self.git.history[1:]:
            def mutate(doc):
                rows = doc if filename == 'pages' else doc['pages']
                next(row for row in rows if row['pageKey'] == key)[field] = value
            self.mutate_doc(sha, filename, mutate)

    def test_order_matches_previous_renderer_max_plus_one(self):
        for order in (1, 40):
            with self.subTest(order=order):
                self.batch, self.evidence, self.git = fixture()
                self.change_first_member_everywhere('pages', 'order', order)
                with self.assertRaisesRegex(ValueError, 'pinned renderer|checkpoint changed'):
                    self.check()

    def test_sitemap_flag_matches_pinned_registry(self):
        self.change_first_member_everywhere('architecture', 'sitemapIndexable', False)
        with self.assertRaisesRegex(ValueError, 'pinned renderer'):
            self.check()

    def test_renderer_sitemap_false_when_pinned_registry_disabled(self):
        key = (BASE, '.github/site-factory-sites.json')
        registry = json.loads(self.git.documents[key]); registry['sites'][GOYANG_SITE]['productionEnabled'] = False
        self.git.documents[key] = encode(registry)
        new_keys = {row['pageKey'] for row in self.batch['members']}
        for sha in self.git.history[1:]:
            def mutate(doc):
                for row in doc['pages']:
                    if row['pageKey'] in new_keys: row['sitemapIndexable'] = False
            self.mutate_doc(sha, 'architecture', mutate)
        self.check()

    def test_last_snapshot_top_level_mode_cannot_be_changed(self):
        for sha in (self.evidence['items'][-1]['commitSha'], FINAL):
            self.mutate_doc(sha, 'publish-manifest', lambda d: d.update(snapshotMode='mutable'))
        self.evidence['qa']['manifestSha256'] = hashlib.sha256(
            self.git.documents[(FINAL, ROOT + '/src/data/publish-manifest.json')]).hexdigest()
        with self.assertRaisesRegex(ValueError, 'pinned renderer: publish-manifest'):
            self.check()

    def test_last_architecture_home_cannot_be_repointed(self):
        for sha in (self.evidence['items'][-1]['commitSha'], FINAL):
            self.mutate_doc(sha, 'architecture', lambda d: d.update(home={'url': 'https://example.com/wrong-home/'}))
        with self.assertRaisesRegex(ValueError, 'pinned renderer: architecture'):
            self.check()

    def test_intermediate_hub_wrong_then_restored_fails(self):
        self.mutate_doc(self.evidence['items'][0]['commitSha'], 'architecture',
                        lambda d: d['hubs'][0].update(children=999))
        with self.assertRaisesRegex(ValueError, 'pinned renderer: architecture'):
            self.check()

    def test_renderer_code_must_match_pinned_controller(self):
        self.git.documents[(BASE, 'site-factory/engine/render_snapshot.py')] += b'\n# other renderer\n'
        with self.assertRaisesRegex(ValueError, 'renderer differs from pinned'):
            self.check()

    def test_earlier_checkpoint_mutation_detected(self):
        self.mutate_doc(self.evidence['items'][1]['commitSha'],'pages',lambda d:d[2].update(description='changed'))
        with self.assertRaisesRegex(ValueError,'pinned renderer'):self.check()


if __name__=='__main__':unittest.main()
