import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
const dist='dist';
const origin=(process.env.SITE_URL||'https://yongin.fwith.kr').replace(/\/$/,'');
const canonicalHost=new URL(origin).hostname;
const siteIndexable=process.env.SITE_INDEXABLE==='true';
const errors=[],htmlFiles=[];
function walk(dir){for(const name of readdirSync(dir)){const p=join(dir,name),st=statSync(p);st.isDirectory()?walk(p):p.endsWith('.html')&&htmlFiles.push(p);}}
walk(dist);
function routeFor(file){const rel=relative(dist,file).split(sep).join('/');if(rel==='index.html')return'/';if(rel==='404.html'||rel==='404/index.html')return null;if(rel.endsWith('/index.html'))return'/'+rel.slice(0,-'index.html'.length);return'/'+rel.replace(/\.html$/,'/');}
function normalize(pathname){let p=decodeURIComponent(pathname||'/');if(!p.startsWith('/'))p='/'+p;if(p!=='/'&&!p.endsWith('/'))p+='/';return p;}
function robotsFor(html){return html.match(/<meta[^>]+name=["']robots["'][^>]+content=["']([^"']+)["']/i)?.[1]||html.match(/<meta[^>]+content=["']([^"']+)["'][^>]+name=["']robots["']/i)?.[1]||'';}
const pages=new Map();for(const file of htmlFiles){const route=routeFor(file);if(route)pages.set(normalize(route),{file,html:readFileSync(file,'utf8')});}
const sitemapFiles=readdirSync(dist).filter(n=>/^sitemap-\d+\.xml$/.test(n));if(!sitemapFiles.length)errors.push('No sitemap-N.xml files generated.');
const sitemapRoutes=new Set();for(const name of sitemapFiles){const xml=readFileSync(join(dist,name),'utf8');for(const m of xml.matchAll(/<loc>([^<]+)<\/loc>/g)){try{sitemapRoutes.add(normalize(new URL(m[1]).pathname));}catch{errors.push(`${name}: invalid loc`);}}}
for(const [route,{html}] of pages){const noindex=/noindex/i.test(robotsFor(html));if(siteIndexable){if(noindex&&sitemapRoutes.has(route))errors.push(`Noindex route in sitemap: ${route}`);if(!noindex&&!sitemapRoutes.has(route))errors.push(`Sitemap missing indexable route: ${route}`);}else if(!noindex)errors.push(`Staging route must remain noindex: ${route}`);}
const placeholderPatterns=[/준비하고 있습니다/,/페이지 준비 중/,/향후 업데이트 예정/,/자동 생성/,/fallback/i,/placeholder/i,/TODO/];
const inbound=new Map([...pages.keys()].map(r=>[r,0]));
for(const [source,{html}] of pages){for(const pattern of placeholderPatterns)if(pattern.test(html))errors.push(`${source}: developer/placeholder wording detected`);const body=html.replace(/<script[\s\S]*?<\/script>/gi,' ').replace(/<style[\s\S]*?<\/style>/gi,' ').replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim();if(body.length<180)errors.push(`${source}: page text too thin`);for(const m of html.matchAll(/href=["']([^"'#]+)["']/g)){const href=m[1];if(/^(mailto:|tel:|javascript:)/i.test(href))continue;let target;try{if(/^https?:\/\//i.test(href)){const u=new URL(href);if(u.hostname!==canonicalHost)continue;target=normalize(u.pathname);}else target=normalize(new URL(href,origin+source).pathname);}catch{continue;}if(target!==source&&pages.has(target))inbound.set(target,(inbound.get(target)??0)+1);}}
for(const [route,count] of inbound){const noindex=/noindex/i.test(robotsFor(pages.get(route)?.html??''));if(route!=='/'&&count===0&&!noindex)errors.push(`Orphan page: ${route}`);}
const manifest=JSON.parse(readFileSync('src/data/publish-manifest.json','utf8'));const approved=(manifest.pages||[]).filter(p=>['approved','published'].includes(p.status));
const hubCategories=['funeral','business','school','event','gift','order','regions'];const hubStats=[];
for(const category of hubCategories){const children=approved.filter(p=>p.routeType==='category'&&p.category===category),hub=`/${category}/`;if(children.length===0){if(pages.has(hub))errors.push(`Hub exists without content: ${hub}`);continue;}if(!pages.has(hub)){errors.push(`Hub missing: ${hub}`);continue;}const noindex=/noindex/i.test(robotsFor(pages.get(hub).html));if(siteIndexable){if(children.length<3&&!noindex)errors.push(`Thin hub must be noindex: ${hub}`);if(children.length>=3&&noindex)errors.push(`Hub with 3+ docs should index: ${hub}`);}hubStats.push(`${category}=${children.length}`);}
if(errors.length){console.error('SITE GRAPH QA FAILED');for(const e of errors)console.error('- '+e);process.exit(1);}
console.log(`SITE GRAPH QA PASSED: mode=${siteIndexable?'production':'staging'}, pages=${pages.size}, hubs=${hubStats.join(',')||'none'}`);
