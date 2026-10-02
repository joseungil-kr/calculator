import assert from 'node:assert/strict';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

// Execute the actual collection filter and selection block used by Astro.
const layout = fs.readFileSync(fileURLToPath(new URL('../src/layouts/ArticleLayout.astro', import.meta.url)), 'utf8');
const selection = layout.slice(layout.indexOf('const activePageKeys='), layout.indexOf('const formatDate='))
  .replace(/^const hrefFor=.*\n/m, '');
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const select = new AsyncFunction('architecturePages', 'getCollection', 'relatedPageKeys', 'pageKey', 'category', selection + '\nreturn related.map(a=>a.data.pageKey);');
const article = (key, category = 'order', draftStatus = 'approved') => ({ data: { pageKey: key, category, draftStatus } });
const articles = [article('self'), article('a'), article('b'), article('c'), article('d'), article('e'), article('f', 'gift'), article('published', 'order', 'published'), article('draft', 'order', 'draft'), article('merged'), article('noindex')];
const architecturePages = articles.map(({ data }) => ({ pageKey: data.pageKey, status: data.pageKey === 'merged' ? 'merged' : 'active', sitemapIndexable: data.pageKey !== 'noindex' }));
const run = (keys, collection = articles, architecture = architecturePages) => select(architecture, async (name, filter) => {
  assert.equal(name, 'articles');
  return collection.filter(filter);
}, keys, 'self', 'order');

test('one approved target stays one target without automatic fill', async () => {
  assert.deepEqual(await run(['b']), ['b']);
});
test('two approved targets preserve the reviewed order', async () => {
  assert.deepEqual(await run(['e', 'a']), ['e', 'a']);
});
test('more than four reviewed targets are not silently truncated', async () => {
  assert.deepEqual(await run(['f', 'd', 'c', 'b', 'a']), ['f', 'd', 'c', 'b', 'a']);
});
test('duplicate targets retain their first reviewed position', async () => {
  assert.deepEqual(await run(['b', 'a', 'b']), ['b', 'a']);
});
test('self, unknown, draft, merged and noindex targets never appear', async () => {
  assert.deepEqual(await run(['self', 'unknown', 'draft', 'merged', 'noindex', 'published', 'a']), ['published', 'a']);
});
test('an explicit list with no eligible target does not trigger fallback', async () => {
  assert.deepEqual(await run(['self', 'unknown', 'draft']), []);
});
test('legacy empty-list fallback keeps category priority and deterministic four-card limit', async () => {
  assert.deepEqual(await run([]), ['a', 'b', 'c', 'd']);
});
test('legacy fallback can include another category after eligible same-category targets', async () => {
  assert.deepEqual(await run([], [article('self'), article('b'), article('a'), article('f', 'gift')]), ['a', 'b', 'f']);
});
test('empty collections render no related targets', async () => {
  assert.deepEqual(await run([], [], []), []);
  assert.deepEqual(await run(['a'], [], []), []);
});
