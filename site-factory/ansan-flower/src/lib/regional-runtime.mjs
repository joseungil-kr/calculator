import coverage from '../data/region-coverage.json' with {type:'json'};
import policy from '../data/region-policy.json' with {type:'json'};
import manifest from '../data/publish-manifest.json' with {type:'json'};
import architecture from '../data/architecture.json' with {type:'json'};
import {regionalRows,directoryGroups,regionalMetadataFields} from './regions.mjs';
export {coverage,policy,architecture};
export const regionalPages=regionalRows(manifest.pages,architecture,coverage,policy);
export function groupsFor(pages){return directoryGroups(pages,architecture,coverage,policy);}
export function assertRegionalInput(pages){
 const regional=pages.filter(p=>p.category==='regions'||p.pageType==='regional-service');
 if(regional.length!==regionalPages.length)throw new Error('Regional input/manifest count mismatch');
 for(const page of regional){const frozen=regionalPages.find(p=>p.pageKey===page.pageKey);
  for(const field of ['pageKey','snapshotId','slug','category','pageType',...regionalMetadataFields])if(JSON.stringify(page[field])!==JSON.stringify(frozen?.[field]))throw new Error('Regional input/manifest mismatch '+field);
 }
 return regionalPages;
}
