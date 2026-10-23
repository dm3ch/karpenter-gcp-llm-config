---
name: karpenter-core-upgrade
description: Discover the latest stable karpenter-core release and assess upgrading karpenter-provider-gcp, including integration changes, feature gates/settings, and optional provider support. Assessment first; explicit consent before implementation, fork publication, follow-up issues, or live validation.
---

# Upgrade karpenter-core

A dependency bump is not compatibility evidence; an upstream feature is not automatically supported on GCP. Default to read-only research and local assessment files. Paths below are **provider-root-relative**; `.pi/` is a separate Git repository. Links are skill-relative.

For repair/metrics migration examples or historical questions, read [v1.15 lessons](references/v1.15-lessons.md). These are historical evidence, not current release facts or instructions to restore removed code.

## 1. Establish baseline and pin a target

- Read repository instructions; inspect remotes, branch/status, intended base, and existing upgrade PRs. Preserve unrelated work, follow remote safety policy without speculative rewrites, and never inspect credentials/kubeconfigs for research.
- Use the [knowledge-base skill](../knowledge-base/SKILL.md) for unfamiliar context; verify against source. For previous migrations use `mem_context`, then focused search/full observations; merged results supersede intermediate designs.
- Record core version/replacements from `go.mod` and `vendor/modules.txt`, Go/toolchain, Kubernetes libraries, and controller-runtime.
- Resolve ambiguous release policy; recommend the latest stable, non-prerelease, non-draft **core** release (`sigs.k8s.io/karpenter`), not the GCP/AWS provider or a development branch.
- Enable web tools as needed. Check official `kubernetes-sigs/karpenter` releases/tags/notes and corroborate with the Go module proxy. `GOFLAGS=-mod=mod go list -m -json sigs.k8s.io/karpenter@latest` may populate the cache but must not change project dependencies. Inspect version/time/GoVersion/replacements; verify the stable tag. Report disagreement/unavailable sources rather than claiming certainty.
- Record discovery date, exact baseline/target, and source links; keep the target pinned. If already current, avoid a no-op PR. Read intervening release notes and compare exact tagged old/new source using `fetch_content`, not manual read-only clones. Other providers are comparative evidence, not a GCP specification.

## 2. Assess required integration and effective behavior

Build a table: **change | old/new contract | GCP impact | required/optional | files | validation**, with source/tag references. Inspect:

- CloudProvider interfaces, typed errors, repair validation/actions/fallbacks, optional capabilities, wrappers and fakes.
- `cmd/controller/main.go` constructors/controller registration, shared stores/caches, matchers, lifecycle/startup validation, and feature-dependent wiring.
- Changed core call sites, including interruption handling. Audit metric names, labels, reason casing, and units: obsolete label emissions can compile yet panic. Test provider-owned emissions.
- Scheduling, disruption, repair, termination, registration, and garbage collection: nil/zero defaults, budgets/vetoes, replacement ordering, initialization, timeouts, retries, and idempotency—not just signatures.
- Module compatibility: reconcile necessary transitives, without unrelated updates or blindly downgrading Kubernetes/controller-runtime to upstream minimums.
- CRD fields/defaults/validation/served versions/ownership, controller-versus-CRD upgrade order, chart values/schema/templates, Kubernetes RBAC and GCP IAM independently.
- Operator docs/examples/`MIGRATION.md`; preserve unrelated notes. Unchanged gate defaults do not prove unchanged behavior for existing opt-in users.

Classify mandatory compatibility, low-risk opt-in exposure, and separate feature work. A required method may return the upstream typed unsupported error only if supported configuration keeps it unreachable; verify that path rather than advertising support or faking success.

## 3. Audit gates, settings, and optional features

Compare the **complete** old/new upstream gate registry/parser/defaults, including changed existing gates and removed/renamed/graduated gates. Trace Helm values → schema → deployment `FEATURE_GATES` → parser → registration/runtime.

Record: **gate | old/new stage/default | current GCP default | readiness/dependencies | proposed exposure/default | rationale/migration impact**.

Preserve intentional GCP overrides unless evidence and approval justify changes. Separate configurable, default-enabled, and actually supported; explain partial static/dynamic support, prerequisites, incompatible combinations, and rejection versus silent ignoring. Do not enable alpha features automatically or serialize graduated gates blindly.

Review ordinary settings too: flags/env defaults, validation, escape hatches, scheduler options, deprecations, conditional RBAC/CRDs, GKE/Kubernetes versions and IAM. Add only approved permissions; align generated settings/chart docs.

Inventory optional interfaces/capabilities even absent from headlines. For each, explain core versus provider responsibilities, operator benefit, GKE/Compute/CSI constraints, APIs/permissions/data, replay/recovery/idempotency, compatibility, estimated complexity/risk, and useful validation. Recommend minimum migration, disabled opt-in, deferral, or not applicable; show why deferral preserves the supported migration path. No invented universal constants.

Search existing issues before proposing follow-ups; record existing links, gaps, and dependencies. Significant feature/API work follows the proposal process, not silent migration expansion.

## 4. Save assessment and obtain approval

Save `.pi/plans/karpenter-core-<target>.md`, ignored/local, containing baseline/target/date/sources, required changes, gate/settings matrix, optional-feature decisions and deduplicated issue proposals, bounded steps/docs/validation, risks, exclusions, and unapproved live checks.

Follow applicable oracle trajectory review for non-trivial plans, then summarize with the file path and stop for human approval. Use Plannotator only in the applicable plan-mode/user-requested workflow.

Establish **separate explicit scopes** for implementation/default decisions, signed commits, fork push/Draft PR, and each follow-up issue/target repository. Plan approval is not publication consent. Local issue drafts are not permission to publish. Deployment, E2Es, IAM, cleanup, and reconciliation require their own operation/environment approval. Assessment-only requests stop here.

## 5. Implement only approved scope

- Use an ignored provider `.worktree/` unless in-place work was explicitly approved; never temporary sibling repositories under `~/Workspace`.
- Read the [unit-testing skill](../unit-testing/SKILL.md). Make narrow adapters/wiring, preserve approved defaults, and avoid speculative scaffolding/refactors.
- Update core and necessary transitives; regenerate sums/vendor through the repository workflow, not hand edits.
- Inspect Makefile/generation/CI. Run applicable generation and inspect it: current scripts copy canonical vendored core CRDs to both charts and intentionally exclude external CRDs. Re-evaluate if upstream packaging changes.
- Align chart values/schema/env, conditional RBAC, settings docs, and migration notes; explain changed opt-in semantics and escape hatches.
- Protect provider-owned behavior with focused regressions, including changed metric contracts. Do not re-test upstream controller/matcher internals or add assertions solely for unreachable unsupported stubs.
- Add behavioral E2E specs when needed, favoring one coherent scenario over many provisioning-heavy variants; executing them requires separate consent.

## 6. Validate, review, and publish only as authorized

Start with affected packages, then applicable generation/chart/CRD/docs checks and full presubmit for broad migrations. Record actual commands/results; environment failures are gaps, not passes. `make presubmit` includes generation, lint/deadcode, chart/CRD, unit, and docs checks; some mutate files or require a clean tracked diff. Distinguish expected edits from drift, never bypass checks.

Compile E2Es only through a verified compile-only path after checking bootstrap/TestMain; `go test ./...` is not a safe generic compile command. For authorized live checks use the [E2E skill](../karpenter-gcp-e2e/SKILL.md); record exact SHA/image/preset/artifacts and separate infrastructure incompatibility from regression.

Review concrete non-trivial diffs with fresh context, then compare every approved plan step against diff/check evidence; report deviations and residual risk before publication.

For authorized publication: fill current templates (`/kind`, docs/migration checklist, `N/A` instead of dangling `Fixes #`), fetch/rebase latest target, rerun checks, and verify signed/DCO commits. Stop for signing help if needed. Push only to the approved fork; authorized rewrites require verified old head and exact force-with-lease. Create PR with explicit repository/base/fork head and `--draft`. Publish only specifically approved enhancement issues, link real URLs in an authorized body update, and verify PR head/base/draft state and issue URLs. No unsolicited comments/pings, promotion, merge, deployment, or cleanup as implicit final steps.
