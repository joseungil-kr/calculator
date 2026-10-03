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
test('every approved Seongnam article receives exactly one safe purchase point without mutation', () => {
  const pages = JSON.parse(fs.readFileSync(new URL('../src/data/pages.json', import.meta.url)));
  const before = JSON.stringify(pages);
  assert.equal(pages.length, 22);
  for (const page of pages) {
    const blocks = displayMarkdownBlocks(page.contentMarkdown, page.firstAnswer);
    const boundary = orderBannerBoundary(blocks);
    const headings = blocks.flatMap((b,i) => b.type==='h2'?[i]:[]);
    assert.ok(headings.slice(2,-1).includes(boundary), page.pageKey);
  }
  assert.equal(JSON.stringify(pages), before);
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
