from pathlib import Path
import json
root=Path('dist')
pages=json.loads(Path('src/data/pages.json').read_text(encoding='utf-8'))
html=list(root.rglob('*.html'))
assert len(html)>=14, len(html)
assert not (root/'pricing'/'index.html').exists()
assert not (root/'quote'/'index.html').exists()
assert (root/'work-types'/'index.html').exists()
assert (root/'areas'/'index.html').exists()
forbidden_visible=['검색어','검색의도','Business Truth','Production','Shadow','검증용','콘텐츠와 CTA','중복문서','페이지를 분리한 이유','페이지의 역할','허브로 돌아']
for p in pages:
    rel='index.html' if p['url']=='/' else p['url'].strip('/')+'/index.html'
    fp=root/rel
    assert fp.exists(), f'missing {fp}'
    s=fp.read_text(encoding='utf-8')
    assert '<title>' in s and p['primaryKeyword'] in s
    assert 'name="robots" content="noindex,follow"' in s
    assert 'tel:01053221952' in s, p['pageKey']
    assert 'sms:01053221952' in s, p['pageKey']
    assert '영진스카이' in s, p['pageKey']
    assert '당일예약 및 출동 가능' in s, p['pageKey']
    assert '1톤' in s and '2.5톤' in s and '3톤' in s and '5톤' in s
    for term in forbidden_visible: assert term not in s,(p['pageKey'],term)
    if p['url']!='/':
        assert 'class="breadcrumb"' in s
        assert s.count('data-context-link="true"')>=2
    if p['queryClass'] in ('local-commercial','work-commercial'):
        assert s.count('data-local-evidence="true"')>=2
home=(root/'index.html').read_text(encoding='utf-8')
assert 'sf-img-hero-home' in home
assert '영진스카이 현장 이미지' in home
assert '실제 현장사진' in home
assert '문자로 견적 문의' in home
for hub in [root/'work-types'/'index.html',root/'areas'/'index.html']:
    s=hub.read_text(encoding='utf-8')
    assert 'tel:01053221952' in s and 'sms:01053221952' in s
print(f'STATIC REAL-SITE QA PASSED: html={len(html)}, realCTA=1, generatedVisuals=1, fieldPhotos=1, noindex=1')
