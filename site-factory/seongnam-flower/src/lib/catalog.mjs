/** Map buyer intent to real catalog families. Unknown intent never inherits wreaths. */
export function productFamilies(page) {
  if(page.pageType==='regional-service'){if(!Array.isArray(page.regionalProductFamilies))throw new Error('Missing regional product binding');return page.regionalProductFamilies;}
  if (page.pageType === 'business-opening') return ['congrats'];
  if (['school-event', 'station-transit'].includes(page.pageType)) return ['bouquet'];
  if (['hospital-visit', 'personal-gift'].includes(page.pageType)) return ['bouquet', 'basket'];
  if (page.category === 'funeral' || page.pageType === 'funeral-facility') return ['funeral'];
  if (page.pageType === 'event-venue') {
    if (page.visualIntent === 'event_wreath') return ['congrats'];
    if (page.visualIntent === 'performance_venue') return ['bouquet'];
    return ['bouquet', 'basket', 'congrats'];
  }
  if (['price-guide', 'message-guide', 'order-help'].includes(page.pageType)) {
    const funeral=/근조/.test(page.primaryKeyword || '');
    const congrats=/축하/.test(page.primaryKeyword || '');
    if ((funeral && page.visualIntent==='congrats_wreath') || (congrats && page.visualIntent==='funeral_wreath'))
      throw new Error('Product visual intent contradicts promised wreath family');
    if (funeral && congrats) return ['funeral','congrats'];
    if (page.visualIntent === 'funeral_wreath' || funeral) return ['funeral'];
    if (page.visualIntent === 'congrats_wreath' || congrats) return ['congrats'];
    return /화환/.test(page.primaryKeyword || '') ? ['funeral', 'congrats'] : ['bouquet', 'basket', 'funeral', 'congrats'];
  }
  return [];
}
export function selectProducts(page, products, limit = 3) {
  if(page.pageType==='regional-service'){if(!Array.isArray(page.regionalProductKeys))throw new Error('Missing regional product binding');return page.regionalProductKeys.map(key=>{const p=products.find(p=>p.key===key);if(!p)throw new Error('Missing registered regional product');return p;}).slice(0,limit);}
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
  if (families.length && families.every(f => ['bouquet', 'basket'].includes(f))) return '전달하기 좋은 꽃선물';
  return '목적에 맞는 꽃 상품 비교';
}

/** Initial selection spans the site's advertised purposes; no price or SKU aliases. */
export function homeProducts(products) {
  const keys = ['funeral-basic', 'congrats-basic', 'funeral-premium', 'congrats-premium', 'funeral-xl', 'congrats-xl'];
  return keys.map(key => products.find(p => p.key === key)).filter(Boolean);
}
