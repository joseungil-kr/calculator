# Goyang regional routing review candidate

This is route-support code, not a content or release approval. It adds no regional
Draft, approved snapshot, Publish Queue record, domain binding or deployment.

## Contract

- Site: `goyang-flower-v2`; one geographic hub `/regions/`.
- Existing Publisher wire: `ROUTE_TYPE=category`, `CATEGORY=regions`,
  `PAGE_TYPE=regional-service`, `PAGE_ROLE=REGION_SERVICE_LANDING`,
  `PARENT_HUB=/regions/`, `LOCALIZATION_POLICY=local-required`.
- Stable legal-dong URLs and administrative crosswalks are in
  `src/data/region-coverage.json`. Counts describe the verified official source,
  not a completion or content-quality gate.
- The three districts are groups, not additional required landing pages.
  Groups with no actual approved child stay hidden. No regional hub is generated
  until it has an actual approved regional child. Unpublished crosswalk names
  are plain text, never placeholder links.
- This site-only directory assumes one direct representative per mapped legal
  dong. A later shared-page or N:M design needs separate reviewed support.
- Regional product selection requires an explicit `VISUAL_INTENT`:
  `flower_delivery`, `flower_gift`, `funeral_wreath`, or `congrats_wreath`.
  They select existing catalog families only; this does not validate the catalog
  against today's product availability or approve prices, assets, or claims.
- An indexable site's one/two-child hub stays `noindex,follow` and outside the
  sitemap. An unapproved preview remains `noindex,nofollow,noarchive` everywhere.

## Required before actual consumption

1. Independently review this exact code revision and the separate trusted-main
   registry opt-in. The registry proposal changes only Goyang's category/type
   support and `administrativeCoverage` to region `goyang`, basis `legal`.
2. Explicitly register the Goyang-scoped Blueprint extension. The active
   `flower-local-v2` Blueprint read on 2026-10-03 still lists the six service
   categories and lacks `regional-service`. Existing enum choices support
   `category` and `REGION_SERVICE_LANDING`; inventing a new route enum is unnecessary.
3. Resolve current catalog and approved CTA alignment with real business-source
   evidence. No SKU, price, image or existing approved body changes in this patch.
4. For each real regional page, complete query/local-evidence/content review and
   the existing Writer → independent Reviewer → frozen Publisher path. A local
   test fixture or computed digest is never approval.
5. Prepare and independently approve the exact revision's authorized extension
   QA/deployment path. The existing fixed one-snapshot canary restoration and
   generic Goyang staging refusal remain unchanged. This patch opens no gate.

## Verification

Run `npm test`, then the existing `npm run build` with `SITE_INDEXABLE=false`.
The unchanged one-detail canary must still generate exactly HOME, its service
hub, and its approved detail (plus 404), with no empty `/regions/` route.
Synthetic fixture builds may exercise the region UI and indexable thin-hub
policy in a disposable test copy. They must never be published or counted as
customer content, source approval, actual HTTP QA, or coverage completion.

Rules are pinned at `8986a1936615cd0d814b816db7816488e40bacc1` under
`site-factory/contracts/rules/`: all three originals, `COMBINED_RULES.md`,
`PRECEDENCE_AND_COVERAGE.md`, and `source-manifest.json`. The v1.2-first C01–C14
and nonconflicting A01–A10 requirements remain unchanged.
