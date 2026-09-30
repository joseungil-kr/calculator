import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const manifestPath = path.join(root, 'src/data/publish-manifest.json');
const pageMapPath = path.join(root, 'src/data/page-map.json');

function fail(message) {
  console.error('[snapshot] ' + message);
  process.exit(1);
}

if (!fs.existsSync(manifestPath)) fail('publish-manifest.json is missing');
if (!fs.existsSync(pageMapPath)) fail('page-map.json is missing');

const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
const pageMap = JSON.parse(fs.readFileSync(pageMapPath, 'utf8'));

if (manifest.schemaVersion !== 2) fail('unsupported manifest schemaVersion');
if (pageMap.schemaVersion !== 2) fail('unsupported page-map schemaVersion');
if (manifest.snapshotMode !== 'git-frozen') fail('snapshotMode must be git-frozen');
if (!Array.isArray(manifest.pages) || manifest.pages.length === 0) fail('manifest has no pages');
if (!Array.isArray(pageMap.pages)) fail('page map pages must be an array');

const seenPageKeys = new Set();
const seenUrls = new Set();
const mapByPageKey = new Map(pageMap.pages.map((p) => [p.pageKey, p]));

for (const page of manifest.pages) {
  for (const key of ['pageKey','draftKey','sourceRecordId','snapshotId','slug','category','routeType','file','url','status']) {
    if (!page[key]) fail(`manifest page missing ${key}: ${JSON.stringify(page)}`);
  }
  if (!['top_level','category'].includes(page.routeType)) fail(`invalid routeType: ${page.routeType}`);

  const expectedUrl = page.routeType === 'top_level'
    ? `/${page.slug}/`
    : `/${page.category}/${page.slug}/`;
  if (page.url !== expectedUrl) fail(`manifest route mismatch for ${page.pageKey}: ${page.url} != ${expectedUrl}`);

  if (seenPageKeys.has(page.pageKey)) fail(`duplicate pageKey: ${page.pageKey}`);
  if (seenUrls.has(page.url)) fail(`duplicate url: ${page.url}`);
  seenPageKeys.add(page.pageKey);
  seenUrls.add(page.url);

  const filePath = path.join(root, page.file);
  if (!fs.existsSync(filePath)) fail(`content file missing: ${page.file}`);
  const content = fs.readFileSync(filePath, 'utf8');

  const field = (name) => {
    const m = content.match(new RegExp('^' + name + ':\\s*["\\\']?([^"\\\'\\n]+)["\\\']?\\s*$', 'm'));
    return m ? m[1].trim() : null;
  };

  const checks = {
    pageKey: page.pageKey,
    snapshotId: page.snapshotId,
    sourceDraftKey: page.draftKey,
    sourceRecordId: page.sourceRecordId,
    slug: page.slug,
    routeType: page.routeType,
    category: page.category,
  };

  for (const [name, expected] of Object.entries(checks)) {
    const actual = field(name);
    if (actual !== expected) fail(`${page.file}: ${name}=${actual} expected ${expected}`);
  }

  const draftStatus = field('draftStatus');
  if (!['approved','published'].includes(draftStatus)) {
    fail(`${page.file}: draftStatus must be approved or published`);
  }

  const mapped = mapByPageKey.get(page.pageKey);
  if (!mapped) fail(`page-map missing pageKey: ${page.pageKey}`);
  for (const key of ['snapshotId','slug','category','routeType','url','sourceRecordId']) {
    if (mapped[key] !== page[key]) fail(`page-map mismatch for ${page.pageKey}: ${key}`);
  }
}

console.log(`[snapshot] OK: ${manifest.pages.length} frozen page(s), site=${manifest.siteKey}, schema=v2`);
