import { readFileSync } from 'node:fs';

const origin = (process.env.SITE_ORIGIN || 'https://ansan.fwith.kr').replace(/\/$/, '');
const key = process.env.INDEXNOW_KEY;
const endpoint = process.env.INDEXNOW_ENDPOINT || 'https://searchadvisor.naver.com/indexnow';

if (!key) throw new Error('INDEXNOW_KEY is required.');

const urls = JSON.parse(readFileSync('indexnow-urls.json', 'utf8'));
if (!Array.isArray(urls) || urls.length === 0) {
  console.log('IndexNow: no changed public URLs to submit.');
  process.exit(0);
}

const host = new URL(origin).host;
const keyLocation = `${origin}/${key}.txt`;

for (let i = 0; i < urls.length; i += 10000) {
  const urlList = urls.slice(i, i + 10000);
  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'content-type': 'application/json; charset=utf-8' },
    body: JSON.stringify({ host, key, keyLocation, urlList }),
  });
  const body = await res.text();
  if (![200, 202].includes(res.status)) {
    throw new Error(`IndexNow failed HTTP ${res.status}: ${body.slice(0,500)}`);
  }
  console.log(`IndexNow accepted ${urlList.length} URL(s): HTTP ${res.status}`);
}
