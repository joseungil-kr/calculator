from pathlib import Path
import json,re
root=Path('dist'); pages=json.loads(Path('src/data/pages.json').read_text(encoding='utf-8'))
assert (root/'index.html').exists(); assert (root/'sitemap-index.xml').exists(); assert (root/'robots.txt').exists()
for cat in ['funeral','business','school','event','gift','order']: assert (root/cat/'index.html').exists(),cat
for p in pages:
 fp=root/p['url'].strip('/')/'index.html'; assert fp.exists(),p['url']; s=fp.read_text(encoding='utf-8')
 assert p['primaryKeyword'] in s; assert '<h1' in s.lower(); assert 'index,follow' in s.lower(); assert 'tel:18440644' in s; assert 'https://fwith.co.kr' in s; assert 'data-snapshot-id=' in s
 assert '검색의도' not in s and 'Business Truth' not in s and 'Shadow' not in s
home=(root/'index.html').read_text(encoding='utf-8'); assert '수원 꽃배달' in home and '59,000원부터' in home and '1844-0644' in home
print(f'SUWON V1.2 STATIC QA PASSED pages={len(pages)}')