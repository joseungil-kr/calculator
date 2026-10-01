# Suwon regional site renderer

`src/data/pages.json` is the renderer input. A publication adapter must update the page, publish manifest, page map and architecture together with the same `pageKey`, `url` and immutable `snapshotId`. Page types must fit their category. A missing or conflicting product intent never falls back to unrelated wreaths.

Company facts come from `business-truth.json`. The catalog contains official product URLs, verified prices and representative product photography, with variation and delivery-fee caveats. New company claims or products need verified sources.

## Checks

- `npm ci`
- `npm test`
- `npm run test:growth` (isolated noindex build with one more page)
- `SITE_INDEXABLE=true npm run build`
- `SITE_INDEXABLE=true python3 -m unittest discover -s tests -v`
- `SITE_INDEXABLE=false SITE_URL=https://your-authorized-preview.example npm run build`

Build includes Astro type checks, exact generated metadata/sitemap/snapshot parity, internal-link/orphan checks and data/intent integrity. Neither build nor tests require a fixed number of pages. Preview is noindex by default. All known sources are escaped by Astro; optional snapshot Markdown supports plain paragraphs, headings, lists, strong text and safe links. Raw HTML is displayed as text.

## Customer-intent gates

`scripts/qa_intent.mjs` runs inside the graph gate. It checks answer dimensions, not a fixed section template: usable quoted ribbon examples and sender formats; handheld performance bouquets versus separately described installed wreaths; gift-format decisions; hospital permission checks; detailed address information; and prices from the verified catalog. Section count, order and FAQ count remain flexible.

`tests/fixtures/original-intent-failures.json` preserves the reviewed source revision's ribbon and performance defects. The before/after test proves those inputs fail the new gate and repaired snapshots pass. Rendered mutation tests separately reject internal jargon, missing examples, incorrect product photography/prices, unrelated wreath order paths, sibling venues labeled as purchase stages and all-wreath home displays. A school growth fixture uses general address guidance, preserving the 31st-page, escaped Markdown and discovery tests without reproducing the old wreath-path defect.

The labeled blank-ribbon illustration in `editorial-assets.json` is an editorial hero only. Real product cards retain the official photos, exact prices and SKU links. Any new content batch must advance immutable snapshot IDs in all four registries and pass a fresh hosted desktop/mobile business review before release; technical success alone does not establish commercial alignment.

On constrained local environments set `ASTRO_TELEMETRY_DISABLED=1` and use a writable npm cache. The repository keeps a dependency lockfile.

## Deployment boundaries

`wrangler.jsonc` is the existing production Worker/domain. `wrangler.staging.jsonc` is an isolated no-route QA Worker. Use only the authorized deployment workflow, which must verify QA and exact live revision. Do not run the staging configuration against the production domain.

IndexNow selection and submission require `SITE_INDEXABLE=true`, registered production `SITE_URL`, and `LIVE_QA_VERIFIED_REVISION` matching the exact 40-character built revision. This value is set only after live QA succeeds. A 403/manual-review state cannot authorize submission. Scripts are not run by the build.
