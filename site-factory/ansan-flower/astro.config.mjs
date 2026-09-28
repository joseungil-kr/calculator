import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

const site = process.env.SITE_URL || 'https://ansanflowerdelivery.com';

export default defineConfig({
  site,
  output: 'static',
  integrations: [sitemap()],
  trailingSlash: 'always',
});
