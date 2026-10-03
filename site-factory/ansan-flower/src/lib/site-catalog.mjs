import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const fail=message=>{throw new Error(`Site catalog: ${message}`);};
const read=file=>JSON.parse(fs.readFileSync(file,'utf8'));
const digest=bytes=>crypto.createHash('sha256').update(bytes).digest('hex');
const unique=(values,label)=>{if(new Set(values).size!==values.length)fail(`duplicate ${label}`);};

export function jpegDimensions(bytes) {
  if(bytes[0]!==0xff||bytes[1]!==0xd8)fail('image MIME is not JPEG');
  let i=2;
  while(i+4<=bytes.length){
    if(bytes[i++]!==0xff)fail('invalid JPEG marker');
    while(bytes[i]===0xff)i++;
    const marker=bytes[i++];
    if(marker===0xd9||marker===0xda)break;
    if(marker===0x01||(marker>=0xd0&&marker<=0xd7))continue;
    const length=bytes.readUInt16BE(i);
    if(length<2||i+length>bytes.length)fail('invalid JPEG segment');
    if([0xc0,0xc1,0xc2,0xc3,0xc5,0xc6,0xc7,0xc9,0xca,0xcb,0xcd,0xce,0xcf].includes(marker)){
      if(length<8)fail('invalid JPEG frame');
      return {width:bytes.readUInt16BE(i+5),height:bytes.readUInt16BE(i+3)};
    }
    i+=length;
  }
  fail('JPEG dimensions missing');
}

/** Source-local opt-in. Global Airtable status never acts as site activation. */
export function validateSiteCatalog(catalog,legacy,business,siteKey,readAsset,evidence) {
  if(siteKey!=='ansan-flower-test'||catalog?.siteKey!=='ansan-flower-test')fail('unsupported site-local scope');
  if(!['candidate','approved'].includes(catalog.status)||(catalog.enabled&&catalog.status!=='approved'))fail('catalog activation requires reviewed source');
  if(evidence?.schemaVersion!==1||evidence.siteKey!=='ansan-flower-test'||evidence.brandKey!==business.brandKey||evidence.truthKey!==business.truthKey||evidence.sourceLevel!=='official_business_source'||!evidence.verifiedAt||evidence.catalogBaseId!=='appOthiezu3SqH2Nu'||evidence.catalogTableId!=='tbl7qSHi0lTDjPE5A'||!Array.isArray(evidence.products))fail('missing site-scoped catalog evidence');
  if(catalog?.schemaVersion!==1||catalog.siteKey!==siteKey||catalog.brandKey!==business.brandKey||catalog.truthKey!==business.truthKey||typeof catalog.enabled!=='boolean')fail('site/brand/truth mismatch');
  if(!Array.isArray(catalog.products)||!Array.isArray(catalog.pageBindings))fail('missing products/bindings');
  unique(catalog.products.map(p=>p.productKey),'product key');
  unique(evidence.products.map(p=>p.productKey),'evidence product key');
  unique(catalog.products.map(p=>p.sku),'SKU');
  unique(catalog.products.map(p=>p.catalogRecordId),'Catalog record');
  unique(catalog.pageBindings.map(p=>p.pageKey),'page binding');
  const legacyKeys=new Set(legacy.map(p=>p.productKey||p.key));
  for(const p of catalog.products){
    const verified=evidence.products.find(row=>row.productKey===p.productKey);
    if(!verified||Object.keys(verified).length!==Object.keys(p).length||Object.keys(verified).some(field=>JSON.stringify(verified[field])!==JSON.stringify(p[field])))fail('verified product tuple drift');
    const expectedFamily={flower_bouquet:'bouquet',flower_basket:'basket'}[p.category];
    if(!expectedFamily||p.family!==expectedFamily)fail('unsupported product family');
    if(!/^[GA][0-9]{3}$/.test(p.sku||'')||p.productKey!==`${p.family}-${p.sku.toLowerCase()}`||legacyKeys.has(p.productKey))fail('exact product key/SKU mismatch');
    if((p.family==='bouquet'&&!p.sku.startsWith('G'))||(p.family==='basket'&&!p.sku.startsWith('A')))fail('SKU family mismatch');
    if(!/^rec[A-Za-z0-9]{14}$/.test(p.catalogRecordId||'')||!['draft','active'].includes(p.catalogStatus)||p.brandKey!==business.brandKey)fail('Catalog identity mismatch');
    if(typeof p.name!=='string'||!p.name.trim()||!Number.isSafeInteger(p.price)||p.price<=0||p.priceKind!=='public_sale'||p.currency!=='KRW'||!p.priceNotice)fail('unknown or invalid public sale price');
    if(p.sourceUrl!==`https://fwith.co.kr/shop/item.php?it_id=${p.sku}`||p.sourceImageUrl!==`https://fwith.co.kr/data/item/flower379/${p.sku}/thumb-1_500x500.jpg`||p.onlineOrderUrl!==business.onlineOrderUrl)fail('official source/CTA identity mismatch');
    if(p.sourceLevel!=='official_business_source'||p.assetType!=='real_product'||!p.imageAlt||!/^\d{4}-\d{2}-\d{2}T/.test(p.verifiedAt||'')||p.availability!=='public_listing_orderable_stock_unconfirmed')fail('missing source/availability qualification');
    if(p.image!==`/images/products/${p.productKey}.jpg`||p.imageType!=='image/jpeg'||!Number.isSafeInteger(p.imageWidth)||!Number.isSafeInteger(p.imageHeight)||Math.min(p.imageWidth,p.imageHeight)<1||!/^[a-f0-9]{64}$/.test(p.imageSha256||''))fail('invalid local image binding');
    const bytes=readAsset(p.image),dimensions=jpegDimensions(bytes);
    if(digest(bytes)!==p.imageSha256||dimensions.width!==p.imageWidth||dimensions.height!==p.imageHeight)fail('image bytes/dimensions mismatch');
  }
  const allKeys=new Set([...legacyKeys,...catalog.products.map(p=>p.productKey)]);
  for(const binding of catalog.pageBindings){
    if(!/^[a-zA-Z0-9_-]+$/.test(binding.pageKey||'')||!['candidate','approved'].includes(binding.status)||!Array.isArray(binding.productKeys)||!binding.productKeys.length)fail('invalid page selection');
    unique(binding.productKeys,'page product key');
    if(binding.productKeys.some(key=>!allKeys.has(key)))fail('unknown selected product key');
  }
  return catalog;
}

export function readSiteCatalog(root,siteKey) {
  const file=path.join(root,'src/data/site-catalog.json');
  if(!fs.existsSync(file))return null;
  const base=fs.realpathSync(path.join(root,'public'));
  return validateSiteCatalog(read(file),read(path.join(root,'src/data/products.json')),read(path.join(root,'src/data/business-truth.json')),siteKey,image=>{
    const file=fs.realpathSync(path.join(base,image.slice(1)));
    if(!file.startsWith(base+path.sep))fail('image escapes site root');
    return fs.readFileSync(file);
  },read(path.join(root,'src/data/site-catalog-evidence.json')));
}

export function loadSiteProducts(root,siteKey) {
  const legacy=read(path.join(root,'src/data/products.json')),catalog=readSiteCatalog(root,siteKey);
  return catalog?.enabled ? [...legacy,...catalog.products] : legacy;
}

export function pageProductKeys(root,siteKey,pageKey) {
  const catalog=readSiteCatalog(root,siteKey);
  if(!catalog?.enabled)return [];
  const binding=catalog.pageBindings.find(p=>p.pageKey===pageKey);
  return binding?.status==='approved' ? binding.productKeys : [];
}
