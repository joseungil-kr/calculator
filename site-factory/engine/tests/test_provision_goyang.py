import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ENGINE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('provision_goyang', ENGINE / 'provision_goyang.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.repo = self.base / 'repo'
        self.repo.mkdir()
        self.run_git('init', '-q')
        self.run_git('config', 'user.name', 'Local test')
        self.run_git('config', 'user.email', 'local-test@example.invalid')
        self.source = {
            'src/data/site-config.json': {'siteKey': 'template-only', 'region': '신규 지역', 'previewUrl': 'https://template.example.invalid', 'stagingWorker': 'template-qa', 'productionApproved': False, 'naverVerification': ''},
            'src/data/architecture.json': {'siteKey': 'template-only', 'home': {'url': '/', 'pageRole': 'REGION_SERVICE_LANDING', 'primaryKeyword': ''}, 'hubs': [{'url': '/' + c + '/', 'category': c, 'label': c, 'children': 0, 'indexable': False, 'menuVisible': False} for c in p.CATEGORY_TYPES], 'pages': []},
            'src/data/publish-manifest.json': {'siteKey': 'template-only', 'pages': [], 'snapshotLedger': {}},
            'src/data/page-map.json': {'siteKey': 'template-only', 'pages': []},
            'src/data/pages.json': [],
            'wrangler.jsonc': {'name': 'template-prod-disabled', 'workers_dev': True, 'assets': {'directory': './dist/'}},
            'wrangler.staging.jsonc': {'name': 'template-qa', 'workers_dev': True, 'assets': {'directory': './dist/'}},
        }
        self.source = {key: p.encode(value) for key, value in self.source.items()}
        # Binary preservation and source-content reuse are byte exact.
        self.source['public/product.jpg'] = b'\xff\xd8\xff\x00original-approved-product'
        for path, data in self.source.items():
            self.write(p.SOURCE_ROOT + '/' + path, data)
        self.source_revision = self.commit()
        self.source_tree = self.run_git('rev-parse', self.source_revision + ':' + p.SOURCE_ROOT).strip()
        self.pins = patch.multiple(p, SOURCE_REVISION=self.source_revision, SOURCE_TREE=self.source_tree, SOURCE_COUNT=len(self.source))
        self.pins.start()
        self.addCleanup(self.pins.stop)
        self.templates = {'schemaVersion': 1, 'templates': {p.TEMPLATE_KEY: {'sourceBranch': p.SOURCE_BRANCH, 'sourceRoot': p.SOURCE_ROOT, 'sourceRevision': p.SOURCE_REVISION, 'productionReady': False}}}
        self.registry = {'schemaVersion': 1, 'sites': {'ansan-flower-test': {'repo': p.REPOSITORY, 'branch': 'site-factory-ansan-v1', 'root': 'site-factory/ansan-flower', 'worker': 'ansan-flower-guide-test', 'productionEnabled': True, 'unrelatedExistingSetting': ['keep', 7]}}}
        self.write(p.TEMPLATE_REGISTRY_PATH, p.encode(self.templates))
        self.write(p.REGISTRY_PATH, p.encode(self.registry))
        self.control = self.commit()

    def run_git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], stderr=subprocess.DEVNULL).decode()

    def write(self, path, data):
        dest = self.repo / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)

    def commit(self):
        self.run_git('add', '.')
        self.run_git('commit', '-qm', 'Local fixture')
        return self.run_git('rev-parse', 'HEAD').strip()

    def prepare(self, target='absent'):
        return p.prepare(self.repo, self.control, target)

    def save_registry(self):
        self.write(p.REGISTRY_PATH, p.encode(self.registry))
        self.control = self.commit()

    def test_exact_six_adaptations_empty_pages_and_policy(self):
        outputs, plan = self.prepare()
        target = {path[len('target-files/' + p.ROOT + '/'):]: data for path, data in outputs.items() if path.startswith('target-files/' + p.ROOT + '/')}
        self.assertEqual(set(target), set(self.source))
        self.assertEqual({path for path in target if target[path] != self.source[path]}, p.ADAPTATIONS)
        self.assertEqual(target['src/data/pages.json'], self.source['src/data/pages.json'])
        self.assertEqual(target['public/product.jpg'], self.source['public/product.jpg'])
        p.validate_empty(target, p.SITE_KEY)
        registry = json.loads(outputs['control-files/' + p.REGISTRY_PATH])
        self.assertEqual(registry['sites']['ansan-flower-test'], self.registry['sites']['ansan-flower-test'])
        self.assertEqual(registry['sites'][p.SITE_KEY], p.site_entry())
        self.assertEqual(plan['customerPagesCreated'], 0)
        self.assertEqual(plan['externalActionsPerformed'], [])

    def test_deterministic_plan_and_byte_identical_materialization(self):
        outputs, plan = self.prepare()
        self.assertEqual((outputs, plan), self.prepare())
        output = self.base / 'bundle'
        self.assertTrue(p.materialize(outputs, output))
        before = {f: f.stat().st_mtime_ns for f in output.rglob('*') if f.is_file()}
        self.assertFalse(p.materialize(outputs, output))
        self.assertEqual(before, {f: f.stat().st_mtime_ns for f in output.rglob('*') if f.is_file()})

    def test_same_target_is_noop_and_changed_customer_page_is_not_overwritten(self):
        outputs, _ = self.prepare()
        for path, data in outputs.items():
            if path.startswith('target-files/'):
                self.write(path[len('target-files/'):], data)
        target = self.commit()
        self.assertEqual(self.prepare(target)[1]['targetState'], 'unchanged')
        self.write(p.ROOT + '/src/data/pages.json', p.encode([{'reviewed': True}]))
        changed = self.commit()
        with self.assertRaisesRegex(p.ProvisionError, 'never overwrite'):
            self.prepare(changed)
        self.assertEqual(json.loads((self.repo / p.ROOT / 'src/data/pages.json').read_text()), [{'reviewed': True}])

    def test_existing_unprovenanced_target_rejected(self):
        for path, data in p.adapt(self.source).items():
            self.write(p.ROOT + '/' + path, data)
        target = self.commit()
        with self.assertRaisesRegex(p.ProvisionError, 'provenance'):
            self.prepare(target)

    def test_provenance_hash_and_source_manifest(self):
        outputs, plan = self.prepare()
        proof = json.loads(outputs['target-files/' + p.PROVENANCE_PATH])
        bootstrap_id = proof.pop('bootstrapId')
        self.assertEqual(bootstrap_id, p.sha256(p.encode(proof)))
        self.assertEqual(plan['bootstrapId'], bootstrap_id)
        self.assertEqual(proof['sourceManifestSha256'], p.sha256(p.encode(proof['sourceManifest'])))
        self.assertEqual(len(proof['sourceManifest']), len(self.source))

    def test_source_pin_mismatch_rejected(self):
        self.templates['templates'][p.TEMPLATE_KEY]['sourceRevision'] = 'f' * 40
        self.write(p.TEMPLATE_REGISTRY_PATH, p.encode(self.templates))
        self.control = self.commit()
        with self.assertRaisesRegex(p.ProvisionError, 'exact reviewed source pin'):
            self.prepare()

    def test_source_tree_mismatch_rejected(self):
        with patch.object(p, 'SOURCE_TREE', 'f' * 40):
            with self.assertRaisesRegex(p.ProvisionError, 'independently reviewed source'):
                self.prepare()

    def test_mutable_ref_rejected(self):
        with self.assertRaisesRegex(p.ProvisionError, 'full lowercase commit SHA'):
            p.prepare(self.repo, 'HEAD', 'absent')

    def test_registered_identity_and_policy_collisions(self):
        for field, value in [('root', 'site-factory/ansan-flower'), ('productionEnabled', True), ('approvedRevision', 'f' * 40), ('growthPaused', False)]:
            with self.subTest(field=field):
                registry = copy.deepcopy(self.registry)
                registry['sites'][p.SITE_KEY] = p.site_entry()
                registry['sites'][p.SITE_KEY][field] = value
                with self.assertRaisesRegex(p.ProvisionError, 'identity/policy collision'):
                    p.validate_registry(registry)

    def test_protected_root_branch_url_and_worker_collisions(self):
        for field, value in [('root', p.ROOT), ('root', 'site-factory'), ('root', p.ROOT + '/child'), ('branch', p.BRANCH), ('siteUrl', p.SITE_URL + '/'), ('stagingUrl', p.STAGING_URL), ('worker', p.PRODUCTION_PLACEHOLDER), ('stagingWorker', p.STAGING_WORKER)]:
            with self.subTest(field=field, value=value):
                registry = copy.deepcopy(self.registry)
                registry['sites']['ansan-flower-test'][field] = value
                with self.assertRaises(p.ProvisionError):
                    p.validate_registry(registry)

    def test_registered_exact_identity_is_noop(self):
        self.registry['sites'][p.SITE_KEY] = p.site_entry()
        self.save_registry()
        self.assertEqual(self.prepare()[1]['registryState'], 'unchanged')

    def test_nonempty_pages_ledger_and_visible_empty_hubs_rejected(self):
        for path, mutate in [
            ('src/data/pages.json', lambda value: value.append({'customer': 'old region'})),
            ('src/data/publish-manifest.json', lambda value: value['snapshotLedger'].update(old='snapshot')),
            ('src/data/architecture.json', lambda value: value['hubs'][0].update(menuVisible=True)),
            ('src/data/architecture.json', lambda value: value['hubs'][0].update(indexable=True)),
            ('src/data/site-config.json', lambda value: value.update(productionApproved=True)),
            ('wrangler.staging.jsonc', lambda value: value.update(routes=['protected.example/*'])),
        ]:
            with self.subTest(path=path):
                source = self.source.copy()
                value = json.loads(source[path])
                mutate(value)
                source[path] = p.encode(value)
                with self.assertRaises(p.ProvisionError):
                    p.adapt(source)

    def test_source_symlinks_and_untracked_build_paths_rejected(self):
        (self.repo / p.SOURCE_ROOT / 'linked').symlink_to('/etc/hosts')
        target = self.commit()
        with self.assertRaisesRegex(p.ProvisionError, 'regular'):
            p.read_tree(self.repo, target, p.SOURCE_ROOT)
        for name in ('../escape', '/tmp/escape', 'a/../b', 'a\\b', 'dist/index.html', '.astro/data', 'node_modules/x', 'src/data/build-revision.json', 'a\nb', 'a//b'):
            with self.subTest(name=name), self.assertRaises(p.ProvisionError):
                p.safe_path(name)

    def test_unlisted_source_and_extra_target_files_rejected(self):
        with patch.object(p, 'SOURCE_COUNT', len(self.source) + 1):
            with self.assertRaisesRegex(p.ProvisionError, '54 tracked'):
                self.prepare()
        outputs, _ = self.prepare()
        for path, data in outputs.items():
            if path.startswith('target-files/'):
                self.write(path[len('target-files/'):], data)
        self.write(p.ROOT + '/stale-region.txt', b'not approved')
        target = self.commit()
        with self.assertRaisesRegex(p.ProvisionError, 'never overwrite'):
            self.prepare(target)

    def test_output_conflict_and_symlink_rejected_without_change(self):
        outputs, _ = self.prepare()
        output = self.base / 'bundle'
        output.mkdir()
        (output / 'operator.txt').write_text('preserve')
        with self.assertRaisesRegex(p.ProvisionError, 'Output collision'):
            p.materialize(outputs, output)
        self.assertEqual((output / 'operator.txt').read_text(), 'preserve')
        link = self.base / 'linked-output'
        link.symlink_to(output, target_is_directory=True)
        with self.assertRaisesRegex(p.ProvisionError, 'Symlink'):
            p.materialize(outputs, link)

    def test_known_branch_absent_and_stale_revision_guards(self):
        self.run_git('branch', p.BRANCH, self.control)
        with self.assertRaisesRegex(p.ProvisionError, 'already exists locally'):
            self.prepare()
        with self.assertRaisesRegex(p.ProvisionError, 'disagrees'):
            self.prepare(self.source_revision)

    def test_occupied_control_root_rejected(self):
        self.write(p.ROOT + '/unexpected.txt', b'preserve')
        self.control = self.commit()
        with self.assertRaisesRegex(p.ProvisionError, 'already exists on control'):
            self.prepare()

    def test_replacement_tree_cannot_substitute_unreviewed_source(self):
        outputs, _ = self.prepare()
        self.write(p.SOURCE_ROOT + '/public/product.jpg', b'unreviewed content')
        alternative = self.commit()
        replacement = self.run_git('rev-parse', alternative + ':' + p.SOURCE_ROOT).strip()
        self.run_git('replace', self.source_tree, replacement)
        self.assertEqual(self.prepare()[0], outputs)

    def test_inherited_git_repository_redirection_is_ignored(self):
        outputs, _ = self.prepare()
        with patch.dict(os.environ, {'GIT_DIR': '/nonexistent/evil', 'GIT_WORK_TREE': '/nonexistent/evil', 'GIT_NO_REPLACE_OBJECTS': '0'}):
            self.assertEqual(self.prepare()[0], outputs)

    def test_concurrent_empty_output_directory_is_not_replaced(self):
        outputs, _ = self.prepare()
        output = self.base / 'bundle'
        publish = p.publish_directory
        observed_inode = []
        def race(temporary, destination):
            destination.mkdir()
            observed_inode.append(destination.stat().st_ino)
            publish(temporary, destination)
        with patch.object(p, 'publish_directory', race):
            with self.assertRaisesRegex(p.ProvisionError, 'concurrently created'):
                p.materialize(outputs, output)
        self.assertTrue(output.is_dir())
        self.assertEqual(output.stat().st_ino, observed_inode[0])
        self.assertEqual(list(output.iterdir()), [])
        self.assertFalse(list(self.base.glob('.bundle-*')))

    def test_parent_symlink_swap_cannot_redirect_output(self):
        outputs, _ = self.prepare()
        parent = self.base / 'output-parent'
        parent.mkdir()
        moved = self.base / 'original-parent'
        unrelated = self.base / 'unrelated'
        unrelated.mkdir()
        (unrelated / 'preserve.txt').write_text('preserve')
        mkdtemp = p.tempfile.mkdtemp
        def race(*args, **kwargs):
            parent.rename(moved)
            parent.symlink_to(unrelated, target_is_directory=True)
            return mkdtemp(*args, **kwargs)
        with patch.object(p.tempfile, 'mkdtemp', race):
            with self.assertRaisesRegex(p.ProvisionError, 'parent changed'):
                p.materialize(outputs, parent / 'bundle')
        self.assertEqual(sorted(f.name for f in unrelated.iterdir()), ['preserve.txt'])
        self.assertEqual((unrelated / 'preserve.txt').read_text(), 'preserve')
        self.assertEqual(list(moved.iterdir()), [])

    def test_output_write_failure_does_not_publish_partial_bundle(self):
        outputs, _ = self.prepare()
        output = self.base / 'bundle'
        with patch.object(Path, 'write_bytes', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                p.materialize(outputs, output)
        self.assertFalse(output.exists())
        self.assertFalse(list(self.base.glob('.bundle-*')))


if __name__ == '__main__':
    unittest.main()
