import {defineConfig} from 'astro/config';
import sitemap from '@astrojs/sitemap';
import config from './src/data/site-config.json' with {type:'json'};
import architecture from './src/data/architecture.json' with {type:'json'};
import {regionalPages} from './src/lib/regional-runtime.mjs';
const site = process.env.SITE_URL || config.previewUrl;
const thinHubs=new Set(architecture.hubs.filter(h=>h.children<3).map(h=>h.url));
export default defineConfig({site, output:'static', trailingSlash:'always', integrations:[sitemap({filter: page => {
  const path=new URL(page).pathname;
  if(path.startsWith('/regions/'))return process.env.SITE_INDEXABLE==='true' && config.productionApproved===true && (path==='/regions/' ? regionalPages.length>=3 : regionalPages.some(p=>p.url===path));
  return !path.startsWith('/404') && !thinHubs.has(path);
}})]});
