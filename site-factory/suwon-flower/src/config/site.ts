import truth from '../data/business-truth.json';
import architecture from '../data/architecture.json';
import pages from '../data/pages.json';
const domain = (import.meta.env.SITE_URL || 'https://suwon.fwith.kr').replace(/\/$/, '');
export const site = {
  brand: truth.brand, region: '수원', domain,
  indexable: import.meta.env.SITE_INDEXABLE === 'true',
  phone: truth.phone, phoneHref: truth.phoneHref, orderUrl: truth.onlineOrderUrl,
  phoneOrderHours: truth.phoneOrderHours.replace('-', '~'),
  onlineOrderHours: truth.onlineOrderHours,
  orderHours: `전화 ${truth.phoneOrderHours.replace('-', '~')} · 온라인 ${truth.onlineOrderHours} 접수`,
  deliveryNotice: truth.deliveryNotice, productVariationNotice: truth.productVariationNotice,
  naverVerification: '80fedf144567fea99fe833d2937731a190854c41'
};
export const groups = architecture.hubs.filter(h => pages.some(p => p.category === h.category)).map(h => ({cat: h.category, label: h.label, url: h.url}));

// Region menu threshold is independent of the six existing service menus.
export const regionalMenuEligible = (pages as {category:string}[]).filter(p=>p.category==='regions').length>=5;
