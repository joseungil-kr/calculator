from pathlib import Path
import re
root=Path('dist')
html=list(root.rglob('*.html'))
assert len(html)>=16, len(html)
for p in html:
    s=p.read_text(encoding='utf-8')
    assert '<title>' in s
    assert 'name="robots" content="noindex,follow"' in s
    assert '<h1' in s
print(f'STATIC QA PASSED: html={len(html)}')
