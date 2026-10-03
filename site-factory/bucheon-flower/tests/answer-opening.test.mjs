import assert from 'node:assert/strict';
import test from 'node:test';
import fs from 'node:fs';
import {displayMarkdownBlocks,markdownBlocks} from '../src/lib/content.mjs';

const answer='빈소와 상주 성함을 확인한 뒤 주문해 주세요.';
const rest='\n\n## 주문 정보\n\n[전화 주문](tel:18440644)\n\n- 공식 출처 확인';
test('drops only the identical plain first paragraph and keeps all later blocks',()=>{
  assert.deepEqual(displayMarkdownBlocks(answer+rest,answer),markdownBlocks(rest));
});
test('keeps different text and treats a single time-range tilde as plain text',()=>{
  const different='배송지부터 확인해 주세요.';
  assert.deepEqual(displayMarkdownBlocks(different+rest,answer),markdownBlocks(different+rest));
  const hours='전화주문 08:00~23:00';
  assert.deepEqual(displayMarkdownBlocks(hours+rest,hours),markdownBlocks(rest));
});
test('keeps a later repetition even after dropping the first paragraph',()=>{
  assert.deepEqual(displayMarkdownBlocks(answer+'\n\n'+answer+rest,answer),markdownBlocks(answer+rest));
});
test('compares existing renderer text exactly without whitespace or Unicode normalization',()=>{
  for(const first of [' '+answer,answer+' ',answer.replace('빈소와','빈소와  '),answer.replace('.','!')])
    assert.deepEqual(displayMarkdownBlocks(answer+rest,first),markdownBlocks(answer+rest));
  assert.deepEqual(displayMarkdownBlocks('가'+rest,'가'),markdownBlocks('가'+rest));
});
test('existing multiline paragraph rendering is retained before exact comparison',()=>{
  const text='빈소와 상주 성함을\n확인한 뒤 주문해 주세요.';
  assert.deepEqual(displayMarkdownBlocks(text+rest,answer),markdownBlocks(rest));
});
for(const value of [undefined,null,'','   ',42])test(`no valid first answer: ${String(value)}`,()=>{
  assert.deepEqual(displayMarkdownBlocks(answer+rest,value),markdownBlocks(answer+rest));
});
for(const [label,lead] of Object.entries({
  'link':`[${answer}](https://fwith.co.kr)`,
  'strong':`**${answer}**`,
  'emphasis':`*${answer}*`,
  'underscore':`_${answer}_`,
  'strikethrough':`~~${answer}~~`,
  'inline code':'`'+answer+'`',
  'image':`![${answer}](/image.jpg)`,
  'raw tag':`<p>${answer}</p>`,
  'attributed paragraph':`<p class="intro">${answer}</p>`,
  'inline span':`<span>${answer}</span>`,
  'comment':answer+'<!-- keep -->',
  'leading comment':'<!-- keep -->\n'+answer,
  'heading':'## '+answer,
  'list':'- '+answer,
  'ordered list':'1. '+answer,
  'reference link':'['+answer+'][source]',
  'named entity':'&copy;',
  'numeric entity':'&#128;',
  'escaped ampersand':'&amp;',
  'unknown entity':'&uncertain;',
  'incomplete entity':'&amp',
}))test(`preserves ${label}, even if its raw spelling is the firstAnswer`,()=>{
  for(const firstAnswer of [lead,answer])
    assert.deepEqual(displayMarkdownBlocks(lead+rest,firstAnswer),markdownBlocks(lead+rest));
});
test('eligible frozen pages remove exactly one duplicate and other pages stay intact',()=>{
  const pages=JSON.parse(fs.readFileSync(new URL('../src/data/pages.json',import.meta.url)));
  const before=JSON.stringify(pages);
  for(const page of pages){
    const original=markdownBlocks(page.contentMarkdown);
    const first=original[0];
    const eligible=first?.type==='p' && first.text===page.firstAnswer && !/[<>&*_`\[\]]|~~/.test(first.text);
    assert.deepEqual(displayMarkdownBlocks(page.contentMarkdown,page.firstAnswer),eligible?original.slice(1):original);
  }
  assert.equal(JSON.stringify(pages),before);
});
test('component receives the independently retained hero answer without raw HTML or CSS changes',()=>{
  const detail=fs.readFileSync(new URL('../src/pages/[category]/[slug].astro',import.meta.url),'utf8');
  const component=fs.readFileSync(new URL('../src/components/MarkdownContent.astro',import.meta.url),'utf8');
  assert.match(detail,/<p>\{page.firstAnswer\}<\/p>/);
  assert.match(detail,/<MarkdownContent content=\{page.contentMarkdown\} firstAnswer=\{page.firstAnswer\}\/>/);
  assert.match(component,/displayMarkdownBlocks/);assert.doesNotMatch(component,/set:html|<style/);
});
