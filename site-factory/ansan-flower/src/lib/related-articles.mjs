// Automatic links need evidence of a next decision, not a neighbouring category.
// Use the existing intent metadata; never infer a purpose from a venue's name.
const purposePatterns = [
  ['funeral', /근조|장례|조문|추모|condolence|funeral/i],
  ['visit', /병문안|문병|hospital[- ]visit/i],
  ['graduation', /졸업|입학|graduation|school[- ]entrance/i],
  ['opening', /개업|이전|opening[- ]business|business[- ]opening/i],
  ['event', /행사|공연|전시|event|performance/i],
  ['gift', /약속|선물|생일|기념일|감사|프로포즈|승진|gift|anniversary/i],
];
const purposeByType = {
  'funeral-facility': 'funeral',
  hospital: 'visit',
  'station-transit': 'gift',
  'opening-business': 'opening',
  'event-venue': 'event',
};

function purposes(page, includeDescription = false) {
  // A hospital funeral facility is a funeral journey, not a hospital visit.
  if (page.category === 'funeral' || page.pageType === 'funeral-facility') return new Set(['funeral']);
  const intent = [page.primaryKeyword, page.title, page.h1, includeDescription && page.description].filter(Boolean).join(' ');
  const result = new Set(purposePatterns.filter(([, pattern]) => pattern.test(intent)).map(([purpose]) => purpose));
  if (purposeByType[page.pageType]) result.add(purposeByType[page.pageType]);
  return result;
}

/**
 * Explicit reviewed links retain their order and are never topped up.
 * Fallback is deliberately conservative: decision guides only, compatible with
 * the current purpose. Unrecognised or missing intent is not proof of relevance.
 *
 * @template {{ data: Record<string, any> }} T
 * @param {{ articles: T[], architecturePages: Record<string, any>[], current: Record<string, any>, relatedPageKeys?: string[] }} options
 * @returns {T[]}
 */
export function selectRelatedArticles({ articles, architecturePages, current, relatedPageKeys = [] }) {
  const eligible = articles.filter(({ data }) => data.pageKey !== current.pageKey);
  if (relatedPageKeys.length) {
    return [...new Set(relatedPageKeys)].flatMap((key) => {
      const article = eligible.find(({ data }) => data.pageKey === key);
      return article ? [article] : [];
    });
  }

  const architecture = new Map(architecturePages.map((page) => [page.pageKey, page]));
  const metadata = (data) => ({ ...data, ...architecture.get(data.pageKey) });
  const source = metadata(current);
  const sourcePurposes = purposes(source);
  const sourceIsFuneral = sourcePurposes.has('funeral');
  return eligible.flatMap((article) => {
    const target = metadata(article.data);
    // Another facility, meeting point, or regional landing is not an order step.
    if (target.routeType !== 'category' || target.category === 'places' || target.category === 'regions'
      || ['PLACE_LANDING', 'REGION_SERVICE_LANDING', 'HUB'].includes(target.pageRole)
      || ['hospital', 'station-transit', 'funeral-facility', 'event-venue', 'regional-service'].includes(target.pageType)) return [];

    const orderHelp = target.pageType === 'order-help' || target.category === 'order-help';
    const flowerKnowledge = target.pageType === 'flower-knowledge' || target.category === 'flower-knowledge';
    // Message/order guides can have broad titles but recipient-specific advice.
    // Their summary is purpose evidence, not permission to treat them as universal.
    // General care guides may mention example occasions without being about them.
    const targetPurposes = purposes(target, orderHelp);
    // Generic bouquet/care advice is not a substitute for condolence-wreath help.
    if (sourceIsFuneral && !targetPurposes.has('funeral') && !orderHelp) return [];
    if (targetPurposes.size) {
      if ([...targetPurposes].some((purpose) => !sourcePurposes.has(purpose))) return [];
    } else if (!orderHelp && !(flowerKnowledge && sourcePurposes.size && !sourceIsFuneral)) {
      return [];
    }

    const rank = orderHelp ? 0 : targetPurposes.size ? 1 : 2;
    return [{ article, rank }];
  })
    .sort((a, b) => a.rank - b.rank || a.article.data.pageKey.localeCompare(b.article.data.pageKey, 'ko'))
    .map(({ article }) => article);
}
