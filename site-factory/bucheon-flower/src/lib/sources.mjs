export const sourceTypeLabels = Object.freeze({
  official: '공공·기관', business: '사업자', facility: '시설',
  education: '교육기관', professional: '전문자료', reference: '참고자료',
});

// The reviewed array is authoritative; only older pages without it use source.
// Never normalize, deduplicate, reorder, or silently drop a reviewed source.
export function pageSources(page) {
  const sources = page.sources == null ? (page.source ? [page.source] : []) : page.sources;
  if (!Array.isArray(sources)) throw new Error('Page sources must be an array');
  for (const source of sources) {
    let url;
    try { url = new URL(source?.url); } catch { throw new Error('Invalid source HTTPS URL'); }
    if (url.protocol !== 'https:' || !url.hostname || url.username || url.password ||
        source.url !== source.url.trim() || /[\u0000-\u0020\u007f\\]/.test(source.url)) {
      throw new Error('Source must be an HTTPS URL without credentials or control characters');
    }
    if (typeof source.name !== 'string' || !source.name.trim() ||
        !Object.hasOwn(sourceTypeLabels, source.type) ||
        typeof source.verifiedAt !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(source.verifiedAt)) {
      throw new Error('Source name, supported type, and verification date are required');
    }
  }
  return sources;
}
