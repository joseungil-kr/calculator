"""Shared v2 bootstrap and isolated staging compatibility proof; no services."""
from contextlib import redirect_stdout
import copy
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

import test_provision_goyang as fixture

p = fixture.p
SITE = 'seongnam-flower-v2'
TRIAL = SITE + '-trial-20261002'
WORKFLOW = Path(__file__).resolve().parents[3] / '.github/workflows/site-staging-deploy.yml'


class RegionTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixture.BootstrapTests('runTest')
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def prepare(self, target='absent', launch=TRIAL):
        f = self.fixture
        return p.prepare(f.repo, f.control, target, SITE, launch)

    def test_distinct_trial_launch_is_required_and_legacy_is_never_reused(self):
        for launch in (None, 'seongnam-flower-v2-launch', 'seongnam-flower-v2-trial-', '../trial', 'wrong-trial-1'):
            with self.subTest(launch=launch), self.assertRaisesRegex(p.ProvisionError, 'distinct explicit regional trial'):
                self.prepare(launch=launch)
        proof = json.loads(self.prepare()[0]['target-files/' + p.target_contract(SITE)['provenancePath']])
        self.assertEqual(proof['launchKey'], TRIAL)
        self.assertEqual(proof['customerPages'], 0)
        self.assertEqual(proof['trialDetailTarget'], 1)
        self.assertFalse(proof['snapshotApprovalGranted'])

    def test_seongnam_uses_same_six_adaptations_and_preserves_all_other_bytes(self):
        source = self.fixture.source
        adapted = p.adapt(source, SITE)
        self.assertEqual({name for name in source if source[name] != adapted[name]}, p.ADAPTATIONS)
        self.assertEqual(adapted['public/product.jpg'], source['public/product.jpg'])
        config = json.loads(adapted['src/data/site-config.json'])
        self.assertEqual(config['region'], '성남')
        self.assertEqual(config['previewUrl'], 'https://seongnam-flower-guide-qa.joseungil.workers.dev')
        self.assertEqual(json.loads(adapted['src/data/architecture.json'])['home']['primaryKeyword'], '성남 꽃배달')
        p.validate_empty(adapted, SITE)

    def test_all_existing_regions_are_preserved_and_registration_is_only_a_proposal(self):
        f = self.fixture
        f.registry['sites'][p.SITE_KEY] = p.site_entry()
        f.save_registry()
        outputs, plan = self.prepare()
        registry = json.loads(outputs['control-files/' + p.REGISTRY_PATH])
        self.assertEqual({key: registry['sites'][key] for key in f.registry['sites']}, f.registry['sites'])
        self.assertEqual(registry['sites'][SITE], p.site_entry(SITE))
        self.assertTrue(registry['sites'][SITE]['stagingBuildIsolation'])
        self.assertEqual(plan['registryState'], 'add')
        self.assertEqual(plan['externalActionsPerformed'], [])
        self.assertEqual(plan['targetBranch'], 'site-factory-seongnam-v2')
        self.assertEqual(plan['trialDetailTarget'], 1)
        self.assertFalse((f.repo / 'site-factory/seongnam-flower').exists())

    def test_trial_identity_is_deterministic_and_part_of_resume_provenance(self):
        outputs, plan = self.prepare()
        self.assertEqual((outputs, plan), self.prepare())
        for path, data in outputs.items():
            if path.startswith('target-files/'):
                self.fixture.write(path[len('target-files/'):], data)
        revision = self.fixture.commit()
        self.assertEqual(self.prepare(revision)[1]['targetState'], 'unchanged')
        with self.assertRaisesRegex(p.ProvisionError, 'matching bootstrap provenance'):
            self.prepare(revision, SITE + '-trial-other')

    def test_unknown_regions_protected_targets_and_customer_content_fail_closed(self):
        with self.assertRaisesRegex(p.ProvisionError, 'allowlist'):
            p.target_contract('ansan-flower-test')
        registry = copy.deepcopy(self.fixture.registry)
        registry['sites']['protected'] = {'root': 'site-factory/seongnam-flower'}
        with self.assertRaisesRegex(p.ProvisionError, 'root collision'):
            p.validate_registry(registry, SITE)
        outputs, _ = self.prepare()
        for path, data in outputs.items():
            if path.startswith('target-files/'):
                self.fixture.write(path[len('target-files/'):], data)
        self.fixture.write('site-factory/seongnam-flower/src/data/pages.json', p.encode([{'existingCustomer': True}]))
        revision = self.fixture.commit()
        with self.assertRaisesRegex(p.ProvisionError, 'never overwrite'):
            self.prepare(revision)

    def test_goyang_public_defaults_and_policy_are_preserved(self):
        target = p.target_contract()
        self.assertEqual(target['root'], p.ROOT)
        self.assertEqual(target['branch'], p.BRANCH)
        self.assertEqual(target['stagingWorker'], p.STAGING_WORKER)
        self.assertEqual(p.checked_launch_key(p.SITE_KEY, None), p.LAUNCH_KEY)
        self.assertNotIn('stagingBuildIsolation', p.site_entry())
        self.assertEqual(p.adapt(self.fixture.source), p.adapt(self.fixture.source, p.SITE_KEY))

    def test_dry_run_cli_does_not_materialize_or_contact_services(self):
        f = self.fixture
        stdout = io.StringIO()
        with patch.object(sys, 'argv', ['provision_goyang.py', '--repo', str(f.repo), '--control-revision', f.control,
                                       '--target-revision', 'absent', '--site-key', SITE, '--launch-key', TRIAL, '--dry-run']), \
                patch.object(p, 'materialize', side_effect=AssertionError('must not write')), redirect_stdout(stdout):
            p.main()
        self.assertEqual(json.loads(stdout.getvalue())['launchKey'], TRIAL)


class StagingTests(unittest.TestCase):
    def resolve(self, entry, key=SITE, revision='a' * 40):
        text = WORKFLOW.read_text(encoding='utf-8')
        block = re.search(r'- name: Resolve isolated preview target.*?python3 - <<\'PYTHON\'\n(.*?)\n          PYTHON', text, re.S).group(1)
        code = '\n'.join(line[10:] for line in block.splitlines())
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            (temp / 'control/.github').mkdir(parents=True)
            (temp / 'control/.github/site-factory-sites.json').write_text(json.dumps({'sites': {key: entry}}), encoding='utf-8')
            previous = Path.cwd()
            try:
                os.chdir(temp)
                with patch.dict(os.environ, {'SITE_KEY': key, 'REVISION': revision, 'ISSUE_BODY': '',
                                             'GITHUB_REPOSITORY': p.REPOSITORY, 'GITHUB_OUTPUT': str(temp / 'outputs')}, clear=True):
                    exec(code, {})
                return dict(line.split('=', 1) for line in (temp / 'outputs').read_text().splitlines())
            finally:
                os.chdir(previous)

    def test_seongnam_isolated_path_is_fixed_and_paused(self):
        result = self.resolve(p.site_entry(SITE))
        self.assertEqual(result['url'], 'https://seongnam-flower-guide-qa.joseungil.workers.dev')
        self.assertEqual(result['build_root'], 'preview-build')
        self.assertEqual(result['isolated'], 'true')
        self.assertEqual(result['branch'], 'site-factory-seongnam-v2')

    def test_isolated_identity_and_closed_gates_cannot_be_relaxed(self):
        for field, value in [('productionEnabled', True), ('growthPaused', False), ('autoDeploySnapshots', True),
                             ('stagingWorker', p.STAGING_WORKER), ('branch', p.BRANCH), ('root', p.ROOT),
                             ('requireSnapshotApproval', False), ('indexnowKey', 'unapproved'), ('templateKey', 'wrong'),
                             ('stagingBuildIsolation', False)]:
            entry = p.site_entry(SITE)
            entry[field] = value
            with self.subTest(field=field), self.assertRaises(SystemExit):
                self.resolve(entry)
        with self.assertRaises(SystemExit):
            self.resolve(p.site_entry(SITE), revision='HEAD')

    def test_suwon_legacy_path_and_goyang_canonical_guard_are_preserved(self):
        registry = json.loads((WORKFLOW.parents[1] / 'site-factory-sites.json').read_text(encoding='utf-8'))['sites']
        result = self.resolve(registry['suwon-flower-test'], 'suwon-flower-test')
        self.assertEqual(result['url'], registry['suwon-flower-test']['stagingUrl'])
        self.assertEqual(result['build_root'], 'target/site-factory/suwon-flower')
        self.assertEqual(result['isolated'], 'false')
        with self.assertRaisesRegex(SystemExit, 'legacy staging would revert'):
            self.resolve(registry[p.SITE_KEY], p.SITE_KEY)

    def test_only_opted_in_v2_builds_are_isolated_and_version_pinned(self):
        text = WORKFLOW.read_text(encoding='utf-8')
        self.assertIn("if: steps.target.outputs.isolated == 'true'", text)
        self.assertIn('git -C target merge-base --is-ancestor', text)
        self.assertIn('git -C target archive "$REVISION:$ROOT" | tar -xf - -C preview-build', text)
        self.assertIn('wrangler@4.146.0', text)
        self.assertIn('wrangler@latest', text)
        self.assertIn("SITE_INDEXABLE: 'false'", text)
        self.assertNotIn('schedule:', text)


if __name__ == '__main__':
    unittest.main()
