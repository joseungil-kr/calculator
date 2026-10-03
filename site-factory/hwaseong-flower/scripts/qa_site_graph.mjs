import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, sep } from 'node:path';

const dist = 'dist';
const origin = (process.env.SITE_URL || 'https://hwaseong.fwith.kr').replace(/\/$/, '');
const canonicalHost = new URL(origin).hostname;
const siteIndexable = process.env.SITE_INDEXABLE === 'true';
const errors = [];
const htmlFiles = [];
function walk(dir) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    const st = statSync(path);
    if (st.isDirectory()) walk(path);
    else if (path.endsWith('.html')) htmlFiles.push(path);
  }
}
walk(dist);
function routeFor(file) {
  const rel = relative(dist, file).split(sep).join('/');
  if (rel === 'index.html') return '/';
  if (rel === '404.html' || rel === '404/index.html') return null;
  if (rel.endsWith('/index.html')) return '/' + rel.slice(0, -'index.html'.length);
  return '/' + rel.replace(/\.html$/, '/');
}
function normalize(pathname) {
  let p = decodeURIComponent(pathname || '/');
  if (!p.startsWith('/')) p = '/' + p;
  if (p !== '/' && !p.endsWith('/')) p += '/';
  return p;
}
function robotsFor(html) {
  return html.match(/<meta[^>]+name=["']robots["'][^>]+content=["']([^"']+)["']/i)?.[1]
    || html.match(/<meta[^>]+content=["']([^"']+)["'][^>]+name=["']robots["']/i)?.[1]
    || '';
}
const pages = new Map();
for (const file of htmlFiles) {
  const route = routeFor(file);
  if (!route) continue;
  pages.set(normalize(route), { file, html: readFileSync(file, 'utf8') });
}
const sitemapFiles = readdirSync(dist).filter(n => /^sitemap-\d+\.xml$/.test(n));
if (sitemapFiles.length === 0) errors.push('No sitemap-N.xml files generated.');
const sitemapRoutes = new Set();
for (const name of sitemapFiles) {
  const xml = readFileSync(join(dist, name), 'utf8');
  for (const m of xml.matchAll(/<loc>([^<]+)<\/loc>/g)) {
    try { sitemapRoutes.add(normalize(new URL(m[1]).pathname)); }
    catch { errors.push(`${name}: invalid <loc> ${m[1]}`); }
  }
}
for (const [route, { html }] of pages) {
  const noindex = /noindex/i.test(robotsFor(html));
  if (siteIndexable) {
    if (noindex && sitemapRoutes.has(route)) errors.push(`Noindex route must not be in sitemap: ${route}`);
    if (!noindex && !sitemapRoutes.has(route)) errors.push(`Sitemap missing indexable HTML route: ${route}`);
  } else if (!noindex) {
    errors.push(`Staging route must remain noindex: ${route}`);
  }
}
for (const route of sitemapRoutes) {
  if (!pages.has(route)) errors.push(`Sitemap contains URL without generated HTML: ${route}`);
  else if (siteIndexable && /noindex/i.test(robotsFor(pages.get(route).html))) errors.push(`Sitemap contains noindex URL: ${route}`);
}
const placeholderPatterns = [
  /준비하고 있습니다/, /페이지 준비 중/, /상세 문서 수가 아직 적더라도/, /메뉴가 빈 화면이 되지 않도록/,
  /초기 콘텐츠 발행 순서/, /향후 업데이트 예정/, /이 글의 역할/, /한 가지 질문에 집중해/,
  /자동으로 연결합니다/, /관련 콘텐츠를 자동으로/, /콘텐츠가 없습니다/, /해당 문서가 없습니다/,
  /허브 문서/, /coming soon/i, /\bfallback\b/i, /\bplaceholder\b/i, /\bTODO\b/
];
const inbound = new Map([...pages.keys()].map(r => [r, 0]));
for (const [source, { html }] of pages) {
  for (const pattern of placeholderPatterns) if (pattern.test(html)) errors.push(`${source}: developer/placeholder wording detected (${pattern})`);
  const bodyText = html.replace(/<script[\s\S]*?<\/script>/gi, ' ').replace(/<style[\s\S]*?<\/style>/gi, ' ').replace(/<[^>]+>/g, ' ').replace(/&[^;]+;/g, ' ').replace(/\s+/g, ' ').trim();
  if (bodyText.length < 180) errors.push(`${source}: page text is too thin (${bodyText.length} chars)`);
  for (const m of html.matchAll(/href=["']([^"'#]+)["']/g)) {
    const href = m[1];
    if (/^(mailto:|tel:|javascript:)/i.test(href)) continue;
    let target;
    try {
      if (/^https?:\/\//i.test(href)) {
        const u = new URL(href);
        if (u.hostname !== canonicalHost) continue;
        target = normalize(u.pathname);
      } else {
        target = normalize(new URL(href, origin + source).pathname);
      }
    } catch { continue; }
    if (target !== source && pages.has(target)) inbound.set(target, (inbound.get(target) ?? 0) + 1);
  }
}
for (const [route, count] of inbound) {
  const html = pages.get(route)?.html ?? '';
  const noindex = /noindex/i.test(robotsFor(html));
  if (route !== '/' && count === 0 && !noindex) errors.push(`Orphan page detected: ${route}`);
}

const manifest = JSON.parse(readFileSync('src/data/publish-manifest.json', 'utf8'));
const approved = (manifest.pages || []).filter(p => ['approved','published'].includes(p.status));
const hubCategories = ['guide', 'funeral', 'places', 'occasions', 'flower-knowledge', 'order-help', 'regions'];
const hubStats = [];
for (const category of hubCategories) {
  const children = approved.filter(p => p.routeType === 'category' && p.category === category);
  const hub = `/${category}/`;
  if (children.length === 0) {
    if (pages.has(hub)) errors.push(`Hub route exists without real content: ${hub}`);
    continue;
  }
  if (!pages.has(hub)) {
    errors.push(`Category has content but hub route is missing: ${hub}`);
    continue;
  }
  const hubNoindex = /noindex/i.test(robotsFor(pages.get(hub).html));
  if (siteIndexable) {
    if (children.length < 3 && !hubNoindex) errors.push(`Thin hub must be noindex until 3 documents: ${hub}`);
    if (children.length >= 3 && hubNoindex) errors.push(`Hub with 3+ documents should be indexable: ${hub}`);
  } else if (!hubNoindex) {
    errors.push(`Staging hub must remain noindex: ${hub}`);
  }
  for (const page of children) if (!pages.has(normalize(page.url))) errors.push(`Manifest child missing generated HTML: ${page.pageKey} -> ${page.url}`);
  hubStats.push(`${category}=${children.length}${children.length < 3 ? '(noindex)' : '(index)'}`);
}
if (errors.length) {
  console.error('\nSITE GRAPH QA FAILED');
  for (const e of errors) console.error('- ' + e);
  process.exit(1);
}
console.log(`SITE GRAPH QA PASSED: mode=${siteIndexable ? 'production' : 'staging'}, ${pages.size} HTML pages, ${sitemapRoutes.size} sitemap URLs, zero orphans, no developer placeholders. Hubs: ${hubStats.join(', ')}`);
