import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {pageSources,sourceTypeLabels} from '../src/lib/sources.mjs';
const pages=JSON.parse(fs.readFileSync(new URL('../src/data/pages.json',import.meta.url)));
const source={name:'검토된 시설 출처',url:'https://example.org/path?a=1&b=2',type:'facility',verifiedAt:'2026-10-02'};
test('every frozen source is retained in reviewed order without mutation',()=>{
  const before=JSON.stringify(pages);
  for(const page of pages){
    assert.ok(page.sources.length>0);
    assert.deepEqual(pageSources(page),page.sources);
    assert.equal(pageSources(page)[0],page.sources[0]);
  }
  assert.equal(JSON.stringify(pages),before);
});
test('legacy primary-only page remains supported without inventing sources',()=>{
  assert.deepEqual(pageSources({source}),[source]);
  assert.deepEqual(pageSources({}),[]);
  assert.deepEqual(pageSources({sources:[],source}),[]);
  assert.deepEqual(pageSources({sources:[source],source:{...source,name:'obsolete'}}),[source]);
});
test('URLs, queries, duplicate entries, and trailing slash are not rewritten',()=>{
  const sources=[source,source,{...source,url:'https://fwith.co.kr/'},{...source,url:'https://fwith.co.kr'}];
  assert.deepEqual(pageSources({sources}),sources);
});
test('unsafe or malformed URLs fail closed instead of hiding a source',()=>{
  for(const url of ['http://example.org','javascript:alert(1)','data:text/html,test','//example.org','https://user:secret@example.org','https://example.org/\npath','https://example.org/a b','https://example.org\\evil','invalid']){
    assert.throws(()=>pageSources({sources:[source,{...source,url}]}));
  }
});
test('invalid reviewed metadata and non-array sources fail closed',()=>{
  for(const change of [{name:''},{type:'unverified'},{verifiedAt:''},{verifiedAt:'tomorrow'}])
    assert.throws(()=>pageSources({sources:[{...source,...change}]}));
  assert.throws(()=>pageSources({sources:{}}));
  assert.deepEqual(Object.keys(sourceTypeLabels),['official','business','facility','education','professional','reference']);
});
test('renderer uses escaped expressions, accessible source links and existing stacked cards',()=>{
  const template=fs.readFileSync(new URL('../src/pages/[category]/[slug].astro',import.meta.url),'utf8');
  const block=template.slice(template.indexOf('{sources.map'),template.indexOf('\n{!page.contentMarkdown && page.faq'));
  assert.match(block,/\{source.name\}/);assert.match(block,/href=\{source.url\}/);
  assert.match(block,/datetime=\{source.verifiedAt\}/);assert.match(block,/data-source-type=\{source.type\}/);
  assert.match(block,/aria-label=/);assert.doesNotMatch(block,/set:html|page\.source\./);
  assert.match(block,/class="source-card"/);
  assert.match(block,/출처 확인 →/);assert.doesNotMatch(block,/공식정보 확인|아래 공식 출처|시설 안내|상품과 주문 안내/);
});
