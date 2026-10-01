import {readFileSync,writeFileSync,existsSync} from 'node:fs';
import {verifyPublication,submissionPayload,receiptKey} from './indexnow_contract.mjs';
const selection=JSON.parse(readFileSync('indexnow-urls.json','utf8'));
const build=JSON.parse(readFileSync('src/data/build-revision.json','utf8'));
if(selection.revision!==build.revision)throw new Error('Stale IndexNow selection');
verifyPublication({...selection,indexable:process.env.SITE_INDEXABLE,verifiedRevision:process.env.LIVE_QA_VERIFIED_REVISION});
const key=process.env.INDEXNOW_KEY;
if(readFileSync(`public/${key}.txt`,'utf8').trim()!==key)throw new Error('Public verification key file mismatch');
const endpoint=process.env.INDEXNOW_ENDPOINT||'https://searchadvisor.naver.com/indexnow';
if(!['https://searchadvisor.naver.com/indexnow','https://api.indexnow.org/indexnow'].includes(endpoint))throw new Error('Unapproved IndexNow endpoint');
const fingerprint=receiptKey(selection);
if(existsSync('indexnow-receipt.json')&&JSON.parse(readFileSync('indexnow-receipt.json','utf8')).fingerprint===fingerprint){console.log('IndexNow already accepted for this selection');process.exit(0);}
if(!selection.urlList.length){console.log('IndexNow: no changed public URLs');process.exit(0);}
for(let i=0;i<selection.urlList.length;i+=10000){
 const payload=submissionPayload({...selection,key,urlList:selection.urlList.slice(i,i+10000)});
 const response=await fetch(endpoint,{method:'POST',headers:{'content-type':'application/json; charset=utf-8'},body:JSON.stringify(payload),signal:AbortSignal.timeout(30000)});
 if(![200,202].includes(response.status))throw new Error(`IndexNow rejected HTTP ${response.status}`);
 console.log(`IndexNow accepted ${payload.urlList.length} URLs: HTTP ${response.status}`);
}
writeFileSync('indexnow-receipt.json',JSON.stringify({fingerprint,revision:selection.revision,acceptedAt:new Date().toISOString()},null,2)+'\n');
