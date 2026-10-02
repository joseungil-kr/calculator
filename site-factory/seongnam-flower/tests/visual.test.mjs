import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {detailIllustration} from '../src/lib/visual.mjs';
import {selectProducts} from '../src/lib/catalog.mjs';

const read = name => JSON.parse(fs.readFileSync(new URL(`../src/data/${name}.json`, import.meta.url)));
const editorial = read('editorial-assets');
const products = read('products');
const opening = {pageType:'business-opening',category:'business',primaryKeyword:'성남 개업화환',visualIntent:'congrats_wreath',assetSlot:'REAL_PROOF'};

test('rendered REAL_PROOF and editorial gates retain positive and negative coverage', () => {
  execFileSync('python3',[new URL('./visual_static_test.py',import.meta.url).pathname],{stdio:'pipe'});
});

test('opening REAL_PROOF selects official congratulatory products, never editorial art', () => {
  assert.equal(detailIllustration(opening, editorial), null);
  const selected = selectProducts(opening, products);
  assert.deepEqual(selected.map(p => [p.officialSku,p.price]), [['C200',59000],['C203',79000],['C204',99000]]);
  assert.ok(selected.every(p => p.assetType === 'real_product' && p.family === 'congrats'));
});
test('REAL_PROOF also wins over the legacy event_wreath illustration trigger', () => {
  assert.equal(detailIllustration({...opening,pageType:'event-venue',visualIntent:'event_wreath'},editorial),null);
});
test('dedicated actual-wreath intent is not overridden when a legacy record lacks a slot', () => {
  assert.equal(detailIllustration({...opening,assetSlot:undefined},editorial),null);
});
test('existing approved funeral canary still uses its official product hero', () => {
  const page=read('pages').find(p => p.pageKey === 'seongnam-snuh-funeral-wreath');
  assert.ok(page);
  assert.equal(detailIllustration(page,editorial),null);
  assert.equal(selectProducts(page,products)[0].officialSku,'B201');
});
test('legacy explanation-only illustration retains its explicit AI caption', () => {
  const asset=detailIllustration({pageType:'business-opening'},editorial);
  assert.equal(asset.assetType,'editorial_illustration');
  assert.match(asset.caption,/AI 일러스트/);
});
test('square editorial art cannot silently satisfy wide or split asset slots', () => {
  for (const assetSlot of ['HERO_WIDE','SPLIT_VISUAL','CONTENT_IMAGE','CTA_BANNER','CARD_THUMBNAIL'])
    assert.throws(() => detailIllustration({...opening,assetSlot},editorial),/No compatible opening illustration/);
});
test('actual renderer uses the visual resolver and keeps the non-cropping product CSS', () => {
  const template=fs.readFileSync(new URL('../src/pages/[category]/[slug].astro',import.meta.url),'utf8');
  assert.match(template,/const illustration=detailIllustration\(page,editorial\)/);
  const css=fs.readFileSync(new URL('../src/styles/global.css',import.meta.url),'utf8');
  assert.match(css,/\.hero-products img,\.detail-product img,\.product-card img\{object-fit:contain/);
});
