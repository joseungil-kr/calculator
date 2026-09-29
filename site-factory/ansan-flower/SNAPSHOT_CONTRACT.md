# Site Factory Snapshot Contract

Production builds must be reproducible and must not depend on live Airtable reads.

## Source roles

- Airtable Sites / Page Plan / Draft Lab: editorial and operational source of truth.
- Airtable Publish Queue: immutable handoff created only after Editor approval.
- Git snapshot: source of truth for what is actually publishable in production.
- Astro: reads only Git-tracked Markdown/JSON during production build.
- Cloudflare: builds and serves the Git snapshot.

## Publish invariant

An approved page is copied into Publish Queue with a unique `snapshot_id`.
After that copy is created, later Draft Lab edits do not change that queued snapshot.
A new revision must create a new snapshot id.

## Git artifacts

Each publish must update:

1. `src/content/articles/<slug>.md`
2. `src/data/publish-manifest.json`
3. `src/data/page-map.json`

Article frontmatter must contain:

- pageKey
- snapshotId
- sourceDraftKey
- sourceRecordId
- category
- structureType
- region
- verifiedAt
- sourceUrls
- draftStatus

## Build gate

`npm run build` first runs `scripts/validate_snapshot.mjs`.

The build fails when:

- a manifest file is missing,
- a listed content file is missing,
- page keys or URLs collide,
- article provenance does not match the manifest,
- page-map and manifest disagree,
- draftStatus is not approved/published.

## Preview vs production

A future preview site may read Airtable directly.
Production must continue to build from frozen Git snapshots.
