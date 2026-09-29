import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, sep } from 'node:path';

const dist = 'dist';
const origin = (process.env.SITE_URL || 'https://ansan.fwith.kr').replace(/\/$/, '');
const canonicalHost = new URL(origin).hostname;
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
for (const route of pages.keys()) if (!sitemapRoutes.has(route)) errors.push(`Sitemap missing public HTML route: ${route}`);
for (const route of sitemapRoutes) if (!pages.has(route)) errors.push(`Sitemap contains URL without generated HTML: ${route}`);

const placeholderPatterns = [
  /준비하고 있습니다/,
  /페이지 준비 중/,
  /상세 문서 수가 아직 적더라도/,
  /메뉴가 빈 화면이 되지 않도록/,
  /초기 콘텐츠 발행 순서/,
  /향후 업데이트 예정/,
  /coming soon/i,
  /\bTODO\b/,
];

const inbound = new Map([...pages.keys()].map(r => [r, 0]));
for (const [source, { html }] of pages) {
  for (const pattern of placeholderPatterns) {
    if (pattern.test(html)) errors.push(`${source}: developer/placeholder wording detected (${pattern})`);
  }
  const bodyText = html
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&[^;]+;/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
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
for (const [route, count] of inbound) if (route !== '/' && count === 0) errors.push(`Orphan page detected: ${route}`);

// Public nav hubs must be backed by real approved/published content. No fallback copy is allowed.
const configSource = readFileSync('src/config/site.ts', 'utf8');
const navHrefs = [...configSource.matchAll(/href:\s*['"]([^'"]+)['"]/g)].map(m => normalize(m[1]));
const hubRoutes = [...new Set(navHrefs.filter(route => {
  const slug = route.replace(/^\//, '').replace(/\/$/, '');
  return slug && existsSync(join('src', 'pages', slug, 'index.astro'));
}))];
const manifest = JSON.parse(readFileSync('src/data/publish-manifest.json', 'utf8'));
const approved = (manifest.pages || []).filter(p => ['approved','published'].includes(p.status));
for (const hub of hubRoutes) {
  const category = hub.replace(/^\//, '').replace(/\/$/, '');
  const children = approved.filter(p => p.category === category);
  if (children.length === 0) errors.push(`Public hub has no real approved/published content: ${hub}`);
  for (const page of children) {
    if (!pages.has(normalize(page.url))) errors.push(`Manifest child missing generated HTML: ${page.pageKey} -> ${page.url}`);
  }
}

if (errors.length) {
  console.error('\nSITE GRAPH QA FAILED');
  for (const e of errors) console.error('- ' + e);
  process.exit(1);
}
console.log(`SITE GRAPH QA PASSED: ${pages.size} public HTML pages, ${sitemapRoutes.size} sitemap URLs, zero orphans, no developer placeholders, all ${hubRoutes.length} public hubs covered by real content.`);
