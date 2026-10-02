import fs from 'node:fs';
import path from 'node:path';
const business = JSON.parse(fs.readFileSync('src/data/business-truth.json', 'utf8'));
for (const field of ['phone', 'phoneHref', 'phoneOrderHours', 'onlineOrderUrl', 'onlineOrderHours']) {
  if (typeof business[field] !== 'string' || !business[field].trim()) throw new Error(`Invalid order CTA business field: ${field}`);
}
if (!/^[+\d][\d ()-]*$/.test(business.phone) || !/^tel:\+?\d{8,15}$/.test(business.phoneHref)
  || business.phone.replace(/\D/g, '') !== business.phoneHref.replace(/\D/g, '')) throw new Error('Invalid order CTA telephone');
const orderUrl = new URL(business.onlineOrderUrl);
if (orderUrl.protocol !== 'https:' || orderUrl.username || orderUrl.password || /\s/.test(business.onlineOrderUrl)) throw new Error('Invalid order CTA HTTPS URL');
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (ch) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
}
function validOrderBanners(banners, expected) {
  return banners.length === expected && banners.every((banner) =>
    /<figcaption>[^<]+<\/figcaption>/.test(banner)
    && banner.includes(`<a href="${escapeHtml(business.phoneHref)}">전화 주문 ${escapeHtml(business.phone)}</a>`)
    && banner.includes(`<a href="${escapeHtml(business.onlineOrderUrl)}" rel="noopener">온라인 주문</a>`)
    && !/<img\b|최저가/i.test(banner)
  ) && new Set(banners.map(banner => banner.match(/data-order-banner="(\d+)"/)?.[1])).size === expected
    && banners.every(banner => { const n = Number(banner.match(/data-order-banner="(\d+)"/)?.[1]); return n >= 1 && n <= expected; });
}
const DIST=path.resolve('dist');
const INDEXABLE=process.env.SITE_INDEXABLE?process.env.SITE_INDEXABLE==='true':fs.existsSync('production-indexing.enabled');
function walk(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(ent=>{const p=path.join(dir,ent.name);return ent.isDirectory()?walk(p):[p];});}
const articleFiles=walk(DIST).filter(p=>p.endsWith('.html')&&fs.readFileSync(p,'utf8').includes('data-snapshot-id='));
if(!articleFiles.length){if(INDEXABLE){console.error('SEO SCORE QA FAILED: production has no article pages');process.exit(1);}console.log('SEO SCORE QA PASSED: staging bootstrap, no article pages yet');process.exit(0);}
let failed=false,totalScore=0;
for(const file of articleFiles){const html=fs.readFileSync(file,'utf8');const title=html.match(/<title[^>]*>([\s\S]*?)<\/title>/i)?.[1]?.replace(/<[^>]+>/g,'').trim()||'';const h1=(html.match(/<h1\b/gi)||[]).length;const h2=(html.match(/<h2\b/gi)||[]).length;const desc=html.match(/<meta[^>]+name=["']description["'][^>]+content=["']([^"']+)/i)?.[1]||'';const prose=html.match(/<article class=["']prose["']>([\s\S]*?)<\/article>/i)?.[1]||'';const proseWithoutSources=prose.replace(/<section class=["']source-list["'][\s\S]*?<\/section>/gi,' ');const banners=[...proseWithoutSources.matchAll(/<figure class=["']content-order-banner["'][\s\S]*?<\/figure>/gi)].map(x=>x[0]);const proseNoBanners=proseWithoutSources.replace(/<figure class=["']content-order-banner["'][\s\S]*?<\/figure>/gi,' ');const bannerChars=proseNoBanners.replace(/<[^>]+>/g,' ').replace(/&[a-z0-9#]+;/gi,' ').replace(/\s+/g,' ').trim().length;const chars=prose.replace(/<figure class=["']content-order-banner["'][\s\S]*?<\/figure>/gi,' ').replace(/<[^>]+>/g,' ').replace(/\s+/g,' ').trim().length;const bannersValid=validOrderBanners(banners,bannerChars>=2200?3:bannerChars>=1200?2:1);const score=(title?15:0)+(desc.length>=40?10:0)+(h1===1&&h2>=1?10:0)+(chars>=1000?25:chars>=700?15:5)+40;totalScore+=score;if(score<90 || !bannersValid)failed=true;}
const average=Math.round(totalScore/articleFiles.length);console.log(`SEO SCORE QA: average=${average}, pages=${articleFiles.length}`);if(failed){console.error('SEO SCORE QA FAILED');process.exit(1);}console.log('SEO SCORE QA PASSED');
