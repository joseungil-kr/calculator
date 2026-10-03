// Presentation only: choose one complete-block boundary without changing content.
// Prefer the reviewed middle-section placement, with no article-length quota.
export function orderBannerBoundary(blocks) {
  if (!blocks.length) return -1;
  const headings=blocks.flatMap((block,index)=>block.type==='h2'?[index]:[]);
  let candidates=headings.slice(2,-1);
  if (!candidates.length) candidates=headings.filter(index=>index>0);
  if (!candidates.length) candidates=blocks.flatMap((block,index)=>
    index>0 && !['h2','h3'].includes(blocks[index-1].type)
      && !(block.type==='li' && blocks[index-1].type==='li') ? [index] : []);
  // A single paragraph/list has no internal boundary; retain it intact.
  if (!candidates.length) return blocks.length;
  const length=blocks.reduce((total,block)=>total+block.text.length,0);
  let best=candidates[0], distance=Infinity;
  for(const index of candidates) {
    const before=blocks.slice(0,index).reduce((total,block)=>total+block.text.length,0);
    const difference=Math.abs(before-length/2);
    if(difference<distance){best=index;distance=difference;}
  }
  return best;
}
