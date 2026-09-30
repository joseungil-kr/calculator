import { readFileSync } from 'node:fs';
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

const site = process.env.SITE_URL || 'https://ansan.fwith.kr';
const manifest = JSON.parse(readFileSync(new URL('./src/data/publish-manifest.json', import.meta.url), 'utf8'));
const architecture = JSON.parse(readFileSync(new URL('./src/data/architecture.json', import.meta.url), 'utf8'));
const approved = (manifest.pages || []).filter((page) => ['approved', 'published'].includes(page.status));
const hubCategories = ['guide', 'funeral', 'places', 'occasions', 'flower-knowledge', 'order-help'];
const activeArchitecture = (architecture.pages || []).filter(
  (page) => page.sitemapIndexable !== false && page.status !== 'merged'
);
const activePageKeys = new Set(activeArchitecture.map((page) => page.pageKey));
const detailPages = approved.filter(
  (page) => page.routeType === 'category' && activePageKeys.has(page.pageKey)
);
const categoryCounts = detailPages.reduce((acc, page) => {
  acc[page.category] = (acc[page.category] ?? 0) + 1;
  return acc;
}, {});
const noindexHubs = new Set(
  hubCategories.filter((category) => (categoryCounts[category] ?? 0) > 0 && (categoryCounts[category] ?? 0) < 3).map((category) => `/${category}/`)
);
const knownArticlePaths = new Set((manifest.pages || []).map((page) => page.url));
const indexableArticlePaths = new Set(activeArchitecture.map((page) => page.url));
const blockedArchitecturePaths = new Set(
  (architecture.pages || [])
    .filter((page) => page.sitemapIndexable === false || page.status === 'merged')
    .map((page) => page.url)
);

export default defineConfig({
  site,
  output: 'static',
  integrations: [sitemap({ filter: (page) => {
    const pathname = new URL(page).pathname;
    if (noindexHubs.has(pathname)) return false;
    if (blockedArchitecturePaths.has(pathname)) return false;
    if (knownArticlePaths.has(pathname)) return indexableArticlePaths.has(pathname) || !architecture.pages.some((item) => item.url === pathname);
    return true;
  } })],
  trailingSlash: 'always',
});
