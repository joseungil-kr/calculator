import assert from 'node:assert/strict';
import test from 'node:test';
import { removeRepeatedOpeningParagraph } from '../src/lib/article-opening.mjs';

const answer = '빈소와 상주 성함을 확인한 뒤 주문해 주세요.';
const rest = '\n<h2 id="order">주문 정보</h2><p><a href="tel:18440644">전화 주문</a></p><ul><li>공식 출처 확인</li></ul>';
test('removes only the identical plain lead while preserving the exact remaining HTML', () => {
  assert.equal(removeRepeatedOpeningParagraph(`<p>${answer}</p>${rest}`, answer), rest);
});
test('preserves existing leading whitespace and the remaining document order', () => {
  assert.equal(removeRepeatedOpeningParagraph(`\n  <p>${answer}</p>${rest}`, answer), '\n  ' + rest);
});
test('matches supported escaped plain text without interpreting it as markup', () => {
  assert.equal(removeRepeatedOpeningParagraph('<p>문의 &amp; 안내 &lt;확인&gt; &quot;주문&quot; &#39;문구&#39; &#xAC00;</p>' + rest, '문의 & 안내 <확인> "주문" \'문구\' 가'), rest);
});
test('does not remove later repeated paragraphs', () => {
  assert.equal(removeRepeatedOpeningParagraph(`<p>${answer}</p><p>${answer}</p>${rest}`, answer), `<p>${answer}</p>${rest}`);
});
for (const value of [undefined, '', '   ']) {
  test(`absent or blank first answer preserves output: ${String(value)}`, () => {
    const html = `<p>${answer}</p>${rest}`;
    assert.equal(removeRepeatedOpeningParagraph(html, value), html);
  });
}
for (const [name, lead] of Object.entries({
  'different text': '<p>배송지부터 확인해 주세요.</p>',
  'different whitespace': `<p> ${answer}</p>`,
  'link': `<p><a href="https://fwith.co.kr">${answer}</a></p>`,
  'strong emphasis': `<p><strong>${answer}</strong></p>`,
  'emphasis': `<p><em>${answer}</em></p>`,
  'inline code': `<p><code>${answer}</code></p>`,
  'line break': `<p>${answer}<br></p>`,
  'image': `<p>${answer}<img src="/order.webp" alt="주문"></p>`,
  'span': `<p><span>${answer}</span></p>`,
  'comment': `<p>${answer}<!-- preserve --></p>`,
  'paragraph attributes': `<p class="intro">${answer}</p>`,
  'leading heading': `<h2>먼저 확인</h2><p>${answer}</p>`,
  'leading list': `<ul><li><p>${answer}</p></li></ul>`,
  'leading comment': `<!-- preserve --><p>${answer}</p>`,
  'unclosed paragraph': `<p>${answer}`
})) {
  test(`preserves ${name}`, () => {
    const html = lead + rest;
    assert.equal(removeRepeatedOpeningParagraph(html, answer), html);
  });
}
for (const [raw, answerText] of [
  ['&copy;', '&copy;'], ['&APOS;', "'"], ['&#128;', '\u0080'],
  ['&#0;', '\u0000'], ['&#xD800;', '\ud800'], ['&#99999999;', ''], ['&amp', '&']
]) {
  test(`preserves uncertain entity ${raw}`, () => {
    const html = `<p>${raw}</p>${rest}`;
    assert.equal(removeRepeatedOpeningParagraph(html, answerText), html);
  });
}
