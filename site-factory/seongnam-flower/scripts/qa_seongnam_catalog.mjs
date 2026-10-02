import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {homeProducts, productFamilies} from '../src/lib/catalog.mjs';
import {hubGuides, hubGuide, hubProducts} from '../src/lib/hubs.mjs';
const read=name=>JSON.parse(fs.readFileSync(`src/data/${name}.json`,'utf8'));
const products=read('products'),proof=read('catalog-provenance'),pages=read('pages');
const sourceBytes=fs.readFileSync('src/data/catalog-source-evidence.json');
assert.equal(crypto.createHash('sha256').update(sourceBytes).digest('hex'),proof.sourceEvidenceSha256);
const evidence=JSON.parse(sourceBytes);
assert.equal(evidence.total_records,8);
assert.equal(proof.siteKey,'seongnam-flower-v2');
assert.equal(proof.launchKey,'seongnam-flower-v2-trial-20261002');
assert.equal(products.length,8);
assert.equal(new Set(products.map(p=>p.key)).size,8);
assert.equal(new Set(products.map(p=>p.officialSku)).size,8);
assert.deepEqual(Object.fromEntries(['funeral','congrats'].map(f=>[f,products.filter(p=>p.family===f).length])),{funeral:4,congrats:4});
assert.deepEqual(products.map(p=>p.officialSku),['B201','B203','B205','B060','C200','C203','C204','C205']);
for (const p of products) {
 const source=proof.products.find(x=>x.key===p.key);
 assert.ok(source);
 const record=evidence.products.find(x=>x.product_key===p.key);
 assert.ok(record);assert.equal(record.airtable_record_id,source.airtableRecordId);
 assert.equal(record.official_observed.sku,p.officialSku);
 assert.equal(record.official_observed.product_name,p.name);
 assert.equal(record.official_observed.price_krw,p.price);
 assert.equal(record.official_observed.detail_url,p.sourceUrl);
 assert.equal(record.official_observed.detail_image_url,p.sourceImageUrl);
 assert.equal(p.orderUrl,'https://fwith.co.kr');
 assert.equal(p.officialSku,source.officialSku);
 assert.equal(p.name,source.name);assert.equal(p.price,source.price);
 assert.equal(p.sourceUrl,source.detailEvidenceUrl);
 assert.equal(p.img,source.image.path);assert.equal(p.sourceImageUrl,source.image.url);
 assert.ok(p.img.startsWith('/images/products/seongnam-official-20261002/'));
 assert.equal(crypto.createHash('sha256').update(fs.readFileSync(`public${p.img}`)).digest('hex'),source.image.sha256);
}
assert.deepEqual([...new Set(homeProducts(products).map(p=>p.family))].sort(),['congrats','funeral']);
for (const category of new Set(pages.map(p=>p.category))) {
 assert.ok(hubGuides[category]);hubProducts(category,products,3,pages);
 const guide=hubGuide(category,pages);
 if (category==='event' && guide.families.length===1 && guide.families[0]==='congrats') {
  const basic=products.find(p=>p.key==='congrats-basic');
  assert.ok(basic && guide.intro.includes(`${basic.price.toLocaleString('en-US')}원`),'Event hub base-price promise drift');
 }
}
for (const page of pages) {
 const expected=productFamilies(page);
 assert.ok(expected.length,`Unmapped page intent: ${page.pageKey}`);
 for (const f of expected) assert.ok(products.some(p=>p.family===f),`Missing promised product family ${f}: ${page.pageKey}`);
}
const home=fs.readFileSync('src/pages/index.astro','utf8');
assert.ok(!/꽃다발|꽃바구니|졸업|병문안/.test(home),'Home promises unavailable snapshot family');
assert.equal(read('business-truth').onlineOrderUrl,'https://fwith.co.kr');
assert.equal(read('site-config').productionApproved,false);
console.log(`SEONGNAM CATALOG QA PASSED: 8 official SKUs, 8 hashed images, home CTA, ${pages.length} existing detail promises`);
