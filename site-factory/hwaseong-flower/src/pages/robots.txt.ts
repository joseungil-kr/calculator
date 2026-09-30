import { siteConfig } from '../config/site';

export const prerender = true;

export function GET() {
  const body = siteConfig.indexable
    ? `User-agent: *\nAllow: /\n\nSitemap: ${siteConfig.siteUrl.replace(/\/$/, '')}/sitemap-index.xml\n`
    : 'User-agent: *\nDisallow: /\n';

  return new Response(body, {
    headers: {
      'Content-Type': 'text/plain; charset=utf-8',
    },
  });
}
