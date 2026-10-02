import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from batch_barrier import GATES, GitEvidence, check, identity
from render_snapshot import frozen_hashes, parse_payload, validate_content
from test_engine import payload

BASE, COMMIT, FINAL = 'a' * 40, 'b' * 40, 'c' * 40
ROOT = 'site/src/data/'


class MemoryGit:
    def __init__(self, documents):
        self.documents = documents

    def read(self, revision, path):
        return self.documents[(revision, path)]

    def ancestor(self, older, newer):
        return (older, newer) in {(BASE, COMMIT), (COMMIT, FINAL)}


def fixture():
    batch = {'schemaVersion': 1, 'batchId': 'seongnam-initial-50', 'siteKey': 'test', 'targetDetails': 50,
             'canaryPageKey': 'detail-0', 'ruleRevision': BASE, 'templateRevision': BASE, 'registryRevision': BASE,
             'members': [{'pageKey': f'detail-{i}', 'intentKey': f'intent-{i}'} for i in range(50)]}
    batch['membershipHash'] = identity(batch)
    rows, items = [], []
    for i, member in enumerate(batch['members']):
        args = {'PAGE_KEY': member['pageKey'], 'INTENT_KEY': member['intentKey'], 'SLUG': f'detail-{i}',
                'SNAPSHOT_ID': f'snapshot-{i}', 'PUBLISH_QUEUE_RECORD_ID': f'rec{i:014d}'}
        body = payload(**args)
        _, reviewed = frozen_hashes(validate_content(parse_payload(body)))
        body = payload(**args, APPROVAL_STATUS='approved', APPROVED_SNAPSHOT_HASH=reviewed)
        p = validate_content(parse_payload(body))
        storage, reviewed = frozen_hashes(p)
        rows.append({'pageKey': member['pageKey'], 'snapshotId': p['SNAPSHOT_ID'], 'snapshotHash': storage,
                     'draftKey': p['DRAFT_KEY'], 'sourceRecordId': p['SOURCE_RECORD_ID'], 'publishQueueRecordId': p['PUBLISH_QUEUE_RECORD_ID'],
                     'url': p['url'], 'status': 'approved', 'approvalVerified': True})
        items.append(member | {'ruleRevision': BASE, 'templateRevision': BASE, 'registryRevision': BASE,
                              'draftRevision': 'writer-v1', 'payload': body, 'reviewDigest': reviewed,
                              'snapshotHash': storage, 'queueRecordId': p['PUBLISH_QUEUE_RECORD_ID'],
                              'issueUrl': f'https://github.com/owner/repo/issues/{i+1}', 'snapshotId': p['SNAPSHOT_ID'],
                              'commitSha': COMMIT, 'reviewSourceSha': BASE,
                              'reviewerApproval': {'status': 'approved', 'reviewer': 'fixture-reviewer',
                                                   'evidenceUrl': 'https://example.com/review', 'draftRevision': 'writer-v1',
                                                   'reviewDigest': reviewed, 'membershipHash': batch['membershipHash']}})
    manifest = json.dumps({'siteKey': 'test', 'pages': rows}).encode()
    docs = {(BASE, '.github/site-factory-sites.json'): json.dumps({'sites': {'test': {'repo': 'owner/repo', 'branch': 'site', 'root': 'site'}}}).encode(),
            (BASE, ROOT + 'publish-manifest.json'): b'{"pages": []}',
            (COMMIT, ROOT + 'publish-manifest.json'): manifest,
            (FINAL, ROOT + 'publish-manifest.json'): manifest,
            (FINAL, ROOT + 'architecture.json'): json.dumps({'hubs': [{'url': '/gift/'}], 'pages': [r | {'intentKey': f'intent-{i}'} for i, r in enumerate(rows)]}).encode()}
    qa = {'sourceSha': FINAL, 'manifestSha256': hashlib.sha256(manifest).hexdigest(), 'state': 'passed',
          'environment': 'staging', 'noindex': True, 'reviewer': 'fixture-independent-qa',
          'evidenceUrl': 'https://example.com/qa', 'gates': sorted(GATES),
          'routes': [{'url': url, 'state': 'passed', 'noindex': True} for url in ['/', '/gift/'] + [r['url'] for r in rows]]}
    return batch, {'batchId': batch['batchId'], 'membershipHash': batch['membershipHash'], 'items': items,
                   'finalSourceSha': FINAL, 'qa': qa}, MemoryGit(docs)


class BarrierTests(unittest.TestCase):
    def setUp(self):
        self.batch, self.evidence, self.git = fixture()

    def check(self):
        return check(self.batch, self.evidence, self.git)

    def test_exact_fifty_staging_only_and_no_mutation(self):
        before = copy.deepcopy((self.batch, self.evidence, self.git.documents))
        result = self.check()
        self.assertEqual((result['state'], result['detailCount'], result['homeCount'], result['hubCount'], result['qaRouteCount']),
                         ('staging_complete', 50, 1, 1, 52))
        self.assertFalse(result['productionApproved']); self.assertFalse(result['indexNowAllowed'])
        self.assertEqual(before, (self.batch, self.evidence, self.git.documents))
        self.assertEqual(result, self.check())

    def test_order_independent_identity(self):
        self.batch['members'].reverse()
        self.assertEqual(identity(self.batch), self.batch['membershipHash'])
        self.check()

    def test_fail_closed_mutations(self):
        mutations = [
            lambda b, e: b.update(targetDetails=49),
            lambda b, e: b['members'].pop(),
            lambda b, e: b['members'][1].update(intentKey='intent-0'),
            lambda b, e: b.update(canaryPageKey='missing'),
            lambda b, e: b.update(ruleRevision='d' * 40),
            lambda b, e: e.update(batchId='other'),
            lambda b, e: e['items'].pop(),
            lambda b, e: e['items'].append(copy.deepcopy(e['items'][0])),
            lambda b, e: e['items'][1].update(queueRecordId=e['items'][0]['queueRecordId']),
            lambda b, e: e['items'][0].update(draftRevision='writer-v2'),
            lambda b, e: e['items'][0]['reviewerApproval'].update(status='pending'),
            lambda b, e: e['items'][0]['reviewerApproval'].update(reviewDigest='0' * 64),
            lambda b, e: e['items'][0].update(reviewDigest='0' * 64),
            lambda b, e: e['items'][0].update(snapshotHash='0' * 64),
            lambda b, e: e['items'][0].update(templateRevision='d' * 40),
            lambda b, e: e['items'][0].update(issueUrl='https://github.com/other/repo/issues/1'),
            lambda b, e: e['items'][0].update(commitSha='d' * 40),
            lambda b, e: e['items'][0].update(reviewSourceSha=FINAL),
            lambda b, e: e['qa'].update(sourceSha=COMMIT),
            lambda b, e: e['qa'].update(manifestSha256='0' * 64),
            lambda b, e: e['qa'].update(environment='production'),
            lambda b, e: e['qa'].update(noindex=False),
            lambda b, e: e['qa']['gates'].pop(),
            lambda b, e: e['qa']['routes'].pop(),
            lambda b, e: e['qa']['routes'][0].update(state='http403'),
            lambda b, e: e['qa']['routes'][0].update(noindex=False),
        ]
        for number, mutate in enumerate(mutations):
            with self.subTest(number=number):
                b, e = copy.deepcopy((self.batch, self.evidence))
                mutate(b, e)
                with self.assertRaises(ValueError):
                    check(b, e, self.git)

    def test_final_manifest_mismatch(self):
        path = (FINAL, ROOT + 'publish-manifest.json')
        doc = json.loads(self.git.documents[path]); doc['pages'][0]['snapshotHash'] = '0' * 64
        self.git.documents[path] = json.dumps(doc).encode()
        with self.assertRaisesRegex(ValueError, 'final manifest'):
            self.check()

    def test_new_related_link_invalidates_approval(self):
        self.evidence['items'][0]['payload'] += '\n---BEGIN-RELATED-PAGE-KEYS---\ndetail-49\n---END-RELATED-PAGE-KEYS---'
        with self.assertRaises(ValueError): self.check()

    def test_reapproved_future_related_link_still_rejected(self):
        item = self.evidence['items'][0]
        body = item['payload'] + '\n---BEGIN-RELATED-PAGE-KEYS---\ndetail-49\n---END-RELATED-PAGE-KEYS---'
        p = validate_content(parse_payload(body)); _, reviewed = frozen_hashes(p)
        body = body.replace(item['reviewDigest'], reviewed)
        storage, _ = frozen_hashes(validate_content(parse_payload(body)))
        item.update(payload=body, reviewDigest=reviewed, snapshotHash=storage, draftRevision='writer-v2')
        item['reviewerApproval'].update(reviewDigest=reviewed, draftRevision='writer-v2')
        with self.assertRaisesRegex(ValueError, 'related links'):
            self.check()

    def test_git_reads_committed_bytes_and_checks_history(self):
        with tempfile.TemporaryDirectory() as directory:
            def run(*args):
                return subprocess.check_output(['git', '-C', directory, *args], stderr=subprocess.DEVNULL).decode().strip()
            run('init'); run('config', 'user.name', 'Fixture'); run('config', 'user.email', 'fixture@example.invalid')
            path = Path(directory) / 'manifest.json'; path.write_text('committed')
            run('add', '.'); run('commit', '-m', 'fixture'); revision = run('rev-parse', 'HEAD')
            path.write_text('dirty')
            git = GitEvidence(directory)
            self.assertEqual(git.read(revision, 'manifest.json'), b'committed')
            self.assertTrue(git.ancestor(revision, revision))
            with self.assertRaises(ValueError): git.read('main', 'manifest.json')
            with self.assertRaises(ValueError): git.read(revision, '../manifest.json')


if __name__ == '__main__':
    unittest.main()
