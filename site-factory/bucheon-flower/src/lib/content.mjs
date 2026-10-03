// Deliberately small Markdown subset. Raw HTML stays text; Astro escapes every token.
export function safeHref(value) {
  if (typeof value !== 'string' || /[\s\u0000-\u001f]/.test(value)) return null;
  if (value.startsWith('/') && !value.startsWith('//') && !value.includes('\\')) return value;
  try { const u = new URL(value); return ['https:', 'http:', 'tel:'].includes(u.protocol) ? value : null; } catch { return null; }
}
export function inlineTokens(text) {
  const parts = []; const re = /\[([^\]]+)\]\(([^)]+)\)|\*\*([^*]+)\*\*/g; let last=0;
  for (const m of text.matchAll(re)) {
    if (m.index > last) parts.push({type:'text', text:text.slice(last,m.index)});
    parts.push(m[3] ? {type:'strong',text:m[3]} : {type:'link',text:m[1],href:safeHref(m[2])}); last=m.index+m[0].length;
  }
  if (last < text.length) parts.push({type:'text',text:text.slice(last)});
  return parts;
}
export function markdownBlocks(markdown) {
  const blocks=[]; let paragraph=[];
  const flush=()=>{if(paragraph.length){blocks.push({type:'p',text:paragraph.join(' ')});paragraph=[];}};
  for(const line of markdown.replace(/\r/g,'').split('\n')) {
    if(!line.trim()){flush();continue;}
    const heading=line.match(/^(#{1,6})\s+(.+)$/);
    const item=line.match(/^(?:[-*]|\d+\.)\s+(.+)$/);
    if(heading){flush();blocks.push({type:heading[1].length<=2?'h2':'h3',text:heading[2]});}
    else if(item){flush();blocks.push({type:'li',text:item[1]});}
    else paragraph.push(line.trim());
  }
  flush(); return blocks;
}

// This renderer creates plain <p> elements from text-only paragraph blocks.
// Match their exact text before escaping; do not decode entities or normalize it.
// Markup-like or uncertain input stays visible, even when its spelling matches.
export function displayMarkdownBlocks(markdown, firstAnswer) {
  const blocks=markdownBlocks(markdown);
  const lead=blocks[0];
  if (!lead || lead.type!=='p' || typeof firstAnswer!=='string' || !firstAnswer.trim()) return blocks;
  const tokens=inlineTokens(lead.text);
  if (tokens.length!==1 || tokens[0].type!=='text' || /[<>&*_`\[\]]|~~/.test(lead.text)) return blocks;
  return lead.text===firstAnswer ? blocks.slice(1) : blocks;
}
