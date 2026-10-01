import fs from 'node:fs';
import assert from 'node:assert/strict';
import {validateCustomerIntent} from './qa_intent.mjs';

export function runIntentRegressionProof(data) {
  const fixture=JSON.parse(fs.readFileSync(new URL('../tests/fixtures/original-intent-failures.json',import.meta.url),'utf8'));
  const reproduced=[];
  for(const before of fixture.pages) {
    let failure;
    try {validateCustomerIntent(before,data.products);} catch(error) {failure=error.message;}
    assert.ok(failure,`Original defect unexpectedly passed: ${before.pageKey}`);
    // The original ribbon typo is also a defect. Removing just that typo must
    // still fail the missing-answer dimension, rather than hiding behind it.
    let answerFailure;
    if(before.pageType==='message-guide') {
      const withoutTypo=JSON.parse(JSON.stringify(before).replaceAll('문구은','문구는'));
      try {validateCustomerIntent(withoutTypo,data.products);} catch(error) {answerFailure=error.message;}
      assert.match(answerFailure || '',/missing usable/);
    }
    const after=data.pages.find(p=>p.pageKey===before.pageKey);
    assert.ok(after,`Missing repaired counterpart: ${before.pageKey}`);
    assert.notEqual(after.snapshotId,before.snapshotId,'Repaired content must have a new snapshot');
    assert.equal(validateCustomerIntent(after,data.products),true);
    reproduced.push({pageKey:before.pageKey,before:'REJECTED',failure,...(answerFailure?{answerFailure}:{}),after:'PASSED'});
  }
  for(const page of data.pages)assert.equal(validateCustomerIntent(page,data.products),true);
  return {sourceRevision:fixture.sourceRevision,reproduced,approvedPagesPassed:data.pages.length};
}

if(process.argv[1]?.endsWith('/qa_intent_regressions.mjs')) {
  const read=name=>JSON.parse(fs.readFileSync(`src/data/${name}.json`,'utf8'));
  console.log('INTENT BEFORE/AFTER PROOF',JSON.stringify(runIntentRegressionProof({pages:read('pages'),products:read('products')}),null,2));
}
