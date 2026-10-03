/** An explicit reviewed slot takes priority over a legacy page-type fallback. */
export function detailIllustration(page, editorial) {
  if (page.assetSlot === 'REAL_PROOF' || page.assetSlot === 'NONE') return null;
  // This template has real catalog photography and one square editorial asset.
  // Other dedicated slots need a separately reviewed adapter, not a guessed crop.
  if (page.assetSlot) throw new Error(`No compatible detail asset for slot: ${page.assetSlot}`);
  if (['congrats_wreath', 'funeral_wreath'].includes(page.visualIntent)) return null;
  return page.pageType === 'business-opening' || page.visualIntent === 'event_wreath'
    ? editorial.openingWreath : null;
}
