import assert from 'node:assert/strict';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { selectRelatedArticles } from '../src/lib/related-articles.mjs';

// Exercise the actual Astro collection filter and selector call, not a copy.
const layout = fs.readFileSync(fileURLToPath(new URL('../src/layouts/ArticleLayout.astro', import.meta.url)), 'utf8');
const collection = layout.slice(layout.indexOf('const activePageKeys ='), layout.indexOf('const detailCategoryCounts ='));
const selection = layout.slice(layout.indexOf('const related = selectRelatedArticles('), layout.indexOf('const formatDate ='));
assert.ok(selection.includes('articles: allArticles'));
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const select = new AsyncFunction('architecturePages', 'getCollection', 'relatedPageKeys', 'pageKey', 'category', 'effectivePageType', 'title', 'h1', 'selectRelatedArticles', collection + selection + '\nreturn related.map(a=>a.data.pageKey);');
const article = (pageKey, fields = {}) => ({ data: { pageKey, category: 'guide', pageType: 'general-guide', routeType: 'category', draftStatus: 'approved', ...fields } });
const current = { pageKey: 'self', category: 'places', pageType: 'hospital', title: '병문안 꽃' };
const articles = [
  article('self', current),
  article('order', { category: 'order-help', pageType: 'order-help', title: '꽃 주문 전 수령정보 확인' }),
  article('message', { pageType: 'order-help', title: '꽃 선물 문구' }),
  article('care', { category: 'flower-knowledge', pageType: 'flower-knowledge', title: '절화 보관 방법' }),
  article('graduation', { category: 'occasions', title: '졸업 꽃다발 포장' }),
  article('funeral-guide', { category: 'funeral', title: '근조화환 리본 문구' }),
  article('funeral-place', { category: 'funeral', pageType: 'funeral-facility', title: '같은 병원 장례식장 근조화환' }),
  article('other-place', { category: 'places', pageType: 'hospital', title: '다른 병원 병문안 꽃' }),
  article('published', { draftStatus: 'published' }),
  article('draft', { draftStatus: 'draft' }), article('merged'), article('noindex'),
];
const architectureFor = (input) => input.map(({ data }) => ({ pageKey: data.pageKey, status: data.pageKey === 'merged' ? 'merged' : 'primary', sitemapIndexable: data.pageKey !== 'noindex' }));
const run = (keys = [], { input = articles, source = current, architecture = architectureFor(input) } = {}) => select(architecture, async (name, filter) => {
  assert.equal(name, 'articles');
  return input.filter(filter);
}, keys, source.pageKey, source.category, source.pageType, source.title, source.h1, selectRelatedArticles);

for (const [name, keys, expected] of [
  ['a single reviewed target is not filled', ['care'], ['care']],
  ['explicit order wins over inferred purpose and support rank', ['graduation', 'order'], ['graduation', 'order']],
  ['more than four reviewed targets remain in order', ['care', 'order', 'published', 'graduation', 'message'], ['care', 'order', 'published', 'graduation', 'message']],
  ['duplicates retain first reviewed position', ['care', 'order', 'care'], ['care', 'order']],
  ['self, unknown, draft, merged and noindex are excluded', ['self', 'unknown', 'draft', 'merged', 'noindex', 'published', 'order'], ['published', 'order']],
  ['ineligible explicit list does not cause fallback', ['self', 'unknown', 'draft'], []],
]) test(name, async () => assert.deepEqual(await run(keys), expected));

for (const [name, source, expected] of [
  ['hospital visit excludes funeral, graduation and another facility', current, ['order', 'care']],
  ['legacy general-guide school purpose gets graduation help', { ...current, pageType: 'general-guide', title: '대학 입학·졸업식 꽃' }, ['order', 'graduation', 'care']],
  ['station meeting gets gifting support', { ...current, pageType: 'station-transit', title: '역에서 약속 전 꽃' }, ['message', 'order', 'care']],
  ['event purpose does not treat every occasion as relevant', { ...current, pageType: 'event-venue', title: '문화광장 행사 꽃' }, ['order', 'care']],
  ['funeral keeps condolence and order help, without gift filler', { ...current, category: 'funeral', pageType: 'funeral-facility', title: '병원 장례식장 근조화환' }, ['order', 'funeral-guide']],
  ['unknown purpose does not guess gifting or funeral', { ...current, pageType: 'general-guide', title: '꽃 안내' }, ['order']],
]) test(name, async () => assert.deepEqual(await run([], { source }), expected));

test('a reviewed funeral next step is unchanged', async () => {
  assert.deepEqual(await run(['order'], { source: { ...current, category: 'funeral', pageType: 'funeral-facility' } }), ['order']);
});
test('matching event guide can be selected', async () => {
  const input = [...articles, article('event-guide', { category: 'occasions', title: '야외 행사 꽃 포장' })];
  assert.deepEqual(await run([], { input, source: { ...current, pageType: 'event-venue', title: '문화광장 행사 꽃' } }), ['order', 'event-guide', 'care']);
});
test('funeral advice is rejected even when filed under order help', async () => {
  const input = [...articles, article('condolence-order', { category: 'order-help', title: '근조화환 주문 확인' })];
  assert.deepEqual(await run([], { input }), ['order', 'care']);
});
test('architecture purpose wins over legacy content default', async () => {
  const architecture = [...architectureFor(articles), { ...current, pageType: 'funeral-facility', category: 'funeral' }];
  assert.deepEqual(await run([], { architecture, source: { ...current, pageType: 'general-guide', title: '' } }), ['order', 'funeral-guide']);
});
test('place landing cannot masquerade as next order step', async () => {
  const input = [...articles, article('broad-place-guide', { pageType: 'order-help', title: '주문 도움' })];
  const architecture = architectureFor(input).map((page) => page.pageKey === 'broad-place-guide' ? { ...page, pageRole: 'PLACE_LANDING' } : page);
  assert.deepEqual(await run([], { input, architecture }), ['order', 'care']);
});
test('overlapping venue words cannot justify an unrelated purpose', async () => {
  const input = [article('self', current), article('same-name', { category: 'occasions', title: '병문안대학 졸업식 꽃' })];
  assert.deepEqual(await run([], { input }), []);
});
test('fallback has no four-card quota or cap and a stable order', async () => {
  const input = [article('self'), ...['f', 'e', 'd', 'c', 'b', 'a'].map((key) => article(key, { category: 'order-help', title: '수령 정보 확인' }))];
  assert.deepEqual(await run([], { input }), ['a', 'b', 'c', 'd', 'e', 'f']);
  assert.deepEqual(await run([], { input: [...input].reverse() }), ['a', 'b', 'c', 'd', 'e', 'f']);
});
test('one relevant guide stays one; active unrelated articles do not pad it', async () => {
  assert.deepEqual(await run([], { input: articles.filter(({ data }) => data.pageKey !== 'care') }), ['order']);
});
test('no relevant target means no cards despite other active articles', async () => {
  assert.deepEqual(await run([], { input: articles.filter(({ data }) => !['order', 'care'].includes(data.pageKey)) }), []);
});
test('empty collections produce no cards', async () => {
  assert.deepEqual(await run([], { input: [] }), []);
  assert.deepEqual(await run(['order'], { input: [] }), []);
});

// Read real frozen metadata: synthetic titles must not hide mixed-purpose guides.
const sourceArchitecture = JSON.parse(fs.readFileSync(new URL('../src/data/architecture.json', import.meta.url), 'utf8')).pages;
function frozenArticle(pageKey) {
  const frontmatter = fs.readFileSync(new URL(`../src/content/articles/${pageKey}.md`, import.meta.url), 'utf8').split('---')[1];
  const field = (name) => {
    const raw = frontmatter.match(new RegExp(`^${name}:\\s*(.+)$`, 'm'))?.[1];
    return raw?.startsWith('"') || raw?.startsWith('[') ? JSON.parse(raw) : raw;
  };
  return article(pageKey, Object.fromEntries(['category', 'pageType', 'routeType', 'title', 'description', 'h1', 'relatedPageKeys', 'draftStatus'].map((key) => [key, field(key)])));
}
const frozenArticles = sourceArchitecture.map(({ pageKey }) => frozenArticle(pageKey));
const runFrozen = (pageKey, keys = []) => run(keys, {
  input: frozenArticles,
  architecture: sourceArchitecture,
  source: { ...frozenArticles.find(({ data }) => data.pageKey === pageKey).data, ...sourceArchitecture.find((page) => page.pageKey === pageKey) },
});
test('real mixed opening, promotion and condolence message guide is not a visit or graduation recommendation', async () => {
  const message = frozenArticles.find(({ data }) => data.pageKey === 'ansan-flower-launch-04').data;
  assert.match(message.description, /개업·이전·승진·조문/);
  assert.deepEqual(await runFrozen('ansan-flower-launch-09'), ['ansan-flower-launch-03', 'ansan-flower-launch-05', 'ansan-flower-launch-21']);
  assert.deepEqual(await runFrozen('ansan-flower-launch-07'), ['ansan-flower-launch-03', 'ansan-flower-launch-15', 'ansan-flower-launch-05', 'ansan-flower-launch-21']);
});
test('real reviewed station and funeral links retain their exact original order', async () => {
  for (const pageKey of ['ansan-flower-launch-10', 'ansan-flower-launch-31']) {
    const keys = frozenArticles.find(({ data }) => data.pageKey === pageKey).data.relatedPageKeys;
    assert.ok(keys.length);
    assert.deepEqual(await runFrozen(pageKey, keys), keys);
  }
});
test('generic flower-care summary examples do not turn it into a specific event journey', async () => {
  const input = [article('self'), article('seasonal', { category: 'guide', pageType: 'flower-knowledge', title: '계절별 꽃 관리', description: '기온과 수분관리, 행사 환경을 확인합니다.' })];
  assert.deepEqual(await run([], { input }), ['seasonal']);
});
