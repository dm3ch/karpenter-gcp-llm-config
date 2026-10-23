---
name: karpenter-gcp-e2e
description: Run explicitly approved GCP E2Es for a PR and/or release. Inspect and authorize deployment side effects including cleanup, deploy the exact source/release, then use e2e-runner with standard selection and 20 workers. Publish/replace the PR report only with explicit posting approval.
---

# Karpenter GCP E2E

Paths below are **provider-root-relative**, not this skill directory; `.pi/` is a separate Git repository. Links are skill-relative.

## 1. Confirm scope and side effects

A PR number, release, review request, or invoking this skill is not live-operation consent. Gather supplied inputs without asking again:

- PR/repository and/or release; exact intended test/source revision.
- Existing project, location, region, prefix, cluster, namespace, and relevant overrides. Keep credentials/environment identifiers out of public reports.
- Runner location/ref if absent from the checkout.
- Selection: **`standard`**; global **`GINKGO_PROCS=20`**, unless explicitly overridden. Inherited Make default 4 is not an override. Do not silently reduce concurrency, narrow selection, or derive worker count from quotas; report capacity blockers and ask.
- **Separate posting approval and destination** if a PR report is wanted. Execution permission alone does not authorize a comment; otherwise return a local report.

Inspect selected scripts before consent/execution. **Current `hack/e2e-deploy.sh` always cleans labeled E2E resources and the test namespace before deployment**, can create a PriorityClass, publishes a source image, and installs/upgrades CRDs/controller. Obtain explicit approval for these operations on the resolved target, including embedded cleanup. No cleanup approval means stop: this script has no deploy-only switch.

Batch missing approvals/target questions; state source/release, selection, workers, side effects, and any proposed publication. Do not re-request consent already granted for that exact scope. Setup, teardown, IAM grants, environment repair, extra cleanup, retries, and redeployment are not implicit extensions. Never overlap another run on the cluster; check before deployment/cleanup as well as testing.

## 2. Resolve exact source, runner, and target

- Read repository instructions; inspect PR/release metadata and scripts. Use an isolated provider `.worktree/` unless in-place work was explicitly approved; preserve the user's checkout. Record exact SHA/tag and dirty state. For PR plus release, use PR tests against that published release unless told otherwise.
- Locate/read `hack/e2e-runner` (or supplied helper), preset definitions, reporting, environment, and cancellation before execution. Inspect help for side effects first; do not invent flags or substitute raw Ginkgo when the helper is absent. Ask for its path/ref.
- Current wrapper: `make e2e-tests E2E_SELECTION=standard GINKGO_PROCS=20 E2E_REPORT=<artifact-dir>/report.md`. Confirm against this revision, including `RELEASE_VERSION`. Selection supports `standard`, `gpu`, `all`, `provisioning`, or comma-separated feature directories; do not mix presets with directories. Standard excludes GPU **and extended local SSD**; GPU execution requires explicit consent.
- Current deployment derives cluster as `${E2E_PREFIX}-cluster` and fixes namespace to `karpenter-system`; cleanup also checks the prefix-derived context. Runner cluster/namespace overrides do **not** override deployment. Stop on unsupported targets; do not silently substitute another cluster or assume exported runner variables fix deployment.
- Create fresh ignored artifacts, e.g. `.pi/e2e-results/<timestamp>-pr-<number>/`. Preserve separate deployment/runner logs, statuses, and report; never reuse stale results.

## 3. Preflight and deploy

- Verify tools/auth without printing tokens or credential contents. Require project/location and explicit region rather than Make's fallback. Resolve credential paths absolutely. If using `E2E_SA_PATH`, map it to `GOOGLE_APPLICATION_CREDENTIALS`; supported gcloud login plus ADC does not require a key.
- When using the main checkout's allowed `.envrc`, use `direnv exec <main-checkout> <command>` in each shell, then enter the source worktree. Do not source/copy secrets or assume worktree inheritance. Never run `direnv allow`; ask the user if authorization is needed.
- Reconcile inherited project/location/region/prefix/cluster/namespace, pod ranges, tag key, and node/controller service accounts against the approved target. Keep resolved values private/run-local; apply overrides after direnv consistently for refresh/deploy/tests/monitoring. Do not rewrite `.envrc` without approval.
- Verify kubeconfig's exact target. If absent, refresh the approved target with `gcloud container clusters get-credentials <cluster> --location <location> --project <project>` using configured `KUBECONFIG`. On not-found, inspect metadata read-only and ask; do not provision. Helm uses the active context, not an automatically selected cluster.
- Verify effective node/controller identities, account existence/enabled state, existing node pool identity and relevant IAM read-only. An inherited account may belong to an obsolete prefix. Stop on mismatch; do not guess replacements, create accounts, grant roles, or redeploy without approval.
- Check relevant capabilities (e.g. IPv4 versus dual-stack); disclose coverage limits. Do not reconfigure infrastructure to broaden coverage.
- For source: run inspected `hack/e2e-deploy.sh` from the exact worktree with `RELEASE_VERSION` **unset**. For published release: set it explicitly to the requested chart version; do not build today's checkout instead. Record dirty builds honestly.
- Capture true deployment status with `pipefail`; require successful rollout/image verification before tests. Keep digest/details private and redact publication. On failure, stop—never test the old deployment. Produce a truthful failure report.

## 4. Run and observe

Use inspected helper/wrapper with the resolved selection and effective **20 global workers** (or explicit override), never manual per-suite waves. Verify flags/environment actually select that count.

The runner acquires/renews/releases Lease `karpenter-e2e-tests` in the controller namespace. Never bypass a held Lease or fall back to unlocked `make e2e-test`. This lock covers tests only, not deployment/cleanup.

Before launching, read [launcher, cleanup, and cancellation details](references/execution.md). Default to detached tmux with a run script, correct environment, `pipefail`, stage/status files, and separate deployment/runner exit codes. If wrappers break cancellation, build the inspected runner locally and invoke its binary with identical environment/arguments; record this launcher-only deviation. Do not change selection, locking, or reporting. If tmux is unavailable, ask before installation or a different launcher.

Tell the user session name and absolute log/report paths. Monitor with short calls; a timeout is not reason to duplicate a run. Cancel only on request; request shutdown rather than killing the session. Verify process/Lease/resource state before claiming clean termination; no leftover kills, Lease clearing, or extra deletion without approval.

After approved cleanup, verify previous-run objects and cloud instances are gone; a delete message is insufficient. Controllers can recreate claims while old workloads/pools remain. Stop if claims still reference prior-run pools; no finalizer removal or unapproved follow-up deletion.

Read the fresh report **and companion controller log** promptly. Check panics/unexpected errors, distinguish cleanup noise, and disclose missing samples/log collection failures even when specs pass. Preserve real exit status; no automatic retries, redeploys, quota changes, broadened selections, or cleanup. Report residual resources.

## 5. Report and optionally publish

- If deployment/runner failed before reporting, write an explicitly failed/cancelled/incomplete `report.md` with stage and evidence; never invent counts or label incomplete work passed.
- Identify tested PR SHA, deployed source/release, selection, effective workers, available counts/results, and coverage/environment limits. A changed PR head is not covered by the old run. Preserve original artifacts; make a separate sanitized publication copy if needed. No raw uploads without separate approval.
- No PR or no posting approval: return local report only. If authorized, use hidden marker `<!-- karpenter-gcp-e2e-report -->` plus sanitized content.
- Resolve authenticated account with `gh api`; paginate **all** PR issue comments. Match marker **and author identity**. PATCH the exact owned comment endpoint, otherwise POST. Use JSON file/stdin (e.g. `jq --rawfile`), not shell interpolation. Never use `gh pr comment --edit-last`, overwrite another author's/unrelated comment, or delete duplicates. With multiple owned matches update newest and flag duplicates; ask before adopting an older unmarked report's exact ID.
- Posting failure is separate from test failure; retain local report and never claim an update succeeded.

Finish with tested revision/release, selection/workers, deployment/test outcome, report path, authorized comment URL if published, blockers, and residual resources. A successful comment update cannot hide failed tests.
