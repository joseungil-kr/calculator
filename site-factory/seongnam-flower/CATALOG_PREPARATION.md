# Seongnam trial catalog reconciliation (proposal)

This follows, and does not replace, the immutable bootstrap from main
`638081fee18ceef9b2e148e26e152a5a60761c82` and template
`2ead40cecc0fe0925f69395e4798a35c0aec1894`.
The bootstrap provenance describes the original 54-file tree only. Apply this
catalog change as a separate reviewed commit, never rewrite bootstrap hashes
or rerun the empty bootstrap over this reconciled site.

- Site: `seongnam-flower-v2`
- Launch: `seongnam-flower-v2-trial-20261002`
- Exactly eight verified catalog records: four funeral, four congratulatory
- Internal product keys are not official SKUs
- Official names, prices, source detail URLs and eight newly downloaded image
  files are tied together in `src/data/catalog-provenance.json`; the source
  handoff is preserved in `src/data/catalog-source-evidence.json`
- Official detail URLs are evidence only; every online CTA is the Business
  Truth home `https://fwith.co.kr`
- Earlier catalog images remain untouched and unreferenced by this snapshot.
  No equivalence to the official SKU images is claimed.
- The business sells bouquets/baskets, but these are not present in this
  verified eight-record snapshot. No old template fallback is allowed.
- Home advertises these wreath families only. Funeral, business and order
  hubs select them. School/event/gift hubs fail closed until explicitly
  reconciled with a broader approved catalog.

No customer detail, Draft, Queue, snapshot approval, deployment or production
permission is created by this change. Zero details remain in pages/manifest.
Noindex, production-disabled and growth-paused boundaries remain unchanged.
Existing Goyang and all other regional files are untouched.

## Gates

Run with Node 22 and the committed lockfile:

```
npm ci --no-audit --no-fund
npm test
ASTRO_TELEMETRY_DISABLED=1 SITE_INDEXABLE=false \
  SITE_URL=https://seongnam-flower-guide-qa.joseungil.workers.dev \
  SITE_FACTORY_REVISION=<exact-published-full-sha> npm run build
SITE_INDEXABLE=true node scripts/assert_preview_boundary.mjs
```

The last command must fail. `qa_seongnam_catalog.mjs` checks the source evidence
hash, exact record/SKU membership, names/prices, image hashes and CTA, along
with home and any later detail/hub product promises. Its tests reject missing
records, detail-page CTAs and substitution of unverified old images.

Local preparation validation: 33 provisioning Python tests; 11 Node catalog
unit/negative tests; full Astro check/build/static/bootstrap gates on Node
22.23.3 passed. Zero detail routes and zero empty hub routes were generated.
Local fixture build revisions are not proof of remote publication.

Before publication: clear the hosted Worker collision check, reread main and
target refs, and recompute the bootstrap/registry proposal if main changed.
Publish and read back through the established authorized path. Only then may
the existing Creator/Reviewer/Publisher proceed with the real one-detail frozen
payload. Final hosted image/mobile/detail/canonical/snapshot QA remains due.

Hosted Worker absence was proven by the read-only preflight:
https://github.com/joseungil-kr/fwith-site-factory/actions/runs/37002076875
Checked 2026-10-02T11:38:10.522016Z, account and scripts HTTP 200,
account verified, exact Seongnam QA Worker absent. No deployment performed.
