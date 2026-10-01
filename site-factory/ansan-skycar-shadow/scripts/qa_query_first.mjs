import fs from 'node:fs';
const pages=JSON.parse(fs.readFileSync('src/data/pages.json','utf8'));
const arch=JSON.parse(fs.readFileSync('src/data/architecture.json','utf8'));
if(pages.length!==12) throw new Error('Expected 12 query pages');
const seen=new Set(), headingSets=[];
const linkRe=/\[\[([^|]+)\|([^\]]+)\]\]/g;
const audienceForbidden=/(검색어|검색의도|SEO|상위노출|페이지를 분리|페이지의 역할|지역 페이지|가격 페이지|견적 페이지|대표 페이지|중복문서|cluster|Business Truth|Production|Shadow|QA|검증용|콘텐츠와 CTA|사용자는|사용자가|검색자는|검색자가|페이지에서는|페이지에서 임의|허브로 돌아|지역 랜딩|설계할 때 실제 지역 맥락)/i;
function commonPrefix(a,b){let i=0; while(i<a.length&&i<b.length&&a[i]===b[i]) i++; return i;}
function toks(s){return new Set(s.replace(/[^\p{L}\p{N}]+/gu,' ').split(/\s+/).filter(x=>x.length>1));}
function sim(a,b){const A=toks(a),B=toks(b); const inter=[...A].filter(x=>B.has(x)).length; const uni=new Set([...A,...B]).size; return uni?inter/uni:0;}
for(const p of pages){
 if(!p.primaryKeyword||!p.title.startsWith(p.primaryKeyword)) throw new Error('Title alignment fail: '+p.pageKey);
 if(!p.h1.includes(p.primaryKeyword)||!p.firstAnswer.includes(p.primaryKeyword)) throw new Error('H1/answer alignment fail: '+p.pageKey);
 if(!p.cardSummary) throw new Error('cardSummary missing: '+p.pageKey);
 if(p.cardSummary.startsWith(p.primaryKeyword)) throw new Error('Title-summary repeat: '+p.pageKey);
 if(commonPrefix(p.title,p.cardSummary)>8) throw new Error('Title-summary common prefix >8: '+p.pageKey);
 if(sim(p.cardSummary,p.firstAnswer)>=0.70) throw new Error('Summary-firstAnswer similarity >=0.70: '+p.pageKey);
 if(seen.has(p.keywordCluster)) throw new Error('Duplicate cluster: '+p.keywordCluster); seen.add(p.keywordCluster);
 if(!Array.isArray(p.sections)||p.sections.length<7||!Array.isArray(p.faq)||p.faq.length<3) throw new Error('Content depth fail: '+p.pageKey);
 const headings=p.sections.map(s=>s[0]).join('|'); if(headingSets.includes(headings)) throw new Error('Duplicated H2: '+p.pageKey); headingSets.push(headings);
 const inline=[...p.sections.map(s=>s[1]).join(' ').matchAll(linkRe)].map(m=>m[1]);
 if(p.url!=='/'&&inline.length<2) throw new Error('Context links <2: '+p.pageKey);
 if(!Array.isArray(p.conversionTargets)||!p.conversionTargets.every(k=>inline.includes(k))) throw new Error('Conversion path missing: '+p.pageKey);
 if(['local-commercial','work-commercial'].includes(p.queryClass)&&(!Array.isArray(p.localEvidence)||p.localEvidence.length<2)) throw new Error('Local evidence <2: '+p.pageKey);
 const visible=[p.firstAnswer,...p.sections.flat(),...p.faq.flat(),p.cardSummary,p.cta?.label||''].join(' ');
 if(audienceForbidden.test(visible)) throw new Error('Audience gate fail: '+p.pageKey);
 if(!Array.isArray(p.humanCheckRequired)) throw new Error('Human-check metadata missing: '+p.pageKey);
}
for(const cat of ['work-types','areas']){
 const arr=pages.filter(p=>p.category===cat);
 for(let i=0;i<arr.length;i++) for(let j=i+1;j<arr.length;j++) if(sim(arr[i].cardSummary,arr[j].cardSummary)>=0.75) throw new Error('Sibling summaries too similar: '+arr[i].pageKey+' '+arr[j].pageKey);
}
if(arch.pages.filter(p=>p.status==='primary').length!==12) throw new Error('Architecture mismatch');
console.log('CONTENT WRITING QA PASSED: titleSummaryDifferent=12, conversionPath=12, audience=12');
