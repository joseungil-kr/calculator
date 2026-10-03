import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {productSocialImage} from '../src/lib/social-image.mjs';
const read=name=>JSON.parse(fs.readFileSync(new URL('../src/data/'+name,import.meta.url)));
const products=read('products.json'),proof=read('social-image-provenance.json');
test('every existing official product keeps its verified file bytes and social metadata',()=>{
  const before=JSON.stringify({products,proof});
  for(const product of products) {
    const image=productSocialImage(product,proof,'https://goyang.fwith.kr','꽃이랑');
    const record=proof.products.find(row=>row.key===product.key);
    assert.equal(image.url,'https://goyang.fwith.kr'+product.img);
    assert.equal(image.alt,'꽃이랑 '+product.name);
    assert.deepEqual([image.width,image.height],record.image.dimensions);
    assert.equal(image.type,record.image.type);
    assert.equal(crypto.createHash('sha256').update(fs.readFileSync(new URL('../public'+product.img,import.meta.url))).digest('hex'),record.image.sha256);
  }
  assert.equal(JSON.stringify({products,proof}),before);
});
test('unverified renamed remote or missing social products and unsafe origins fail',()=>{
  const product=products[0];
  for(const bad of [undefined,{...product,key:'unknown'},{...product,assetType:'ai_editorial'},
    {...product,sourceLevel:'unknown'},{...product,name:'Other'},{...product,sourceUrl:'https://other.example'},
    {...product,img:'https://other.example/image.jpg'},{...product,img:'/missing.jpg'}])
    assert.throws(()=>productSocialImage(bad,proof,'https://goyang.fwith.kr','꽃이랑'));
  for(const origin of ['http://goyang.fwith.kr','https://user:password@goyang.fwith.kr','https://goyang.fwith.kr/path','https://goyang.fwith.kr/?query=1'])
    assert.throws(()=>productSocialImage(product,proof,origin,'꽃이랑'));
  for(const change of [p=>p.products.push(p.products[0]),p=>p.products[0].image.dimensions=[-1,480],
    p=>p.products[0].image.type='image/png',p=>p.products[0].image.sha256='missing']) {
    const bad=structuredClone(proof);change(bad);assert.throws(()=>productSocialImage(product,bad,'https://goyang.fwith.kr','꽃이랑'));
  }
});
test('home hub and detail layouts supply a verified product while 404 opts out',()=>{
  for(const name of ['index.astro','[category]/index.astro','[category]/[slug].astro'])
    assert.match(fs.readFileSync(new URL('../src/pages/'+name,import.meta.url),'utf8'),/socialProduct=\{/);
  assert.match(fs.readFileSync(new URL('../src/layouts/BaseLayout.astro',import.meta.url),'utf8'),/socialImage=is404 \? null/);
});
