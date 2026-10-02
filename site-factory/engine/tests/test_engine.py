import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ENGINE = Path(__file__).resolve().parents[1]
def module(name):
    spec = importlib.util.spec_from_file_location(name, ENGINE / (name + ".py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
snap = module("render_snapshot"); planner = module("plan_batch"); live = module("verify_live")

def payload(**changes):
    values = {"PUBLISH_QUEUE_RECORD_ID":"recAAAAAAAAAAAAAA", "SITE_KEY":"test", "PAGE_KEY":"test-page-01", "DRAFT_KEY":"draft-01", "SOURCE_RECORD_ID":"recBBBBBBBBBBBBBB", "SNAPSHOT_ID":"snapshot-01", "TARGET_REPO":"owner/repo", "TARGET_BRANCH":"site", "TARGET_ROOT":"site", "SLUG":"hospital-visit", "CATEGORY":"gift", "STRUCTURE_TYPE":"commercial", "PAGE_TYPE":"hospital-visit", "LOCALIZATION_POLICY":"local-required", "REGION":"수원", "VERIFIED_AT":"2026-10-01", "PRIMARY_KEYWORD":"수원 병문안 꽃", "TITLE":"수원 병문안 꽃 | 병실 반입과 수령 확인", "DESCRIPTION":"병실 반입 규정과 받는 분 일정을 먼저 확인하고 작은 꽃선물을 상담하세요.", "CONTENT":"수원 병문안 꽃은 병실 반입 규정과 수령 일정을 먼저 확인한 뒤 크기와 향을 고려해 선택하세요. 받는 분의 퇴원 일정과 병동별 꽃 반입 조건은 해당 시설에서 직접 확인하는 것이 좋습니다.\n\n## 상담 전에 확인할 정보\n\n정확한 병원명과 병동, 희망 전달시간을 준비하면 상담이 빠릅니다. 시설 정책과 상품 구성, 실제 배송 가능 여부는 확인 후 안내합니다. 꽃선물 상담은 실제 업체의 전화로 문의해 주세요.", "SOURCES":"https://example.com/official", "SOURCE-NAMES":"공식 시설", "SOURCE-TYPES":"facility"}
    values.update(changes)
    blocks={k:v for k,v in values.items() if k in {"TITLE","DESCRIPTION","CONTENT","SOURCES","SOURCE-NAMES","SOURCE-TYPES","RELATED-PAGE-KEYS","CARD-SUMMARY","FIRST-ANSWER"}}
    return "\n".join(f"{k}: {v}" for k,v in values.items() if k not in blocks) + "\n" + "\n".join(f"---BEGIN-{k}---\n{v}\n---END-{k}---" for k,v in blocks.items())

class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); data=self.root/'site/src/data'; data.mkdir(parents=True)
        for name in ['publish-manifest','page-map']:(data/(name+'.json')).write_text(json.dumps({'siteKey':'test','pages':[]}))
        (data/'architecture.json').write_text(json.dumps({'siteKey':'test','hubs':[{'url':'/gift/','category':'gift','children':0}], 'pages':[]}))
        (data/'pages.json').write_text('[]')
        self.registry={'sites':{'test':{'repo':'owner/repo','branch':'site','root':'site','allowedCategories':['gift','funeral'],'allowedPageTypes':['hospital-visit','funeral-facility'],'categoryPageTypes':{'gift':['hospital-visit'],'funeral':['funeral-facility']},'snapshotRenderer':'structured-json-v12','productionEnabled':False}}}
    def bytes(self):return {str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
    def render(self,body=None):return snap.render(body or payload(),self.registry,self.root)
    def assert_rejected_unchanged(self,body):
        before=self.bytes()
        with self.assertRaises(snap.SnapshotError):self.render(body)
        self.assertEqual(before,self.bytes())
    def test_canonical_renderer_and_parity(self):
        result=self.render(); data=self.root/'site/src/data'
        p=json.loads((data/'pages.json').read_text())[0]
        self.assertEqual(result['renderer'],'structured-json-v12');self.assertIn('병문안',p['contentMarkdown'])
        self.assertFalse((self.root/'site/src/content/articles').exists())
        for file in ['publish-manifest','page-map','architecture']:
            row=json.loads((data/(file+'.json')).read_text())['pages'][0]
            self.assertEqual(row['snapshotId'],p['snapshotId']);self.assertEqual(row['url'],p['url'])
    def test_byte_identical_replay(self):
        self.render();before=self.bytes();r=self.render();self.assertEqual(r['changedFiles'],[]);self.assertEqual(before,self.bytes())
    def test_immutable_id_reuse_fails(self):
        self.render();self.assert_rejected_unchanged(payload(CONTENT=payload_content()+' changed'))
    def test_legacy_unhashed_snapshot_cannot_be_overwritten(self):
        self.render();p=self.root/'site/src/data/publish-manifest.json';d=json.loads(p.read_text());del d['pages'][0]['snapshotHash'];p.write_text(json.dumps(d));self.assert_rejected_unchanged(payload())
    def test_explicit_supersession(self):
        self.render();r=self.render(payload(SNAPSHOT_ID='snapshot-02',PUBLISH_QUEUE_RECORD_ID='recCCCCCCCCCCCCCC',SUPERSEDES_SNAPSHOT_ID='snapshot-01'));self.assertEqual(r['snapshotId'],'snapshot-02')
    def test_stale_supersession_fails(self):
        self.render();self.assert_rejected_unchanged(payload(SNAPSHOT_ID='snapshot-02',SUPERSEDES_SNAPSHOT_ID='wrong'))
    def test_missing_draft_reports_actionable_failure(self):self.assert_rejected_unchanged(payload(DRAFT_KEY=''))
    def test_path_traversal_page_key_fails(self):self.assert_rejected_unchanged(payload(PAGE_KEY='../escape'))
    def test_header_injection_fails(self):self.assert_rejected_unchanged(payload(PAGE_KEY='safe\nTARGET_ROOT: ../escape'))
    def test_wrong_root_fails(self):self.assert_rejected_unchanged(payload(TARGET_ROOT='../escape'))
    def test_wrong_blueprint_pair_fails(self):self.assert_rejected_unchanged(payload(CATEGORY='funeral'))
    def test_source_credentials_fail(self):self.assert_rejected_unchanged(payload(SOURCES='https://user:password@example.com/'))
    def test_missing_provenance_fails(self):self.assert_rejected_unchanged(payload(SOURCES=''))
    def test_raw_html_fails(self):self.assert_rejected_unchanged(payload(CONTENT=payload_content()+'\n<script>alert(1)</script>'))
    def test_title_keyword_collision_fails(self):
        self.render();self.assert_rejected_unchanged(payload(PAGE_KEY='other',SLUG='other',SNAPSHOT_ID='other',INTENT_KEY='different'))
    def test_unknown_renderer_fails(self):
        self.registry['sites']['test']['snapshotRenderer']='mystery';self.assert_rejected_unchanged(payload())
    def test_preexisting_parity_failure_fails(self):
        p=self.root/'site/src/data/page-map.json';p.write_text(json.dumps({'pages':[{'pageKey':'wrong'}]}));self.assert_rejected_unchanged(payload())
    def test_file_replacement_failure_rolls_back(self):
        before=self.bytes();original=Path.replace;count=[0]
        def flaky(path,target):
            count[0]+=1
            if count[0]==2:raise OSError('simulated interrupted transaction')
            return original(path,target)
        with patch.object(Path,'replace',flaky):
            with self.assertRaises(OSError):self.render()
        self.assertEqual(before,self.bytes())
    def test_markdown_adapter_remains_supported(self):
        self.registry['sites']['test']['snapshotRenderer']='markdown-v1';self.render();text=(self.root/'site/src/content/articles/test-page-01.md').read_text();self.assertIn('snapshotId: "snapshot-01"',text)
    def test_markdown_review_fields_reach_article_and_replay_identically(self):
        self.registry['sites']['test']['snapshotRenderer']='markdown-v1'
        values={'H1':'수원 병문안 꽃 선택 조건', 'CARD-SUMMARY':'병동 반입 조건을 먼저 확인하세요.',
                'FIRST-ANSWER':'병동의 생화 반입과 수령 시간을 먼저 확인하세요.',
                'QUERY_CLASS':'core-commercial', 'VISUAL_INTENT':'product-selection', 'ASSET_SLOT':'FLOWER_SELECTION'}
        body=payload(**values);self.render(body)
        article=(self.root/'site/src/content/articles/test-page-01.md').read_text()
        fields={line.split(': ',1)[0]:json.loads(line.split(': ',1)[1]) for line in article.split('---',2)[1].strip().splitlines()}
        names={'H1':'h1','CARD-SUMMARY':'cardSummary','FIRST-ANSWER':'firstAnswer','QUERY_CLASS':'queryClass','VISUAL_INTENT':'visualIntent','ASSET_SLOT':'assetSlot'}
        for header,field in names.items():self.assertEqual(fields[field],values[header])
        before=self.bytes();self.assertEqual(self.render(body)['changedFiles'],[]);self.assertEqual(before,self.bytes())
    def test_markdown_blank_review_fields_preserve_legacy_bytes(self):
        self.registry['sites']['test']['snapshotRenderer']='markdown-v1'
        baseline=self.render();before=self.bytes()
        blank=payload(**{key:'' for key in ['H1','CARD-SUMMARY','FIRST-ANSWER','QUERY_CLASS','VISUAL_INTENT','ASSET_SLOT']})
        result=self.render(blank)
        self.assertEqual(result['changedFiles'],[]);self.assertEqual(before,self.bytes());self.assertEqual(baseline['approvalHash'],result['approvalHash'])
    def test_markdown_review_fields_are_immutable_and_approval_bound(self):
        self.registry['sites']['test']['snapshotRenderer']='markdown-v1'
        values={'H1':'수원 병문안 꽃 선택', 'CARD-SUMMARY':'반입 조건 확인', 'FIRST-ANSWER':'병동에 반입 조건을 확인하세요.',
                'QUERY_CLASS':'core-commercial','VISUAL_INTENT':'product-selection','ASSET_SLOT':'FLOWER_SELECTION'}
        proof=self.render(payload(**values))['approvalHash']
        self.render(payload(**values,APPROVAL_STATUS='approved',APPROVED_SNAPSHOT_HASH=proof))
        for key in values:
            with self.subTest(field=key):
                changed={**values,key:values[key]+' changed'}
                self.assert_rejected_unchanged(payload(**changed))
                self.assert_rejected_unchanged(payload(**changed,APPROVAL_STATUS='approved',APPROVED_SNAPSHOT_HASH=proof))
    def test_markdown_review_fields_support_explicit_supersession(self):
        self.registry['sites']['test']['snapshotRenderer']='markdown-v1'
        self.render(payload(H1='수원 병문안 꽃 이전 제목'))
        self.render(payload(H1='수원 병문안 꽃 검수 제목',SNAPSHOT_ID='snapshot-02',PUBLISH_QUEUE_RECORD_ID='recCCCCCCCCCCCCCC',SUPERSEDES_SNAPSHOT_ID='snapshot-01'))
        text=(self.root/'site/src/content/articles/test-page-01.md').read_text()
        self.assertIn('h1: "수원 병문안 꽃 검수 제목"',text);self.assertNotIn('이전 제목',text)
    def test_legacy_business_source_type_is_compatible(self):self.render(payload(**{'SOURCE-TYPES':'business'}))
    def test_snapshot_id_cannot_bind_another_page(self):
        self.render();self.assert_rejected_unchanged(payload(PAGE_KEY='other',SLUG='other',PRIMARY_KEYWORD='수원 새 꽃',TITLE='수원 새 꽃 | 새 주문',PUBLISH_QUEUE_RECORD_ID='recCCCCCCCCCCCCCC'))
    def test_queue_record_cannot_bind_another_snapshot(self):
        self.render();self.assert_rejected_unchanged(payload(PAGE_KEY='other',SLUG='other',PRIMARY_KEYWORD='수원 새 꽃',TITLE='수원 새 꽃 | 새 주문',SNAPSHOT_ID='snapshot-02'))
    def test_retired_snapshot_id_stays_immutable(self):
        self.render();self.render(payload(SNAPSHOT_ID='snapshot-02',PUBLISH_QUEUE_RECORD_ID='recCCCCCCCCCCCCCC',SUPERSEDES_SNAPSHOT_ID='snapshot-01'))
        self.assert_rejected_unchanged(payload(PAGE_KEY='other',SLUG='other',PRIMARY_KEYWORD='수원 새 꽃',TITLE='수원 새 꽃 | 새 주문',PUBLISH_QUEUE_RECORD_ID='recDDDDDDDDDDDDDD'))
    def test_missing_approval_is_explicit_stage_only(self):self.assertFalse(self.render()['approvalVerified'])
    def test_approval_hash_must_match_frozen_payload(self):self.assert_rejected_unchanged(payload(APPROVAL_STATUS='approved',APPROVED_SNAPSHOT_HASH='0'*64))
    def test_approval_of_exact_snapshot(self):
        result=self.render();approved=self.render(payload(APPROVAL_STATUS='approved',APPROVED_SNAPSHOT_HASH=result['approvalHash']));self.assertTrue(approved['approvalVerified'])
    def test_legacy_redirect_history_is_preserved(self):
        self.registry['sites']['test']['snapshotRenderer']='markdown-v1'
        path=self.root/'site/src/data/architecture.json';d=json.loads(path.read_text());row={'pageKey':'retired','url':'/old/','status':'merged','sitemapIndexable':False};d['pages'].append(row);path.write_text(json.dumps(d))
        self.render();self.assertIn(row,json.loads(path.read_text())['pages'])
    def test_legacy_separate_home_is_preserved(self):
        self.registry['sites']['test']['snapshotRenderer']='markdown-v1'
        path=self.root/'site/src/data/architecture.json';d=json.loads(path.read_text());row={'pageKey':'home','url':'/','pageRole':'REGION_SERVICE_LANDING','primaryKeyword':'지역 꽃배달'};d['pages'].append(row);path.write_text(json.dumps(d))
        self.render();self.assertIn(row,json.loads(path.read_text())['pages'])
    def test_structured_renderer_rejects_extra_home_record(self):
        path=self.root/'site/src/data/architecture.json';d=json.loads(path.read_text());d['pages'].append({'pageKey':'home','url':'/','pageRole':'REGION_SERVICE_LANDING'});path.write_text(json.dumps(d));self.assert_rejected_unchanged(payload())
    def test_legacy_publication_compatibility_is_preserved(self):
        self.registry['sites']['test']['snapshotRenderer']='markdown-v1'
        result=self.render();self.assertTrue(result['publicationApproved']);self.assertFalse(result['approvalVerified']);self.assertEqual(result['approvalMode'],'legacy-trusted-writer')
    def test_structured_publication_requires_versioned_approval(self):self.assertFalse(self.render()['publicationApproved'])
    def test_review_proof_can_precede_server_allocated_queue_id(self):
        p=snap.validate_content(snap.parse_payload(payload()));a,b=snap.frozen_hashes(p)
        p['PUBLISH_QUEUE_RECORD_ID']='recCCCCCCCCCCCCCC';c,d=snap.frozen_hashes(p)
        self.assertEqual(b,d);self.assertNotEqual(a,c)
    def test_empty_optional_publisher_headers_do_not_change_review_hash(self):
        p=snap.validate_content(snap.parse_payload(payload()));a,b=snap.frozen_hashes(p)
        p['SUPERSEDES_SNAPSHOT_ID']='';p['APPROVAL_STATUS']='';p['APPROVED_SNAPSHOT_HASH']=''
        self.assertEqual((a,b),snap.frozen_hashes(p))
    def test_blank_new_optional_headers_keep_legacy_renderer_defaults(self):
        absent=self.render();baseline=json.loads((self.root/'site/src/data/pages.json').read_text())[0]
        self.assertEqual((baseline['queryClass'],baseline['visualIntent'],baseline['assetSlot']),('support-info','consultation','NONE'))
        self.render(payload(QUERY_CLASS='',VISUAL_INTENT='',ASSET_SLOT=''))
        blank=json.loads((self.root/'site/src/data/pages.json').read_text())[0]
        self.assertEqual((blank['queryClass'],blank['visualIntent'],blank['assetSlot']),('support-info','consultation','NONE'))
        self.assertEqual(absent['approvalHash'],self.render(payload())['approvalHash'])
    def test_h1_header_is_preserved_and_bound_to_review_hash(self):
        custom=payload(H1='수원 병문안 꽃 주문 조건과 선택')
        parsed=snap.parse_payload(custom)
        self.assertEqual(parsed['H1'],'수원 병문안 꽃 주문 조건과 선택')
        proof=self.render(custom)['approvalHash']
        self.render(payload(H1='수원 병문안 꽃 주문 조건과 선택',APPROVAL_STATUS='approved',APPROVED_SNAPSHOT_HASH=proof))
        page=json.loads((self.root/'site/src/data/pages.json').read_text())[0]
        self.assertEqual(page['h1'],'수원 병문안 꽃 주문 조건과 선택')
        self.assert_rejected_unchanged(payload(H1='수원 병문안 꽃 다른 제목',APPROVAL_STATUS='approved',APPROVED_SNAPSHOT_HASH=proof))
    def test_h1_header_injection_fails(self):
        self.assert_rejected_unchanged(payload(H1='safe\nTARGET_ROOT: other'))

def payload_content():return snap.parse_payload(payload())['CONTENT']

class PlanningTests(unittest.TestCase):
    def input(self):
        b={field:['verified'] for field in planner.BLUEPRINT_FIELDS};b['blueprintKey']='flower';b['pageTypes']=['hospital-visit']
        return {'blueprint':b,'fingerprint':{'brandKey':'flower','brand':'꽃','conversionChannels':[{'value':'tel:18440644','sourceLevel':'operator_confirmed'}]},'policy':{'launchVolume':8,'growthVolume':3,'growthPaused':True},'queries':[{'primaryKeyword':'수원 꽃','intentKey':'suwon|flower','queryClass':'core-commercial','pageType':'hospital-visit','queryEvidence':['operator']} ]}
    def test_launch_volume_is_configurable(self):self.assertEqual(planner.plan(self.input(),'launch',4)['volume'],4)
    def test_growth_stays_paused(self):self.assertEqual(planner.plan(self.input(),'growth')['state'],'paused')
    def test_bootstrap_missing_inputs(self):self.assertEqual(planner.plan({},'launch')['state'],'bootstrap_required')
    def test_duplicate_intent_is_one_page(self):
        d=self.input();d['queries'].append({**d['queries'][0],'primaryKeyword':'수원 꽃 가격'});self.assertEqual(len(planner.plan(d,'launch')['selected']),1)
    def test_unknown_conversion_cannot_publish(self):
        d=self.input();d['fingerprint']['conversionChannels'][0]['sourceLevel']='industry_default'
        with self.assertRaises(ValueError):planner.plan(d,'launch')

class LiveTests(unittest.TestCase):
    def test_wrong_revision_cannot_be_verified(self):
        with self.assertRaises(AssertionError):live.validate_html('<h1>x</h1>','https://example.com','/','a'*40)
    def test_semantically_valid_page_has_one_canonical_h1_revision(self):
        html='<meta name="site-factory-revision" content="'+ 'a'*40 +'"><meta name="robots" content="index,follow"><link rel="canonical" href="https://example.com/"><h1>x</h1><script type="application/ld+json">{}</script>'
        live.validate_html(html,'https://example.com','/','a'*40)

if __name__=='__main__':unittest.main()
