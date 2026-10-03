import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import {productSocialImage} from '../src/lib/social-image.mjs';
const products=JSON.parse(fs.readFileSync(new URL('../src/data/products.json',import.meta.url)));
const provenance=JSON.parse(fs.readFileSync(new URL('../src/data/social-image-provenance.json',import.meta.url)));
test('every source-pinned product maps to its real unchanged image bytes and generic origin',()=>{
  for(const product of products){
    const image=productSocialImage(product,provenance,'https://example.invalid','검증 브랜드');
    const proof=provenance.products.find(row=>row.key===product.key);
    const bytes=fs.readFileSync(new URL('../public'+product.img,import.meta.url));
    assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),proof.image.sha256);
    assert.equal(image.url,'https://example.invalid'+product.img);
    assert.equal(image.alt,'검증 브랜드 '+product.name);
    assert.ok(image.width>0&&image.height>0);
    assert.ok(image.type.startsWith('image/'));
  }
});
test('different region/brand uses same verified photo without inventing a local image',()=>{
  const image=productSocialImage(products[0],provenance,'https://bucheon.example.invalid','다른 브랜드');
  assert.equal(image.alt,'다른 브랜드 '+products[0].name);
  assert.match(image.url,/^https:\/\/bucheon\.example\.invalid\//);
});
test('unverified product, changed SKU binding, external image and invalid origin fail closed',()=>{
  for(const change of [{assetType:'editorial_illustration'},{sourceLevel:'unknown'},{name:'다른 상품'},
      {sourceUrl:'https://other.invalid/product'},{orderUrl:'https://other.invalid/buy'},
      {img:'https://other.invalid/photo.jpg'},{img:'/images/products/../other.jpg'},{key:'unknown'}])
    assert.throws(()=>productSocialImage({...products[0],...change},provenance,'https://example.invalid','브랜드'));
  for(const origin of ['http://example.invalid','https://user:password@example.invalid'])
    assert.throws(()=>productSocialImage(products[0],provenance,origin,'브랜드'));
  const broken=structuredClone(provenance);broken.products[0].image.dimensions=[0,500];
  assert.throws(()=>productSocialImage(products[0],broken,'https://example.invalid','브랜드'));
});
