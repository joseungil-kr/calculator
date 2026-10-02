#!/usr/bin/env python3
"""Read-only initial-50 barrier over existing single-snapshot Publisher evidence."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess

from render_snapshot import parse_payload, validate_content, frozen_hashes

REVISIONS = ('ruleRevision', 'templateRevision', 'registryRevision')
GATES = {'build', 'static', 'graph', 'canonical', 'h1', 'schema', 'robots', 'sitemap', '404'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':')).encode()).hexdigest()


def sha(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{40}', value) is not None


def identity(batch):
    """Order-independent identity; callers must retain the originally frozen hash."""
    return digest({key: batch[key] for key in
                   ('batchId', 'siteKey', 'targetDetails', 'canaryPageKey', *REVISIONS)} |
                  {'members': sorted(batch['members'], key=lambda row: row['pageKey'])})


def indexed(rows, key):
    require(isinstance(rows, list), f'{key} rows must be a list')
    result = {}
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get(key), str) and row[key], f'Missing {key}')
        require(row[key] not in result, f'Duplicate {key}: {row[key]}')
        result[row[key]] = row
    return result


class GitEvidence:
    """Only committed bytes: dirty working files cannot satisfy the barrier."""
    def __init__(self, workspace):
        self.workspace = workspace

    def run(self, *args):
        return subprocess.check_output(['git', '-C', str(self.workspace), *args], stderr=subprocess.PIPE)

    def read(self, revision, path):
        require(sha(revision), 'Expected full lowercase source SHA')
        p = PurePosixPath(path)
        require(not p.is_absolute() and '..' not in p.parts, 'Unsafe evidence path')
        return self.run('show', f'{revision}:{path}')

    def ancestor(self, older, newer):
        require(sha(older) and sha(newer), 'Expected full checkpoint SHA')
        return subprocess.run(['git', '-C', str(self.workspace), 'merge-base', '--is-ancestor', older, newer],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def check(batch, evidence, git):
    """Fail closed; external reviewer/QA assertions must come from trusted consumers."""
    require(batch.get('schemaVersion') == 1, 'Unsupported batch schema')
    require(batch.get('targetDetails') == 50 and type(batch['targetDetails']) is int,
            'Initial batch target is exactly 50; never shrink for query shortage')
    for key in ('batchId', 'siteKey', 'canaryPageKey'):
        require(isinstance(batch.get(key), str) and batch[key].strip(), f'Missing {key}')
    for key in REVISIONS:
        require(sha(batch.get(key)), f'Missing pinned {key}')
    members = indexed(batch['members'], 'pageKey')
    require(len(members) == 50, 'Exactly 50 researched detail members required; insufficient queries remain blocked')
    indexed(batch['members'], 'intentKey')
    require(all(set(m) == {'pageKey', 'intentKey'} for m in members.values()), 'Membership is detail page/intent only')
    require(batch['canaryPageKey'] in members, 'Canary must be a counted detail member')
    require(batch.get('membershipHash') == identity(batch), 'Frozen membership/revision identity changed')
    require(evidence.get('batchId') == batch['batchId'] and
            evidence.get('membershipHash') == batch['membershipHash'], 'Evidence batch identity mismatch')
    final = evidence.get('finalSourceSha')
    require(sha(final), 'Final exact source SHA required')
    registry = json.loads(git.read(batch['registryRevision'], '.github/site-factory-sites.json'))
    target = registry['sites'][batch['siteKey']]
    root = target['root'].strip('/')
    path = root + '/src/data/publish-manifest.json'
    raw_manifest = git.read(final, path)
    manifest = json.loads(raw_manifest)
    require(manifest.get('siteKey') == batch['siteKey'], 'Manifest site mismatch')
    pages = indexed(manifest['pages'], 'pageKey')
    architecture = json.loads(git.read(final, root + '/src/data/architecture.json'))
    architecture_pages = indexed(architecture['pages'], 'pageKey')
    indexed(manifest['pages'], 'url')
    checkpoints = indexed(evidence['items'], 'pageKey')
    require(set(checkpoints) == set(members), 'Missing or extra item checkpoint')
    for field in ('queueRecordId', 'issueUrl', 'snapshotId'):
        indexed(evidence['items'], field)
    for key, member in members.items():
        item = checkpoints[key]
        require(key in architecture_pages and architecture_pages[key].get('intentKey') == member['intentKey'],
                f'{key}: final architecture intent mismatch')
        require(item.get('intentKey') == member['intentKey'], f'{key}: intent mismatch')
        require(all(item.get(r) == batch[r] for r in REVISIONS), f'{key}: pinned revisions changed')
        require(isinstance(item.get('draftRevision'), str) and item['draftRevision'].strip(), f'{key}: missing Writer revision')
        require(re.fullmatch(r'https://github\.com/' + re.escape(target['repo']) + r'/issues/[1-9][0-9]*', item['issueUrl']), f'{key}: wrong Publisher issue')
        payload = validate_content(parse_payload(item['payload']))
        require(payload['SITE_KEY'] == batch['siteKey'] and payload['PAGE_KEY'] == key and
                payload.get('INTENT_KEY') == member['intentKey'], f'{key}: payload identity mismatch')
        require(payload['TARGET_REPO'] == target['repo'] and payload['TARGET_BRANCH'] == target['branch'] and
                payload['TARGET_ROOT'] == target['root'], f'{key}: Publisher target mismatch')
        require(payload['ROUTE_TYPE'] == 'category', f'{key}: HOME/HUB cannot count as details')
        require(architecture_pages[key].get('url') == payload['url'], f'{key}: final architecture route mismatch')
        storage, reviewed = frozen_hashes(payload)
        require(item.get('reviewDigest') == reviewed and item.get('snapshotHash') == storage,
                f'{key}: changed content or graph needs new Writer revision and Reviewer approval')
        approval = item.get('reviewerApproval', {})
        require(approval.get('status') == 'approved' and bool(approval.get('reviewer')) and
                bool(approval.get('evidenceUrl')) and approval.get('draftRevision') == item['draftRevision'] and
                approval.get('reviewDigest') == reviewed and approval.get('membershipHash') == batch['membershipHash'],
                f'{key}: exact Reviewer approval required')
        require(payload.get('APPROVAL_STATUS') == 'approved' and payload.get('APPROVED_SNAPSHOT_HASH') == reviewed,
                f'{key}: Publisher approval mismatch')
        require(item['queueRecordId'] == payload['PUBLISH_QUEUE_RECORD_ID'] and item['snapshotId'] == payload['SNAPSHOT_ID'],
                f'{key}: Queue/snapshot mismatch')
        commit, review_source = item.get('commitSha'), item.get('reviewSourceSha')
        require(git.ancestor(review_source, commit) and git.ancestor(commit, final), f'{key}: checkpoints outside final history')
        baseline = indexed(json.loads(git.read(review_source, path))['pages'], 'pageKey')
        require(all(related in baseline and baseline[related].get('status') == 'approved' and
                    baseline[related].get('approvalVerified') is True for related in payload['relatedKeys']),
                f'{key}: related links must exist in the current explicitly approved review manifest')
        committed = indexed(json.loads(git.read(commit, path))['pages'], 'pageKey')
        expected = {'snapshotId': payload['SNAPSHOT_ID'], 'snapshotHash': storage, 'draftKey': payload['DRAFT_KEY'],
                    'sourceRecordId': payload['SOURCE_RECORD_ID'], 'publishQueueRecordId': item['queueRecordId'],
                    'url': payload['url'], 'status': 'approved', 'approvalVerified': True}
        for label, table in [('checkpoint', committed), ('final', pages)]:
            require(key in table and all(table[key].get(k) == v for k, v in expected.items()),
                    f'{key}: {label} manifest no longer matches approved snapshot')
    routes = {'/'} | {row['url'] for row in pages.values()} | {row['url'] for row in architecture.get('hubs', [])}
    qa = evidence.get('qa', {})
    require(qa.get('sourceSha') == final and qa.get('manifestSha256') == hashlib.sha256(raw_manifest).hexdigest(),
            'QA must bind exact final source and manifest bytes')
    require(qa.get('state') == 'passed' and qa.get('environment') == 'staging' and qa.get('noindex') is True and
            bool(qa.get('reviewer')) and bool(qa.get('evidenceUrl')), 'Independent noindex staging QA required')
    require(set(qa.get('gates', [])) == GATES, 'Missing whole-site QA gates')
    reports = indexed(qa.get('routes', []), 'url')
    require(set(reports) == routes and all(r.get('state') == 'passed' and r.get('noindex') is True for r in reports.values()),
            'Every final HOME/HUB/detail route must pass noindex QA; blocked HTTP is not success')
    return {'state': 'staging_complete', 'batchId': batch['batchId'], 'membershipHash': batch['membershipHash'],
            'finalSourceSha': final, 'detailCount': 50, 'homeCount': 1,
            'hubCount': len({r['url'] for r in architecture.get('hubs', [])}), 'qaRouteCount': len(routes),
            'productionApproved': False, 'indexNowAllowed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--workspace', type=Path, default=Path('.'))
    args = parser.parse_args()
    try:
        result = check(json.loads(args.batch.read_text()), json.loads(args.evidence.read_text()), GitEvidence(args.workspace))
    except (ValueError, KeyError, TypeError, AttributeError, OSError, subprocess.SubprocessError) as error:
        print(json.dumps({'state': 'blocked', 'reason': str(error)}))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
