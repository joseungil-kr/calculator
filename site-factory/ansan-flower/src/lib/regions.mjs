/** Explicit data adapter. Geographic inventory is not permission to publish. */
const fail = reason => { throw new Error(`Regional service: ${reason}`); };
const unique=(items,key)=>{const values=items.map(x=>x[key]);if(values.some(x=>!x)||new Set(values).size!==values.length)fail(`duplicate/missing ${key}`);};
const pathSafe=url=>/^\/[a-z0-9-]+\/[a-z0-9-]+\/$/.test(url);
const official=(value,hosts)=>{try{const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password&&hosts.includes(u.hostname);}catch{return false;}};
export const isRegional = page => page.category==='regions'||page.pageType==='regional-service';
export function validateDefinition(coverage,policy) {
 if(coverage?.schemaVersion!==2||policy?.schemaVersion!==1||coverage.siteKey!==policy.siteKey||coverage.scopeKey!==policy.scopeKey||!policy.scopeKey)fail('site/scope opt-in mismatch');
 if(coverage.unitBasis!=='legal-dong-plus-eup-myeon'||coverage.countIsPageQuota!==false)fail('unsupported unit basis or quota');
 if(!Array.isArray(policy.officialHosts)||!policy.officialHosts.length||!Array.isArray(policy.unitTypes)||!policy.unitTypes.length)fail('missing trusted policy');
 if(!/^\d{4}-\d{2}-\d{2}$/.test(coverage.verifiedAt||'')||!coverage.sourceBasisDate||!coverage.officialSourceUrls?.length)fail('missing provenance');
 if(coverage.officialSourceUrls.some(url=>!official(url,policy.officialHosts)))fail('untrusted official source');
 for(const field of ['districts','units','administrativeCrosswalk','representatives'])if(!Array.isArray(coverage[field]))fail(`missing ${field}`);
 unique(coverage.districts,'key');unique(coverage.units,'unitKey');unique(coverage.administrativeCrosswalk,'aliasKey');
 const districts=new Set(coverage.districts.map(x=>x.key));const units=new Map(coverage.units.map(x=>[x.unitKey,x]));
 for(const d of coverage.districts)if(!/^[a-z][a-z0-9-]*$/.test(d.key)||!d.name||!coverage.officialSourceUrls.includes(d.sourceUrl))fail('district source mismatch');
 for(const u of coverage.units)if(!u.name||!policy.unitTypes.includes(u.unitType)||!u.districtKeys?.length||new Set(u.districtKeys).size!==u.districtKeys.length||u.districtKeys.some(x=>!districts.has(x))||!Array.isArray(u.legalRi))fail(`invalid unit ${u.unitKey}`);
 for(const a of coverage.administrativeCrosswalk){
  if(!a.name||!districts.has(a.districtKey)||!Array.isArray(a.relations))fail('invalid administrative alias');
  if(!a.relations.length&&!a.unresolvedCandidateNames?.length)fail('empty alias requires explicit unresolved evidence');
  unique(a.relations,'unitKey');
  for(const rel of a.relations)if(!units.has(rel.unitKey)||!units.get(rel.unitKey).districtKeys.includes(a.districtKey)||!['whole','partial','name-only','historical'].includes(rel.scope))fail(`invalid alias relation ${a.aliasKey}`);
 }
 for(const key of ['pageKey','url','intentKey','primaryKeyword'])unique(coverage.representatives,key);
 const assigned=new Set();
 for(const r of coverage.representatives){
  if(!pathSafe(r.url)||!r.primaryKeyword||!r.queryEvidence||!r.unitKeys?.length||!['regional','existing'].includes(r.routeMode)||!['candidate','approved','reserved'].includes(r.status))fail('invalid representative');
  if(r.routeMode==='regional'&&r.url!==`/regions/${r.slug}/`)fail('regional canonical mismatch');
  for(const key of r.unitKeys){if(!units.has(key)||assigned.has(key))fail('duplicate/unknown canonical unit');assigned.add(key);}
 }
 return coverage;
}
export function regionalRows(pages,architecture,coverage,policy) {
 validateDefinition(coverage,policy);
 const rows=pages.filter(isRegional);
 if(rows.length&&architecture.siteKey!==coverage.siteKey)fail('architecture site mismatch');
 if(rows.length&&policy.enabled!==true)fail('region scope is disabled');
 unique(rows,'pageKey');unique(rows,'url');
 for(const p of rows){
  const r=coverage.representatives.find(r=>r.pageKey===p.pageKey);
  const n=architecture.pages.find(n=>n.pageKey===p.pageKey);
  if(!r||r.status!=='approved'||r.routeMode!=='regional'||p.category!=='regions'||p.pageType!=='regional-service'||p.routeType!=='category'||p.url!==r.url||p.slug!==r.slug||p.scopeKey!==policy.scopeKey||p.status!=='approved'||p.approvalVerified!==true||!p.snapshotId||!p.snapshotHash)fail(`route/approval mismatch ${p.pageKey}`);
  if(n?.url!==p.url||n?.pageRole!=='REGION_SERVICE_LANDING'||n.parentHub!=='/regions/'||n.localizationPolicy!=='local-required'||n.intentKey!==r.intentKey||n.scopeKey!==policy.scopeKey)fail(`semantic mismatch ${p.pageKey}`);
 }
 return rows;
}
export function directoryGroups(pages,architecture,coverage,policy) {
 const rows=regionalRows(pages,architecture,coverage,policy);if(policy.enabled!==true)return [];
 const published=new Map(rows.map(p=>[p.pageKey,p]));
 const representatives=coverage.representatives.filter(r=>r.status==='approved'&&published.has(r.pageKey));
 return coverage.districts.map(d=>({...d,items:representatives.filter(r=>r.unitKeys.some(key=>coverage.units.find(u=>u.unitKey===key).districtKeys.includes(d.key))).map(r=>({representative:r,page:published.get(r.pageKey),aliases:coverage.administrativeCrosswalk.filter(a=>a.districtKey===d.key&&a.relations.some(rel=>r.unitKeys.includes(rel.unitKey))).map(a=>({name:a.name,scope:a.relations.find(rel=>r.unitKeys.includes(rel.unitKey)).scope}))}))})).filter(d=>d.items.length);
}
export function aliasTargets(name,pages,architecture,coverage,policy) {
 const groups=directoryGroups(pages,architecture,coverage,policy);return [...new Set(groups.flatMap(d=>d.items).filter(x=>x.aliases.some(a=>a.name===name)||x.representative.unitKeys.some(k=>(coverage.units.find(u=>u.unitKey===k).name===name||coverage.units.find(u=>u.unitKey===k).legalRi.includes(name)))).map(x=>x.page.url))];
}
export function hubState(count,siteIndexable=false){if(!Number.isInteger(count)||count<0)fail('invalid hub count');return {exists:count>0,indexable:siteIndexable&&count>=3,menu:count>=5,sitemap:siteIndexable&&count>=3};}

export function validateRegionalPurchase(page,products,text='') {
 if(!isRegional(page))return;
 const mode=page.regionalPurchaseMode,keys=page.regionalProductKeys,families=page.regionalProductFamilies;
 if(!['catalog','consultation-only'].includes(mode)||!Array.isArray(keys)||!Array.isArray(families))fail('missing purchase contract');
 if(mode==='consultation-only'&&(keys.length||families.length))fail('consultation-only has product promises');
 if(mode==='catalog'&&!keys.length)fail('missing product mapping');
 const mapping={funeral_wreath:'funeral',congrats_wreath:'congrats',flower_bouquet:'bouquet',flower_basket:'basket'};
 const actual=keys.map(key=>{const product=products.find(p=>(p.key||p.productKey)===key);if(!product?.sourceUrl)fail('unverified product key');return product.family||mapping[product.category];});
 if(new Set(actual).size!==families.length||families.some(f=>!actual.includes(f)))fail('product family binding mismatch');
 const claims=regionalCustomerClaims(text);
 for(const family of claims.families)if(!families.includes(family))fail('missing promised family '+family);
 if(mode==='consultation-only'&&claims.priceOrDelivery)fail('consultation-only price/delivery promise');
}

/** Common explicit claims only; independent content/source review remains mandatory. */
export function regionalCustomerClaims(text) {
 const compact=text.normalize('NFKC').replace(/[\s\u200b-\u200d\ufeff]+/g,'');
 const terms={bouquet:/꽃다발|부케/,basket:/꽃바구니/,funeral:/(?:근조|장례)(?:[0-9]+단)?화환|근조[·/ㆍ]축하화환/,congrats:/(?:축하|개업)(?:[0-9]+단)?화환/};
 const families=Object.entries(terms).filter(([,pattern])=>pattern.test(compact)).map(([family])=>family);
 const price=/(?:[0-9]+(?:[.,][0-9]+)*|[일이삼사오육칠팔구십백천만억]+)(?:[십백천만억]+)?원|(?:₩|KRW)[0-9]/i.test(compact);
 const negative=/^(?:을|를|이|가|은|는)?(?:하지않|하지못|할수없|되지않|되는것(?:이|은)?아|아니|아닙|없|불가)/;
 let delivery=false;
 for(const sentence of compact.split(/[.!?。！？\n]/)){
  for(const match of sentence.matchAll(/무료(?:배송|배달)|배송비무료/g))if(!negative.test(sentence.slice(match.index+match[0].length)))delivery=true;
  if(/배송|배달|도착/.test(sentence))for(const match of sentence.matchAll(/보장|확약/g))if(!negative.test(sentence.slice(match.index+match[0].length)))delivery=true;
 }
 return {families,priceOrDelivery:price||delivery};
}

export const regionalMetadataFields=['scopeKey','regionUnitKeys','regionalPurchaseMode','regionalProductKeys','regionalProductFamilies','ogImage','ogImageAlt','ogImageSha256','ogImageSourceUrl','ogImageWidth','ogImageHeight','ogImageType'];
/** All derived fields come from the existing reviewed source binding, never an implicit fallback. */
export function regionalMetadata(coverage,policy,products,pageKey) {
 const r=coverage.representatives.find(r=>r.pageKey===pageKey);
 const matches=(policy.visualBindings||[]).filter(a=>a.pageKey===pageKey),a=matches[0];
 if(!r||matches.length!==1||a.status!=='approved'||!['brand','real_product'].includes(a.assetType)||!a.verifiedAt)fail('missing reviewed binding');
 if(!['catalog','consultation-only'].includes(a.purchaseMode)||!Array.isArray(a.productKeys)||new Set(a.productKeys).size!==a.productKeys.length)fail('invalid purchase binding');
 if((a.purchaseMode==='catalog'&&!a.productKeys.length)||(a.purchaseMode==='consultation-only'&&a.productKeys.length))fail('purchase mode/key binding mismatch');
 const mapping={funeral_wreath:'funeral',congrats_wreath:'congrats',flower_bouquet:'bouquet',flower_basket:'basket'};
 const families=[...new Set(a.productKeys.map(key=>{const matches=products.filter(p=>(p.key||p.productKey)===key);if(matches.length!==1||!matches[0].sourceUrl)fail('missing exact catalog binding');const family=matches[0].family||mapping[matches[0].category];if(!['bouquet','basket','funeral','congrats'].includes(family))fail('invalid bound family');return family;}))];
 if(!a.image||!a.alt||!a.sourceUrl||!/^[a-f0-9]{64}$/.test(a.sha256||'')||!Number.isInteger(a.width)||!Number.isInteger(a.height)||Math.min(a.width,a.height)<1||!['image/png','image/jpeg','image/webp'].includes(a.type))fail('incomplete image binding');
 return {scopeKey:policy.scopeKey,regionUnitKeys:r.unitKeys,regionalPurchaseMode:a.purchaseMode,regionalProductKeys:a.productKeys,regionalProductFamilies:families,ogImage:a.image,ogImageAlt:a.alt,ogImageSha256:a.sha256,ogImageSourceUrl:a.sourceUrl,ogImageWidth:a.width,ogImageHeight:a.height,ogImageType:a.type};
}
export function assertRegionalMetadata(record,coverage,policy,products) {
 const expected=regionalMetadata(coverage,policy,products,record.pageKey);
 for(const field of regionalMetadataFields)if(JSON.stringify(record[field])!==JSON.stringify(expected[field]))fail(`reviewed source binding drift ${record.pageKey}: ${field}`);
 return expected;
}
