import test from 'node:test';
import assert from 'node:assert/strict';
import {productFamilies,selectProducts,homeProducts} from '../src/lib/catalog.mjs';
import {nextSteps,relatedReading} from '../src/lib/journey.mjs';
import {hubGuides,hubProducts} from '../src/lib/hubs.mjs';
import {validateCustomerIntent} from '../scripts/qa_intent.mjs';
import {runIntentRegressionProof} from '../scripts/qa_intent_regressions.mjs';
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

test('all current pages satisfy intent answers without a shared section template',()=>{
 for(const page of data.pages)assert.equal(validateCustomerIntent(page,data.products),true);
 const message=structuredClone(data.pages.find(p=>p.pageType==='message-guide'));
 message.sections.reverse();assert.equal(validateCustomerIntent(message,data.products),true);
});
test('message title cannot pass with no usable examples',()=>{
 const p=structuredClone(data.pages.find(p=>p.pageType==='message-guide'));
 p.firstAnswer='근조·개업·이전·공연 문구를 정하세요.';
 p.sections=[['문구를 골라보세요','근조·개업·이전·공연에 맞는 문구와 개인·회사·단체 발신자를 정하세요.']];p.faq=[];
 assert.throws(()=>validateCustomerIntent(p,data.products),/missing usable/);
});
test('customer copy rejects internal catalog jargon',()=>{
 const p=structuredClone(data.pages[0]);p.sections[0][1]+=' 실제 Product Catalog 기준으로';
 assert.throws(()=>validateCustomerIntent(p,data.products),/internal\/invalid/);
});
test('performance hero, answer, body and price cannot drift to wreath orders',()=>{
 for(const original of data.pages.filter(p=>p.visualIntent==='performance_venue')) {
  assert.ok(selectProducts(original,data.products).every(p=>p.family==='bouquet'));
  const intro=structuredClone(original);intro.firstAnswer='축하화환은 59,000원부터 선택할 수 있습니다.';
  assert.throws(()=>validateCustomerIntent(intro,data.products),/performance primary/);
  const body=structuredClone(original);body.sections.push(['주문','축하화환 상품을 선택해 주문하세요.']);
  assert.throws(()=>validateCustomerIntent(body,data.products),/performance body/);
  const price=structuredClone(original);price.firstAnswer='출연자에게 직접 건네는 꽃다발은 59,000원입니다.';
  assert.throws(()=>validateCustomerIntent(price,data.products),/performance primary price/);
  const named=structuredClone(original);named.sections.push(['가격','소소한 행복(G105)은 59,000원입니다.']);
  assert.throws(()=>validateCustomerIntent(named,data.products),/catalog price/);
 }
});
test('gift and graduation journeys never contain wreath-order or sibling-venue stages',()=>{
 for(const p of data.pages.filter(p=>['hospital-visit','personal-gift','school-event','station-transit'].includes(p.pageType)||p.visualIntent==='performance_venue')) {
  const next=nextSteps(p,data.pages);
  assert.ok(next.some(x=>x.visualIntent==='order_address'));
  assert.ok(next.every(x=>!['wreath_order','wreath_message','hospital-visit','school-event'].includes(x.visualIntent)&&['order-help','price-guide'].includes(x.pageType)));
  assert.ok(!relatedReading(p,data.pages).some(x=>next.includes(x)));
 }
});
test('home and hubs show real purpose-appropriate catalog choices',()=>{
 assert.deepEqual(new Set(homeProducts(data.products).map(p=>p.family)),new Set(['funeral','congrats','bouquet','basket']));
 for(const [cat,guide] of Object.entries(hubGuides)) {
  const choices=hubProducts(cat,data.products);
  assert.ok(guide.decision.length>0 && choices.length>0);
  assert.ok(choices.every(p=>guide.families.includes(p.family)&&p.assetType==='real_product'));
 }
});
test('anniversary and transit reading does not inherit hospital-visit intent',()=>{
 for(const p of data.pages.filter(p=>['personal-gift','station-transit'].includes(p.pageType)))
  assert.ok(relatedReading(p,data.pages).every(x=>x.pageType===p.pageType));
});
test('original reviewed ribbon and performance failures reject; repaired pages pass',()=>{
 const proof=runIntentRegressionProof(data);
 assert.equal(proof.reproduced.length,2);assert.equal(proof.approvedPagesPassed,data.pages.length);
 assert.ok(proof.reproduced.every(p=>p.before==='REJECTED'&&p.after==='PASSED'));
});
