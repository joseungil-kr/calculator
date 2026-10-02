import {productFamilies} from './catalog.mjs';

// Resolve existing approved routes by purpose. Reading about another venue is
// useful context, but is never a purchase stage for the current destination.
export function nextSteps(page, pages) {
  const families = productFamilies(page);
  if (!families.length) return [];
  const wreathOnly = families.length > 0 && families.every(f => ['funeral', 'congrats'].includes(f));
  const approved = pages.filter(p => p.status === 'approved' && p.approvalVerified === true && p.snapshotId
    && p.pageKey !== page.pageKey && p.url !== page.url
    && ['order', page.category].includes(p.category)
    && ['price-guide', 'message-guide', 'order-help'].includes(p.pageType)
    && families.every(family => productFamilies(p).includes(family)));
  // Prefer the same scope; never choose a different family just because it
  // happens to be the first price guide in the catalog.
  const ranked = [...approved].sort((a,b) =>
    Number(productFamilies(a).length !== families.length) - Number(productFamilies(b).length !== families.length)
    || Number(a.category !== page.category) - Number(b.category !== page.category));
  const byIntent = (intent, type) => ranked.find(p => p.pageType === type && p.visualIntent === intent);
  // A price decision leads to ordering help, not another price-guide loop.
  const price = page.pageType === 'price-guide' ? undefined : ranked.find(p => p.pageType === 'price-guide');
  const candidates = [price, byIntent('order_address','order-help')];
  if (wreathOnly) candidates.push(byIntent('wreath_message','message-guide'),
    byIntent('wreath_delivery','order-help'), byIntent('wreath_order','order-help'));
  else candidates.push(byIntent('same_day_order','order-help'));
  // If no suitable approved guide exists, the template's real phone/order CTA
  // stays available. Venue reading is never inserted as an ordering stage.
  return [...new Set(candidates)].filter(Boolean);
}

export function relatedReading(page, pages) {
  const next = new Set(nextSteps(page, pages).map(p => p.pageKey));
  return (page.relatedKeys || []).map(key => pages.find(p => p.pageKey === key))
    .filter(p => p && p.pageKey !== page.pageKey && !next.has(p.pageKey)
      && p.category === page.category
      && (page.category !== 'gift' || p.pageType === page.pageType)
      && (page.category !== 'event' || p.visualIntent === page.visualIntent)
      && productFamilies(p).some(f => productFamilies(page).includes(f)));
}
