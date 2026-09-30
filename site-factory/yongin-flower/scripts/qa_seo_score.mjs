import fs from 'node:fs';
import path from 'node:path';
const DIST=path.resolve('dist');
const INDEXABLE=process.env.SITE_INDEXABLE?process.env.SITE_INDEXABLE==='true':fs.existsSync('production-indexing.enabled');
function walk(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(ent=>{const p=path.join(dir,ent.name);return ent.isDirectory()?walk(p):[p];});}
const articleFiles=walk(DIST).filter(p=>p.endsWith('.html')&&fs.readFileSync(p,'utf8').includes('data-snapshot-id='));
if(!articleFiles.length){if(INDEXABLE){console.error('SEO SCORE QA FAILED: production has no article pages');process.exit(1);}console.log('SEO SCORE QA PASSED: staging bootstrap, no article pages yet');process.exit(0);}
let failed=false,totalScore=0;
for(const file of articleFiles){const html=fs.readFileSync(file,'utf8');const title=html.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1]?.replace(/<[^>]+>/g,'').trim()||'';const h1=(html.match(/<h1\b/gi)||[]).length;const h2=(html.match(/<h2\b/gi)||[]).length;const desc=html.match(/<meta[^>]+name=["']description["'][^>]+content=["']([^"']+)/i)?.[1]||'';const prose=html.match(/<article class=["']prose["']>([\s\S]*?)<\/article>/i)?.[1]||'';const chars=prose.replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim().length;const score=(title?15:0)+(desc.length>=40?10:0)+(h1===1&&h2>=1?10:0)+(chars>=1000?25:chars>=700?15:5)+40;totalScore+=score;if(score<90)failed=true;}
const average=Math.round(totalScore/articleFiles.length);console.log(`SEO SCORE QA: average=${average}, pages=${articleFiles.length}`);if(failed){console.error('SEO SCORE QA FAILED');process.exit(1);}console.log('SEO SCORE QA PASSED');
