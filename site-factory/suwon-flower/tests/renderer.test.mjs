import test from 'node:test';
import assert from 'node:assert/strict';
import {productFamilies,selectProducts} from '../src/lib/catalog.mjs';
import {markdownBlocks,inlineTokens,safeHref} from '../src/lib/content.mjs';
import {validateGraph,loadGraph} from '../scripts/qa_graph.mjs';
const data=loadGraph();
test('baseline registries and source provenance are aligned',()=>validateGraph(data));
test('hospital, school and personal gifts never inherit wreath products',()=>{
 for(const pageType of ['hospital-visit','school-event','personal-gift','station-transit']){
  const selected=selectProducts({pageType,visualIntent:'consultation'},data.products);
  assert.ok(selected.length>0);assert.ok(selected.every(p=>['bouquet','basket'].includes(p.family)));
 }
});
test('unknown intent fails closed without invented catalog matches',()=>assert.deepEqual(productFamilies({pageType:'unknown'}),[]));
test('growth beyond thirty pages succeeds without numeric ceiling',()=>{
 const d=structuredClone(data),p=structuredClone(d.pages[0]);p.pageKey='growth-fixture';p.slug='growth-fixture';p.url='/funeral/growth-fixture/';p.snapshotId='growth-v1';p.primaryKeyword='새 검색의도';p.intentKey='new-intent';d.pages.push(p);
 for(const collection of [d.manifest.pages,d.map.pages,d.architecture.pages])collection.push({...structuredClone(collection[0]),pageKey:p.pageKey,url:p.url,snapshotId:p.snapshotId,intentKey:p.intentKey});
 d.architecture.hubs.find(h=>h.category==='funeral').children++;
 assert.equal(validateGraph(d).pages,data.pages.length+1);
});
test('stale registry and duplicate routes fail',()=>{
 const d=structuredClone(data);d.manifest.pages[0].snapshotId='stale';assert.throws(()=>validateGraph(d),/parity/);
 const dup=structuredClone(data);dup.pages[1].url=dup.pages[0].url;assert.throws(()=>validateGraph(dup),/URL/);
});
test('Markdown retains headings/text but rejects executable links',()=>{
 assert.equal(safeHref('javascript:alert(1)'),null);assert.equal(safeHref('//evil.test'),null);assert.equal(safeHref('data:text/html,evil'),null);
 assert.equal(safeHref('/order/suwon-flower-delivery-price/'),'/order/suwon-flower-delivery-price/');
 assert.equal(inlineTokens('[bad](javascript:alert)')[0].href,null);
 assert.equal(markdownBlocks('<script>alert(1)</script>')[0].text,'<script>alert(1)</script>');
 assert.equal(markdownBlocks('## Heading\n\nParagraph')[0].type,'h2');
});

test('conflicting hospital category cannot resurrect funeral product imagery',()=>{
 const p={pageType:'hospital-visit',category:'funeral'};assert.ok(selectProducts(p,data.products).every(x=>x.family==='bouquet'||x.family==='basket'));
 const d=structuredClone(data);d.pages[0].pageType='hospital-visit';assert.throws(()=>validateGraph(d),/Category\/pageType/);
});
import {verifyPublication,submissionPayload} from '../scripts/indexnow_contract.mjs';
test('IndexNow requires exact live production verification',()=>{
 const production={origin:'https://suwon.fwith.kr',indexable:'true',revision:'a'.repeat(40),verifiedRevision:'a'.repeat(40)};
 assert.doesNotThrow(()=>verifyPublication(production));
 for(const patch of [{indexable:'false'},{origin:'https://preview.invalid'},{verifiedRevision:'manual_required'},{revision:'local'}])assert.throws(()=>verifyPublication({...production,...patch}));
 assert.throws(()=>submissionPayload({origin:production.origin,key:'a'.repeat(64),urlList:['https://other.example/']}));
});
