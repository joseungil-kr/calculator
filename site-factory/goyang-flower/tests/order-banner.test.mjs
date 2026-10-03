import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {markdownBlocks} from '../src/lib/content.mjs';
import {orderBannerBoundary} from '../src/lib/order-banner.mjs';

const sections=(count,length=300)=>Array.from({length:count},(_,index)=>[
  {type:'h2',text:`Section ${index}`},{type:'p',text:'가'.repeat(length)}
]).flat();
test('long regional content gets one middle-section boundary without changing its blocks',()=>{
  const blocks=sections(5),before=JSON.stringify(blocks);
  assert.equal(orderBannerBoundary(blocks),4);
  assert.equal(JSON.stringify(blocks),before);
});
test('short and sparse content keeps a purchase point without adding a length quota',()=>{
  assert.equal(orderBannerBoundary([]),-1);
  for(const blocks of [sections(3),sections(6,20),[{type:'p',text:'짧은 안내'}]]) {
    const before=JSON.stringify(blocks),boundary=orderBannerBoundary(blocks);
    assert.ok(boundary>0 && boundary<=blocks.length);
    assert.equal(JSON.stringify(blocks),before);
  }
});
test('fallback never separates a heading from its text or splits a contiguous list',()=>{
  for(const blocks of [[{type:'h3',text:'안내'},{type:'p',text:'내용'}],
    [{type:'li',text:'하나'},{type:'li',text:'둘'}],
    [{type:'p',text:'소개'},{type:'li',text:'하나'},{type:'li',text:'둘'},{type:'p',text:'끝'}]]) {
    const boundary=orderBannerBoundary(blocks);
    if(boundary<blocks.length){
      assert.ok(!['h2','h3'].includes(blocks[boundary-1].type));
      assert.ok(!(blocks[boundary-1].type==='li' && blocks[boundary].type==='li'));
    }
  }
});
test('each current approved regional Markdown gets one unchanged-content boundary',()=>{
  const pages=JSON.parse(fs.readFileSync(new URL('../src/data/pages.json',import.meta.url))),before=JSON.stringify(pages);
  for(const page of pages.filter(page=>page.category==='regions' && page.pageType==='regional-service')) {
    const blocks=markdownBlocks(page.contentMarkdown),copy=JSON.stringify(blocks),boundary=orderBannerBoundary(blocks);
    assert.ok(boundary>0 && boundary<=blocks.length,page.pageKey);
    assert.equal(JSON.stringify(blocks),copy,page.pageKey);
  }
  assert.equal(JSON.stringify(pages),before);
});
test('renderer opts in only regional-service details and leaves ordinary Markdown disabled',()=>{
  const detail=fs.readFileSync(new URL('../src/pages/[category]/[slug].astro',import.meta.url),'utf8');
  const markdown=fs.readFileSync(new URL('../src/components/MarkdownContent.astro',import.meta.url),'utf8');
  assert.match(detail,/regionalOrderBanner=\{page.pageType==='regional-service' && page.category==='regions'\}/);
  assert.match(markdown,/Astro.props.regionalOrderBanner === true \? orderBannerBoundary\(blocks\) : -1/);
});
test('banner uses verified site values and scoped-in-output CSS without new price or image claims',()=>{
  const component=fs.readFileSync(new URL('../src/components/InlineOrderBanner.astro',import.meta.url),'utf8');
  assert.match(component,/<aside[^>]+aria-label=/);
  assert.match(component,/href=\{site.phoneHref\}/);
  assert.match(component,/href=\{site.orderUrl\}/);
  assert.match(component,/class="inline-order-phone btn"/);
  assert.match(component,/class="inline-order-online btn"/);
  assert.match(component,/site.phoneOrderHours/);assert.match(component,/site.onlineOrderHours/);
  assert.match(component,/배송시간을 보장하지 않습니다/);
  assert.match(component,/<style is:inline>/);assert.match(component,/min-height:48px/);
  assert.doesNotMatch(component,/<img|<p[ >]|<h[1-6][ >]|<li[ >]|set:html|성남|안산|무료|최저가|당일배송 보장|\d[,.]?\d{3}원/);
});
