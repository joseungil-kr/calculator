import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {loadSiteProducts,readSiteCatalog,pageProductKeys,validateSiteCatalog,jpegDimensions} from '../src/lib/site-catalog.mjs';
import {regionalMetadata,validateRegionalPurchase} from '../src/lib/regions.mjs';
const root=path.resolve(new URL('..',import.meta.url).pathname),site='ansan-flower-test';
const read=name=>JSON.parse(fs.readFileSync(path.join(root,'src/data',name+'.json'),'utf8'));
const legacy=read('products'),catalog=read('site-catalog'),business=read('business-truth'),evidence=read('site-catalog-evidence');
const asset=image=>fs.readFileSync(path.join(root,'public',image));
const validate=x=>validateSiteCatalog(x,legacy,business,site,asset,evidence);
const mutate=fn=>{const c=structuredClone(catalog);fn(c);return c;};
const inactiveCatalog=()=>mutate(c=>{c.enabled=false;c.status='candidate';for(const binding of c.pageBindings)binding.status='candidate';});
function withCatalogFixture(c,check){
  const r=fs.mkdtempSync(path.join(os.tmpdir(),'ansan-catalog-'));
  try{
    fs.cpSync(path.join(root,'src/data'),path.join(r,'src/data'),{recursive:true});
    fs.cpSync(path.join(root,'public/images/products'),path.join(r,'public/images/products'),{recursive:true});
    const write=()=>fs.writeFileSync(path.join(r,'src/data/site-catalog.json'),JSON.stringify(c));
    write();check(r,write);
  }finally{fs.rmSync(r,{recursive:true,force:true});}
}
test('disabled candidates preserve the exact eight legacy products and no page cards',()=>{
  const c=inactiveCatalog();
  withCatalogFixture(c,r=>{
    assert.equal(readSiteCatalog(r,site).enabled,false);
    assert.equal(readSiteCatalog(r,site).status,'candidate');
    assert.deepEqual(loadSiteProducts(r,site),legacy);
    assert.equal(legacy.length,8);
    assert.deepEqual(pageProductKeys(r,site,'ansan-flower-launch-10'),[]);
    assert.equal(readSiteCatalog(r,site).products.length,2);
  });
});
test('reviewed production activation exposes only the approved site-local binding',()=>{
  assert.equal(catalog.enabled,true);assert.equal(catalog.status,'approved');
  assert.deepEqual(loadSiteProducts(root,site),[...legacy,...catalog.products]);
  assert.deepEqual(catalog.pageBindings,[{pageKey:'ansan-flower-launch-10',status:'approved',productKeys:['bouquet-g108']}]);
  assert.deepEqual(pageProductKeys(root,site,'ansan-flower-launch-10'),['bouquet-g108']);
  assert.deepEqual(pageProductKeys(root,site,'ansan-flower-launch-09'),[]);
});
test('fresh exact Catalog records remain global draft, with correct SKU family and sales price',()=>{assert.deepEqual(catalog.products.map(p=>[p.productKey,p.catalogRecordId,p.catalogStatus,p.price]),[['bouquet-g108','recB0zK3opxjytmBb','draft',60000],['basket-a155','recwJ9oe2fxBo2rBc','draft',65000]]);for(const p of catalog.products)assert.deepEqual(jpegDimensions(asset(p.image)),{width:500,height:500});});
for(const [name,fn] of [
 ['wrong site',c=>c.siteKey='goyang-flower-v2'],['wrong brand',c=>c.brandKey='another-brand'],['wrong truth',c=>c.truthKey='unknown'],['unregistered family',c=>c.products[0].family='orchid'],['bad category',c=>c.products[0].category='flower_basket'],['another SKU alias',c=>c.products[0].productKey='bouquet-happiness'],['unknown selected key',c=>c.pageBindings[0].productKeys=['nonexistent']],['duplicate SKU',c=>c.products.push({...c.products[0]})],['unknown price',c=>c.products[0].price=null],['zero price',c=>c.products[0].price=0],['cost mislabeled as sale',c=>c.products[0].priceKind='cost'],['wrong image hash',c=>c.products[0].imageSha256='0'.repeat(64)],['wrong image pixel dimensions',c=>c.products[0].imageWidth=501],['wrong image MIME',c=>c.products[0].imageType='image/png'],['image/key mismatch',c=>c.products[0].image=c.products[1].image],['wrong official SKU source',c=>c.products[0].sourceUrl=c.products[1].sourceUrl],['wrong official image SKU',c=>c.products[0].sourceImageUrl=c.products[1].sourceImageUrl],['item URL used as order CTA',c=>c.products[0].onlineOrderUrl=c.products[0].sourceUrl],['unsupported guaranteed availability',c=>c.products[0].availability='in_stock_guaranteed']
])for(const [mode,enabled,status] of [['disabled',false,'candidate'],['active',true,'approved']])test(`source rejects ${name} while ${mode}`,()=>assert.throws(()=>validate(mutate(c=>{c.enabled=enabled;c.status=status;fn(c);})),/Site catalog/));
test('bad actual image bytes and non-JPEG bytes fail',()=>{assert.throws(()=>validateSiteCatalog(catalog,legacy,business,site,()=>Buffer.from('not an image'),evidence),/JPEG/);assert.throws(()=>validateSiteCatalog(catalog,legacy,business,site,image=>{const b=Buffer.from(asset(image));b[b.length-8]^=1;return b;},evidence),/image bytes/);});
test('missing optional definition has exactly the old behavior',()=>{const r=fs.mkdtempSync(path.join(os.tmpdir(),'ansan-catalog-'));fs.mkdirSync(path.join(r,'src/data'),{recursive:true});fs.writeFileSync(path.join(r,'src/data/products.json'),JSON.stringify(legacy));assert.deepEqual(loadSiteProducts(r,'unrelated-city'),legacy);assert.deepEqual(pageProductKeys(r,'unrelated-city','any'),[]);fs.rmSync(r,{recursive:true,force:true});});
test('catalog activation and individual page approval are independent gates',()=>{
  const c=inactiveCatalog();c.enabled=true;c.status='approved';
  withCatalogFixture(c,(r,write)=>{
    assert.deepEqual(loadSiteProducts(r,site),[...legacy,...catalog.products]);
    assert.deepEqual(pageProductKeys(r,site,'ansan-flower-launch-10'),[]);
    c.pageBindings[0].status='approved';write();
    assert.deepEqual(pageProductKeys(r,site,'ansan-flower-launch-10'),['bouquet-g108']);
    assert.deepEqual(pageProductKeys(r,site,'ansan-flower-launch-09'),[]);
    c.enabled=false;write();
    assert.deepEqual(loadSiteProducts(r,site),legacy);
    assert.deepEqual(pageProductKeys(r,site,'ansan-flower-launch-10'),[]);
  });
});
test('regional family gate sees gifts only through the activated site-scoped loader',()=>{const c=read('region-coverage'),p=read('region-policy'),key='ansan-flower-test-region-sangnok-sa';assert.throws(()=>regionalMetadata(c,p,legacy,key),/reviewed binding/);p.visualBindings[0].status='approved';assert.throws(()=>regionalMetadata(c,p,legacy,key),/exact catalog/);const products=[...legacy,...catalog.products],row={pageKey:key,pageType:'regional-service',...regionalMetadata(c,p,products,key)};assert.deepEqual(row.regionalProductFamilies,['bouquet','basket']);validateRegionalPurchase(row,products,'꽃다발과 꽃바구니를 선택하고 주문합니다.');assert.throws(()=>validateRegionalPurchase(row,products,'근조화환을 주문합니다.'),/missing promised family/);});

for(const [name,fn] of [['wrong positive sale price',c=>c.products[0].price=1],['invented name',c=>c.products[0].name='없는 상품'],['substituted Catalog record',c=>c.products[0].catalogRecordId='recAAAAAAAAAAAAAA']])test(`exact verified tuple rejects ${name}`,()=>assert.throws(()=>validate(mutate(fn)),/tuple drift/));
test('enabled alone cannot publish an unreviewed candidate catalog on home',()=>{
  const c=inactiveCatalog();c.enabled=true;
  assert.throws(()=>validate(c),/requires reviewed source/);
  c.status='approved';assert.doesNotThrow(()=>validate(c));
});
test('same-brand tuple is not authorization for another city, even with caller changed',()=>{const c=mutate(c=>{c.siteKey='goyang-flower-v2';c.enabled=true;c.status='approved';});assert.throws(()=>validateSiteCatalog(c,legacy,business,'goyang-flower-v2',asset,{...evidence,siteKey:'goyang-flower-v2'}),/site-local scope/);});
test('missing or duplicate source evidence cannot be replaced by presentation fields',()=>{assert.throws(()=>validateSiteCatalog(catalog,legacy,business,site,asset,null),/evidence/);assert.throws(()=>validateSiteCatalog(catalog,legacy,business,site,asset,{...evidence,products:[...evidence.products,evidence.products[0]]}),/duplicate evidence/);});

for(const value of [true,false,'1'])test(`schema version rejects ${JSON.stringify(value)} in definition and proof`,()=>{assert.throws(()=>validate(mutate(c=>c.schemaVersion=value)),/Site catalog/);assert.throws(()=>validateSiteCatalog(catalog,legacy,business,site,asset,{...evidence,schemaVersion:value}),/evidence/);});
test('JSON numeric schema 1.0 has the same semantics as 1',()=>assert.doesNotThrow(()=>validateSiteCatalog({...catalog,schemaVersion:1.0},legacy,business,site,asset,{...evidence,schemaVersion:1.0})));
