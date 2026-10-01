from pathlib import Path
root=Path('dist')
html=list(root.rglob('*.html'))
assert len(html)>=16, len(html)
for p in html:
    s=p.read_text(encoding='utf-8')
    assert '<title>' in s
    assert 'name="robots" content="noindex,follow"' in s
    assert '<h1' in s
    assert 'alignment 100/100' not in s
    assert 'priority 3' not in s
    assert 'keywordCluster' not in s
    assert 'PRIMARY QUERY' not in s
print(f'STATIC QA PASSED: html={len(html)}, internal_meta_hidden=1')
