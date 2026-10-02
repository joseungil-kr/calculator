import {productFamilies} from './catalog.mjs';

// Resolve existing approved routes by purpose. Reading about another venue is
// useful context, but is never a purchase stage for the current destination.
export function nextSteps(page, pages) {
  const families = productFamilies(page);
  const wreathOnly = families.length > 0 && families.every(f => ['funeral', 'congrats'].includes(f));
  const byIntent = intent => pages.find(p => p.category === 'order' && p.visualIntent === intent);
  const price = pages.find(p => p.pageType === 'price-guide' && p.category === page.category)
    || pages.find(p => p.pageType === 'price-guide' && p.category === 'order');
  const candidates = [price, byIntent('order_address')];
  if (wreathOnly) candidates.push(byIntent('wreath_message'), byIntent('wreath_order'));
  else candidates.push(byIntent('same_day_order'));
  return [...new Set(candidates)].filter(p => p && p.pageKey !== page.pageKey);
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
