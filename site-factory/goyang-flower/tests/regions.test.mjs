import test from 'node:test';
import assert from 'node:assert/strict';
import coverage from '../src/data/region-coverage.json' with {type:'json'};
import {validateRegionDefinition, regionUnit, regionGroups, validateRegionalGraph} from '../src/lib/regions.mjs';
import {productFamilies} from '../src/lib/catalog.mjs';
import {loadGraph, validateGraph} from '../scripts/qa_graph.mjs';

const makePage = (unit = coverage.units[0]) => ({
  pageKey:unit.pageKey, slug:unit.slug, url:unit.url, category:'regions',
  pageType:'regional-service', routeType:'category', status:'approved',
  approvalVerified:true, snapshotId:'test-fixture-not-an-approval', visualIntent:'flower_delivery'
});
const makeArchitecture = page => ({siteKey:'goyang-flower-v2', pages:[{
  ...page, pageRole:'REGION_SERVICE_LANDING', parentHub:'/regions/', localizationPolicy:'local-required'
}]});

test('official input retains legal and administrative bases without double counting', () => {
  validateRegionDefinition(coverage);
  assert.equal(coverage.districts.length,3);
  assert.equal(coverage.units.length,53);
  assert.equal(coverage.administrativeCrosswalk.length,44);
  assert.deepEqual(coverage.districts.map(d => coverage.units.filter(u => u.districtKey === d.key).length),[32,13,8]);
  const samsong2=coverage.administrativeCrosswalk.find(a=>a.name==='삼송2동');
  assert.equal(samsong2.relations.length,2);
  assert.ok(samsong2.relations.every(r=>r.scope==='partial'));
  assert.ok(coverage.units.find(u=>u.name==='고양동').url.includes('deogyang-goyang'));
  assert.ok(coverage.units.find(u=>u.name==='일산동').url.includes('ilsanseo-ilsan'));
});
test('definition has no fixed count pass condition', () => {
  const c=structuredClone(coverage);
  c.units=c.units.slice(0,1); c.districts=c.districts.slice(0,1);
  c.administrativeCrosswalk=c.administrativeCrosswalk.map(a=>({...a,relations:a.relations.filter(r=>r.legalUnitKey===c.units[0].unitKey)})).filter(a=>a.relations.length);
  assert.doesNotThrow(()=>validateRegionDefinition(c));
});
test('empty official list, duplicate route, cross-district and unknown relation fail closed', () => {
  for (const mutate of [c=>c.units=[],c=>c.units[1].url=c.units[0].url,
    c=>c.administrativeCrosswalk[0].relations[0].legalUnitKey='absent',
    c=>c.administrativeCrosswalk[0].districtKey='ilsanseo',
    c=>c.administrativeCrosswalk[0].relations[0].scope='all']) {
    const c=structuredClone(coverage);mutate(c);assert.throws(()=>validateRegionDefinition(c),/Region coverage/);
  }
});
test('empty regional input creates no groups or planned links', () => {
  assert.deepEqual(regionGroups([],coverage),[]);
  assert.deepEqual(regionGroups(loadGraph().pages,coverage),[]);
});
test('only actual approved pages appear under their district', () => {
  const page=makePage();const groups=regionGroups([page],coverage);
  assert.equal(groups.length,1);assert.equal(groups[0].items.length,1);
  assert.equal(groups[0].items[0].page.url,page.url);
  assert.equal(groups[0].key,coverage.units[0].districtKey);
});
test('the complete official route map groups without inventing separate administrative pages', () => {
  const groups=regionGroups(coverage.units.map(unit=>makePage(unit)),coverage);
  assert.deepEqual(groups.map(group=>group.items.length),[32,13,8]);
  assert.equal(groups.flatMap(group=>group.items).length,coverage.units.length);
});
test('unknown, wrong-slug, pending and unapproved regional routes fail', () => {
  for(const patch of [{pageKey:'unknown'},{url:'/regions/phantom/'},{slug:'phantom'},
    {category:'funeral'},{pageType:'funeral-facility'},{status:'pending'},
    {approvalVerified:false},{snapshotId:''},{routeType:'top_level'}]) {
    assert.throws(()=>regionUnit({...makePage(),...patch},coverage),/Region route or approval mismatch/);
  }
});
test('regional graph requires the real region role, parent and local-required policy', () => {
  const page=makePage();const architecture=makeArchitecture(page);
  assert.equal(validateRegionalGraph([page],architecture,coverage).publishedRegionalPages,1);
  for(const patch of [{pageRole:'PLACE_LANDING'},{parentHub:'/funeral/'},{localizationPolicy:'global'},{routeType:'region'}]) {
    const a=structuredClone(architecture);Object.assign(a.pages[0],patch);
    assert.throws(()=>validateRegionalGraph([page],a,coverage),/Region semantics mismatch/);
  }
});
test('regional product intent is explicit and never defaults to funeral', () => {
  assert.deepEqual(productFamilies(makePage()),['bouquet','basket','funeral','congrats']);
  assert.deepEqual(productFamilies({...makePage(),visualIntent:'flower_gift'}),['bouquet','basket']);
  assert.throws(()=>productFamilies({...makePage(),visualIntent:'consultation'}),/explicit supported/);
  assert.deepEqual(productFamilies({pageType:'unknown',category:'regions'}),[]);
});
test('regional product promises reject the opposite wreath family in both directions', () => {
  for (const [primaryKeyword,visualIntent] of [
    ['강매동근조화환','congrats_wreath'],['강매동축하화환','funeral_wreath']
  ]) assert.throws(()=>productFamilies({...makePage(),primaryKeyword,visualIntent}),/contradicts promised wreath family/);
  assert.deepEqual(productFamilies({...makePage(),primaryKeyword:'강매동 근조화환',visualIntent:'funeral_wreath'}),['funeral']);
  assert.deepEqual(productFamilies({...makePage(),primaryKeyword:'강매동 축하화환',visualIntent:'congrats_wreath'}),['congrats']);
});
test('whole graph rejects regional keyword versus wreath visual-intent contradictions', () => {
  // In-memory fixture only: no Draft, snapshot, catalog or real content is changed.
  const graph=(primaryKeyword,visualIntent)=>{
    const data=loadGraph();
    const page={...makePage(),primaryKeyword,visualIntent,title:primaryKeyword,h1:primaryKeyword,
      description:'Synthetic graph test description',cardSummary:'Synthetic graph test card',
      firstAnswer:'Synthetic graph test answer',source:{url:coverage.officialSourceUrls[0],verifiedAt:coverage.verifiedAt}};
    data.pages.push(page);
    data.manifest.pages.push({...page});data.map.pages.push({...page});
    data.architecture.pages.push({...makeArchitecture(page).pages[0],intentKey:'synthetic-regional-product-test'});
    data.architecture.hubs.find(hub=>hub.category==='regions').children=1;
    return data;
  };
  assert.deepEqual(validateGraph(graph('강매동근조화환','funeral_wreath')),{pages:2,hubs:2});
  assert.deepEqual(validateGraph(graph('강매동축하화환','congrats_wreath')),{pages:2,hubs:2});
  assert.throws(()=>validateGraph(graph('강매동근조화환','congrats_wreath')),/contradicts promised wreath family/);
  assert.throws(()=>validateGraph(graph('강매동축하화환','funeral_wreath')),/contradicts promised wreath family/);
});
test('unchanged frozen canary graph remains valid with no regional content', () => {
  const data=loadGraph();assert.deepEqual(validateGraph(data),{pages:1,hubs:1});
  assert.equal(data.manifest.snapshotLedger['goyang-ilsan-paik-r2-20261002T040830'].snapshotHash,
    '1419cc48f44a3618cbc365ac7f3796d4cd35dc5522eeff655a22f4caadfbdf10');
});
