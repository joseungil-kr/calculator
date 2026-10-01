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
forbidden_visible=['검색어','검색의도','Business Truth','Production','Shadow','검증용','콘텐츠와 CTA','중복문서','페이지를 분리한 이유','페이지의 역할','지역 페이지','가격 페이지','견적 페이지','대표 페이지','허브로 돌아']
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
    for term in forbidden_visible:
        assert term not in s, (p['pageKey'], term)
    if p['url']!='/':
        assert 'class="breadcrumb"' in s
        assert s.count('data-context-link="true"')>=2, (p['pageKey'],s.count('data-context-link="true"'))
    if p['queryClass'] in ('local-commercial','work-commercial'):
        assert s.count('data-local-evidence="true"')>=2, (p['pageKey'],s.count('data-local-evidence="true"'))
for hub in [root/'work-types'/'index.html', root/'areas'/'index.html']:
    hs=hub.read_text(encoding='utf-8')
    for term in forbidden_visible:
        assert term not in hs, (str(hub), term)
print(f'STATIC HARD-GATE QA PASSED: html={len(html)}, audienceConversion=1, contextualLinks=1, localEvidence=1, singleChildHubsRemoved=1')
