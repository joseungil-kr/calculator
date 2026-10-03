import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';

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

const layout = fs.readFileSync(new URL('../src/layouts/BaseLayout.astro', import.meta.url), 'utf8');
const headerScript = layout.match(/<script is:inline>([\s\S]*?)<\/script>/)[1];

function assertHeaderClearance(source) {
  assert.match(source, /--site-header-min-height:70px/);
  assert.match(source, /\.header-inner\{[^}]*min-height:var\(--site-header-min-height\)/);
  assert.match(source, /@media\(max-width:860px\)\{[^}]+\}?:root\{--site-header-min-height:62px\}/);
  assert.match(source, /\.site-header\{[^}]*border-bottom:1px solid/);
  const clearance = source.match(/html\{scroll-padding-top:calc\(var\(--site-header-height,calc\(var\(--site-header-min-height\) \+ 1px\)\) \+ (\d+)px\)\}/);
  assert.ok(clearance, 'Reserve measured header height, with a shared CSS fallback including the border');
  const focus = source.match(/a:focus-visible\{outline:(\d+)px[^}]*outline-offset:(\d+)px/);
  assert.ok(Number(clearance[1]) > Number(focus[1]) + Number(focus[2]), 'Keep the complete outline below the sticky header');
}

function runHeaderScript({ source = headerScript, observer = true, headerPresent = true, fonts = true } = {}) {
  const writes = [];
  const properties = new Map();
  const resize = new Map();
  const fontEvents = new Map();
  const observers = [];
  let height = 62.666667;
  let fontsReady;
  const header = { dataset: {}, getBoundingClientRect: () => ({ height }) };
  const document = {
    querySelector: selector => selector === '.site-header' && headerPresent ? header : null,
    documentElement: { style: {
      getPropertyValue: name => properties.get(name) || '',
      setProperty: (name, value) => { properties.set(name, value); writes.push({ name, value }); },
    } },
    fonts: fonts ? {
      ready: { then: callback => { fontsReady = callback; } },
      addEventListener: (event, callback) => fontEvents.set(event, callback),
    } : undefined,
  };
  const window = { addEventListener: (event, callback, options) => resize.set(event, { callback, options }) };
  const context = { document, window };
  if (observer) {
    context.ResizeObserver = window.ResizeObserver = class {
      constructor(callback) { this.callback = callback; observers.push(this); }
      observe(target, options) { this.target = target; this.box = options.box; }
    };
  }
  const run = () => vm.runInNewContext(source, context);
  run();
  return { run, writes, properties, resize, fontEvents, observers, header,
    setHeight: value => { height = value; }, ready: () => fontsReady?.() };
}

function assertMeasuredHeader(source = headerScript) {
  const state = runHeaderScript({ source });
  assert.equal(state.properties.get('--site-header-height'), '62.666667px', 'Measure synchronously before main-content is parsed');
  assert.equal(state.observers.length, 1);
  assert.equal(state.observers[0].target, state.header);
  assert.equal(state.observers[0].box, 'border-box');
  for (const height of [70.666667, 126.5, 63]) {
    state.setHeight(height);
    state.observers[0].callback();
    assert.equal(state.properties.get('--site-header-height'), `${height}px`, 'Follow viewport, font/wrapping and shrink changes');
  }
  const count = state.writes.length;
  state.observers[0].callback();
  assert.equal(state.writes.length, count, 'Unchanged geometry must not trigger another style write');
  state.run();
  assert.equal(state.observers.length, 1, 'Do not register duplicate observers');
  assert.ok(state.writes.every(write => write.name === '--site-header-height'), 'Never change bottom clearance or other styles');
}

test('sticky header scrollport reserves both responsive minima, measured height and full outline', () => {
  assertHeaderClearance(css);
  assertMobileFocusClearance(css);
  assert.ok(layout.indexOf('<script is:inline>') > layout.indexOf('</header>'));
  assert.ok(layout.indexOf('</script>', layout.indexOf('<script is:inline>')) < layout.indexOf('<main id="main-content">'));
});

test('header measurement is immediate, fractional, reactive and duplicate-safe without resize feedback', () => {
  assertMeasuredHeader();
});

test('without ResizeObserver, resize and font readiness/completion refresh the measured height', () => {
  const state = runHeaderScript({ observer: false });
  assert.equal(state.properties.get('--site-header-height'), '62.666667px');
  assert.equal(state.resize.get('resize').options.passive, true);
  state.setHeight(71);
  state.resize.get('resize').callback();
  assert.equal(state.properties.get('--site-header-height'), '71px');
  state.setHeight(98.5);
  state.ready();
  assert.equal(state.properties.get('--site-header-height'), '98.5px');
  state.setHeight(114);
  state.fontEvents.get('loadingdone')();
  assert.equal(state.properties.get('--site-header-height'), '114px');
  state.run();
  assert.equal(state.resize.size, 1);
});

test('missing header or font API is safe and leaves CSS fallback intact', () => {
  const absent = runHeaderScript({ headerPresent: false });
  assert.equal(absent.writes.length, 0);
  assert.equal(absent.observers.length, 0);
  assert.equal(runHeaderScript({ observer: false, fonts: false }).properties.get('--site-header-height'), '62.666667px');
});

test('negative: missing top padding, missing border fallback or inadequate outline clearance fails', () => {
  for (const source of [
    css.replace(/html\{scroll-padding-top:[^}]+\}/, ''),
    css.replace('var(--site-header-min-height) + 1px', 'var(--site-header-min-height)'),
    css.replace(/(scroll-padding-top:[^}]+) \+ 8px/, '$1 + 4px'),
  ]) assert.throws(() => assertHeaderClearance(source));
});

test('negative: delayed initial measurement, fixed-height measurement or no resize observation fails', () => {
  for (const source of [
    headerScript.replace('  updateHeaderHeight();', ''),
    headerScript.replace('header.getBoundingClientRect().height', '63'),
    headerScript.replace("new ResizeObserver(updateHeaderHeight).observe(header, { box: 'border-box' });", ''),
    headerScript.replace(' || header.dataset.focusClearanceReady', ''),
  ]) assert.throws(() => assertMeasuredHeader(source));
});
