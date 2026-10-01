from pathlib import Path
import json,re
root=Path('dist')
pages=json.loads(Path('src/data/pages.json').read_text(encoding='utf-8'))
html=list(root.rglob('*.html'))
assert len(html)>=14, len(html)
assert not (root/'pricing'/'index.html').exists(), 'single-child pricing hub exists'
assert not (root/'quote'/'index.html').exists(), 'single-child quote hub exists'
assert (root/'work-types'/'index.html').exists()
assert (root/'areas'/'index.html').exists()
for p in pages:
    rel='index.html' if p['url']=='/' else p['url'].strip('/')+'/index.html'
    fp=root/rel
    assert fp.exists(), f'missing {fp}'
    s=fp.read_text(encoding='utf-8')
    assert '<title>' in s
    assert 'name="robots" content="noindex,follow"' in s
    assert '<h1' in s and p['primaryKeyword'] in s
    assert 'alignment 100/100' not in s
    assert 'priority 3' not in s
    assert 'keywordCluster' not in s
    assert 'PRIMARY QUERY' not in s
    if p['url']!='/':
        assert 'class="breadcrumb"' in s
        assert s.count('data-context-link="true"')>=2, (p['pageKey'],s.count('data-context-link="true"'))
    if p['queryClass'] in ('local-commercial','work-commercial'):
        assert s.count('data-local-evidence="true"')>=2, (p['pageKey'],s.count('data-local-evidence="true"'))
print(f'STATIC HARD-GATE QA PASSED: html={len(html)}, contextualLinks=1, localEvidence=1, singleChildHubsRemoved=1')
