# Scheduled Creator: deterministic Goyang bootstrap

`provision_goyang.py` prepares infrastructure only for the existing Goyang launch.
It is a local proposal builder, not a second publisher, workflow or scheduler.
It never contacts a service, commits/pushes, deploys, changes Airtable, creates
customer content, grants snapshot approval or enables production/growth.

## Fixed contract

- Repository: `joseungil-kr/fwith-site-factory`
- Site / launch: `goyang-flower-v2` / `goyang-flower-v2-launch`
- Target branch / root: `site-factory-goyang-v2` / `site-factory/goyang-flower`
- Trusted template: `flower-local-v2`, branch `site-factory-flower-v2-template`
- Source revision: `b1cd645bc252e0e11bdab6a0442bb3e0e6cfe3df`
- Source root: `site-factory/templates/flower-local-v2`
- Independently reviewed source tree: `cc0ce35a65c72829d4d9e9eedd2e7b18c261c8e4`
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
the scheduled Reviewer may use the already-existing `[SITE-STAGING-DEPLOY]`
issue trigger with `SITE_KEY: goyang-flower-v2` and
`EXPECTED_REVISION: <that full snapshot commit SHA>`. Do not add a new workflow,
schedule, broad trigger, token or permission. Hosted detail/hub/catalog/image,
mobile, metadata, snapshot and link QA remain required; a local bootstrap build
or homepage-only preview check cannot establish them.

## Reproducible local checks

```sh
python3 -m unittest discover -s site-factory/engine/tests -p test_provision_goyang.py -v
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
