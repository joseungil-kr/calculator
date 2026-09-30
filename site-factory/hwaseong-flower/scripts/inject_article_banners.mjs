import fs from 'node:fs';
import path from 'node:path';

const DIST = path.resolve('dist');
const BANNERS = [
  {
    src: '/images/banners/order-banner-01.webp',
    alt: '여성 플로리스트가 꽃다발을 제작하는 꽃배달 주문 안내 배너, 편리하게 주문하세요, 근조화환 생화 최저가, 전화 1844-0644'
  },
  {
    src: '/images/banners/order-banner-02.webp',
    alt: '여성 플로리스트가 근조화환을 제작하는 꽃배달 주문 안내 배너, 편리하게 주문하세요, 근조화환 생화 최저가, 전화 1844-0644'
  },
  {
    src: '/images/banners/order-banner-03.webp',
    alt: '여성 플로리스트가 꽃바구니를 제작하는 꽃배달 주문 안내 배너, 편리하게 주문하세요, 근조화환 생화 최저가, 전화 1844-0644'
  }
];

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

function stableSeed(input) {
  let h = 0;
  for (const ch of input) h = ((h << 5) - h + ch.codePointAt(0)) | 0;
  return Math.abs(h);
}

function renderBanner(banner, index) {
  return `
<figure class="content-order-banner" data-order-banner="${index + 1}">
  <a href="tel:18440644" aria-label="꽃배달 전화 주문 1844-0644">
    <img src="${banner.src}" alt="${banner.alt}" width="1200" height="400" loading="lazy" decoding="async">
  </a>
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
  const seed = stableSeed(path.relative(DIST, file));
  const inserts = fractions.map((fraction, i) => {
    const target = Math.floor(body.length * fraction);
    const pos = boundaries.reduce((best, x) => Math.abs(x - target) < Math.abs(best - target) ? x : best, boundaries[0]);
    const banner = BANNERS[(seed + i) % BANNERS.length];
    return { pos, html: renderBanner(banner, i) };
  }).sort((a, b) => b.pos - a.pos);

  for (const ins of inserts) body = body.slice(0, ins.pos) + ins.html + body.slice(ins.pos);
  html = html.slice(0, bodyStart) + body + html.slice(bodyEnd);
  fs.writeFileSync(file, html);
  changed++;
}

console.log(`ARTICLE BANNERS INJECTED: ${changed} article page(s)`);
