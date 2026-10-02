import fs from 'node:fs';
import path from 'node:path';

const DIST = path.resolve('dist');
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

function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((ent) => {
    const p = path.join(dir, ent.name);
    return ent.isDirectory() ? walk(p) : [p];
  });
}

function plainText(html) {
  return html
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&[a-z0-9#]+;/gi, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function bannerCount(charCount) {
  if (charCount >= 2200) return 3;
  if (charCount >= 1200) return 2;
  return 1;
}

function renderBanner(index) {
  return `
<figure class="content-order-banner" data-order-banner="${index + 1}">
  <figcaption>꽃 주문 안내</figcaption>
  <p>전화 주문 ${escapeHtml(business.phoneOrderHours)} · 온라인 주문 ${escapeHtml(business.onlineOrderHours)} 접수</p>
  <div class="content-order-banner-actions">
    <a href="${escapeHtml(business.phoneHref)}">전화 주문 ${escapeHtml(business.phone)}</a>
    <a href="${escapeHtml(business.onlineOrderUrl)}" rel="noopener">온라인 주문</a>
  </div>
</figure>`;
}

let changed = 0;
for (const file of walk(DIST).filter((p) => p.endsWith('.html'))) {
  let html = fs.readFileSync(file, 'utf8');
  if (!html.includes('data-snapshot-id=') || !html.includes('<article class="prose">')) continue;
  if (html.includes('data-order-banner=')) continue;

  const startTag = '<article class="prose">';
  const start = html.indexOf(startTag);
  const sourceStart = html.indexOf('<section class="source-list"', start);
  const articleEnd = html.indexOf('</article>', start);
  if (start < 0 || articleEnd < 0) continue;

  const bodyStart = start + startTag.length;
  const bodyEnd = sourceStart > bodyStart && sourceStart < articleEnd ? sourceStart : articleEnd;
  let body = html.slice(bodyStart, bodyEnd);
  const chars = plainText(body).length;
  const count = bannerCount(chars);

  const boundaryRe = /<\/(?:p|ul|ol|blockquote)>/gi;
  const boundaries = [];
  let m;
  while ((m = boundaryRe.exec(body))) boundaries.push(m.index + m[0].length);
  if (boundaries.length === 0) continue;

  const fractions = count === 1 ? [0.50] : count === 2 ? [0.34, 0.68] : [0.26, 0.53, 0.80];
  const inserts = fractions.map((fraction, i) => {
    const target = Math.floor(body.length * fraction);
    const pos = boundaries.reduce((best, x) => Math.abs(x - target) < Math.abs(best - target) ? x : best, boundaries[0]);
    return { pos, html: renderBanner(i) };
  }).sort((a, b) => b.pos - a.pos);

  for (const ins of inserts) body = body.slice(0, ins.pos) + ins.html + body.slice(ins.pos);
  html = html.slice(0, bodyStart) + body + html.slice(bodyEnd);
  fs.writeFileSync(file, html);
  changed++;
}

console.log(`ARTICLE BANNERS INJECTED: ${changed} article page(s)`);
