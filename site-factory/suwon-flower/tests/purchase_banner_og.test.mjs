import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {socialImageFor} from '../src/lib/social-image.mjs';
const pages=JSON.parse(fs.readFileSync('src/data/pages.json','utf8'));
const architecture=JSON.parse(fs.readFileSync('src/data/architecture.json','utf8'));
const routes=['/',...architecture.hubs.filter(h=>pages.some(p=>p.category===h.category)).map(h=>h.url),...pages.map(p=>p.url)];
test('all registered content routes have one middle purchase panel and verified social image',()=>{
  assert.equal(new Set(routes).size,routes.length);
  for(const route of routes){
    const html=fs.readFileSync(`dist${route}index.html`,'utf8');
    assert.equal((html.match(/data-purchase-banner="middle"/g)||[]).length,1,route);
    const panel=html.split('data-purchase-banner="middle"')[1].split('</aside>')[0];
    assert.match(panel,/href="tel:18440644"/);
    assert.match(panel,/href="https:\/\/fwith\.co\.kr"/);
    assert.doesNotMatch(panel,/<img\b/);
    const og=[...html.matchAll(/property="og:image" content="([^"]+)"/g)];assert.equal(og.length,1);
    assert.ok(og[0][1].startsWith('https://suwon.fwith.kr/images/products/'));
    const path=og[0][1].replace('https://suwon.fwith.kr','');const meta=socialImageFor({img:path});assert.equal(meta.path,path);
    for(const [key,value] of [['width',meta.width],['height',meta.height],['type',meta.type]])assert.ok(html.includes(`property="og:image:${key}" content="${value}"`));
    assert.ok(fs.existsSync(`public${path}`));
    assert.equal((html.match(/<h1(?:\s|>)/g)||[]).length,1);
    assert.ok(html.includes(`rel="canonical" href="https://suwon.fwith.kr${route}"`));
  }
});
test('an unknown catalog reference falls back to a verified existing product asset',()=>{
 for(const img of ['https://untrusted.invalid/x.jpg','constructor','toString','__proto__']) {
  assert.equal(socialImageFor({img}).path,'/images/products/bouquet-happiness.jpg',img);
 }
 assert.equal(socialImageFor().path,'/images/products/bouquet-happiness.jpg');
});
