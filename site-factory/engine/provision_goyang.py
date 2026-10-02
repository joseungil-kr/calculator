#!/usr/bin/env python3
"""Prepare a deterministic, local-only reviewed v2 region bootstrap.

This deliberately has no network, commit, push, deployment, Airtable, content
writer or approval operation. The existing scheduled Creator consumes the bundle.
"""
import argparse
import ctypes
import contextlib
import errno
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile

REPOSITORY = 'joseungil-kr/fwith-site-factory'
SITE_KEY = 'goyang-flower-v2'
LAUNCH_KEY = 'goyang-flower-v2-launch'
BRANCH = 'site-factory-goyang-v2'
ROOT = 'site-factory/goyang-flower'
TEMPLATE_KEY = 'flower-local-v2'
SOURCE_BRANCH = 'site-factory-flower-v2-template'
SOURCE_ROOT = 'site-factory/templates/flower-local-v2'
SOURCE_REVISION = '2ead40cecc0fe0925f69395e4798a35c0aec1894'
# Independently reviewed 54-file tree, not the source branch's mutable HEAD.
SOURCE_TREE = '52fa60037b12c0762dda16b61ab95c3fc62270b1'
SOURCE_COUNT = 54
STAGING_WORKER = 'goyang-flower-guide-qa'
PRODUCTION_PLACEHOLDER = 'goyang-flower-prod-disabled'
STAGING_URL = 'https://goyang-flower-guide-qa.joseungil.workers.dev'
SITE_URL = 'https://goyang.fwith.kr'
REGISTRY_PATH = '.github/site-factory-sites.json'
TEMPLATE_REGISTRY_PATH = '.github/site-factory-templates.json'
PROVENANCE_PATH = '.github/site-factory-provisioning/goyang-flower-v2.json'
ADAPTATIONS = {
    'src/data/site-config.json', 'src/data/architecture.json',
    'src/data/publish-manifest.json', 'src/data/page-map.json',
    'wrangler.staging.jsonc', 'wrangler.jsonc',
}
CATEGORY_TYPES = {
    'funeral': ['funeral-facility', 'order-help', 'price-guide'],
    'business': ['business-opening'], 'school': ['school-event'],
    'event': ['event-venue'],
    'gift': ['hospital-visit', 'personal-gift', 'station-transit'],
    'order': ['order-help', 'price-guide', 'message-guide'],
}
REGIONS = {'goyang-flower-v2': '고양', 'seongnam-flower-v2': '성남'}


class ProvisionError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ProvisionError(message)


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def git(repo, *args, optional=False):
    # Ignore caller Git redirections/replacement objects and forbid promisor
    # lazy fetches: all source bytes must already be present locally.
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    env.update(GIT_NO_REPLACE_OBJECTS='1', GIT_NO_LAZY_FETCH='1',
               GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL=os.devnull)
    run = subprocess.run(['git', '--no-optional-locks', '-C', str(repo), *args], capture_output=True, env=env)
    if run.returncode:
        if optional:
            return None
        raise ProvisionError('Git object read failed: ' + ' '.join(args) + '\n' + run.stderr.decode(errors='replace'))
    return run.stdout


def full_commit(repo, value):
    require(bool(re.fullmatch('[0-9a-f]{40}', value)), 'A full lowercase commit SHA is required')
    require(git(repo, 'cat-file', '-t', value).strip() == b'commit', 'Expected a commit object')
    return value


def safe_path(name):
    path = PurePosixPath(name)
    require(bool(name) and not path.is_absolute() and str(path) == name
            and all(p not in {'.', '..', '.git', 'node_modules', 'dist', '.astro'} for p in path.parts)
            and '\\' not in name and not any(ord(c) < 32 for c in name), 'Unsafe/untracked build path: ' + name)
    require(path.name != 'build-revision.json', 'Generated revision cannot be provisioned')
    return name


def read_tree(repo, revision, root):
    safe_path(root)
    rows = git(repo, 'ls-tree', '-rz', revision, '--', root).split(b'\0')
    files, manifest = {}, []
    for row in filter(None, rows):
        meta, raw_path = row.split(b'\t', 1)
        mode, kind, oid = meta.decode().split()
        path = raw_path.decode('utf-8')
        require(path.startswith(root + '/'), 'Destination root is occupied by a non-directory')
        relative = safe_path(path[len(root) + 1:])
        require(mode == '100644' and kind == 'blob', 'Only regular non-executable source blobs are allowed: ' + path)
        require(relative not in files, 'Duplicate source path')
        data = git(repo, 'cat-file', 'blob', oid)
        # Verify bytes, even when Git is configured to use replacement objects.
        require(hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == oid,
                'Source blob hash mismatch: ' + relative)
        files[relative] = data
        manifest.append({'path': relative, 'mode': mode, 'gitBlob': oid, 'sha256': sha256(data)})
    return files, manifest


def read_json(repo, revision, path):
    try:
        return json.loads(git(repo, 'show', revision + ':' + path))
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ProvisionError('Invalid JSON: ' + path) from error


def target_contract(site_key=SITE_KEY):
    require(site_key in REGIONS, 'Region is not in the reviewed v2 bootstrap allowlist')
    region_slug = site_key.split('-')[0]
    worker = region_slug + '-flower-guide-qa'
    return {'siteKey': site_key, 'region': REGIONS[site_key],
            'branch': 'site-factory-' + region_slug + '-v2', 'root': 'site-factory/' + region_slug + '-flower',
            'siteUrl': 'https://' + region_slug + '.fwith.kr', 'stagingWorker': worker,
            'productionWorker': region_slug + '-flower-prod-disabled',
            'stagingUrl': 'https://' + worker + '.joseungil.workers.dev',
            'provenancePath': '.github/site-factory-provisioning/' + site_key + '.json'}


def checked_launch_key(site_key, launch_key):
    if site_key == SITE_KEY:
        require(launch_key in (None, LAUNCH_KEY), 'Goyang launch identity is fixed')
        return LAUNCH_KEY
    require(isinstance(launch_key, str) and re.fullmatch(re.escape(site_key) + r'-trial-[a-z0-9][a-z0-9-]{0,50}', launch_key),
            'A distinct explicit regional trial launch key is required; legacy 30-page launch cannot be reused')
    return launch_key


def site_entry(site_key=SITE_KEY):
    target = target_contract(site_key)
    entry = {
        'repo': REPOSITORY, 'branch': target['branch'], 'root': target['root'], 'siteUrl': target['siteUrl'],
        'primaryLandingSlug': '', 'heroPath': '', 'worker': target['productionWorker'],
        'launchMode': 'staging', 'productionEnabled': False,
        'naverVerification': '', 'indexnowKey': '', 'templateKey': TEMPLATE_KEY,
        'allowedCategories': list(CATEGORY_TYPES),
        'allowedPageTypes': list(dict.fromkeys(t for values in CATEGORY_TYPES.values() for t in values)),
        'categoryPageTypes': CATEGORY_TYPES, 'snapshotRenderer': 'structured-json-v12',
        'growthPaused': True, 'autoDeploySnapshots': False, 'graphScript': 'scripts/qa_graph.mjs',
        'stagingWranglerConfig': 'wrangler.staging.jsonc', 'stagingUrl': target['stagingUrl'],
        'requireRevisionApproval': True, 'requireSnapshotApproval': True,
        'approvedRevision': '', 'approvalEvidenceUrl': '',
    }
    if site_key != SITE_KEY:
        entry.update(stagingBuildIsolation=True, stagingWorker=target['stagingWorker'])
    return entry


def validate_registry(registry, site_key=SITE_KEY):
    require(registry.get('schemaVersion') == 1 and isinstance(registry.get('sites'), dict),
            'Unsupported trusted site registry')
    target = target_contract(site_key)
    expected = site_entry(site_key)
    existing = registry['sites'].get(site_key)
    require(existing is None or existing == expected, 'Regional registry identity/policy collision; no overwrite')
    for key, site in registry['sites'].items():
        require(isinstance(site, dict), 'Malformed registered site: ' + key)
        if key == site_key:
            continue
        require(site.get('branch') != target['branch'], 'Protected/existing branch collision: ' + key)
        other_root = str(site.get('root', '')).strip('/')
        require(not other_root or not (other_root == target['root'] or target['root'].startswith(other_root + '/') or other_root.startswith(target['root'] + '/')),
                'Protected/existing root collision: ' + key)
        for field in ('siteUrl', 'stagingUrl'):
            require(str(site.get(field, '')).rstrip('/').lower() not in {target['siteUrl'].lower(), target['stagingUrl'].lower()},
                    'Registered URL collision: ' + key)
        for field in ('worker', 'stagingWorker'):
            require(site.get(field) not in {target['stagingWorker'], target['productionWorker']}, 'Registered Worker collision: ' + key)
    return existing is not None


def validate_empty(files, site_key):
    data = lambda name: json.loads(files['src/data/' + name + '.json'])
    require(data('pages') == [], 'Bootstrap must contain zero customer pages')
    for name in ('architecture', 'publish-manifest', 'page-map'):
        value = data(name)
        require(value['siteKey'] == site_key and value['pages'] == [], 'Nonempty or mismatched ' + name)
    require(data('publish-manifest')['snapshotLedger'] == {}, 'Snapshot ledger must be empty')
    architecture = data('architecture')
    require(architecture['home']['url'] == '/' and architecture['home']['pageRole'] == 'REGION_SERVICE_LANDING',
            'Unexpected home contract')
    require([h['category'] for h in architecture['hubs']] == list(CATEGORY_TYPES), 'Unexpected hubs')
    for hub in architecture['hubs']:
        require(hub['url'] == '/' + hub['category'] + '/' and hub['children'] == 0
                and hub['indexable'] is False and hub['menuVisible'] is False, 'Empty hub must remain hidden and noindex')
    config = data('site-config')
    require(config['siteKey'] == site_key and config['productionApproved'] is False and config['naverVerification'] == '',
            'Production/verification state must remain disabled')
    for name in ('wrangler.jsonc', 'wrangler.staging.jsonc'):
        conf = json.loads(files[name])
        require('route' not in conf and 'routes' not in conf and conf['workers_dev'] is True
                and conf['assets']['directory'] == './dist/', 'Worker must have no custom/production routes')
    require(json.loads(files['wrangler.jsonc'])['name'] != json.loads(files['wrangler.staging.jsonc'])['name'],
            'QA and production names must be distinct')


def adapt(source, site_key=SITE_KEY):
    validate_empty(source, 'template-only')
    target = target_contract(site_key)
    files = dict(source)
    for name in sorted(ADAPTATIONS):
        value = json.loads(files[name])
        if name.startswith('src/data/'):
            value['siteKey'] = site_key
            if name.endswith('/site-config.json'):
                value.update(region=target['region'], previewUrl=target['stagingUrl'], stagingWorker=target['stagingWorker'])
            elif name.endswith('/architecture.json'):
                value['home']['primaryKeyword'] = target['region'] + ' 꽃배달'
        else:
            value['name'] = target['stagingWorker'] if name == 'wrangler.staging.jsonc' else target['productionWorker']
        files[name] = encode(value)
    require({p for p in files if files[p] != source[p]} == ADAPTATIONS, 'Only the six reviewed adaptations are permitted')
    validate_empty(files, site_key)
    return files


def manifest_for(files):
    return [{'path': name, 'sha256': sha256(data)} for name, data in sorted(files.items())]


def prepare(repo, control_revision, target_revision, site_key=SITE_KEY, launch_key=None):
    target = target_contract(site_key)
    launch_key = checked_launch_key(site_key, launch_key)
    full_commit(repo, control_revision)
    full_commit(repo, SOURCE_REVISION)
    template_registry = read_json(repo, control_revision, TEMPLATE_REGISTRY_PATH)
    require(template_registry.get('schemaVersion') == 1, 'Unsupported template registry')
    expected_template = {'sourceBranch': SOURCE_BRANCH, 'sourceRoot': SOURCE_ROOT,
                         'sourceRevision': SOURCE_REVISION, 'productionReady': False}
    require(template_registry.get('templates', {}).get(TEMPLATE_KEY) == expected_template,
            'Trusted registry does not contain the exact reviewed source pin')
    tree = git(repo, 'rev-parse', SOURCE_REVISION + ':' + SOURCE_ROOT).decode().strip()
    require(tree == SOURCE_TREE, 'Source tree differs from independently reviewed source')
    source, source_manifest = read_tree(repo, SOURCE_REVISION, SOURCE_ROOT)
    require(len(source) == SOURCE_COUNT, 'Expected exactly 54 tracked source files')
    files = adapt(source, site_key)
    registry = read_json(repo, control_revision, REGISTRY_PATH)
    already_registered = validate_registry(registry, site_key)
    # A root accidentally present on main must never be silently overwritten.
    control_files, _ = read_tree(repo, control_revision, target['root'])
    require(not control_files, 'Target root already exists on control revision')
    provenance = {
        'schemaVersion': 1, 'kind': 'site-factory-infrastructure-bootstrap-v1',
        'siteKey': site_key, 'launchKey': launch_key, 'repository': REPOSITORY,
        'branch': target['branch'], 'root': target['root'],
        'templateKey': TEMPLATE_KEY, 'sourceBranch': SOURCE_BRANCH,
        'sourceRoot': SOURCE_ROOT, 'sourceRevision': SOURCE_REVISION,
        'sourceTree': SOURCE_TREE, 'sourceManifest': source_manifest,
        'sourceManifestSha256': sha256(encode(source_manifest)),
        'adaptedFiles': sorted(ADAPTATIONS), 'targetManifest': manifest_for(files),
        'customerPages': 0, 'snapshotApprovalGranted': False,
        'productionEnabled': False, 'growthPaused': True, 'autoDeploySnapshots': False,
    }
    if site_key != SITE_KEY:
        provenance['trialDetailTarget'] = 1
    provenance['bootstrapId'] = sha256(encode(provenance))
    target_files = {target['root'] + '/' + name: data for name, data in files.items()}
    target_files[target['provenancePath']] = encode(provenance)
    # Caller must read branch existence remotely, then fetch the exact SHA.
    # Local refs provide a second collision guard, not remote absence evidence.
    known_refs = [git(repo, 'rev-parse', '--verify', ref, optional=True)
                  for ref in ('refs/heads/' + target['branch'], 'refs/remotes/origin/' + target['branch'])]
    if target_revision == 'absent':
        require(not any(known_refs), 'Target branch already exists locally; supply its exact remote revision')
        target_state = 'create'
    else:
        full_commit(repo, target_revision)
        require(all(ref is None or ref.decode().strip() == target_revision for ref in known_refs),
                'Observed target revision disagrees with a local branch/ref; refresh before retry')
        observed, _ = read_tree(repo, target_revision, target['root'])
        require(observed == files, 'Existing target differs from exact bootstrap; never overwrite customer content or conflicts')
        require(git(repo, 'show', target_revision + ':' + target['provenancePath'], optional=True) == encode(provenance),
                'Existing target has no matching bootstrap provenance')
        target_state = 'unchanged'
    registry['sites'][site_key] = site_entry(site_key)
    # Preserve the existing registry's ordering and formatting convention.
    proposed_registry = (json.dumps(registry, ensure_ascii=False, indent=2) + '\n').encode()
    plan = {
        'schemaVersion': 1, 'bootstrapId': provenance['bootstrapId'],
        'status': 'local_proposal_only', 'siteKey': site_key, 'launchKey': launch_key,
        'repository': REPOSITORY, 'controlRevision': control_revision,
        'expectedTargetRevision': target_revision, 'targetBranch': target['branch'],
        'targetState': target_state, 'registryState': 'unchanged' if already_registered else 'add',
        'sourceRevision': SOURCE_REVISION, 'sourceTree': SOURCE_TREE,
        'targetFiles': manifest_for(target_files), 'registryPath': REGISTRY_PATH,
        'registrySha256': sha256(proposed_registry), 'customerPagesCreated': 0,
        'externalActionsPerformed': [],
        'publicationPreconditions': [
            'Cloudflare branch/build boundaries independently cleared by the parent',
            'Read current main and target refs; they must equal the expected revisions',
            'Recheck all registered and hosted Worker/route collisions before writing',
            'Use non-force optimistic Git updates; on races recompute from fresh control revision',
            'Commit only listed targetFiles to the target branch; registryPath alone to control main',
            'Actual reviewed Draft must later use the existing frozen Publisher and snapshot approval path',
        ],
    }
    if site_key != SITE_KEY:
        plan['trialDetailTarget'] = 1
    outputs = {'target-files/' + p: b for p, b in target_files.items()}
    outputs['control-files/' + REGISTRY_PATH] = proposed_registry
    outputs['provisioning-plan.json'] = encode(plan)
    return outputs, plan


def publish_directory(temporary, destination):
    """Atomic no-replace publication on the supported Linux execution hosts."""
    libc = ctypes.CDLL(None, use_errno=True)
    rename = getattr(libc, 'renameat2', None)
    require(rename is not None, 'Atomic no-replace directory rename is unavailable; no output published')
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    # AT_FDCWD=-100; RENAME_NOREPLACE=1. A competing empty directory is a
    # collision too; ordinary Path.rename/os.rename would overwrite it.
    result = rename(-100, os.fsencode(temporary), -100, os.fsencode(destination), 1)
    if result:
        code = ctypes.get_errno()
        if code == errno.EEXIST:
            raise ProvisionError('Output was concurrently created; no overwrite')
        raise OSError(code, os.strerror(code), str(destination))


@contextlib.contextmanager
def anchored_parent(destination):
    """Keep writes beneath the checked directory even if its pathname moves."""
    require(hasattr(os, 'O_NOFOLLOW') and Path('/proc/self/fd').is_dir(),
            'Linux no-follow directory handles are required; no output published')
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open('/', flags)
    try:
        for component in destination.parent.parts[1:]:
            next_fd = os.open(component, flags, dir_fd=fd)
            os.close(fd)
            fd = next_fd
        yield Path('/proc/self/fd') / str(fd)
    finally:
        os.close(fd)


def materialize(outputs, destination):
    destination = Path(os.path.abspath(destination))
    for path in outputs:
        safe_path(path)
    # Opening each parent with O_NOFOLLOW blocks both pre-existing symlinks
    # and parent-swap races. Paths below the retained fd stay on that directory.
    try:
        with anchored_parent(destination) as parent:
            anchored = parent / destination.name
            require(not anchored.is_symlink(), 'Symlink output path is forbidden')
            if anchored.exists():
                require(anchored.is_dir(), 'Output destination is occupied')
                found = {}
                for path in anchored.rglob('*'):
                    require(not path.is_symlink(), 'Symlink found in existing output')
                    if path.is_file():
                        found[path.relative_to(anchored).as_posix()] = path.read_bytes()
                    else:
                        require(path.is_dir(), 'Non-regular output entry')
                require(found == outputs, 'Output collision: remove nothing; choose a new empty destination')
                return False
            temporary = Path(tempfile.mkdtemp(prefix='.' + destination.name + '-', dir=parent))
            try:
                for name, data in sorted(outputs.items()):
                    path = temporary / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(data)
                current_parent = os.stat(destination.parent, follow_symlinks=False)
                held_parent = parent.stat()
                require((current_parent.st_dev, current_parent.st_ino) == (held_parent.st_dev, held_parent.st_ino),
                        'Output parent changed during preparation; no output published')
                publish_directory(temporary, anchored)
            finally:
                if temporary.exists():
                    shutil.rmtree(temporary)
            return True
    except OSError as error:
        if error.errno in (errno.ELOOP, errno.ENOTDIR):
            raise ProvisionError('Symlink or non-directory output parent is forbidden') from error
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--control-revision', required=True, help='Fresh full trusted main SHA, never a mutable ref')
    parser.add_argument('--target-revision', required=True, help='Fresh observed full target SHA, or explicit absent')
    parser.add_argument('--site-key', choices=sorted(REGIONS), default=SITE_KEY)
    parser.add_argument('--launch-key', help='Explicit new trial identity for a new region; never reuse its legacy launch')
    output = parser.add_mutually_exclusive_group(required=True)
    output.add_argument('--output', type=Path, help='New bundle directory, or byte-identical prior output (Linux)')
    output.add_argument('--dry-run', action='store_true', help='Validate and print the proposal without writing files')
    args = parser.parse_args()
    try:
        outputs, plan = prepare(args.repo, args.control_revision, args.target_revision, args.site_key, args.launch_key)
        if args.dry_run:
            print(json.dumps(plan, ensure_ascii=False, sort_keys=True))
            return
        written = materialize(outputs, args.output)
        print(json.dumps({'status': plan['status'], 'bootstrapId': plan['bootstrapId'],
                          'targetState': plan['targetState'], 'registryState': plan['registryState'],
                          'outputWritten': written, 'output': str(args.output)}, sort_keys=True))
    except (ProvisionError, KeyError, TypeError, json.JSONDecodeError, OSError) as error:
        parser.exit(1, 'PROVISIONING_BLOCKED: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
