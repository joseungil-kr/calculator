"""Build a new snapshot in an isolated, noindex copy; never changes live source/data."""
from pathlib import Path
import tempfile, shutil, json, os, subprocess
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='suwon-growth-') as tmp:
 target=Path(tmp)
 shutil.copytree(root,target,dirs_exist_ok=True,ignore=shutil.ignore_patterns('node_modules','dist','.astro','__pycache__'))
 (target/'node_modules').symlink_to(root/'node_modules',target_is_directory=True)
 data=target/'src/data';pages=json.loads((data/'pages.json').read_text())
 original=len(pages);prototype=next(p for p in pages if p['pageType']=='school-event')
 key='qa-growth-fixture'
 while any(p['pageKey']==key for p in pages):key+='-next'
 page=dict(prototype);page.update(pageKey=key,slug=key,url='/school/'+key+'/',snapshotId=key+'-v1',title='성장 렌더링 로컬 검증',h1='성장 렌더링 로컬 검증',primaryKeyword='성장 렌더링 로컬 검증',description='공개하지 않는 성장경로 테스트',cardSummary='안전한 스냅샷 렌더링 테스트',intentKey=key,contentMarkdown='## 성장 검증\n\n[주소·수령자 안내](/order/suwon-flower-address-guide/)\n\n<script>alert(1)</script>')
 pages.append(page);(data/'pages.json').write_text(json.dumps(pages,ensure_ascii=False))
 for name in ['publish-manifest','page-map','architecture']:
  record=json.loads((data/(name+'.json')).read_text());entry=dict(next(p for p in record['pages'] if p['pageKey']==prototype['pageKey']));entry.update({k:page[k] for k in ['pageKey','slug','url','snapshotId','title','primaryKeyword','intentKey']});record['pages'].append(entry)
  if name=='architecture':next(h for h in record['hubs'] if h['category']=='school')['children']+=1
  (data/(name+'.json')).write_text(json.dumps(record,ensure_ascii=False))
 env={**os.environ,'ASTRO_TELEMETRY_DISABLED':'1','SITE_INDEXABLE':'false','SITE_URL':'https://preview.invalid','SITE_FACTORY_REVISION':'a'*40}
 subprocess.run(['npm','run','build'],cwd=target,env=env,check=True)
 html=(target/'dist/school'/key/'index.html').read_text()
 assert f'data-snapshot-id="{page["snapshotId"]}"' in html
 assert '&lt;script&gt;alert(1)&lt;/script&gt;' in html and '<script>alert(1)</script>' not in html
 assert page['url'] in (target/'dist/school/index.html').read_text()
 print(f'GROWTH BUILD PASSED: {original} -> {len(pages)} detail pages, snapshot rendered, new hub link, escaped Markdown')
