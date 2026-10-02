import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {hubGuide,hubGuides,hubProducts} from '../src/lib/hubs.mjs';
const products=JSON.parse(fs.readFileSync(new URL('../src/data/products.json',import.meta.url),'utf8'));
const event={category:'event',pageType:'event-venue',visualIntent:'event_wreath',assetSlot:'REAL_PROOF',primaryKeyword:'성남 기업행사 화환'};
test('actual wreath-only event children narrow both hub promises and required products',()=>{
 const children=[event,{...event,primaryKeyword:'성남 결혼식 화환'}];
 const guide=hubGuide('event',children);
 assert.deepEqual(guide.families,['congrats']);
 assert.doesNotMatch([guide.intro,guide.heading,guide.cta,...guide.decision].join(' '),/꽃다발|꽃바구니|50,000원/);
 assert.match(guide.intro,/59,000원/);
 assert.ok(guide.intro.includes(`${products.find(p=>p.officialSku==='C200').price.toLocaleString('en-US')}원`));
 assert.deepEqual(hubProducts('event',products,3,children).map(p=>p.officialSku),['C200','C203','C204']);
});
test('missing verified congratulatory family still fails closed',()=>{
 assert.throws(()=>hubProducts('event',products.filter(p=>p.family!=='congrats'),3,[event]),/missing hub family/);
});
test('performance or mixed event children cannot be hidden by a wreath-only fallback',()=>{
 const performance={...event,visualIntent:'performance_venue',primaryKeyword:'성남 공연 꽃다발'};
 assert.equal(hubGuide('event',[performance]),hubGuides.event);
 assert.equal(hubGuide('event',[event,performance]),hubGuides.event);
 assert.throws(()=>hubProducts('event',products,3,[event,performance]),/missing hub family/);
 assert.throws(()=>hubProducts('event',products,3,[performance]),/missing hub family/);
});
test('no real children and other category guides keep the existing contract',()=>{
 assert.equal(hubGuide('event',[]),hubGuides.event);
 assert.throws(()=>hubProducts('event',products,3,[]),/missing hub family/);
 for(const category of ['funeral','business','order','school','gift'])assert.equal(hubGuide(category,[event]),hubGuides[category]);
});
