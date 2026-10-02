import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {nextSteps,relatedReading} from '../src/lib/journey.mjs';
import {productFamilies} from '../src/lib/catalog.mjs';
import {hubGuide} from '../src/lib/hubs.mjs';
const allPages=JSON.parse(fs.readFileSync(new URL('../src/data/pages.json',import.meta.url),'utf8'));
// Pin the observed seven-page regression while allowing later approved guides
// to extend the live journey without breaking this historical fixture.
const fixtureKeys=['seongnam-snuh-funeral-wreath','seongnam-opening-wreath','seongnam-funeral-wreath-price',
 'seongnam-congrats-wreath-price','seongnam-same-day-wreath','seongnam-corporate-event-wreath','seongnam-wedding-wreath'];
const pages=allPages.filter(p=>fixtureKeys.includes(p.pageKey));
const key=short=>'seongnam-'+short;
const find=short=>pages.find(p=>p.pageKey===key(short));
const next=short=>nextSteps(find(short),pages).map(p=>p.pageKey);
test('current congrats/event journeys choose congrats price and verified delivery help',()=>{
 for(const short of ['opening-wreath','corporate-event-wreath','wedding-wreath'])
  assert.deepEqual(next(short),[key('congrats-wreath-price'),key('same-day-wreath')]);
});
test('current funeral journey retains funeral price and appropriate delivery help',()=>{
 assert.deepEqual(next('snuh-funeral-wreath'),[key('funeral-wreath-price'),key('same-day-wreath')]);
});
test('price guides never point to themselves or another price guide',()=>{
 for(const short of ['funeral-wreath-price','congrats-wreath-price'])assert.deepEqual(next(short),[key('same-day-wreath')]);
});
test('mixed-family delivery guide does not arbitrarily send buyers to one-family pricing',()=>{
 assert.deepEqual(next('same-day-wreath'),[]);
});
test('unapproved/unverified/self/venue candidates are not purchase stages',()=>{
 const page=find('corporate-event-wreath'),price=find('congrats-wreath-price');
 const bad=[{...price,status:'draft'}, {...price,approvalVerified:false}, {...price,snapshotId:''},
  {...price,pageKey:page.pageKey},{...price,url:page.url},find('opening-wreath')];
 for(const target of bad)assert.deepEqual(nextSteps(page,[target]),[]);
});
test('no matching guide returns empty and preserves real conversion CTAs in renderer',()=>{
 assert.deepEqual(nextSteps(find('corporate-event-wreath'),[find('funeral-wreath-price')]),[]);
 const source=fs.readFileSync(new URL('../src/pages/[category]/[slug].astro',import.meta.url),'utf8');
 assert.match(source,/href=\{site.phoneHref\}/);
 assert.match(source,/href=\{hero\?\.orderUrl \|\| site.orderUrl\}/);
 assert.match(source,/journey.length>0/);
});
test('all live targets cover the source family and are approved ordering guides',()=>{
 for(const p of allPages)for(const target of nextSteps(p,allPages)){
  assert.ok(productFamilies(p).every(f=>productFamilies(target).includes(f)));
  assert.equal(target.status,'approved');assert.equal(target.approvalVerified,true);assert.ok(target.snapshotId);
  assert.notEqual(target.pageKey,p.pageKey);assert.notEqual(target.url,p.url);
  assert.ok(['price-guide','message-guide','order-help'].includes(target.pageType));
 }
});
test('home purpose card uses the same actual-child guide as the event hub',()=>{
 const source=fs.readFileSync(new URL('../src/pages/index.astro',import.meta.url),'utf8');
 assert.match(source,/hubGuide\(g.cat,pages\).decision\[0\]/);
 assert.doesNotMatch(source,/hubGuides\[g.cat\]/);
 assert.doesNotMatch(hubGuide('event',pages).decision[0],/꽃다발|꽃바구니/);
 assert.equal(hubGuide('event',pages).decision[0],'행사명·홀 또는 전시장·받는 담당자 확인');
});
test('source relatedKeys are not changed or recast as unrelated ordering links',()=>{
 for(const p of pages){
  const before=JSON.stringify(p);
  nextSteps(p,pages);relatedReading(p,pages);
  assert.equal(JSON.stringify(p),before);
 }
});
