import {readFileSync,writeFileSync} from 'node:fs';
const baseline=readFileSync('public/_headers','utf8').replace(/^\s*X-Robots-Tag:.*\n?/gmi,'');
const indexing=process.env.SITE_INDEXABLE==='true'?'':'  X-Robots-Tag: noindex, nofollow, noarchive\n';
const hubs=JSON.parse(readFileSync('src/data/architecture.json','utf8')).hubs;
const thin=indexing?'':hubs.filter(h=>h.children<3).map(h=>`${h.url}\n  X-Robots-Tag: noindex, nofollow, noarchive\n`).join('');
writeFileSync('dist/_headers',baseline.trimEnd()+'\n'+indexing+thin);
