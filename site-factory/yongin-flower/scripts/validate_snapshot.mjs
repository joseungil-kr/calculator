import fs from 'node:fs';
import path from 'node:path';
const root=process.cwd();
const manifestPath=path.join(root,'src/data/publish-manifest.json');
const pageMapPath=path.join(root,'src/data/page-map.json');
function fail(m){console.error('[snapshot] '+m);process.exit(1);}
if(!fs.existsSync(manifestPath))fail('publish-manifest.json is missing');
if(!fs.existsSync(pageMapPath))fail('page-map.json is missing');
const manifest=JSON.parse(fs.readFileSync(manifestPath,'utf8'));
const pageMap=JSON.parse(fs.readFileSync(pageMapPath,'utf8'));
if(manifest.schemaVersion!==2)fail('unsupported manifest schemaVersion');
if(pageMap.schemaVersion!==2)fail('unsupported page-map schemaVersion');
if(manifest.snapshotMode!=='git-frozen')fail('snapshotMode must be git-frozen');
if(!Array.isArray(manifest.pages))fail('manifest pages must be an array');
if(!Array.isArray(pageMap.pages))fail('page map pages must be an array');
const production=process.env.SITE_INDEXABLE==='true'||fs.existsSync('production-indexing.enabled');
if(manifest.pages.length===0){
  if(production)fail('production manifest has no pages');
  console.log('[snapshot] OK: staging bootstrap with 0 frozen pages');
  process.exit(0);
}
const seenPageKeys=new Set(),seenUrls=new Set(),mapByPageKey=new Map(pageMap.pages.map((p)=>[p.pageKey,p]));
for(const page of manifest.pages){
  for(const key of ['pageKey','draftKey','sourceRecordId','snapshotId','slug','category','routeType','file','url','status'])if(!page[key])fail(`manifest page missing ${key}`);
  const expectedUrl=`/${page.category}/${page.slug}/`;
  if(page.url!==expectedUrl)fail(`manifest route mismatch for ${page.pageKey}`);
  if(seenPageKeys.has(page.pageKey)||seenUrls.has(page.url))fail(`duplicate pageKey/url: ${page.pageKey}`);
  seenPageKeys.add(page.pageKey);seenUrls.add(page.url);
  const filePath=path.join(root,page.file);if(!fs.existsSync(filePath))fail(`content file missing: ${page.file}`);
  const content=fs.readFileSync(filePath,'utf8');
  const field=(name)=>content.match(new RegExp('^'+name+':\\s*["\\\']?([^"\\\'\\n]+)["\\\']?\\s*$','m'))?.[1]?.trim()??null;
  for(const [name,expected] of Object.entries({pageKey:page.pageKey,snapshotId:page.snapshotId,sourceDraftKey:page.draftKey,sourceRecordId:page.sourceRecordId,slug:page.slug,routeType:page.routeType,category:page.category}))if(field(name)!==expected)fail(`${page.file}: ${name} mismatch`);
  if(!['approved','published'].includes(field('draftStatus')))fail(`${page.file}: invalid draftStatus`);
  const mapped=mapByPageKey.get(page.pageKey);if(!mapped)fail(`page-map missing pageKey: ${page.pageKey}`);
}
console.log(`[snapshot] OK: ${manifest.pages.length} frozen page(s), site=${manifest.siteKey}`);
