import config from '../src/data/site-config.json' with {type:'json'};
if (process.env.SITE_INDEXABLE === 'true' && config.productionApproved !== true)
  throw new Error('Production-indexable build is disabled for this unapproved regional template');
