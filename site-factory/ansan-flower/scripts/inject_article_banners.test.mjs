import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const business = JSON.parse(fs.readFileSync(path.join(scriptDir, '../src/data/business-truth.json'), 'utf8'));
const bannerPattern = /\n<figure class="content-order-banner"[\s\S]*?<\/figure>/g;
function fixture(chars = 2400) {
  return `<html><head><title>꽃 주문 준비 안내</title><meta name="description" content="${'주문 전에 확인할 정보입니다. '.repeat(5)}"><link rel="canonical" href="https://example.com/article/"><meta name="robots" content="index,follow"></head><body data-snapshot-id="unchanged-frozen-snapshot"><h1>꽃 주문 안내</h1><h2>확인 정보</h2><a href="/">홈</a><article class="prose"><p>${'가'.repeat(chars)}</p><section class="source-list"><h2>참고 출처</h2><p>${'출처'.repeat(1500)}</p></section></article></body></html>`;
}
function setup(t, html = fixture(), truth = business) {
  const cwd = fs.mkdtempSync(path.join(os.tmpdir(), 'article-cta-'));
  t.after(() => fs.rmSync(cwd, { recursive: true, force: true }));
  fs.mkdirSync(path.join(cwd, 'src/data'), { recursive: true });
  fs.mkdirSync(path.join(cwd, 'dist/article'), { recursive: true });
  fs.writeFileSync(path.join(cwd, 'src/data/business-truth.json'), JSON.stringify(truth));
  const file = path.join(cwd, 'dist/article/index.html');
  fs.writeFileSync(file, html);
  const run = (script) => spawnSync(process.execPath, [path.join(scriptDir, script)], {
    cwd, encoding: 'utf8', env: { ...process.env, SITE_URL: 'https://example.com', SITE_INDEXABLE: 'true' }
  });
  return { cwd, file, run, read: () => fs.readFileSync(file, 'utf8') };
}

for (const [chars, count] of [[300, 1], [1199, 1], [1200, 2], [2199, 2], [2200, 3], [3200, 3]]) {
  test(`injects ${count} accessible CTA(s) for ${chars} body characters without changing frozen HTML`, (t) => {
    const original = fixture(chars);
    const f = setup(t, original);
    const result = f.run('inject_article_banners.mjs');
    assert.equal(result.status, 0, result.stderr);
    const html = f.read();
    const banners = [...html.matchAll(bannerPattern)].map(m => m[0]);
    assert.equal(banners.length, count);
    assert.equal(html.replace(bannerPattern, ''), original);
    for (const banner of banners) {
      assert.match(banner, /<figcaption>꽃 주문 안내<\/figcaption>/);
      assert.ok(banner.includes(`<a href="${business.phoneHref}">전화 주문 ${business.phone}</a>`));
      assert.ok(banner.includes(`<a href="${business.onlineOrderUrl}" rel="noopener">온라인 주문</a>`));
      assert.doesNotMatch(banner, /<img\b|order-banner-0[123]\.webp|최저가/);
    }
    assert.equal(f.run('inject_article_banners.mjs').status, 0);
    assert.equal(f.read(), html, 'repeated injection is byte-identical');
  });
}

test('leaves non-snapshot and non-prose pages unchanged', (t) => {
  for (const original of [fixture().replace('data-snapshot-id=', 'data-unrelated='), fixture().replace('class="prose"', 'class="other"')]) {
    const f = setup(t, original);
    assert.equal(f.run('inject_article_banners.mjs').status, 0);
    assert.equal(f.read(), original);
  }
});

test('escapes business display text and attributes', (t) => {
  const f = setup(t, fixture(), { ...business, phoneOrderHours: '"예약" <문의> & 안내', onlineOrderUrl: 'https://fwith.co.kr/?a=1&b="quoted"' });
  assert.equal(f.run('inject_article_banners.mjs').status, 0);
  const html = f.read();
  assert.ok(html.includes('&quot;예약&quot; &lt;문의&gt; &amp; 안내'));
  assert.ok(html.includes('href="https://fwith.co.kr/?a=1&amp;b=&quot;quoted&quot;"'));
  assert.doesNotMatch(html, /<em>|<문의>/);
});

for (const field of ['phone', 'phoneHref', 'phoneOrderHours', 'onlineOrderUrl', 'onlineOrderHours']) {
  for (const value of [undefined, null, '', '   ', 42]) {
    test(`rejects invalid required business ${field}: ${String(value)}`, (t) => {
      const original = fixture();
      const f = setup(t, original, { ...business, [field]: value });
      assert.equal(f.run('inject_article_banners.mjs').status, 1);
      assert.equal(f.read(), original, 'invalid truth must not write partial CTA output');
      assert.equal(f.run('qa_seo_score.mjs').status, 1);
    });
  }
}
for (const [name, truth] of Object.entries({
  'non-telephone href': { phoneHref: 'javascript:alert(1)' },
  'telephone mismatch': { phoneHref: 'tel:18441234' },
  'telephone markup': { phone: '<em>1844-0644</em>' },
  'insecure order URL': { onlineOrderUrl: 'http://fwith.co.kr' },
  'script order URL': { onlineOrderUrl: 'javascript:alert(1)' },
  'relative order URL': { onlineOrderUrl: '/order/' },
  'credential-bearing order URL': { onlineOrderUrl: 'https://user:pass@fwith.co.kr' },
  'whitespace order URL': { onlineOrderUrl: ' https://fwith.co.kr' }
})) {
  test(`rejects ${name}`, (t) => {
    const original = fixture();
    const f = setup(t, original, { ...business, ...truth });
    assert.equal(f.run('inject_article_banners.mjs').status, 1);
    assert.equal(f.read(), original);
    assert.equal(f.run('qa_seo_score.mjs').status, 1);
  });
}

test('build SEO QA accepts the accessible CTA contract', (t) => {
  const f = setup(t);
  assert.equal(f.run('inject_article_banners.mjs').status, 0);
  const result = f.run('qa_seo_score.mjs');
  assert.equal(result.status, 0, result.stdout + result.stderr);
});

test('CTA text does not increase the article content score', (t) => {
  const original = fixture(660).replace('출처'.repeat(1500), '');
  const results = [business, { ...business, phoneOrderHours: '안내'.repeat(600) }].map(truth => {
    const f = setup(t, original, truth);
    assert.equal(f.run('inject_article_banners.mjs').status, 0);
    return f.run('qa_seo_score.mjs');
  });
  assert.equal(results[0].status, results[1].status);
  assert.equal(results[0].stdout.match(/average=(\d+)/)[1], results[1].stdout.match(/average=(\d+)/)[1]);
});

const mutations = {
  'missing telephone CTA': html => html.replaceAll(`href="${business.phoneHref}"`, 'href="#"'),
  'missing online CTA': html => html.replaceAll(`href="${business.onlineOrderUrl}"`, 'href="#"'),
  'empty accessible telephone label': html => html.replaceAll(`전화 주문 ${business.phone}</a>`, '</a>'),
  'unsupported lowest-price claim': html => html.replace('<figcaption>꽃 주문 안내', '<figcaption>최저가 꽃 주문 안내'),
  ...Object.fromEntries(['01', '02', '03'].map(number => [`old image ${number} reintroduced`, html => html.replace('</figcaption>', `</figcaption><img src="/images/banners/order-banner-${number}.webp" alt="배너">`)])),
  'duplicate banner number': html => html.replace('data-order-banner="2"', 'data-order-banner="1"'),
  'missing CTA': html => html.replace(/\n<figure class="content-order-banner"[\s\S]*?<\/figure>/, '')
};
for (const [name, mutate] of Object.entries(mutations)) {
  test(`build SEO QA rejects ${name}`, (t) => {
    const f = setup(t);
    assert.equal(f.run('inject_article_banners.mjs').status, 0);
    fs.writeFileSync(f.file, mutate(f.read()));
    const result = f.run('qa_seo_score.mjs');
    assert.equal(result.status, 1, result.stdout + result.stderr);
  });
}
