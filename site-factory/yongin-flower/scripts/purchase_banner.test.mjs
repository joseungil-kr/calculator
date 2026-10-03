import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const routes = ['', 'funeral/', 'business/', 'school/', 'event/', 'gift/', 'order/'];
test('every existing home and hub has a real middle phone and official-home order panel', () => {
  for (const route of routes) {
    const html=fs.readFileSync(`dist/${route}index.html`,'utf8');
    assert.equal((html.match(/data-purchase-banner="middle"/g)||[]).length,1,route);
    const panel=html.slice(html.indexOf('data-purchase-banner="middle"')).split('</section>')[0];
    assert.match(panel,/href="tel:18440644"/);
    assert.match(panel,/href="https:\/\/fwith\.co\.kr"/);
    assert.doesNotMatch(panel,/<img\b/);
    assert.equal((html.match(/<h1(?:\s|>)/g)||[]).length,1);
  }
});
