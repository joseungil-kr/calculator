// Presentation only: the frozen Markdown and its displayed blocks stay unchanged.
// Add one purchase point between complete sections, away from the hero and the
// final order section. One is enough alongside the existing hero/footer CTAs.
export function orderBannerBoundary(blocks) {
  const headings = blocks.flatMap((block, index) => block.type === 'h2' ? [index] : []);
  const length = blocks.reduce((total, block) => total + block.text.length, 0);
  if (headings.length < 4 || length < 900) return -1;
  const candidates = headings.slice(2, -1);
  let best = -1;
  let distance = Infinity;
  for (const index of candidates) {
    const before = blocks.slice(0, index).reduce((total, block) => total + block.text.length, 0);
    const difference = Math.abs(before - length / 2);
    if (difference < distance) { best = index; distance = difference; }
  }
  return best;
}
