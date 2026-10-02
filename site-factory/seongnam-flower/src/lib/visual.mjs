/** Dedicated visual intent/slot takes precedence over the legacy page-type fallback. */
export function detailIllustration(page, editorial) {
  if (page.assetSlot === 'REAL_PROOF') return null;
  const opening = page.pageType === 'business-opening' || page.visualIntent === 'event_wreath';
  if (!opening) return null;
  // The existing 1:1 editorial illustration is not a wide/split/content asset.
  // Fail rather than silently crop or relabel it for a dedicated slot.
  if (page.assetSlot)
    throw new Error(`No compatible opening illustration for asset slot: ${page.assetSlot}`);
  if (['congrats_wreath', 'funeral_wreath'].includes(page.visualIntent)) return null;
  return editorial.openingWreath;
}
