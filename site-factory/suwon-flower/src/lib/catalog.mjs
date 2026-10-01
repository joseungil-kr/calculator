/** Map buyer intent to real catalog families. Unknown intent never inherits wreaths. */
export function productFamilies(page) {
  if (page.pageType === 'business-opening') return ['congrats'];
  if (['school-event', 'station-transit'].includes(page.pageType)) return ['bouquet'];
  if (['hospital-visit', 'personal-gift'].includes(page.pageType)) return ['bouquet', 'basket'];
  if (page.category === 'funeral' || page.pageType === 'funeral-facility') return ['funeral'];
  if (page.pageType === 'event-venue') return page.visualIntent === 'event_wreath' ? ['congrats'] : ['bouquet', 'basket', 'congrats'];
  if (['price-guide', 'message-guide', 'order-help'].includes(page.pageType)) return /화환/.test(page.primaryKeyword || '') ? ['funeral', 'congrats'] : ['funeral', 'congrats', 'bouquet'];
  return [];
}
export function selectProducts(page, products, limit = 3) {
  const families = productFamilies(page);
  const rows = families.flatMap(family => products.filter(p => p.family === family));
  if (families.length === 1) return rows.slice(0, limit);
  const first = families.map(family => rows.find(p => p.family === family)).filter(Boolean);
  return [...first, ...rows.filter(p => !first.includes(p))].slice(0, limit);
}
export function productHeading(page) {
  const families = productFamilies(page);
  if (families.length === 1 && families[0] === 'funeral') return '근조화환 상품과 가격';
  if (families.length === 1 && families[0] === 'congrats') return '축하화환 상품과 가격';
  if (families.every(f => ['bouquet', 'basket'].includes(f))) return '전달하기 좋은 꽃선물';
  return '목적에 맞는 꽃 상품 비교';
}
