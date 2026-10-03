/** Geographic routing metadata is never publication or content-quality evidence. */
export function validateRegionDefinition(coverage) {
  const fail = reason => { throw new Error(`Region coverage: ${reason}`); };
  if (coverage?.schemaVersion !== 1 || coverage.siteKey !== 'goyang-flower-v2'
    || coverage.unitBasis !== 'legal' || !coverage.scopeKey) fail('unsupported site or unit basis');
  const route = {routeType:'category', category:'regions', pageType:'regional-service', pageRole:'REGION_SERVICE_LANDING', parentHub:'/regions/'};
  for (const [key, value] of Object.entries(route)) if (coverage.route?.[key] !== value) fail(`unsupported ${key}`);
  if (!coverage.districts?.length || !coverage.units?.length || !coverage.administrativeCrosswalk?.length) fail('empty official definition');
  if (!/^\d{4}-\d{2}-\d{2}$/.test(coverage.verifiedAt || '')
    || !coverage.officialSourceUrls?.length) fail('missing official provenance');
  for (const source of coverage.officialSourceUrls) {
    const url = new URL(source);
    if (url.protocol !== 'https:' || !(url.hostname === 'goyang.go.kr' || url.hostname.endsWith('.goyang.go.kr'))
      || url.username || url.password) fail('untrusted official source');
  }
  const unique = (rows, key) => {
    const values = rows.map(row => row[key]);
    if (values.some(value => !value) || new Set(values).size !== values.length) fail(`duplicate/missing ${key}`);
  };
  for (const key of ['key', 'name']) unique(coverage.districts, key);
  for (const district of coverage.districts) {
    if (!/^[a-z][a-z0-9-]*$/.test(district.key)
      || !coverage.officialSourceUrls.includes(district.sourceUrl)) fail('unsafe district or missing source');
  }
  for (const key of ['unitKey', 'pageKey', 'url', 'slug']) unique(coverage.units, key);
  unique(coverage.administrativeCrosswalk, 'unitKey');
  const districts = new Set(coverage.districts.map(d => d.key));
  const units = new Map(coverage.units.map(u => [u.unitKey, u]));
  for (const unit of coverage.units) {
    if (!districts.has(unit.districtKey) || !unit.name || !/^[a-z0-9-]+$/.test(unit.slug)
      || unit.url !== `/regions/${unit.slug}/`) fail(`unsafe unit route ${unit.unitKey}`);
  }
  const represented = new Set();
  for (const admin of coverage.administrativeCrosswalk) {
    if (!districts.has(admin.districtKey) || !admin.name || !admin.relations?.length) fail(`invalid administrative unit ${admin.unitKey}`);
    unique(admin.relations, 'legalUnitKey');
    for (const relation of admin.relations) {
      const unit = units.get(relation.legalUnitKey);
      if (!unit || unit.districtKey !== admin.districtKey || !['whole', 'partial'].includes(relation.scope)) fail(`invalid crosswalk ${admin.unitKey}`);
      represented.add(unit.unitKey);
    }
  }
  if (represented.size !== units.size) fail('legal unit lacks administrative relation');
  return coverage;
}

export function regionUnit(page, coverage) {
  if (page.category !== 'regions' && page.pageType !== 'regional-service') return null;
  const unit = coverage.units.find(unit => unit.pageKey === page.pageKey);
  if (!unit || page.category !== 'regions' || page.pageType !== 'regional-service'
    || page.routeType !== 'category' || page.url !== unit.url || page.slug !== unit.slug
    || page.status !== 'approved' || page.approvalVerified !== true || !page.snapshotId) {
    throw new Error(`Region route or approval mismatch: ${page.pageKey}`);
  }
  return unit;
}

/** Return only actual approved routes; planned units never become links. */
export function regionGroups(pages, coverage) {
  validateRegionDefinition(coverage);
  const entries = pages.map(page => ({page, unit: regionUnit(page, coverage)})).filter(entry => entry.unit);
  return coverage.districts.map(district => ({...district,
    items: entries.filter(entry => entry.unit.districtKey === district.key),
    administrativeUnits: coverage.administrativeCrosswalk.filter(admin => admin.districtKey === district.key)
  })).filter(district => district.items.length > 0);
}

export function validateRegionalGraph(pages, architecture, coverage) {
  validateRegionDefinition(coverage);
  if (architecture.siteKey !== coverage.siteKey) throw new Error('Region site identity mismatch');
  const regional = pages.filter(page => page.category === 'regions' || page.pageType === 'regional-service');
  for (const page of regional) {
    regionUnit(page, coverage);
    const node = architecture.pages.find(node => node.pageKey === page.pageKey);
    if (node?.pageRole !== 'REGION_SERVICE_LANDING' || node.parentHub !== '/regions/'
      || node.localizationPolicy !== 'local-required' || node.routeType !== 'category') {
      throw new Error(`Region semantics mismatch: ${page.pageKey}`);
    }
  }
  return {plannedUnits: coverage.units.length, publishedRegionalPages: regional.length};
}
