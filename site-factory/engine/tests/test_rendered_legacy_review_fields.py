"""Isolated real-Astro regression for reviewed markdown-v1 fields.

Run with --site-root PATH --site-key KEY. Source articles and baselines are
copied, never edited in place. This test does not publish or make network calls.
"""
import argparse
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from test_engine import payload, snap


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.h1 = []
        self.in_h1 = False
        self.titles = []
        self.in_title = False
        self.site_names = []
        self.attributes = []
        self.descriptions = []
        self.text = []
        self.injected = []
        self.anchors = []
        self.anchor = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'data-review-probe' in attrs or 'data-review-injected' in attrs:
            self.injected.append(attrs)
        if tag == 'a':
            self.anchor = [attrs.get('href'), '']
        if tag == 'h1':
            self.h1.append('')
            self.in_h1 = True
        if tag == 'title':
            self.titles.append('')
            self.in_title = True
        if tag == 'section' and 'data-snapshot-id' in attrs:
            self.attributes.append(attrs)
        if tag == 'meta' and attrs.get('name') == 'description':
            self.descriptions.append(attrs.get('content'))
        if tag == 'meta' and attrs.get('property') == 'og:site_name':
            self.site_names.append(attrs.get('content'))

    def handle_endtag(self, tag):
        if tag == 'h1':
            self.in_h1 = False
        if tag == 'title':
            self.in_title = False
        if tag == 'a' and self.anchor:
            self.anchors.append(self.anchor)
            self.anchor = None

    def handle_data(self, text):
        self.text.append(text)
        if self.anchor:
            self.anchor[1] += text
        if self.in_h1:
            self.h1[-1] += text
        if self.in_title:
            self.titles[-1] += text


def verify(site_root, site_key, registry_path):
    site_root = site_root.resolve()
    registry = json.loads(registry_path.read_text())
    target = registry['sites'][site_key]
    assert target.get('snapshotRenderer', 'markdown-v1') == 'markdown-v1'
    source_files = {p.relative_to(site_root): p.read_bytes()
                    for p in (site_root / 'src').rglob('*') if p.is_file()}
    with tempfile.TemporaryDirectory(prefix='factory-legacy-rendered-') as temp:
        workspace = Path(temp)
        root = workspace / target['root']
        shutil.copytree(site_root, root, ignore=shutil.ignore_patterns(
            'node_modules', 'dist', '.astro', '.wrangler', '.git', 'indexnow-urls.json'))
        (root / 'node_modules').symlink_to(site_root / 'node_modules', target_is_directory=True)
        data = root / 'src/data'
        original = {name: json.loads((data / name).read_text()) for name in
                    ['publish-manifest.json', 'page-map.json', 'architecture.json']}
        region = site_root.name.removesuffix('-flower')
        key = region + '-zz-review-fields-fixture'
        category = target['allowedCategories'][0]
        keyword = '검수 연결 꽃 주문 준비'
        description = '전달 장소와 받는 분의 일정, 꽃을 놓을 공간을 확인하고 상담 전에 준비할 정보를 차례로 정리합니다.'
        reviewed = {
            'H1': keyword + '와 선택 조건',
            'CARD-SUMMARY': '카드 전용 요약: <em data-review-probe="card">공간</em>과 수령 시간을 확인하세요.',
            'FIRST-ANSWER': '검수 첫 답변: <em data-review-probe="answer">수령 시간</em> & 놓을 공간을 확인하세요.',
            'QUERY_CLASS': 'core-commercial',
            'VISUAL_INTENT': 'product-comparison',
            'ASSET_SLOT': 'FLOWER_SELECTION" data-review-injected="yes',
        }
        paragraph = (
            '꽃을 주문할 때는 받는 분이 어디에서 어떤 방식으로 수령하는지 먼저 확인하세요. '
            '직접 들고 이동할 예정이면 손에 들기 편한 크기와 포장 형태를 비교하고, '
            '책상이나 접수대에 놓을 예정이면 공간과 주변 동선을 확인하는 것이 좋습니다. '
            '희망 전달 시간과 정확한 주소, 연락 가능한 담당자, 보내는 분의 이름과 문구를 준비하세요. '
            '실제 재고와 색상, 상품 구성 및 배송 가능 여부는 상담 과정에서 확인합니다. '
            '시설별 반입 조건이나 행사 일정이 바뀔 수 있으므로 최근 안내를 다시 확인하세요. '
        )
        content = '\n\n'.join('## 주문 전 확인 ' + str(i) + '\n\n' + paragraph for i in range(1, 5))
        common = dict(SITE_KEY=site_key, TARGET_REPO=target['repo'], TARGET_BRANCH=target['branch'],
                      TARGET_ROOT=target['root'], PAGE_KEY=key, SLUG=key,
                      SNAPSHOT_ID=key + '-v1', CATEGORY=category,
                      PAGE_TYPE=target['allowedPageTypes'][0], PRIMARY_KEYWORD=keyword,
                      TITLE=keyword + ' | 전달 조건과 상담 정보', DESCRIPTION=description,
                      CONTENT=content, **reviewed)
        body = payload(**common)
        result = snap.render(body, registry, workspace)
        assert result['renderer'] == 'markdown-v1'
        frozen = {name: (data / name).read_bytes() for name in original}
        assert not snap.render(body, registry, workspace)['changedFiles']
        assert all((data / name).read_bytes() == value for name, value in frozen.items())
        for name, document in original.items():
            rows = {row['pageKey']: row for row in json.loads((data / name).read_text())['pages']}
            assert all(rows[row['pageKey']] == row for row in document['pages']), name

        # A second page explicitly links the reviewed article so its card is
        # checked in the related-card path as well as the hub and homepage.
        linked = {**common, 'PAGE_KEY': key + '-linked', 'SLUG': key + '-linked',
                  'SNAPSHOT_ID': key + '-linked-v1', 'PUBLISH_QUEUE_RECORD_ID': 'recCCCCCCCCCCCCCC',
                  'PRIMARY_KEYWORD': '검수 연결 꽃 수령 확인', 'TITLE': '검수 연결 꽃 수령 확인 | 전달 정보',
                  'RELATED-PAGE-KEYS': key, 'H1': '검수 연결 꽃 수령 확인'}
        snap.render(payload(**linked), registry, workspace)
        top = None
        if target.get('primaryLandingSlug'):
            # Exercise the separate v1 top-level route, including its special
            # primary-landing H1 fallback. Only the disposable copy is revised.
            previous = next(row for row in original['publish-manifest.json']['pages']
                            if row['slug'] == target['primaryLandingSlug'])
            top = {**common, 'PAGE_KEY': previous['pageKey'], 'SLUG': previous['slug'],
                   'ROUTE_TYPE': 'top_level', 'SNAPSHOT_ID': key + '-top-v1',
                   'PUBLISH_QUEUE_RECORD_ID': 'recDDDDDDDDDDDDDD',
                   'SUPERSEDES_SNAPSHOT_ID': previous['snapshotId'],
                   'PRIMARY_KEYWORD': '검수 연결 지역 꽃 안내',
                   'TITLE': '검수 연결 지역 꽃 안내 | 주문 준비',
                   'H1': '검수 연결 지역 꽃 안내와 선택'}
            snap.render(payload(**top), registry, workspace)
        env = {**os.environ, 'SITE_URL': target['siteUrl'], 'SITE_INDEXABLE': 'true',
               'GITHUB_SHA': 'a' * 40, 'ASTRO_TELEMETRY_DISABLED': '1'}
        subprocess.run(['npm', 'run', 'build'], cwd=root, env=env, check=True)
        subprocess.run([sys.executable, 'scripts/qa_static.py'], cwd=root, env=env, check=True)
        html = (root / 'dist' / category / key / 'index.html').read_text()
        page = Page(html)
        assert page.h1 == [reviewed['H1']], page.h1
        assert len(page.site_names) == 1
        assert page.titles == [common['TITLE'] + ' | ' + page.site_names[0]], page.titles
        assert page.descriptions == [description], page.descriptions
        assert reviewed['FIRST-ANSWER'] in page.text
        assert not page.injected
        assert len(page.attributes) == 1
        for header, attr in [('QUERY_CLASS', 'data-query-class'),
                             ('VISUAL_INTENT', 'data-visual-intent'), ('ASSET_SLOT', 'data-asset-slot')]:
            assert page.attributes[0][attr] == reviewed[header]
        for path in [root / 'dist' / category / 'index.html', root / 'dist/index.html',
                     root / 'dist' / category / (key + '-linked') / 'index.html']:
            card_page = Page(path.read_text())
            assert any(href == f'/{category}/{key}/' and reviewed['CARD-SUMMARY'] in text
                       for href, text in card_page.anchors), path
            assert not card_page.injected, path
        if top:
            landing = Page((root / 'dist' / top['SLUG'] / 'index.html').read_text())
            assert landing.h1 == [top['H1']], landing.h1
            assert landing.titles == [top['TITLE'] + ' | ' + page.site_names[0]], landing.titles
            assert reviewed['FIRST-ANSWER'] in landing.text
            assert landing.attributes[0]['data-asset-slot'] == reviewed['ASSET_SLOT']
            assert not landing.injected
        assert source_files == {p.relative_to(site_root): p.read_bytes()
                                for p in (site_root / 'src').rglob('*') if p.is_file()}
        print(f'RENDERED LEGACY REVIEW FIELDS PASSED: {site_key}; six fields in actual HTML; '
              'single reviewed H1, independent meta description, first answer, hub/home/related cards, '
              'query/visual/asset attributes, immutable replay, baseline rows and source unchanged')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--site-root', type=Path, required=True)
    parser.add_argument('--site-key', required=True)
    parser.add_argument('--registry', type=Path,
                        default=Path(__file__).resolve().parents[3] / '.github/site-factory-sites.json')
    args = parser.parse_args()
    verify(args.site_root, args.site_key, args.registry)
