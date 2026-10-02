/**
 * Remove a plain opening paragraph only when the separately rendered answer
 * has exactly the same text. Preserve markup and uncertain entity spellings.
 * @param {string} html
 * @param {string | undefined} firstAnswer
 * @returns {string}
 */
export function removeRepeatedOpeningParagraph(html, firstAnswer) {
  if (typeof firstAnswer !== 'string' || !firstAnswer.trim()) return html;
  const opening = html.match(/^(\s*)<p>([^<]*)<\/p>/);
  if (!opening) return html;
  const raw = opening[2];
  if (/&(?!(?:amp|AMP|lt|LT|gt|GT|quot|QUOT|apos|#(?:\d+|[xX][\da-fA-F]+));)/.test(raw)) return html;
  let certain = true;
  const text = raw.replace(/&([^;]+);/g, (_, entity) => {
    const named = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'" };
    if (entity[0] !== '#') return named[entity.toLowerCase()];
    const hex = entity[1] === 'x' || entity[1] === 'X';
    const code = Number.parseInt(entity.slice(hex ? 2 : 1), hex ? 16 : 10);
    if (code < 0x20 || code > 0x10ffff || (code >= 0x7f && code <= 0x9f)
      || (code >= 0xd800 && code <= 0xdfff) || (code >= 0xfdd0 && code <= 0xfdef)
      || (code & 0xfffe) === 0xfffe) {
      certain = false;
      return '';
    }
    return String.fromCodePoint(code);
  });
  if (!certain || text !== firstAnswer) return html;
  return opening[1] + html.slice(opening[0].length);
}
