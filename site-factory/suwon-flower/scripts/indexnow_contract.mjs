import crypto from 'node:crypto';
export function verifyPublication({origin,indexable,revision,verifiedRevision}) {
 if(origin!=='https://suwon.fwith.kr')throw new Error('IndexNow requires registered Suwon production origin');
 if(indexable!=='true')throw new Error('IndexNow disabled for noindex/preview');
 if(!/^[a-f0-9]{40}$/.test(revision||'') || verifiedRevision!==revision)throw new Error('Exact live revision must be verified before IndexNow');
}
export function submissionPayload({origin,key,urlList}) {
 if(!/^[a-f0-9]{32,128}$/i.test(key||''))throw new Error('Invalid public IndexNow verification key');
 if(!Array.isArray(urlList)||urlList.length>10000)throw new Error('Invalid IndexNow URL batch');
 for(const url of urlList)if(new URL(url).origin!==origin||!url.startsWith(origin+'/')||new URL(url).hash)throw new Error('Cross-origin/invalid IndexNow URL');
 return {host:new URL(origin).host,key,keyLocation:`${origin}/${key}.txt`,urlList:[...new Set(urlList)]};
}
export function receiptKey(selection){return crypto.createHash('sha256').update(JSON.stringify(selection)).digest('hex');}
