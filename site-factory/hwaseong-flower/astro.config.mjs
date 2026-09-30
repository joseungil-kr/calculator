import { readFileSync } from 'node:fs';
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

const site = process.env.SITE_URL || 'https://hwaseong.fwith.kr';
const manifest = JSON.parse(readFileSync(new URL('./src/data/publish-manifest.json', import.meta.url), 'utf8'));
const approved = (manifest.pages || []).filter((page) => ['approved', 'published'].includes(page.status));
const hubCategories = ['guide', 'funeral', 'places', 'occasions', 'flower-knowledge', 'order-help'];
const categoryCounts = approved.reduce((acc, page) => {
  acc[page.category] = (acc[page.category] ?? 0) + 1;
  return acc;
}, {});
const noindexHubs = new Set(
  hubCategories.filter((category) => (categoryCounts[category] ?? 0) > 0 && (categoryCounts[category] ?? 0) < 3).map((category) => `/${category}/`)
);

export default defineConfig({
  site,
  output: 'static',
  integrations: [sitemap({ filter: (page) => !noindexHubs.has(new URL(page).pathname) })],
  trailingSlash: 'always',
});
