# Initial 50: read-only completion barrier

`batch_barrier.py` consumes evidence from the existing Writer → Reviewer →
Publish Queue → issue Publisher → `render_snapshot.py` loop. It does not generate
copy, create records/issues, change schedules, publish, approve content, deploy,
or submit IndexNow. `plan_batch.py` remains the candidate selector; a shortage
of actual evidenced intents blocks the target instead of reducing it.

One batch belongs to **one regional site**. Its exactly **50 detail members
include the Seongnam canary** for the Seongnam launch. HOME and HUB routes are
counted separately and never satisfy detail membership. This is an initial-50
contract, not a configurable growth scheduler.

## Frozen batch contract (JSON)

- `schemaVersion`: 1
- `batchId`, `siteKey`: nonempty stable identifiers
- `targetDetails`: 50 (cannot be reduced)
- `canaryPageKey`: the real canary member's page key
- `ruleRevision`, `templateRevision`, `registryRevision`: full lowercase Git SHAs
  for the approved inputs. Registry is read from that exact commit's
  `.github/site-factory-sites.json` in the provided repository.
- `members`: exactly 50 objects with only `pageKey` and `intentKey`; both unique
- `membershipHash`: `batch_barrier.identity(batch)` after membership is frozen

Store the original frozen contract in a trusted reviewed location. Identity is
SHA-256 of canonical sorted-key compact UTF-8 JSON containing the identity fields,
pinned revisions and page-key-sorted membership. Reordering is harmless; changing
membership, intent, canary, revisions or target creates a different identity and
requires a new approval cycle. A self-computed digest is not authorization.

## Checkpoint evidence contract (JSON)

Top-level `batchId`, `membershipHash`, `finalSourceSha`, `items`, `qa`.
`items` must exactly match frozen membership, with no missing/extra/duplicate item.
Each item contains:

- `pageKey`, `intentKey`, all three pinned revision fields
- `draftRevision`: exact external Writer revision, not just the draft record key
- `payload`: exact frozen approved issue body accepted by `render_snapshot.py`
- `reviewDigest`: existing `site-factory-review-sha256-v1` digest
- `snapshotHash`: immutable storage digest including the actual Queue record ID
- `reviewerApproval`: `status="approved"`, `reviewer`, `evidenceUrl`,
  `draftRevision`, `reviewDigest`, and frozen `membershipHash`
- `queueRecordId`, `issueUrl`, `snapshotId`: unique Publisher checkpoints;
  issue URL must belong to the registered repository
- `reviewSourceSha`: committed current manifest used during review
- `commitSha`: resulting immutable single-snapshot commit

All checkpoint commits must be ancestors of `finalSourceSha`; each review source
must be an ancestor of its checkpoint. Both checkpoint and final manifests must
match the exact approved snapshot, queue, draft/source IDs and route. Final
architecture must retain the planned intent and route. The helper reads committed
Git bytes, never dirty working-tree manifests.

Related links are allowed only to pages present and explicitly approved in the
manifest at `reviewSourceSha`. Future planned members are not link targets. Even
an otherwise reapproved new graph fails if it links to a future page. A graph or
content change invalidates its digest; it requires a new Writer revision and
actual Reviewer approval before obtaining new Queue/snapshot evidence. Retain
prior checkpoints externally; this helper does not silently rewrite them.

## Final independent QA contract

`qa` contains:

- `state="passed"`, `environment="staging"`, `noindex=true`
- `sourceSha`: exactly `finalSourceSha`, not an earlier canary/intermediate SHA
- `manifestSha256`: SHA-256 of final committed publish-manifest **raw bytes**
- `reviewer`, `evidenceUrl`: independent QA identity and retrievable report
- `gates`: exactly `build`, `static`, `graph`, `canonical`, `h1`, `schema`,
  `robots`, `sitemap`, `404`
- `routes`: exactly every final manifest route, every architecture hub, and `/`;
  each object has `url`, `state="passed"`, `noindex=true`

A canary-only QA report is insufficient. HTTP403, missing routes, absent approval,
partial commits, missing manifests and a changed final SHA remain blocked. A new
source revision requires a fresh whole-route QA report. Existing preview helpers
may contribute evidence but their limited-route reports do not automatically
satisfy this whole-site contract.

Reviewer and QA assertions must be collected by a trusted operator/consumer from
actual upstream review and QA runs. This helper checks integrity and completeness;
it does not authenticate identities, fetch external Airtable/GitHub review state,
verify signatures, perform HTTP QA, or turn synthetic/local fixture reports into
real approval. Pinned rule/template revisions are identity inputs, not assertions
that their semantic requirements were independently audited.

## Invocation and states

```sh
python3 site-factory/engine/batch_barrier.py \
  --batch /path/to/frozen-batch.json \
  --evidence /path/to/checkpoint-evidence.json \
  --workspace /path/to/full-history-repository
python3 -m unittest discover -s site-factory/engine/tests -p test_batch_barrier.py -v
```

On success, exit 0 emits `staging_complete` with exact SHA, membership hash, detail,
HOME/HUB and QA-route counts. `productionApproved=false` and
`indexNowAllowed=false` always. It never emits `live_verified` or closes publishing
issues. Invalid/incomplete input exits 1 with `state="blocked"`. Missing Git
objects require fetching the ordinary authorized repository history; never guess
at evidence. No workflow is wired to invoke or bypass this barrier automatically.
Production/indexing remain separate, explicitly authorized gates.
