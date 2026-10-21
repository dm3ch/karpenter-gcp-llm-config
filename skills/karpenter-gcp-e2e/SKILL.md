---
name: karpenter-gcp-e2e
description: Run explicitly approved Karpenter GCP E2Es for a requested PR and/or release version. Deploy with e2e-deploy.sh first, use e2e-runner presets (standard by default) with 20 Ginkgo processes, then create or replace a PR comment from report.md. Never deploy or execute E2Es without explicit user approval for the target environment.
---

# Karpenter GCP E2E

## Consent and inputs

Creating, reading, or invoking this skill is not itself permission to run E2Es.
Only deploy and run tests after an explicit user request/approval for those
operations and the target GCP project/cluster. A PR number, release version,
review request, or request to prepare commands alone is not consent.

Gather these inputs, using supplied values rather than asking again:

- PR number/URL and repository, release version, or both.
- Intended source revision and the existing E2E project, location, cluster,
  namespace, and resource prefix. Keep credentials and environment identifiers
  out of public reports.
- `e2e-runner` helper location/ref, if not discoverable in the requested source.
  The user may supply this with the run request; do not assume a globally
  installed executable or invent a helper CLI.
- Preset: **`standard`** unless explicitly overridden.
- `GINKGO_PROCS`: **`20`** unless explicitly overridden. An inherited default of
  4 is not a user override. Do not derive concurrency from automated quota
  detection or silently reduce it. Report capacity blockers and ask before
  changing concurrency or narrowing the requested preset.
- PR comment destination, when a PR is supplied. A request to execute this
  workflow includes publishing its report on that PR; if the user requests
  local-only testing or posting permission is unclear, ask before posting.

Before live actions, confirm any missing deployment/test authorization and target
in one concise question. State the revision/release, preset, concurrency, and
that the workflow deploys first and publishes/replaces the PR report. Do not
repeatedly ask for authorization already explicitly granted for that exact scope.

Never run setup, teardown, additional cleanup, or infrastructure repair under
this approval. Ask separately if the existing environment is missing or broken.
Do not start another run against a cluster already used by a different run.

## Resolve source and helper (read-only)

All repository paths below are relative to the provider repository root, not
this skill directory. Locate the root with Git; `.pi/` is a separate repository.

1. Read repository instructions and inspect the requested PR/release metadata.
   Use an isolated worktree under the provider repository's `.worktree/` for
   PR/source work; do not reset or overwrite the user's checkout.
2. Resolve and record the exact PR head SHA or release tag/commit. For a PR plus
   release version, test the PR's tests against the specified published release
   unless the user says otherwise; make this distinction explicit in the report.
3. Locate `e2e-runner` in the requested checkout or at the user-provided path/ref.
   Read its documentation, implementation, preset definitions, and report output
   behavior. Use its documented help only after inspecting it for side effects.
   Discover the actual invocation, preset option, concurrency option/environment
   handling, artifact directory option, and `report.md` location. Do not guess
   flag names. The previous workflow used `hack/e2e-runner`, wrapped by
   `make e2e-tests E2E_SELECTION=standard GINKGO_PROCS=20`, with
   `E2E_REPORT=<artifact-dir>/report.md`. Use this wrapper when inspection
   confirms it invokes the helper and its signal handling is suitable for the
   launcher below; older checkouts may run raw Ginkgo instead. If a Make/`go run`
   wrapper prevents reliable cancellation, build the inspected helper into the
   local artifact directory and invoke that binary with the wrapper's exact
   environment and arguments. Record this launcher-only deviation; do not change
   selection, concurrency, locking, or reporting behavior.
   If absent, ask for its path/ref rather than substituting raw Ginkgo or a
   legacy Make target and silently losing preset behavior.
4. Verify `standard` (or the requested preset) exists. Prefer the helper's preset
   definitions; do not duplicate suite lists in this skill. Inspect PR-provided
   scripts before executing them, especially when credentials are available.
5. Create a fresh, gitignored local artifact directory for this run, e.g.
   `.pi/e2e-results/<timestamp>-pr-<number>/`. Preserve deployment log, runner
   log, test artifacts, and `report.md` separately. Never reuse a stale report.

## Preflight and deploy the right version

- Check required tools and authentication without printing tokens, credential
  contents, or service-account JSON. Resolve credential paths to absolute paths.
- The previous workflow loaded the main checkout's ignored `.envrc` via
  `direnv`, including its `KUBECONFIG`. Use `direnv exec <main-checkout> <command>`
  in each new shell, then change into the selected source worktree. Do not assume
  a worktree inherits a sibling checkout's `.envrc`. Never copy secrets into
  worktrees or source `.envrc` directly. If it is not allowed, ask the user to
  inspect/authorize it; do not run `direnv allow` on their behalf.
- Treat inherited settings as unverified, even when `direnv` is allowed. Before
  deployment, reconcile project, location, region, prefix, cluster, namespace,
  pod ranges, tag key, and node service-account overrides with the approved
  existing target. Require an explicit region rather than accidentally using
  Make's `us-central1` default. A user-supplied cluster URL can identify the
  intended target; do not silently substitute another discovered cluster. Keep
  resolved values in a private run-local configuration; do not rewrite `.envrc`
  without approval. Apply those overrides after loading `direnv`, consistently
  for credential refresh, deployment, tests, and monitoring.
- Read the selected checkout's `hack/e2e-deploy.sh` and the runner's environment
  contract. Require `E2E_PROJECT_ID` and `E2E_LOCATION`. Map `E2E_SA_PATH` to an
  absolute `GOOGLE_APPLICATION_CREDENTIALS` path when supplied. If this revision
  supports active `gcloud` login plus Application Default Credentials, validate
  both without printing tokens; do not require a service-account key unnecessarily.
- If kubeconfig is empty or the approved context is absent, refresh it using
  `gcloud container clusters get-credentials <cluster> --location <location>
  --project <project>` with the resolved target and configured `KUBECONFIG`.
  Verify the resulting context exactly matches that target. On a not-found
  response, inspect cluster metadata read-only and ask to resolve mismatches;
  do not run setup or assume the environment needs recreation.
  `e2e-deploy.sh` uses Helm's active context; it does not select the cluster.
  Do not deploy on a context mismatch. Align runner cluster/namespace settings
  with the deployment; do not rely on unrelated inherited defaults.
- Before any cleanup or deployment, validate `E2E_NODE_SERVICE_ACCOUNT` and the
  effective chart/controller default against IAM in the target project. An
  inherited account can belong to an obsolete resource prefix even when the
  context is correct. Confirm the account exists and is enabled; inspect the
  existing node pool's service account and relevant IAM bindings as evidence,
  rather than guessing a replacement from its name. Stop on a mismatch and ask
  before correcting the setting or redeploying; do not create accounts or grant
  roles under E2E approval. Also verify any configured controller identity.
- Inspect cluster capabilities relevant to the PR (for example, IPv4-only versus
  dual-stack). State coverage limitations before testing and in the report;
  passing regression tests on IPv4-only infrastructure is not dual-stack
  validation. Do not reconfigure the cluster to expand coverage without consent.
- For a **PR/source run**, execute `hack/e2e-deploy.sh` from the exact source
  worktree with `RELEASE_VERSION` explicitly unset. This builds/pushes the local
  controller image and installs local charts. Check for dirty source and record
  it; never claim a dirty build is exactly the pristine PR SHA.
- For a **published release run**, execute `hack/e2e-deploy.sh` with
  `RELEASE_VERSION` explicitly set to the requested published chart version.
  Do not build the current checkout's controller instead.
- Save deployment output and retain the real exit status if piping through
  `tee` (use `pipefail`). Require successful deployment and read-only rollout /
  image verification before testing. Record the deployed version or image
  digest privately; redact sensitive registry/project details for publication.
- On deployment failure, stop; do not test the previously installed version.
  Prepare a failure report and follow the reporting steps below.

## Run via e2e-runner

Use the helper's documented invocation from the selected test checkout with the
resolved preset and **`GINKGO_PROCS=20`** (or the explicit user override).
If the helper uses a CLI concurrency option instead, pass that too/as required
and verify the effective worker count. Do not assume exporting an environment
variable overrides a hard-coded runner default.

The previous runner selections were `standard` (non-GPU), `gpu`, `all`,
`provisioning`, or comma-separated feature directories. Verify these against
this revision. Do not mix preset names with directory lists. GPU execution
requires explicit consent for that run. Twenty workers is the global spec
concurrency, not twenty per feature; do not add manual per-suite waves.

The runner acquires/renews/releases the Kubernetes Lease `karpenter-e2e-tests`
(previously in `karpenter-system`). Never bypass a held Lease or use an unlocked
legacy `make e2e-test` fallback. This Lease protects tests only: check for active
runs before deployment and any cleanup too. Inspect whether this revision's
deploy target performs cleanup; get separate consent for that cleanup scope
before invoking it. Never add ad-hoc deletion sequences without explicit cleanup
approval. After approved cleanup, verify prior-run objects and cloud instances
are actually gone, not merely that `kubectl delete` printed their names. A live
controller may recreate NodeClaims while old workloads/NodePools still exist;
selector deletion is a snapshot, not protection against that race. If new claims
still reference previous-run NodePools, stop before tests and report them. Only
perform a follow-up deletion within explicitly approved cleanup scope, after
checking no active tests; never force-remove finalizers to hide the problem.

Launch long tests in a detached `tmux` session by default, not a long abortable
agent Bash call. Use a run script in the artifact directory, load its environment,
run the approved command with `pipefail`, capture the actual runner/Make status
(e.g. `${PIPESTATUS[0]}` immediately after `tee`), and write an `exit-code` file.
Record the current stage before each operation and keep separate deployment,
runner, and overall exit statuses. Preserve the interrupted/failed stage in any
fallback report instead of overwriting it with a generic `finished` marker.
Tell the user the session name and absolute log/report paths. Monitor using
short calls; never launch a duplicate because a monitoring call timed out.
If tmux is unavailable, ask before installing it or choosing another launcher.

Inspect the launcher's signal path before starting. `make` and `go run` may exit
on Ctrl-C before the helper writes its report or releases its Lease; a successful
`tmux send-keys` is not proof of graceful shutdown. Prefer running the compiled
helper directly when these wrappers cannot preserve shutdown handling, while
retaining the exact inspected environment/arguments and runner exit status.

Cancel only when requested, using `tmux send-keys -t <session> C-c` to request
shutdown; do not use `tmux kill-session` or agent-tool abort as normal
cancellation. Inspect the helper's own cancellation implementation too; it may
kill child process groups even when the parent handles interrupts. After
interruption, check for surviving runner, Ginkgo, and test-binary processes,
Lease ownership/renewal, and residual E2E resources read-only. Do not call it a
clean shutdown unless those checks support that conclusion. Lease expiry alone
is not evidence that tests stopped; do not steal/delete/clear the Lease or kill
leftovers without approval. A missing session/exit marker is not success. If the
helper did not produce a report or controller logs, collect logs read-only and
write an explicitly cancelled/incomplete fallback report without invented totals.

Capture runner output and its actual exit status without masking failures with
`tee` or report-generation commands. Let the helper generate `report.md` and its
normal artifacts. Read the report and companion controller log as soon as the
run finishes. Scan for panics and unexpected errors, distinguish intentional
cleanup/shutdown noise from real problems, and disclose missing resource samples
or log collection failures even if specs passed.

On failed tests, still collect and publish the report. Do not automatically
retry, broaden the preset, redeploy, change quotas, or delete resources outside
the approved scope. Report residual resources and any suggested follow-up.

## Publish or replace the PR report

1. Read the newly generated `report.md`. If the runner failed before producing
   one (or deployment failed), write a truthful `report.md` stating the failed
   stage, that tests did not run/complete, and the available evidence. Never
   fabricate test counts or label an incomplete run as passed.
2. Ensure the report identifies the tested PR head SHA, deployed source/release,
   preset, effective worker count, result/counts when available, and any
   environment or coverage limitations. Preserve the helper's report; add
   missing context as needed. Keep raw logs/artifacts local unless upload is
   separately approved. Redact secrets and sensitive environment identifiers
   before posting; retain a separate sanitized publication copy if necessary.
3. If no PR was supplied, save the report locally and return its path; do not
   guess a PR or create one. If the PR head changed during testing, label the
   report with the tested SHA and flag that it does not cover the new head.
4. Use a stable hidden marker in the posted body:
   `<!-- karpenter-gcp-e2e-report -->`, followed by the sanitized `report.md`
   content. Do not use `gh pr comment --edit-last`: that may replace an unrelated
   comment.
5. With `gh api`, resolve the authenticated account, then list **all pages** of
   `/repos/{owner}/{repo}/issues/{pr}/comments`. Match both the marker and that
   account's author identity. If a matching comment exists, PATCH its exact
   `/repos/{owner}/{repo}/issues/comments/{comment_id}` endpoint with the new
   body; otherwise POST to the PR's issue-comments endpoint. Send the body via
   a JSON file/stdin (e.g. `jq --rawfile body ...`), not shell interpolation.
   Never edit another author's comment or delete duplicate comments without
   approval. If multiple owned matches exist, update the newest and flag them.
   For an older unmarked E2E report comment, inspect ownership and content and
   ask to adopt its exact comment ID rather than blindly appending a duplicate
   or overwriting unrelated text; include the marker when replacing it.
6. If posting fails, keep the local report and disclose the publishing failure
   separately from the test outcome. Do not claim the PR comment was updated.

Finish with the tested revision/release, preset, concurrency, deployment and test
outcome, local `report.md` path, PR comment URL (if published), and any blockers.
Do not hide failed tests behind a successful comment update.
