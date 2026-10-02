import test from 'node:test';
import assert from 'node:assert/strict';
import {productFamilies} from '../src/lib/catalog.mjs';

const family=(pageType,primaryKeyword,visualIntent='consultation',category='order')=>
  productFamilies({pageType,primaryKeyword,visualIntent,category});
test('funeral-only order promises show funeral products',()=>{
  assert.deepEqual(family('message-guide','고양 근조화환 리본 문구'),['funeral']);
  assert.deepEqual(family('price-guide','고양 근조화환 가격'),['funeral']);
});
test('congratulation-only order promises show congratulations products',()=>{
  assert.deepEqual(family('message-guide','고양 축하화환 리본 문구'),['congrats']);
  assert.deepEqual(family('price-guide','고양 축하화환 가격'),['congrats']);
});
test('broad wreath comparison can show both, gift and performance exclude wreaths',()=>{
  assert.deepEqual(family('message-guide','고양 화환 문구','wreath_message'),['funeral','congrats']);
  assert.deepEqual(family('price-guide','고양 근조·축하화환 가격','flower_price'),['funeral','congrats']);
  assert.throws(()=>family('price-guide','고양 근조·축하화환 가격','funeral_wreath'),/contradicts/);
  assert.deepEqual(family('hospital-visit','고양 병문안 꽃','consultation','gift'),['bouquet','basket']);
  assert.deepEqual(family('event-venue','고양 공연 축하꽃','performance_venue','event'),['bouquet']);
});
