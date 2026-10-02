import {readFileSync,writeFileSync} from 'node:fs';
const baseline=readFileSync('public/_headers','utf8').replace(/^\s*X-Robots-Tag:.*\n?/gmi,'');
const indexing=process.env.SITE_INDEXABLE==='true'?'':'  X-Robots-Tag: noindex, nofollow, noarchive\n';
writeFileSync('dist/_headers',baseline.trimEnd()+'\n'+indexing);
