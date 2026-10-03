import truth from '../data/business-truth.json';
import architecture from '../data/architecture.json';
import pages from '../data/pages.json';
import config from '../data/site-config.json';
const domain = (import.meta.env.SITE_URL || config.previewUrl).replace(/\/$/, '');
export const site = {
  brand: truth.brand, region: config.region, domain,
  indexable: import.meta.env.SITE_INDEXABLE === 'true' && config.productionApproved === true,
  phone: truth.phone, phoneHref: truth.phoneHref, orderUrl: truth.onlineOrderUrl,
  phoneOrderHours: truth.phoneOrderHours.replace('-', '~'), onlineOrderHours: truth.onlineOrderHours,
  orderHours: `전화 ${truth.phoneOrderHours.replace('-', '~')} · 온라인 ${truth.onlineOrderHours} 접수`,
  deliveryNotice: truth.deliveryNotice, productVariationNotice: truth.productVariationNotice,
  naverVerification: config.naverVerification || ''
};
const publishedPages = pages as {category:string}[];
export const groups = architecture.hubs.filter(h => publishedPages.some(p => p.category === h.category)).map(h => ({cat: h.category, label: h.label, url: h.url}));
export const serviceGroups = groups.filter(group => group.cat !== 'regions');
export const menuGroups = architecture.hubs.filter(h => publishedPages.filter(p => p.category === h.category).length >= 5).map(h => ({cat: h.category, label: h.label, url: h.url}));
