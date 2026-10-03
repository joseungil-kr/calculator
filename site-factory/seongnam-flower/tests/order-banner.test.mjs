import assert from 'node:assert/strict';
import test from 'node:test';
import fs from 'node:fs';
import {displayMarkdownBlocks} from '../src/lib/content.mjs';
import {orderBannerBoundary} from '../src/lib/order-banner.mjs';

const sections = (count, length = 300) => Array.from({length: count}, (_, index) => [
  {type: 'h2', text: `Section ${index}`}, {type: 'p', text: '가'.repeat(length)},
]).flat();
test('one midpoint boundary follows two complete sections and precedes the final section', () => {
  const blocks = sections(5);
  const before = JSON.stringify(blocks);
  assert.equal(orderBannerBoundary(blocks), 4);
  assert.equal(JSON.stringify(blocks), before);
});
test('no banner on a short article or fewer than four sections', () => {
  for (const blocks of [[], sections(3), sections(6, 20)]) assert.equal(orderBannerBoundary(blocks), -1);
});
test('paragraphs, lists and subheadings are never split by a banner', () => {
  const blocks = sections(6);
  blocks.splice(4, 0, {type:'li',text:'목록'.repeat(300)}, {type:'h3',text:'하위 항목'}, {type:'p',text:'내용'});
  assert.equal(blocks[orderBannerBoundary(blocks)].type, 'h2');
});
const frozen = JSON.parse(fs.readFileSync(new URL('./fixtures/order-banner-initial22.json', import.meta.url)));
function assertArticleBanners(pages) {
  const before = JSON.stringify(pages);
  for (const page of pages) {
    const blocks = displayMarkdownBlocks(page.contentMarkdown || '', page.firstAnswer);
    const beforeBlocks = JSON.stringify(blocks);
    const boundary = orderBannerBoundary(blocks);
    const headings = blocks.flatMap((b,i) => b.type==='h2'?[i]:[]);
    const length = blocks.reduce((n, block) => n + block.text.length, 0);
    if (headings.length < 4 || length < 900) {
      assert.equal(boundary, -1, page.pageKey);
    } else {
      assert.ok(headings.slice(2,-1).includes(boundary), page.pageKey);
    }
    assert.equal(JSON.stringify(blocks), beforeBlocks, page.pageKey);
  }
  assert.equal(JSON.stringify(pages), before);
}
test('the exact initial 22 frozen articles keep their reviewed banner boundaries', () => {
  assert.equal(frozen.sourceRevision, 'e1d187856a0e88cd7c21fc5a06f81742f32c2143');
  assert.equal(frozen.cases.length, 22);
  assert.equal(new Set(frozen.cases.map(page => page.pageKey)).size, 22);
  assertArticleBanners(frozen.cases);
  for (const page of frozen.cases) {
    assert.equal(orderBannerBoundary(displayMarkdownBlocks(page.contentMarkdown, page.firstAnswer)), page.expectedBoundary, page.pageKey);
  }
});
test('runtime articles follow the per-article banner conditions without fixing the page count', () => {
  const pages = JSON.parse(fs.readFileSync(new URL('../src/data/pages.json', import.meta.url)));
  assertArticleBanners(pages);
  // An unchanged frozen snapshot must retain its exact approved text. A later
  // approved snapshot can replace an article without rewriting this baseline.
  for (const page of pages) {
    const baseline = frozen.cases.find(candidate => candidate.pageKey===page.pageKey && candidate.snapshotId===page.snapshotId);
    if (baseline) {
      assert.equal(page.firstAnswer, baseline.firstAnswer, page.pageKey);
      assert.equal(page.contentMarkdown, baseline.contentMarkdown, page.pageKey);
    }
  }
});
test('growing beyond the baseline accepts long, short, sparse and non-Markdown articles', () => {
  const markdown = blocks => blocks.map(block => block.type==='h2' ? `## ${block.text}` : block.text).join('\n\n');
  const additions = [
    {pageKey:'additional-long', contentMarkdown:markdown(sections(5))},
    {pageKey:'additional-short', contentMarkdown:markdown(sections(4, 20))},
    {pageKey:'additional-sparse', contentMarkdown:markdown(sections(3, 400))},
    {pageKey:'additional-non-markdown'},
  ];
  assertArticleBanners([...frozen.cases, ...additions]);
  assertArticleBanners([]);
});
test('a runtime growth scenario does not require copying every old fixture into runtime data', () => {
  assertArticleBanners([{pageKey:'standalone',contentMarkdown:'간단한 안내입니다.'}]);
});
test('banner uses verified site fields, accessible links and no new product image or price claim', () => {
  const component = fs.readFileSync(new URL('../src/components/InlineOrderBanner.astro',import.meta.url),'utf8');
  assert.match(component, /<aside[^>]+aria-label=/);
  assert.match(component, /href=\{site.phoneHref\}/);
  assert.match(component, /href=\{site.orderUrl\}/);
  assert.match(component, /site.phoneOrderHours/);
  assert.match(component, /site.onlineOrderHours/);
  assert.match(component, /배송시간을 보장하지 않습니다/);
  assert.doesNotMatch(component, /<img|<p[ >]|<h[1-6][ >]|<li[ >]|set:html|안산|무료|최저가|당일배송 보장|\d[,.]?\d{3}원/);
  assert.match(component, /min-height:48px/);
  assert.match(component, /@media\(max-width:600px\)/);
});
