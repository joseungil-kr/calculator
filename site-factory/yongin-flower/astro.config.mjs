import { readFileSync, existsSync } from 'node:fs';
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

import {regionalPages} from './src/lib/regional-runtime.mjs';
const site = process.env.SITE_URL || 'https://yongin.fwith.kr';
const manifest = JSON.parse(readFileSync(new URL('./src/data/publish-manifest.json', import.meta.url), 'utf8'));
const architecture = JSON.parse(readFileSync(new URL('./src/data/architecture.json', import.meta.url), 'utf8'));
const hubCategories = ['funeral', 'business', 'school', 'event', 'gift', 'order', 'regions'];
const activeArchitecture = (architecture.pages || []).filter(
  (page) => page.sitemapIndexable !== false && page.status !== 'merged'
);
const activePageKeys = new Set(activeArchitecture.map((page) => page.pageKey));
const approved = (manifest.pages || []).filter((page) => ['approved', 'published'].includes(page.status));
const detailPages = approved.filter((page) => page.routeType === 'category' && activePageKeys.has(page.pageKey));
const categoryCounts = detailPages.reduce((acc, page) => {
  acc[page.category] = (acc[page.category] ?? 0) + 1;
  return acc;
}, {});
const noindexHubs = new Set(
  hubCategories
    .filter((category) => (categoryCounts[category] ?? 0) > 0 && (categoryCounts[category] ?? 0) < 3)
    .map((category) => `/${category}/`)
);
const knownArticlePaths = new Set((manifest.pages || []).map((page) => page.url));
const indexableArticlePaths = new Set(activeArchitecture.map((page) => page.url));

export default defineConfig({
  site,
  output: 'static',
  integrations: [sitemap({ filter: (page) => {
    const pathname = new URL(page).pathname;
    if (pathname.startsWith('/regions/')) return (process.env.SITE_INDEXABLE === 'true' || (process.env.SITE_INDEXABLE !== 'false' && existsSync('production-indexing.enabled'))) && (pathname==='/regions/' ? regionalPages.length>=3 : regionalPages.some(p=>p.url===pathname));
    if (noindexHubs.has(pathname)) return false;
    if (knownArticlePaths.has(pathname)) return indexableArticlePaths.has(pathname);
    return true;
  } })],
  trailingSlash: 'always',
});
