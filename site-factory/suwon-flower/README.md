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

On constrained local environments set `ASTRO_TELEMETRY_DISABLED=1` and use a writable npm cache. The repository keeps a dependency lockfile.

## Deployment boundaries

`wrangler.jsonc` is the existing production Worker/domain. `wrangler.staging.jsonc` is an isolated no-route QA Worker. Use only the authorized deployment workflow, which must verify QA and exact live revision. Do not run the staging configuration against the production domain.

IndexNow selection and submission require `SITE_INDEXABLE=true`, registered production `SITE_URL`, and `LIVE_QA_VERIFIED_REVISION` matching the exact 40-character built revision. This value is set only after live QA succeeds. A 403/manual-review state cannot authorize submission. Scripts are not run by the build.
