import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const css = fs.readFileSync(new URL('../src/styles/global.css', import.meta.url), 'utf8');

// This guards the CSS contract. The release check must also Tab through the
// hosted page: a source assertion cannot prove browser focus visibility.
function assertMobileFocusClearance(source) {
  const mobile = source.slice(source.lastIndexOf('@media(max-width:860px){'));
  assert.match(mobile, /html\{scroll-padding-bottom:calc\(var\(--mobile-order-bar-height\) \+ var\(--mobile-order-safe-area\) \+ (\d+)px\)\}/);
  const clearance = Number(mobile.match(/scroll-padding-bottom:[^}]* \+ (\d+)px/)[1]);
  const focus = source.match(/a:focus-visible\{outline:(\d+)px[^}]*outline-offset:(\d+)px/);
  assert.ok(focus, 'Keep the visible focus outline');
  assert.ok(clearance > Number(focus[1]) + Number(focus[2]), 'Reserve the entire focus outline above the fixed bar');
  assert.match(mobile, /--mobile-order-safe-area:env\(safe-area-inset-bottom,0px\)/);
  assert.match(mobile, /\.mobile-bar a\{min-height:calc\(var\(--mobile-order-bar-height\) \+ var\(--mobile-order-safe-area\)\)/);
  assert.match(mobile, /footer\{padding-bottom:calc\(34px \+ var\(--mobile-order-bar-height\) \+ var\(--mobile-order-safe-area\)\)/);
}

test('mobile focus scrollport reserves the fixed bar, safe area and full outline', () => {
  assertMobileFocusClearance(css);
});

test('negative: footer spacing alone cannot protect keyboard-focused links', () => {
  assert.throws(() => assertMobileFocusClearance(css.replace(/\s*html\{scroll-padding-bottom:[^}]+\}/, '')));
});

test('negative: scroll clearance must include the same device safe area as the bar', () => {
  assert.throws(() => assertMobileFocusClearance(css.replace(/(scroll-padding-bottom:[^}]+) \+ var\(--mobile-order-safe-area\)/, '$1')));
});

test('negative: a focused button without its outline fully visible is insufficient', () => {
  assert.throws(() => assertMobileFocusClearance(css.replace(/(scroll-padding-bottom:[^}]+) \+ 8px/, '$1 + 4px')));
});
