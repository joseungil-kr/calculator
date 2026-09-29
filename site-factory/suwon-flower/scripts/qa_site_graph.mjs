import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join, relative, sep } from 'node:path';

const dist = 'dist';
const origin = (process.env.SITE_URL || 'https://suwon.fwith.kr').replace(/\/$/, '');
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
  const html = readFileSync(file, 'utf8');
  pages.set(normalize(route), { file, html });
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

for (const route of pages.keys()) {
  if (!sitemapRoutes.has(route)) errors.push(`Sitemap missing public HTML route: ${route}`);
}

for (const route of sitemapRoutes) {
  if (!pages.has(route)) errors.push(`Sitemap contains URL without generated HTML: ${route}`);
}

const inbound = new Map([...pages.keys()].map(r => [r, 0]));
const placeholderPatterns = [
  /준비하고 있습니다/,
  /페이지 준비 중/,
  /coming soon/i,
  /\bTODO\b/,
];

for (const [source, { file, html }] of pages) {
  for (const pattern of placeholderPatterns) {
    if (pattern.test(html)) errors.push(`${source}: placeholder/empty-page wording detected (${pattern})`);
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

    if (target !== source && pages.has(target)) {
      inbound.set(target, (inbound.get(target) ?? 0) + 1);
    }
  }
}

for (const [route, count] of inbound) {
  if (route !== '/' && count === 0) errors.push(`Orphan page detected: ${route}`);
}

if (errors.length) {
  console.error('\nSITE GRAPH QA FAILED');
  for (const e of errors) console.error('- ' + e);
  process.exit(1);
}

console.log(`SITE GRAPH QA PASSED: ${pages.size} public HTML pages, ${sitemapRoutes.size} sitemap URLs, zero orphans, zero empty placeholders.`);
