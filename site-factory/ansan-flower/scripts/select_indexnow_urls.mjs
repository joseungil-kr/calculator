import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';

const origin = (process.env.SITE_ORIGIN || 'https://ansan.fwith.kr').replace(/\/$/, '');
const initial = process.env.INDEXNOW_INITIAL === 'true';
const baseSha = process.env.INDEXNOW_BASE_SHA || '';

async function fetchText(url) {
  const res = await fetch(url, { headers: { 'user-agent': 'SiteFactory-IndexNow/1.0' } });
  if (!res.ok) throw new Error(`Failed to fetch ${url}: HTTP ${res.status}`);
  return await res.text();
}

function locs(xml) {
  return [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m => m[1]);
}

async function liveSitemapUrls() {
  const indexXml = await fetchText(origin + '/sitemap-index.xml');
  const sitemapUrls = locs(indexXml);
  const out = [];
  for (const sm of sitemapUrls) {
    const xml = await fetchText(sm);
    out.push(...locs(xml));
  }
  return [...new Set(out)];
}

const allUrls = await liveSitemapUrls();
let selected = [];

if (initial || !baseSha) {
  selected = allUrls;
} else {
  const root = 'site-factory/ansan-flower';
  let changed = '';
  try {
    changed = execFileSync('git', ['diff','--name-only',baseSha,'HEAD','--','.'], { encoding:'utf8' });
  } catch {}

  const files = changed.split(/\r?\n/).filter(Boolean);
  const sitewide = files.some(p =>
    p.includes('/src/layouts/') ||
    p.includes('/src/components/') ||
    p.includes('/src/styles/') ||
    p.includes('/src/pages/') ||
    p.includes('/src/config/') ||
    p.endsWith('/src/data/business-truth.json') ||
    p.endsWith('/src/data/products.json') ||
    p.endsWith('/scripts/select_indexnow_urls.mjs') ||
    p.endsWith('/scripts/submit_indexnow.mjs')
  );

  if (sitewide) {
    selected = allUrls;
  } else {
    const currentPath = 'src/data/publish-manifest.json';
    const gitPath = root + '/src/data/publish-manifest.json';
    const current = JSON.parse(readFileSync(currentPath, 'utf8'));
    let previous = { pages: [] };
    try {
      previous = JSON.parse(execFileSync('git', ['show', `${baseSha}:${gitPath}`], { encoding:'utf8' }));
    } catch {}

    const prevMap = new Map((previous.pages || []).map(p => [p.pageKey, p]));
    const curMap = new Map((current.pages || []).map(p => [p.pageKey, p]));
    const candidates = new Set();

    for (const [key, page] of curMap) {
      const old = prevMap.get(key);
      if (!old || old.snapshotId !== page.snapshotId || old.url !== page.url || old.status !== page.status) {
        candidates.add(origin + page.url);
        candidates.add(origin + '/');
        if (page.category) candidates.add(origin + '/' + page.category + '/');
      }
    }
    for (const [key, old] of prevMap) {
      if (!curMap.has(key)) candidates.add(origin + old.url);
    }

    const live = new Set(allUrls);
    selected = [...candidates].filter(url => live.has(url) || !curMap.size);
  }
}

writeFileSync('indexnow-urls.json', JSON.stringify([...new Set(selected)], null, 2) + '\n');
console.log(`IndexNow selection: ${selected.length} URL(s), initial=${initial}`);
