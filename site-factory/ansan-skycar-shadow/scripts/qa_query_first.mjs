import fs from 'node:fs';
const pages=JSON.parse(fs.readFileSync('src/data/pages.json','utf8'));
const arch=JSON.parse(fs.readFileSync('src/data/architecture.json','utf8'));
if(pages.length!==12) throw new Error('Expected 12 query pages');
const seen=new Set();
for(const p of pages){
  if(!p.primaryKeyword || !p.title.startsWith(p.primaryKeyword)) throw new Error('Title alignment fail: '+p.pageKey);
  if(!p.h1.includes(p.primaryKeyword)) throw new Error('H1 alignment fail: '+p.pageKey);
  if(!p.firstAnswer.includes(p.primaryKeyword)) throw new Error('First answer alignment fail: '+p.pageKey);
  if(seen.has(p.keywordCluster)) throw new Error('Duplicate keyword cluster: '+p.keywordCluster);
  seen.add(p.keywordCluster);
}
if(pages.filter(p=>p.queryClass==='support-info').length!==0) throw new Error('Support-info quota filler detected');
if(arch.pages.filter(p=>p.status==='primary').length!==12) throw new Error('Architecture primary count mismatch');
console.log('QUERY-FIRST QA PASSED: pages=12, duplicateCluster=0, supportFiller=0, alignment=100');
