import fs from 'node:fs';
const pages=JSON.parse(fs.readFileSync('src/data/pages.json','utf8'));
const arch=JSON.parse(fs.readFileSync('src/data/architecture.json','utf8'));
if(pages.length!==12) throw new Error('Expected 12 query pages');
const seen=new Set();
const headingSets=[];
const linkRe=/\[\[([^|]+)\|([^\]]+)\]\]/g;
for(const p of pages){
  if(!p.primaryKeyword || !p.title.startsWith(p.primaryKeyword)) throw new Error('Title alignment fail: '+p.pageKey);
  if(!p.h1.includes(p.primaryKeyword)) throw new Error('H1 alignment fail: '+p.pageKey);
  if(!p.firstAnswer.includes(p.primaryKeyword)) throw new Error('First answer alignment fail: '+p.pageKey);
  if(seen.has(p.keywordCluster)) throw new Error('Duplicate keyword cluster: '+p.keywordCluster);
  seen.add(p.keywordCluster);
  if(!Array.isArray(p.sections) || p.sections.length<7) throw new Error('Thin section count: '+p.pageKey);
  if(!Array.isArray(p.faq) || p.faq.length<3) throw new Error('FAQ depth fail: '+p.pageKey);
  if(!Array.isArray(p.relatedKeys) || p.relatedKeys.length<3) throw new Error('Related links fail: '+p.pageKey);
  const text=[p.firstAnswer,...p.sections.flat(),...p.faq.flat(),...(p.localEvidence||[]).flatMap(e=>[e.claim,e.sourceName])].join(' ').replace(/\s+/g,' ');
  if(text.length<1300) throw new Error('Thin content: '+p.pageKey+' chars='+text.length);
  const headings=p.sections.map(s=>s[0]).join('|');
  if(headingSets.includes(headings)) throw new Error('Duplicated H2 structure: '+p.pageKey);
  headingSets.push(headings);
  if(p.url!=='/'){
    const inline=[...p.sections.map(s=>s[1]).join(' ').matchAll(linkRe)];
    if(inline.length<2) throw new Error('Contextual internal links <2: '+p.pageKey);
    const hasUpper=inline.some(m=>m[1]==='/' || m[1]==='/work-types/' || m[1]==='/areas/' || m[1]==='skycar-qf-001');
    if(!hasUpper) throw new Error('No upper-context link: '+p.pageKey);
  }
  if(['local-commercial','work-commercial'].includes(p.queryClass)){
    if(!Array.isArray(p.localEvidence) || p.localEvidence.length<2) throw new Error('Local evidence <2: '+p.pageKey);
    for(const e of p.localEvidence){
      if(!e.sourceUrl || !e.sourceName || !e.verifiedAt || !e.claim) throw new Error('Incomplete local evidence: '+p.pageKey);
    }
  }
  if(!p.cta?.targetKey || !p.cta?.label) throw new Error('CTA missing: '+p.pageKey);
}
if(pages.filter(p=>p.queryClass==='support-info').length!==0) throw new Error('Support-info quota filler detected');
if(arch.pages.filter(p=>p.status==='primary').length!==12) throw new Error('Architecture primary count mismatch');
for(const cat of ['pricing','quote']){
  const count=pages.filter(p=>p.category===cat).length;
  const hub=arch.pages.find(p=>p.pageRole==='HUB'&&p.url===`/${cat}/`);
  if(count<=1 && hub) throw new Error('Single-child hub must not exist: '+cat);
}
for(const cat of ['work-types','areas']){
  const count=pages.filter(p=>p.category===cat).length;
  const hub=arch.pages.find(p=>p.pageRole==='HUB'&&p.url===`/${cat}/`);
  if(count>=2 && !hub) throw new Error('Required structural hub missing: '+cat);
}
console.log('QUERY-FIRST HARD-GATE QA PASSED: pages=12, titleH1=12, inlineLinks>=2, localEvidence>=2 for local/work, singleChildHub=0');
