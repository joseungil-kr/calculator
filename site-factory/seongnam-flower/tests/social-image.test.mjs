import assert from 'node:assert/strict';
import test from 'node:test';
import fs from 'node:fs';
import {spawnSync} from 'node:child_process';
import {productSocialImage} from '../src/lib/social-image.mjs';
const products=JSON.parse(fs.readFileSync(new URL('../src/data/products.json',import.meta.url)));
const proof=JSON.parse(fs.readFileSync(new URL('../src/data/catalog-provenance.json',import.meta.url)));
test('verified product images use the canonical HTTPS origin and exact provenance dimensions',()=>{
  const before=JSON.stringify({products,proof});
  for(const origin of ['https://seongnam.fwith.kr','https://seongnam-flower-guide-qa.joseungil.workers.dev'])for(const p of products){
    const image=productSocialImage(p,proof,origin,'꽃이랑');
    assert.equal(image.url,origin+p.img);assert.equal(image.alt,`꽃이랑 ${p.name}`);
    assert.equal(image.type,'image/jpeg');assert.deepEqual([image.width,image.height],[500,500]);
  }
  assert.equal(JSON.stringify({products,proof}),before);
});
test('unverified, renamed, remote and missing products fail instead of publishing invented image metadata',()=>{
  const p=products[0];
  for(const bad of [undefined,{...p,key:'unknown'},{...p,assetType:'ai_editorial'},{...p,sourceLevel:'unknown'},{...p,name:'다른 상품'},{...p,img:'https://elsewhere.example/image.jpg'},{...p,img:'/missing.jpg'}]){
    assert.throws(()=>productSocialImage(bad,proof,'https://seongnam.fwith.kr','꽃이랑'));
  }
  for(const origin of ['http://seongnam.fwith.kr','https://user:password@seongnam.fwith.kr'])assert.throws(()=>productSocialImage(p,proof,origin,'꽃이랑'));
});
test('all three page types provide a real product, and only home/hub gain an additional banner call',()=>{
  for(const path of ['src/pages/index.astro','src/pages/[category]/index.astro','src/pages/[category]/[slug].astro']){
    const text=fs.readFileSync(new URL('../'+path,import.meta.url),'utf8');assert.match(text,/socialProduct=\{/);
    if(!path.endsWith('[slug].astro'))assert.equal((text.match(/<InlineOrderBanner\/>/g)||[]).length,1);
  }
});
test('rendered social metadata gate rejects missing, duplicate and unsafe output',()=>{
  const r=spawnSync('python3',['tests/social_static_test.py'],{cwd:new URL('..',import.meta.url),encoding:'utf8'});
  assert.equal(r.status,0,r.stdout+r.stderr);
});
