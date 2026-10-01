import fs from 'node:fs';
const pages=JSON.parse(fs.readFileSync('src/data/pages.json','utf8'));
const arch=JSON.parse(fs.readFileSync('src/data/architecture.json','utf8'));
if(pages.length!==12) throw new Error('Expected 12 query pages');
const seen=new Set();
const headingSets=[];
for(const p of pages){
  if(!p.primaryKeyword || !p.title.startsWith(p.primaryKeyword)) throw new Error('Title alignment fail: '+p.pageKey);
  if(!p.h1.includes(p.primaryKeyword)) throw new Error('H1 alignment fail: '+p.pageKey);
  if(!p.firstAnswer.includes(p.primaryKeyword)) throw new Error('First answer alignment fail: '+p.pageKey);
  if(seen.has(p.keywordCluster)) throw new Error('Duplicate keyword cluster: '+p.keywordCluster);
  seen.add(p.keywordCluster);
  if(!Array.isArray(p.sections) || p.sections.length<7) throw new Error('Thin section count: '+p.pageKey);
  if(!Array.isArray(p.faq) || p.faq.length<3) throw new Error('FAQ depth fail: '+p.pageKey);
  if(!Array.isArray(p.relatedKeys) || p.relatedKeys.length<3) throw new Error('Related links fail: '+p.pageKey);
  const text=[p.firstAnswer,...p.sections.flat(),...p.faq.flat()].join(' ').replace(/\s+/g,' ');
  if(text.length<1300) throw new Error('Thin content: '+p.pageKey+' chars='+text.length);
  const headings=p.sections.map(s=>s[0]).join('|');
  if(headingSets.includes(headings)) throw new Error('Duplicated H2 structure: '+p.pageKey);
  headingSets.push(headings);
}
if(pages.filter(p=>p.queryClass==='support-info').length!==0) throw new Error('Support-info quota filler detected');
if(arch.pages.filter(p=>p.status==='primary').length!==12) throw new Error('Architecture primary count mismatch');
console.log('QUERY-FIRST CONTENT QA PASSED: pages=12, minSections=7, minFAQ=3, minChars=1300, duplicateCluster=0, duplicateH2Structure=0');
