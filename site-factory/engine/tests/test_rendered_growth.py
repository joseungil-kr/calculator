"""Real Suwon adapter+Astro growth integration, isolated from working source.

Run: python3 site-factory/engine/tests/test_rendered_growth.py --suwon-root PATH
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from test_engine import snap, payload

parser=argparse.ArgumentParser();parser.add_argument('--suwon-root',type=Path,required=True);args=parser.parse_args()
with tempfile.TemporaryDirectory(prefix='site-factory-growth-') as temp:
    workspace=Path(temp);root=workspace/'site'
    shutil.copytree(args.suwon_root,root,ignore=shutil.ignore_patterns('node_modules','dist','.astro','.wrangler','indexnow-urls.json'))
    (root/'node_modules').symlink_to(args.suwon_root.resolve()/'node_modules',target_is_directory=True)
    before=json.loads((root/'src/data/pages.json').read_text())
    registry={'sites':{'test':{'repo':'owner/repo','branch':'site','root':'site','snapshotRenderer':'structured-json-v12','allowedCategories':['gift'],'allowedPageTypes':['hospital-visit'],'categoryPageTypes':{'gift':['hospital-visit']},'productionEnabled':False}}}
    body=payload(PAGE_KEY='isolated-growth-fixture-31',SNAPSHOT_ID='isolated-growth-fixture-31-v1',SLUG='isolated-growth-fixture-31',PRIMARY_KEYWORD='수원 병문안 꽃 반입 확인',TITLE='수원 병문안 꽃 반입 확인 | 수령 일정 상담')
    result=snap.render(body,registry,workspace)
    after=json.loads((root/'src/data/pages.json').read_text())
    assert len(after)==len(before)+1
    assert after[:-1]==before, 'Existing renderer rows changed'
    frozen={name:(root/'src/data'/name).read_bytes() for name in ['pages.json','publish-manifest.json','page-map.json','architecture.json']}
    assert not snap.render(body,registry,workspace)['changedFiles']
    assert all((root/'src/data'/name).read_bytes()==value for name,value in frozen.items())
    env={**os.environ,'SITE_INDEXABLE':'false','SITE_URL':'https://preview.example.com','SITE_FACTORY_REVISION':'a'*40,'ASTRO_TELEMETRY_DISABLED':'1'}
    subprocess.run(['npm','run','build'],cwd=root,env=env,check=True)
    html=(root/'dist/gift/isolated-growth-fixture-31/index.html').read_text()
    assert 'data-snapshot-id="isolated-growth-fixture-31-v1"' in html
    assert '병문안 꽃 반입 확인' in html and 'tel:18440644' in html
    assert '/gift/isolated-growth-fixture-31/' in (root/'dist/gift/index.html').read_text()
    assert 'noindex' in html and 'Disallow: /' in (root/'dist/robots.txt').read_text()
    print('RENDERED GROWTH INTEGRATION PASSED: real31stpage, inboundhub, CTA, snapshot parity, immutable replay; source unchanged')
