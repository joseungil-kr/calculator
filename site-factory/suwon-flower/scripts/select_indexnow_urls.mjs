import {execFileSync} from 'node:child_process';
import {readFileSync,writeFileSync,readdirSync} from 'node:fs';
import {verifyPublication} from './indexnow_contract.mjs';
const origin=(process.env.SITE_URL||process.env.SITE_ORIGIN||'https://suwon.fwith.kr').replace(/\/$/,'');
const {revision}=JSON.parse(readFileSync('src/data/build-revision.json','utf8'));
verifyPublication({origin,revision,indexable:process.env.SITE_INDEXABLE,verifiedRevision:process.env.LIVE_QA_VERIFIED_REVISION});
const sitemap=new Set(readdirSync('dist').filter(p=>/^sitemap-\d+\.xml$/.test(p)).flatMap(file=>[...readFileSync('dist/'+file,'utf8').matchAll(/<loc>([^<]+)<\/loc>/g)].map(m=>m[1])));
if(!sitemap.size)throw new Error('No built sitemap URLs');
const base=process.env.INDEXNOW_BASE_SHA;
let urls=[...sitemap];
if(process.env.INDEXNOW_INITIAL!=='true' && base){
 if(!/^[a-f0-9]{40}$/.test(base))throw new Error('Invalid base revision');
 const prefix=execFileSync('git',['rev-parse','--show-prefix'],{encoding:'utf8'}).trim();
 const changed=execFileSync('git',['diff','--name-only',base,'HEAD','--','.'],{encoding:'utf8'}).trim().split('\n');
 const sitewide=changed.some(p=>/\/(layouts|components|styles|pages|config|lib)\//.test(p)||/(products|business-truth)\.json$/.test(p));
 if(!sitewide){
  const before=JSON.parse(execFileSync('git',['show',`${base}:${prefix}src/data/pages.json`],{encoding:'utf8'}));
  const current=JSON.parse(readFileSync('src/data/pages.json','utf8'));
  const old=new Map(before.map(p=>[p.pageKey,JSON.stringify(p)]));const candidates=new Set();
  for(const p of current)if(old.get(p.pageKey)!==JSON.stringify(p)){candidates.add(origin+p.url);candidates.add(origin+'/');candidates.add(origin+'/'+p.category+'/');}
  urls=[...candidates].filter(url=>sitemap.has(url));
 }
}
const selection={origin,revision,urlList:urls.sort()};
writeFileSync('indexnow-urls.json',JSON.stringify(selection,null,2)+'\n');
console.log(`IndexNow selected ${urls.length} verified public URLs at ${revision}`);
