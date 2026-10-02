import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {homeProducts,selectProducts} from '../src/lib/catalog.mjs';
import {hubProducts} from '../src/lib/hubs.mjs';
const products=JSON.parse(fs.readFileSync(new URL('../src/data/products.json',import.meta.url),'utf8'));
test('verified eight-product snapshot and provenance pass strict gate',()=>execFileSync('node',['scripts/qa_seongnam_catalog.mjs']));
test('home is limited to verified wreath families',()=>assert.deepEqual([...new Set(homeProducts(products).map(p=>p.family))].sort(),['congrats','funeral']));
test('unavailable bouquet intent never falls back to wreaths',()=>assert.deepEqual(selectProducts({pageType:'school-event'},products),[]));
test('unsupported hubs fail closed before activation',()=>{
 for (const category of ['school','event','gift']) assert.throws(()=>hubProducts(category,products),/missing hub family/);
});
test('funeral, business and order hubs only use verified products',()=>{
 for (const category of ['funeral','business','order']) {
  const selected=hubProducts(category,products);assert.ok(selected.length);assert.ok(selected.every(p=>products.includes(p)));
 }
});
const {mkdtempSync,cpSync,readFileSync,writeFileSync}=fs;
function rejectsMutation(edit) {
 const temp=mkdtempSync('/tmp/seongnam-catalog-negative-');
 for(const path of ['src','scripts','public']) cpSync(path,`${temp}/${path}`,{recursive:true});
 const file=`${temp}/src/data/products.json`,rows=JSON.parse(readFileSync(file,'utf8'));
 edit(rows);writeFileSync(file,JSON.stringify(rows));
 assert.throws(()=>execFileSync('node',['scripts/qa_seongnam_catalog.mjs'],{cwd:temp,stdio:'pipe'}));
}
test('missing record fails rather than falling back to template catalog',()=>rejectsMutation(rows=>rows.pop()));
test('product-detail order CTA is rejected',()=>rejectsMutation(rows=>{rows[0].orderUrl=rows[0].sourceUrl;}));
test('legacy unverified image cannot replace pinned official image',()=>rejectsMutation(rows=>{rows[0].img='/images/products/funeral-basic.webp';}));
