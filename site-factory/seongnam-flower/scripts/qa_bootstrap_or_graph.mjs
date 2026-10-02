import fs from 'node:fs';
import {validateGraph,loadGraph} from './qa_graph.mjs';
import config from '../src/data/site-config.json' with {type:'json'};
const pages=JSON.parse(fs.readFileSync('src/data/pages.json','utf8'));
if (pages.length===0) {
  if (process.env.SITE_INDEXABLE==='true' || config.productionApproved === true)
    throw new Error('Empty template cannot build as production');
  console.log('TEMPLATE NOINDEX BOOTSTRAP PASSED: zero published pages');
} else console.log('GRAPH QA PASSED',validateGraph(loadGraph()));
