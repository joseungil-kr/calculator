# Site Factory Snapshot Contract

Production builds are reproducible and never read Airtable directly.

## Source roles

- Airtable Sites / Page Plan / Draft Lab: editorial and operational source of truth.
- Airtable Publish Queue: immutable handoff created only after Editor approval.
- Git snapshot: source of truth for what is publishable in production.
- Astro: reads Git-tracked Markdown/JSON only.
- Cloudflare: builds and serves the Git snapshot.

## URL routing

Every snapshot stores both `slug` and `routeType`.

- `top_level` → `/<slug>/`
- `category` → `/<category>/<slug>/`

Top-level routes are reserved for a small number of core commercial/hub pages such as
`/안산꽃배달/`. Informational, local-entity, occasion and expertise pages normally use
category routes. Keyword-looking URLs are an experiment variable, not a ranking guarantee.

## Publish invariant

An approved page is copied into Publish Queue with a unique `snapshot_id`.
Later Draft Lab edits do not change that queued snapshot. A content revision creates a new
snapshot id. The pre-production v1 test snapshots received a one-time routing metadata
migration before the first real domain launch.

## Git artifacts

Each publish updates:

1. `src/content/articles/<page_key>.md`
2. `src/data/publish-manifest.json`
3. `src/data/page-map.json`

Article frontmatter contains pageKey, snapshotId, sourceDraftKey, sourceRecordId, slug,
routeType, category, structureType, region, verifiedAt, sourceUrls and draftStatus.

## Test vs production indexing

The factory defaults to `SITE_INDEXABLE=false`, emitting meta noindex and robots Disallow.
A real domain must explicitly set `SITE_INDEXABLE=true` only after final live QA and search
registration readiness.
