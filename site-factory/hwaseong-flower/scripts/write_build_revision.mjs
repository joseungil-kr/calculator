import { execSync } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';

let sha = process.env.GITHUB_SHA || process.env.CF_PAGES_COMMIT_SHA || '';
try {
  sha = execSync('git rev-parse HEAD', { encoding: 'utf8' }).trim() || sha;
} catch {}
if (!sha) sha = 'unknown';

mkdirSync('src/data', { recursive: true });
writeFileSync('src/data/build-revision.json', JSON.stringify({ sha }, null, 2) + '\n', 'utf8');
console.log('Build revision:', sha);
