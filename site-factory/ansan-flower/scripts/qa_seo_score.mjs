import fs from 'node:fs';
import path from 'node:path';

const DIST = path.resolve('dist');
const SITE_URL = (process.env.SITE_URL || '').replace(/\/$/, '');
const INDEXABLE = process.env.SITE_INDEXABLE
  ? process.env.SITE_INDEXABLE === 'true'
  : fs.existsSync('production-indexing.enabled');

function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((ent) => {
    const p = path.join(dir, ent.name);
    return ent.isDirectory() ? walk(p) : [p];
  });
}
function textOnly(s) {
  return s.replace(/<script[\s\S]*?<\/script>/gi,' ')
    .replace(/<style[\s\S]*?<\/style>/gi,' ')
    .replace(/<[^>]+>/g,' ')
    .replace(/&[a-z0-9#]+;/gi,' ')
    .replace(/\s+/g,' ').trim();
}
function m(html,re){ return html.match(re)?.[1]?.trim() || ''; }
function expectedBannerCount(chars){ return chars >= 2200 ? 3 : chars >= 1200 ? 2 : 1; }

const rows=[];
let failed=false;
for(const file of walk(DIST).filter(p=>p.endsWith('.html'))){
  const html=fs.readFileSync(file,'utf8');
  if(!html.includes('data-snapshot-id=')) continue;

  const rel='/' + path.relative(DIST,file).replace(/\\/g,'/').replace(/index\.html$/,'').replace(/\.html$/,'');
  const title=textOnly(m(html,/<title[^>]*>([\s\S]*?)<\/title>/i));
  const desc=m(html,/<meta[^>]+name=["']description["'][^>]+content=["']([^"']*)["']/i)
    || m(html,/<meta[^>]+content=["']([^"']*)["'][^>]+name=["']description["']/i);
  const canonical=m(html,/<link[^>]+rel=["']canonical["'][^>]+href=["']([^"']+)["']/i)
    || m(html,/<link[^>]+href=["']([^"']+)["'][^>]+rel=["']canonical["']/i);
  const robots=m(html,/<meta[^>]+name=["']robots["'][^>]+content=["']([^"']+)["']/i)
    || m(html,/<meta[^>]+content=["']([^"']+)["'][^>]+name=["']robots["']/i);
  const h1=(html.match(/<h1\b/gi)||[]).length;
  const h2=(html.match(/<h2\b/gi)||[]).length;
  const internal=(html.match(/<a\b[^>]+href=["']\/(?!\/|#)[^"']*["']/gi)||[]).length;
  const imgs=[...html.matchAll(/<img\b[^>]*>/gi)].map(x=>x[0]);
  const allAlt=imgs.every(tag=>/\balt=["'][^"']+["']/i.test(tag));
  const banners=[...html.matchAll(/<figure class=["']content-order-banner["'][\s\S]*?<\/figure>/gi)].map(x=>x[0]);

  const prose=m(html,/<article class=["']prose["']>([\s\S]*?)<\/article>/i);
  const proseWithoutSources=prose.replace(/<section class=["']source-list["'][\s\S]*?<\/section>/gi,' ');
  const proseNoBanners=proseWithoutSources.replace(/<figure class=["']content-order-banner["'][\s\S]*?<\/figure>/gi,' ');
  const chars=textOnly(proseNoBanners).length;
  const expected=expectedBannerCount(chars);
  const bannerAlt=banners.every(x=>/<img\b[^>]+alt=["'][^"']+["']/i.test(x));
  const bannerUnique=new Set(banners.map(x=>m(x,/src=["']([^"']+)["']/i))).size===banners.length;
  const region=(m(html,/<div class=["']article-meta["'][\s\S]*?<span>([^<]+)<\/span>/i)||'').trim();
  const regionHits=region ? (textOnly(proseNoBanners).match(new RegExp(region,'g'))||[]).length : 0;
  const density=chars ? regionHits / Math.max(1, chars/100) : 0;

  const score={
    title: title ? (title.length<=90 ? 15 : 12) : 0,
    description: desc ? (desc.length>=40 && desc.length<=200 ? 10 : 8) : 0,
    headings: h1===1 ? (h2>=1 ? 10 : 7) : 0,
    internalLinks: internal>=1 ? 10 : 0,
    technical: canonical.startsWith(SITE_URL) && (INDEXABLE ? /index,follow/i.test(robots) : /noindex/i.test(robots)) ? 10 : 0,
    imageAlt: allAlt ? 10 : 0,
    banners: banners.length===expected && bannerAlt && (banners.length===1 || bannerUnique) ? 10 : 0,
    content: chars>=1000 ? 15 : chars>=700 ? 10 : 5,
    keywordNaturalness: density<=2.5 ? 10 : density<=4 ? 7 : 3,
  };
  const total=Object.values(score).reduce((a,b)=>a+b,0);
  const status=total>=90?'PASS':total>=80?'CONDITIONAL':'REVISE';
  rows.push({url:rel.replace(/\/{2,}/g,'/'),score:total,status,banners:`${banners.length}/${expected}`,chars,...score});
  if(total<90) failed=true;
}
console.table(rows);
if(!rows.length){ console.error('SEO SCORE QA FAILED: no article pages found'); process.exit(1); }
const average=Math.round(rows.reduce((s,r)=>s+r.score,0)/rows.length);
console.log(`SEO SCORE QA: average=${average}, pages=${rows.length}, threshold=90`);
if(failed){ console.error('SEO SCORE QA FAILED: one or more article pages scored below 90'); process.exit(1); }
console.log('SEO SCORE QA PASSED');
