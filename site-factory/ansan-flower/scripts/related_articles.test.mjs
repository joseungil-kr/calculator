import assert from 'node:assert/strict';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

// Exercise the actual Astro collection filter and card-selection code.
const layout = fs.readFileSync(fileURLToPath(new URL('../src/layouts/ArticleLayout.astro', import.meta.url)), 'utf8');
const collection = layout.slice(layout.indexOf('const activePageKeys ='), layout.indexOf('const detailCategoryCounts ='));
const selection = layout.slice(layout.indexOf('const nextCategoryPriority:'), layout.indexOf('const formatDate ='))
  .replace('const nextCategoryPriority: Record<string, string[]> =', 'const nextCategoryPriority =');
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const select = new AsyncFunction('architecturePages', 'getCollection', 'relatedPageKeys', 'pageKey', 'category', 'structureType', collection + selection + '\nreturn related.map(a=>a.data.pageKey);');
const article = (pageKey, category = 'funeral', structureType = 'question', draftStatus = 'approved') => ({ data: { pageKey, category, structureType, draftStatus } });
const articles = [article('self'), article('a', 'order-help'), article('b', 'places'), article('c', 'guide'), article('d', 'flower-knowledge'), article('e', 'occasions'), article('f', 'order-help', 'guide'), article('published', 'funeral', 'question', 'published'), article('draft', 'funeral', 'question', 'draft'), article('merged'), article('noindex')];
const architecturePages = articles.map(({ data }) => ({ pageKey: data.pageKey, status: data.pageKey === 'merged' ? 'merged' : 'active', sitemapIndexable: data.pageKey !== 'noindex' }));
const run = (keys, input = articles, architecture = architecturePages) => select(architecture, async (name, filter) => {
  assert.equal(name, 'articles');
  return input.filter(filter);
}, keys, 'self', 'funeral', 'question');

test('a single reviewed target is not filled with other cards', async () => {
  assert.deepEqual(await run(['b']), ['b']);
});
test('explicit order wins over category and structure priority', async () => {
  assert.deepEqual(await run(['e', 'f']), ['e', 'f']);
});
test('more than four reviewed targets remain in order', async () => {
  assert.deepEqual(await run(['e', 'f', 'a', 'b', 'c']), ['e', 'f', 'a', 'b', 'c']);
});
test('duplicate targets retain the first reviewed position', async () => {
  assert.deepEqual(await run(['b', 'a', 'b']), ['b', 'a']);
});
test('self, unknown, draft, merged and noindex targets are excluded', async () => {
  assert.deepEqual(await run(['self', 'unknown', 'draft', 'merged', 'noindex', 'published', 'a']), ['published', 'a']);
});
test('an ineligible explicit list does not cause fallback', async () => {
  assert.deepEqual(await run(['self', 'unknown', 'draft']), []);
});
test('an empty list preserves category and structure ranking with four cards', async () => {
  assert.deepEqual(await run([]), ['f', 'a', 'b', 'c']);
});
test('legacy fallback can render fewer than four eligible cards', async () => {
  assert.deepEqual(await run([], [article('self'), article('a', 'order-help'), article('c', 'guide')]), ['a', 'c']);
});
test('empty collections produce no cards', async () => {
  assert.deepEqual(await run([], [], []), []);
  assert.deepEqual(await run(['a'], [], []), []);
});
