import test from 'node:test';
import assert from 'node:assert/strict';
import {detailIllustration} from '../src/lib/visual.mjs';
const editorial={openingWreath:{assetType:'editorial_illustration'}};
test('explicit real-product or no-editorial slot wins over legacy illustration triggers',()=>{
  for(const pageType of ['business-opening','event-venue'])
    for(const assetSlot of ['REAL_PROOF','NONE'])
      assert.equal(detailIllustration({pageType,visualIntent:'event_wreath',assetSlot},editorial),null);
});
test('unsupported dedicated slots fail instead of silently using unrelated or cropped imagery',()=>{
  for(const assetSlot of ['HERO_WIDE','SPLIT_VISUAL','CONTENT_IMAGE','CTA_BANNER','CARD_THUMBNAIL'])
    for(const pageType of ['business-opening','funeral-facility'])
      assert.throws(()=>detailIllustration({pageType,assetSlot},editorial),/No compatible detail asset/);
});
test('legacy illustration remains explicit, while actual wreath intent uses catalog photography',()=>{
  assert.equal(detailIllustration({pageType:'business-opening'},editorial).assetType,'editorial_illustration');
  assert.equal(detailIllustration({pageType:'business-opening',visualIntent:'congrats_wreath'},editorial),null);
});
