"""Bucheon-only prospective bootstrap. Fixture Git and no service operations."""
import copy
from contextlib import redirect_stdout
import io
import json
import sys
import unittest
from unittest.mock import patch
import test_provision_goyang as fixture
import test_provision_regions as regions

p=fixture.p
SITE='bucheon-flower-v2'
TRIAL=SITE+'-trial-20261004'

class BucheonTests(unittest.TestCase):
    def setUp(self):
        self.f=fixture.BootstrapTests('runTest');self.f.setUp();self.addCleanup(self.f.doCleanups)
        pins=patch.multiple(p,BUCHEON_SOURCE_TREE=self.f.source_tree,BUCHEON_SOURCE_COUNT=len(self.f.source));pins.start();self.addCleanup(pins.stop)
        self.f.templates['templates'][p.BUCHEON_TEMPLATE_REGISTRY_KEY]={'sourceBranch':p.SOURCE_BRANCH,'sourceRoot':p.SOURCE_ROOT,'sourceRevision':self.f.source_revision,'productionReady':False}
        self.save_templates()

    def save_templates(self):
        self.f.write(p.TEMPLATE_REGISTRY_PATH,p.encode(self.f.templates));self.f.control=self.f.commit()

    def prepare(self,target='absent',launch=TRIAL):
        return p.prepare(self.f.repo,self.f.control,target,SITE,launch)

    def test_only_bucheon_is_added_with_isolated_identity(self):
        self.assertEqual(set(p.REGIONS),{'goyang-flower-v2','seongnam-flower-v2',SITE})
        target=p.target_contract(SITE)
        self.assertEqual((target['branch'],target['root']),('site-factory-bucheon-v2','site-factory/bucheon-flower'))
        self.assertEqual(target['stagingWorker'],'bucheon-flower-guide-qa')
        self.assertEqual(target['productionWorker'],'bucheon-flower-prod-disabled')
        with self.assertRaisesRegex(p.ProvisionError,'allowlist'):p.target_contract('namyangju-flower-v2')

    def test_exact_new_profile_required_without_changing_legacy_pin(self):
        legacy=copy.deepcopy(self.f.templates['templates'][p.TEMPLATE_KEY])
        outputs,plan=self.prepare()
        self.assertEqual(plan['sourceTemplateRegistryKey'],p.BUCHEON_TEMPLATE_REGISTRY_KEY)
        self.assertEqual(self.f.templates['templates'][p.TEMPLATE_KEY],legacy)
        adapted={key[len('target-files/site-factory/bucheon-flower/'):]:value for key,value in outputs.items() if key.startswith('target-files/site-factory/bucheon-flower/')}
        self.assertEqual({key for key in self.f.source if self.f.source[key]!=adapted[key]},p.ADAPTATIONS)
        p.validate_empty(adapted,SITE)
        provenance=json.loads(outputs['target-files/'+p.target_contract(SITE)['provenancePath']])
        self.assertEqual(provenance['sourceRevision'],self.f.source_revision)
        self.assertEqual(provenance['customerPages'],0)
        self.assertFalse(provenance['snapshotApprovalGranted'])
        registry=json.loads(outputs['control-files/'+p.REGISTRY_PATH])
        for key,value in self.f.registry['sites'].items():self.assertEqual(registry['sites'][key],value)
        self.assertFalse(registry['sites'][SITE]['productionEnabled'])
        self.assertTrue(registry['sites'][SITE]['growthPaused'])
        self.assertEqual(plan['externalActionsPerformed'],[])

    def test_missing_mutable_or_wrong_source_profile_fails_closed(self):
        entry=copy.deepcopy(self.f.templates['templates'][p.BUCHEON_TEMPLATE_REGISTRY_KEY])
        del self.f.templates['templates'][p.BUCHEON_TEMPLATE_REGISTRY_KEY];self.save_templates()
        with self.assertRaisesRegex(p.ProvisionError,'Missing reviewed Bucheon'):self.prepare()
        self.f.templates['templates'][p.BUCHEON_TEMPLATE_REGISTRY_KEY]={**entry,'sourceRevision':'HEAD'};self.save_templates()
        with self.assertRaisesRegex(p.ProvisionError,'exact published commit'):self.prepare()
        self.f.templates['templates'][p.BUCHEON_TEMPLATE_REGISTRY_KEY]=entry;self.save_templates()
        with patch.object(p,'BUCHEON_SOURCE_TREE','f'*40),self.assertRaisesRegex(p.ProvisionError,'reviewed source'):self.prepare()
        with patch.object(p,'BUCHEON_SOURCE_COUNT',999),self.assertRaisesRegex(p.ProvisionError,'tracked source files'):self.prepare()

    def test_explicit_trial_is_required_and_legacy_launch_is_not_consumed(self):
        for launch in (None,'bucheon-flower-v2-launch','goyang-flower-v2-launch','bucheon-flower-v2-trial-'):
            with self.subTest(launch=launch),self.assertRaisesRegex(p.ProvisionError,'distinct explicit regional trial'):self.prepare(launch=launch)

    def test_resume_is_exact_and_existing_customer_content_is_protected(self):
        outputs,plan=self.prepare();self.assertEqual((outputs,plan),self.prepare())
        for key,value in outputs.items():
            if key.startswith('target-files/'):self.f.write(key[len('target-files/'):],value)
        revision=self.f.commit();self.assertEqual(self.prepare(revision)[1]['targetState'],'unchanged')
        with self.assertRaisesRegex(p.ProvisionError,'bootstrap provenance'):self.prepare(revision,SITE+'-trial-other')
        self.f.write('site-factory/bucheon-flower/src/data/pages.json',p.encode([{'existingCustomer':True}]))
        with self.assertRaisesRegex(p.ProvisionError,'never overwrite'):self.prepare(self.f.commit())

    def test_current_staging_workflow_accepts_only_closed_bucheon_policy(self):
        resolver=regions.StagingTests('runTest')
        result=resolver.resolve(p.site_entry(SITE),SITE)
        self.assertEqual(result['url'],'https://bucheon-flower-guide-qa.joseungil.workers.dev')
        self.assertEqual(result['build_root'],'preview-build')
        for field,value in [('productionEnabled',True),('growthPaused',False),('autoDeploySnapshots',True),('stagingWorker','seongnam-flower-guide-qa')]:
            entry=p.site_entry(SITE);entry[field]=value
            with self.subTest(field=field),self.assertRaises(SystemExit):resolver.resolve(entry,SITE)

    def test_dry_run_cli_never_materializes_or_calls_services(self):
        stdout=io.StringIO()
        with patch.object(sys,'argv',['provision_goyang.py','--repo',str(self.f.repo),'--control-revision',self.f.control,'--target-revision','absent','--site-key',SITE,'--launch-key',TRIAL,'--dry-run']),patch.object(p,'materialize',side_effect=AssertionError('must not write')),redirect_stdout(stdout):p.main()
        self.assertEqual(json.loads(stdout.getvalue())['launchKey'],TRIAL)

if __name__=='__main__':unittest.main()
