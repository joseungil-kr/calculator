"""Read-only compatibility tests against checkout remote branch snapshots."""
import json
from pathlib import Path
import subprocess
import tempfile
from test_engine import payload, snap

REPO = Path(__file__).resolve().parents[3]
registry=json.loads((REPO/'.github/site-factory-sites.json').read_text())
for site_key in ['ansan-flower-test','hwaseong-flower','yongin-flower-v2']:
    target=registry['sites'][site_key]
    with tempfile.TemporaryDirectory(prefix='factory-legacy-') as temp:
        workspace=Path(temp);data=workspace/target['root']/'src/data';data.mkdir(parents=True)
        original={}
        for name in ['publish-manifest.json','page-map.json','architecture.json']:
            text=subprocess.check_output(['git','show',f"origin/{target['branch']}:{target['root']}/src/data/{name}"],cwd=REPO,text=True)
            (data/name).write_text(text);original[name]=json.loads(text)
        keyword='호환성 검증 꽃 주문 준비'
        body=payload(SITE_KEY=site_key,TARGET_REPO=target['repo'],TARGET_BRANCH=target['branch'],TARGET_ROOT=target['root'],PAGE_KEY='compatibility-test-only',SLUG='compatibility-test-only',CATEGORY=target['allowedCategories'][0],PAGE_TYPE=target['allowedPageTypes'][0],PRIMARY_KEYWORD=keyword,TITLE=keyword+' | 실제 파일 호환성 검사')
        result=snap.render(body,registry,workspace)
        assert result['renderer']=='markdown-v1'
        for name,doc in original.items():
            after=json.loads((data/name).read_text())
            rows={r['pageKey']:r for r in after['pages']}
            assert all(rows[r['pageKey']]==r for r in doc['pages']), f'{site_key}: unrelated {name} records changed'
        assert not snap.render(body,registry,workspace)['changedFiles']
        print(f'LEGACY CONTRACT PASSED: {site_key}, preserved architecture home/merged history, baseline rows, idempotent Markdown adapter')
