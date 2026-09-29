import { readdirSync, readFileSync, statSync } from 'node:fs';
import { extname, join } from 'node:path';
import { TextDecoder } from 'node:util';

const roots = ['src', 'scripts', 'public'];
const textExts = new Set(['.astro','.ts','.js','.mjs','.json','.md','.css','.html','.txt','.py','.yml','.yaml']);
const decoder = new TextDecoder('utf-8', { fatal: true });
const errors = [];

function walk(dir) {
  for (const name of readdirSync(dir)) {
    const path = join(dir, name);
    const st = statSync(path);
    if (st.isDirectory()) walk(path);
    else if (textExts.has(extname(path).toLowerCase())) check(path);
  }
}

function check(path) {
  if (path.endsWith('scripts/qa_utf8.mjs')) return;
  const bytes = readFileSync(path);
  let text;
  try {
    text = decoder.decode(bytes);
  } catch (error) {
    errors.push(`${path}: invalid UTF-8 bytes (${error.message})`);
    return;
  }

  if (text.includes('\uFFFD')) {
    errors.push(`${path}: contains Unicode replacement character U+FFFD`);
  }

  const c1 = text.match(/[\u0080-\u009F]/g) ?? [];
  if (c1.length > 0) {
    errors.push(`${path}: contains C1 control characters often produced by mojibake`);
  }

  const latin1High = text.match(/[\u00C0-\u00FF]/g) ?? [];
  if (latin1High.length >= 3) {
    errors.push(`${path}: suspicious Latin-1 byte-decoding pattern (${latin1High.slice(0,12).join('')})`);
  }

  const known = ['Ã','Â','â€','ì ','ë ','ê ','í ','ðŸ'];
  for (const token of known) {
    if (text.includes(token)) {
      errors.push(`${path}: suspicious mojibake token "${token}"`);
      break;
    }
  }
}

for (const root of roots) {
  try { walk(root); } catch {}
}

if (errors.length) {
  console.error('\nUTF-8 QA FAILED');
  for (const e of errors) console.error('- ' + e);
  process.exit(1);
}

console.log('UTF-8 QA PASSED: source text is valid UTF-8 and no common mojibake signatures were found.');
