import {defineConfig} from 'astro/config';
import sitemap from '@astrojs/sitemap';
import architecture from './src/data/architecture.json' with {type:'json'};
import {regionalPages} from './src/lib/regional-runtime.mjs';
const site = process.env.SITE_URL || 'https://suwon.fwith.kr';
export default defineConfig({site, output:'static', trailingSlash:'always', integrations:[sitemap({filter: page => {const path=new URL(page).pathname;if(path.startsWith('/regions/'))return process.env.SITE_INDEXABLE==='true'&&(path==='/regions/'?regionalPages.length>=3:regionalPages.some(p=>p.url===path));return !path.startsWith('/404')&&!architecture.hubs.some(h=>h.url===path&&h.children<3);}})]});
