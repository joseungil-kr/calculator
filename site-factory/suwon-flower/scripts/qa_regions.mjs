import fs from 'node:fs';
import crypto from 'node:crypto';
import path from 'node:path';
import {regionalRows,validateDefinition,validateRegionalPurchase,assertRegionalMetadata} from '../src/lib/regions.mjs';
const read=name=>JSON.parse(fs.readFileSync(`src/data/${name}.json`,'utf8'));
const coverage=read('region-coverage'),policy=read('region-policy'),manifest=read('publish-manifest'),architecture=read('architecture'),map=read('page-map');
validateDefinition(coverage,policy);
const rows=regionalRows(manifest.pages,architecture,coverage,policy);
for(const page of rows){
 const fields=['title','h1','description','cardSummary','firstAnswer'];
 let customer,input;
 if(fs.existsSync('src/data/pages.json')){input=read('pages').find(p=>p.pageKey===page.pageKey);customer=[...fields.map(f=>input[f]||''),input.contentMarkdown||'',...(input.sections||[]).flat(),...(input.faq||[]).flat()].join('\n');}
 else {const parts=fs.readFileSync(page.file,'utf8').split('---');const header=Object.fromEntries(parts[1].trim().split('\n').map(line=>{const i=line.indexOf(':');return [line.slice(0,i),line.slice(i+1).trim()];}));input=Object.fromEntries(Object.entries(header).map(([key,value])=>[key,JSON.parse(value)]));customer=[...fields.map(f=>input[f]||''),parts.slice(2).join('---')].join('\n');}
 for(const output of [page,map.pages.find(p=>p.pageKey===page.pageKey),architecture.pages.find(p=>p.pageKey===page.pageKey),input]){if(!output)throw new Error('Missing regional output');assertRegionalMetadata(output,coverage,policy,read('products'));}
 validateRegionalPurchase(page,read('products'),customer);
 const mapped=map.pages.find(p=>p.pageKey===page.pageKey);
 for(const field of ['url','snapshotId','snapshotHash','scopeKey','ogImage','ogImageAlt'])if(page[field]!==mapped?.[field])throw new Error('Regional page-map mismatch '+field);
 const asset=(policy.visualBindings||[]).find(a=>a.pageKey===page.pageKey);
 if(!asset||asset.status!=='approved'||asset.image!==page.ogImage||asset.alt!==page.ogImageAlt||asset.sha256!==page.ogImageSha256||asset.sourceUrl!==page.ogImageSourceUrl)throw new Error('Regional asset is not bound');
 const image=path.resolve('public',page.ogImage.replace(/^\//,''));
 if(!image.startsWith(path.resolve('public')+path.sep)||crypto.createHash('sha256').update(fs.readFileSync(image)).digest('hex')!==asset.sha256)throw new Error('Regional image mismatch');
}
console.log('REGIONAL CONTRACT PASS',JSON.stringify({siteKey:coverage.siteKey,enabled:policy.enabled,inventoryUnits:coverage.units.length,actualRegionalPages:rows.length,countIsQuota:false}));
