import {defineConfig} from 'astro/config';
import sitemap from '@astrojs/sitemap';
const site = process.env.SITE_URL || 'https://suwon.fwith.kr';
export default defineConfig({site, output:'static', trailingSlash:'always', integrations:[sitemap({filter: page => !new URL(page).pathname.startsWith('/404')})]});
