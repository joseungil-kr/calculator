import type { APIRoute } from 'astro';
import {site} from '../config/site';
export const GET: APIRoute = () => new Response(`User-agent: *\n${site.indexable ? 'Allow: /' : 'Disallow: /'}\n${site.indexable ? `Sitemap: ${site.domain}/sitemap-index.xml\n` : ''}`, {headers:{'Content-Type':'text/plain; charset=utf-8'}});
