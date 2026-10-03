# Scheduled Creator: deterministic v2 region bootstrap

`provision_goyang.py` keeps its original filename/default for compatibility and
now also prepares the allowlisted Seongnam trial using the same engine.
It prepares infrastructure only. Existing hosted Goyang content is not a new
bootstrap and must never be replaced by an empty skeleton.
It is a local proposal builder, not a second publisher, workflow or scheduler.
It never contacts a service, commits/pushes, deploys, changes Airtable, creates
customer content, grants snapshot approval or enables production/growth.

## Fixed contract

- Repository: `joseungil-kr/fwith-site-factory`
- Site / launch: `goyang-flower-v2` / `goyang-flower-v2-launch`
- Target branch / root: `site-factory-goyang-v2` / `site-factory/goyang-flower`
- Trusted template: `flower-local-v2`, branch `site-factory-flower-v2-template`
- Source revision: `2ead40cecc0fe0925f69395e4798a35c0aec1894`
- Source root: `site-factory/templates/flower-local-v2`
- Independently reviewed source tree: `52fa60037b12c0762dda16b61ab95c3fc62270b1`
- This pin adds only the reviewed six-line Goyang mobile footer correction;
  CSS blob `2d84867cf1cbc65120a7cb92ff4fd12620092c04`. Other template bytes
  remain identical to the earlier reviewed 54-file source.
- Exactly 54 regular tracked files. Never copy a working directory or generated
  `node_modules`, `dist`, `.astro` or `build-revision.json`
- Six adapted JSON files only: site config, architecture, manifest, page map,
  staging Wrangler and disabled-production Wrangler
- QA: `goyang-flower-guide-qa`,
  `https://goyang-flower-guide-qa.joseungil.workers.dev`, no custom routes
- `goyang-flower-prod-disabled` is a distinct disabled-production placeholder,
  not an existing Worker or permission to deploy it
- `https://goyang.fwith.kr` is intended-production registry metadata only,
  not DNS setup or production authorization
- `productionEnabled=false`, `growthPaused=true`, `autoDeploySnapshots=false`,
  `structured-json-v12`, both snapshot and revision approval required
- Empty pages, manifest, page map and snapshot ledger; six neutral hidden,
  nonindexable hubs with zero children; regional home keyword only

## Creator invocation

After the deployment-isolation gate is cleared, the existing scheduled Creator
reads the current trusted main SHA and whether the exact target branch exists
through the existing authorized GitHub connection. Retrieve those full commit
objects and the pinned source locally before invoking the helper. Read-only
retrieval is separate from this helper. A stale/missing local branch ref is not
proof of remote absence. Do not use a mutable branch name as a revision argument.

On a Linux execution host with Python 3, Git and `/proc/self/fd`:

```sh
python3 site-factory/engine/provision_goyang.py \
  --repo /path/to/verified/repository \
  --control-revision FULL_CURRENT_TRUSTED_MAIN_SHA \
  --target-revision absent \
  --output /path/to/existing-parent/new-goyang-bundle
```

If the target branch exists, replace `absent` with its freshly read full SHA.
Exact source pin/tree/manifest checks, protected target collisions, empty-state
checks and provenance checks happen before output. Missing objects fail closed;
Git replacement objects, inherited repository redirections and lazy network
fetches are disabled. The helper never regenerates the saved Draft and must
never consume the obsolete NHIMC `goyang-launch-input.json`.

The output contains:

- `target-files/site-factory/goyang-flower/`: exactly the 54 adapted source files
- `target-files/.github/site-factory-provisioning/goyang-flower-v2.json`:
  source and target SHA-256 manifests, source Git blob IDs, source revision/tree,
  six adaptation paths, deterministic bootstrap ID and zero-content boundary
- `control-files/.github/site-factory-sites.json`: existing registry entries
  retained, plus the exact gated Goyang entry; no inherited approval/verification keys
- `provisioning-plan.json`: expected main/target revisions, exact proposed file
  hashes, creation/no-op states and publication preconditions

Replaying into a byte-identical output is a no-op. Existing conflicting output,
symlink paths, concurrent destination creation and changed parent directories
are rejected without overwriting. The exact matching target bootstrap is also a
no-op. Existing target customer content or unrecognized provenance blocks this
bootstrap operation; inspect and continue the established snapshot pipeline
instead of replacing or recreating the target.

## Existing scheduled publication path

The Creator, under the separately authorized project workflow, consumes the
bundle. Before any external write, re-read both remote refs and compare them
with the plan. Also verify no hosted Worker/route collision; a Git registry alone
cannot prove absence in Cloudflare. On any race, recompute from a fresh trusted
control revision, never force-update a branch or overwrite a newer registry.

For `targetState=create`, create the target commit from the trusted control
revision with exactly the listed `target-files` paths, and create the branch
only if still absent. For `targetState=unchanged`, skip target writes. Add the
registry proposal to main only when `registryState=add`, with an optimistic
non-force update based on the recorded control revision. Preserve all unrelated
files and entries. Read back the exact branch commit, 54 target blobs and
provenance, plus the main registry entry, before recording infrastructure ready.
If branch creation succeeds but registration is interrupted, rerun with that
exact branch SHA; its target state is unchanged and registration can resume.

Infrastructure readiness is not customer-content approval or launch completion.
The existing reviewed Draft for 일산백병원 at
`/funeral/ilsan-paik-funeral-wreath/` stays in its established scheduled
Reviewer → frozen Publish Queue → Publisher → `[SITE-SNAPSHOT]` path. Only the
actual approved frozen snapshot adds that one detail. After its exact commit,
the scheduled Reviewer must use `goyang-staging-qa.yml` for read-only QA of
the already-hosted `e4eead3e881b3b4c09a60e2af5befb55b6787413` snapshot.
Generic staging explicitly blocks Goyang to avoid reverting its custom-domain
canonical. Any separate Goyang redeploy still uses the fixed approved workflow.
Do not add a new workflow,
schedule, broad trigger, token or permission. Hosted detail/hub/catalog/image,
mobile, metadata, snapshot and link QA remain required; a local bootstrap build
or homepage-only preview check cannot establish them.

## Seongnam one-detail trial handoff

Do not resume or rewrite the legacy 30-detail launch
`seongnam-flower-v2-launch` / `recwHFihLl4kLNor8`, or silently reuse the queued
Pool `recSfGl7ViUdANzXf`. The parent coordinates Airtable and existing v2 roles.
Use a new explicit launch identity matching `seongnam-flower-v2-trial-*`, for
example `seongnam-flower-v2-trial-20261002`. It is included in immutable
provenance/bootstrap identity with `trialDetailTarget=1` and zero created pages.
Replaying a different trial against existing target provenance fails closed.

Read current remote main, template and target refs; fetch exact objects first.
Local refs do not prove remote absence. A safe Windows/Linux inspection is:

```sh
python3 site-factory/engine/provision_goyang.py \
  --repo /path/to/verified/repository \
  --control-revision FULL_CURRENT_TRUSTED_MAIN_SHA \
  --target-revision absent \
  --site-key seongnam-flower-v2 \
  --launch-key seongnam-flower-v2-trial-20261002 \
  --dry-run
```

On the supported Linux host, replace `--dry-run` with `--output` and a new
bundle path beneath an existing checked parent. Never weaken Linux no-follow
handles or atomic no-replace output checks to make a Windows write succeed.
The Creator consumes the same bundle format/publication preconditions above:
root `site-factory/seongnam-flower`, branch `site-factory-seongnam-v2`,
registry key `seongnam-flower-v2`, QA Worker `seongnam-flower-guide-qa`, and URL
`https://seongnam-flower-guide-qa.joseungil.workers.dev`. Registration is a
proposal until the Creator publishes and reads it back; this code update does
not create a target branch, registry entry, site, Draft or Airtable launch.

Before publication/deployment, independently prove no existing hosted Worker
collision using currently authorized access. Authentication/permission denial
is a blocker, not permission to change tokens, security rules or routes.
No custom domain/DNS setup is needed for this noindex trial.

The existing Creator/Reviewer/Publisher must research and approve the real
one-detail frozen payload; do not handwrite a sample article. Candidate:
분당서울대학교병원 장례식장 근조화환; official source supplied by the parent:
https://www.snubh.org/intro/map/funeral.do . Its final slug/snapshot are chosen
by those roles, not this infrastructure helper. Preserve the actual source,
Draft and frozen payload. Current Airtable catalog (4 funeral + 4 congratulatory
SKUs) differs from this unchanged template catalog (3 funeral, 3 congratulatory,
3 bouquet and 1 basket); home/hub/product promises require existing-role catalog
reconciliation before customer QA or readiness. No missing bouquet/basket may
be promised solely because the skeleton contains old catalog rows.

After registration and the real reviewed snapshot commit, manually run the
existing `site-staging-deploy.yml` with `site_key=seongnam-flower-v2` and
`expected_revision=<full exact published snapshot commit SHA>`. It opts this
new region into an isolated archived Astro build, proves registered branch
ancestry, checks fixed/distinct Worker names and no route/trigger, uses noindex
and pinned Wrangler `4.146.0`, and does not alter legacy site build behavior.
The existing secret is reused, never changed. Source build static/graph/catalog
gates and HTTP home/robots/revision gates run; independent hosted home/hub/detail,
catalog/image/mobile/canonical/snapshot QA still gates the one-detail result.

The later first batch target is explicitly **50 detail documents, including the
Seongnam canary; home and hubs are separate**. Do not reduce it when topics are
insufficient. `plan_batch.py` candidate selection and one-snapshot atomic writes
are not a 50-item completion barrier. Exact batch membership/revisions, resume
checkpoints, all-item approval/manifest parity and final exact-SHA full QA remain
a separate next phase; no new engine/scheduler or completion claim is added here.

## Reproducible local checks

```sh
python3 -m unittest discover -s site-factory/engine/tests -p test_provision_goyang.py -v
python3 -m unittest discover -s site-factory/engine/tests -p test_provision_regions.py -v
python3 -m unittest discover -s site-factory/engine/tests -p test_engine.py -v
python3 -m unittest discover -s site-factory/engine/tests -p test_verify_preview.py -v
python3 site-factory/engine/tests/test_legacy_baselines.py
```

Copy the 54-file target into a separate QA directory, leaving the bundle pristine.
Use Node 22 and the committed lockfile:

```sh
npm ci --no-audit --no-fund
npm test
ASTRO_TELEMETRY_DISABLED=1 SITE_INDEXABLE=false \
  SITE_URL=https://goyang-flower-guide-qa.joseungil.workers.dev \
  SITE_FACTORY_REVISION=<full-local-test-revision> npm run build
SITE_INDEXABLE=true node scripts/assert_preview_boundary.mjs
```

The last command must fail. The bootstrap must produce zero detail pages and
no empty hub route/navigation, with noindex meta/header and `Disallow: /`.
The fixture revision used in a local QA build is not a published target revision.
The existing `test_rendered_growth.py` is a CLI test requiring `--suwon-root`;
it is not import-safe under blanket `unittest discover -p 'test_*.py'`.

## Bucheon scheduled bootstrap trial: reviewed source profile

Bucheon is the only newly supported region. Do not choose another ready Pool row
as a fallback. Existing Goyang and Seongnam source pins, provenance and customer
content remain unchanged.

- Site: `bucheon-flower-v2`; explicit trial: `bucheon-flower-v2-trial-20261004`.
- Branch/root: `site-factory-bucheon-v2` / `site-factory/bucheon-flower`.
- QA Worker: `bucheon-flower-guide-qa`, isolated workers.dev and noindex.
- Disabled production placeholder: `bucheon-flower-prod-disabled`.
- Source registry key: `flower-local-v2-bucheon-bootstrap-r1`.
- Reviewed source subtree: `770d3f2d200d55ded378a649265cca3de81c130e`, exactly 65 source files.
- Source branch/root stay `site-factory-flower-v2-template` /
  `site-factory/templates/flower-local-v2`.
- The new registry entry must contain the actual published 40-character source
  commit, not a branch name, planned SHA or local test fixture commit. The helper
  verifies the trusted registry entry, commit object, fixed subtree and count.
- The existing `flower-local-v2` registry entry and original 54-file source
  profile are retained byte for byte. Only Bucheon selects the new profile.

Publish the independently reviewed generic template commit first, as a
descendant of the current verified template branch. Read back its exact source
subtree and every source blob before registering that commit under the new key.
Then publish the helper/tests/documentation plus only the new template registry
entry on the fresh trusted main. Serialize these writes with the parent; no new
workflow or broadly enabled region selector is required.

The source inventory for social images verifies the retained asset bytes,
dimensions and MIME. It does not certify current product prices, availability,
business policies or a local delivery record. The scheduled Creator must
reconcile actual Business Truth and active Catalog before content review.
Updated catalog/image bindings require their real bytes, decoded dimensions and
MIME to be reverified together. Raw HTML is not a banner implementation path.

Before the actual scheduled invocation, the parent may register only the bounded
scope and its input records. The parent must not create the Bucheon branch,
registry site entry, hosted Worker or customer Draft and call that unattended
bootstrap. The existing scheduled Creator must perform the helper invocation,
consume its exact proposal through the supported Git path, and read it back.
Remote ref/Worker collision checks must use the currently authorized account
and real responses; 403, unavailable metadata and unqueried names are not proof
of absence. Existing credentials may be reused through supported mechanisms;
new credentials, access expansion and mandatory account approvals remain gated.

Example after those prerequisites are independently cleared:
```sh
python3 site-factory/engine/provision_goyang.py \
  --repo /path/to/verified/repository \
  --control-revision FULL_CURRENT_TRUSTED_MAIN_SHA \
  --target-revision absent \
  --site-key bucheon-flower-v2 \
  --launch-key bucheon-flower-v2-trial-20261004 \
  --output /path/to/existing-parent/new-bucheon-trial-bundle
```

The Pool's historical `bucheon-flower-v2-launch` key is not a valid trial key.
Link the explicit trial separately without fabricating an earlier launch.
The helper creates zero customer pages and grants no content approval.
The actual first query, Draft revision, independent review, frozen Queue,
Publisher run, Connector Issue, snapshot and exact isolated staging/hosted QA
must follow the existing roles. A trial of one genuine new detail proves only
that bounded connection; it is not complete city coverage, production release
or indexing. Official lower-region coverage remains a separate explicit
initial-open contract, and neither fixed50 nor quota filler is restored.

Do not assign a promised test time before the code/source pin, scope registration,
actual execution capabilities and account preconditions are ready. Reuse the
existing Creator/Reviewer tasks; any one-time time advancement must be recorded
separately from the regular cadence and restored afterward. A saved prompt or
schedule is not actual invocation evidence.
