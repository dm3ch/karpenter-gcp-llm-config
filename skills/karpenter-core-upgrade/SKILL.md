---
name: karpenter-core-upgrade
description: Discover the latest stable karpenter-core release and assess upgrading karpenter-provider-gcp, including required integration changes, new or changed feature gates, and optional features needing separate support. Use for core upgrade or migration requests. Require explicit user consent before implementation, draft PR publication, or creating feature follow-up issues.
---

# Upgrade karpenter-core

Produce an evidence-backed upgrade assessment first. A dependency bump is not proof of compatibility, and an upstream feature is not automatically supported on GCP.

Read [v1.15 migration lessons](references/v1.15-lessons.md) before the assessment. Those are historical examples, not current release facts or instructions to restore removed code.

## Scope and consent

- Default scope is read-only research plus local assessment/plan files. Do not change dependencies merely to discover the latest version.
- Ask which release policy is intended if ambiguous; recommend the latest stable, non-prerelease, non-draft release of `sigs.k8s.io/karpenter`, not the GCP provider's release. Do not select a development branch or an AWS provider version by mistake.
- Obtain explicit consent for the concrete implementation scope. Separately establish whether signed commits, fork pushes and opening a **Draft PR** are authorized. Plan approval alone is not publication consent.
- Obtain explicit consent for creating the proposed follow-up issues, including their scope and target repository. Drafting issue files locally is not permission to publish them.
- No live GCP/Kubernetes/IAM changes, deployments, E2Es, cleanup or reconciliation without explicit authorization for the operation and target environment. PR consent does not authorize these operations.
- Follow current repository instructions over historical session practices. Never push to canonical `origin`, bypass signing/hooks, post routine comments, ping maintainers, or promote a draft without permission.

Paths below are relative to the **provider repository root**, unless identified as skill-relative links. Resolve the root explicitly; `.pi/` can be a separate Git repository.

## 1. Establish the baseline and discover the target

1. Read repository instructions, inspect `git remote -v`, branch/status and the intended base. Preserve unrelated work and never inspect credentials or kubeconfigs for upgrade research. Follow the applicable remote safety policy; do not rewrite remotes speculatively.
2. Read the sibling [knowledge-base skill](../knowledge-base/SKILL.md), consult it for orientation, then verify claims against the checkout. Use memory for previous migrations (`mem_context`, then focused search/full observations), but prefer the merged result over an intermediate session design.
3. Record the current core version from `go.mod`, any `replace` directives, `vendor/modules.txt`, Go/toolchain version, Kubernetes libraries and controller-runtime. Check for an existing upgrade PR before proposing duplicate work.
4. Enable web tools if needed. Check official `kubernetes-sigs/karpenter` releases/tags and release notes, and corroborate with the Go module proxy. A non-mutating module query is:

   ```bash
   GOFLAGS=-mod=mod go list -m -json sigs.k8s.io/karpenter@latest
   ```

   This may populate the module cache but must not update project dependencies. Inspect `Version`, `Time`, `GoVersion` and replacement metadata; verify the selected stable tag exists. If sources disagree or cannot be reached, report that uncertainty rather than claiming a version is latest.
5. Record discovery time, exact current/target tags and source links. Pin that target for the assessment; do not silently move to another release halfway through implementation. If already current, report that and avoid a no-op PR.
6. Read all intervening release notes for a multi-release jump. Use `fetch_content` for upstream tagged repositories/source (not manual read-only clones). Compare exact old/new source, not only release summaries. AWS/Azure implementations are comparative evidence, not a GCP specification.

## 2. Analyze required integration and behavior changes

Build a concise table: **change | old/new contract | GCP impact | required/optional | affected files | validation**. Include source links or tag/file references for each conclusion.

Inspect at least:

- `pkg/cloudprovider` interfaces: methods, typed errors, repair policy validation/actions/fallbacks, optional capability fields, wrapper and fake implementations.
- `cmd/controller/main.go`: constructors, controller registration, shared caches/stores, matcher injection, lifecycle/startup validation, and feature-dependent wiring.
- Provider call sites of changed core APIs, including `pkg/controllers/interruption`. Inspect changed metric names, labels, reason values and units: code can compile but panic when recording a metric with obsolete labels.
- Core scheduling, disruption, repair, termination, registration and garbage collection behavior used by GCP. Check changed nil/zero defaults, budgets, vetoes, replacement ordering, timeouts, retries and idempotency, not just signatures.
- Go/module compatibility. Reconcile transitive dependencies with the existing repository graph; do not blindly downgrade Kubernetes/controller-runtime to match upstream's minimums or update unrelated modules.
- CRD fields/defaults/validation, served versions and ownership; controller/CRD upgrade ordering; chart values/schema/templates; Kubernetes RBAC and GCP IAM independently.
- Operator-facing docs, examples and `MIGRATION.md`. Unchanged gate defaults do **not** mean unchanged behavior for users who already enabled a gate. Preserve unrelated migration notes.

Classify each integration as mandatory compatibility, low-risk opt-in exposure, or separate feature work. A required method may safely return the upstream typed unsupported error if no configured path invokes it; do not advertise it as supported. Verify that the policy/controller configuration really keeps it unreachable.

## 3. Audit feature gates and related settings

Compare the complete old/new upstream gate registry/parser/defaults with GCP's explicit chart defaults and effective process configuration. Include existing gates whose behavior changed, gates removed/renamed/graduated, and newly introduced gates.

For each relevant gate, record:

| Gate | Old/new upstream stage and default | Current GCP default | GCP readiness and dependencies | Proposed exposure/default | Rationale and migration impact |
| --- | --- | --- | --- | --- | --- |

- Trace `values.yaml` → `values.schema.json` → deployment `FEATURE_GATES` → parser → controller registration/behavior. Explicit Helm values can override changed upstream defaults.
- Preserve intentional GCP overrides unless evidence and user approval justify changing them. Do not enable alpha features just because they are available, nor assume a graduated gate should remain in the serialized gate string.
- Separate “configurable”, “enabled by default”, and “actually supported”. Explain unsupported dependencies, partial support (for example static versus dynamic capacity), incompatible combinations, and whether upstream rejects or silently ignores them.
- Review new ordinary settings as well as gates: escape hatches, scheduler configuration, flags/env defaults, validation and deprecation timelines. Do not automatically expose every upstream option.
- Assess conditional RBAC, CRD prerequisites, GKE/Kubernetes version constraints and IAM. Add permissions only for approved supported paths; no speculative broad grants.
- Keep settings docs and generated chart docs aligned with the recommended defaults and limitations.

## 4. Assess new features separately

Inventory new optional interfaces and user-visible capabilities, even those absent from release headlines. For each, give:

- What core supplies versus what the GCP provider must implement.
- Concrete operator/workload benefit and relevant GKE/Compute/CSI constraints.
- Required APIs, IAM/RBAC, provider data, retry/replay/recovery semantics and compatibility requirements.
- Rough complexity, risk and useful validation; distinguish facts from estimates.
- Recommendation: include in the minimum migration, expose disabled/opt-in, defer with an issue, or not applicable. State why deferral does not break the supported migration path.

Search existing issues before recommending a new one. Record existing issue links, genuine gaps and dependencies. Do not invent universal constants or return success for unsupported functionality to satisfy an interface. Significant API/operator-visible feature work should follow the repository's proposal process rather than expand the migration silently.

## 5. Present the assessment and stop for approval

Save `.pi/plans/karpenter-core-<target>.md` (and a separate assessment if useful). Keep AI artifacts local/ignored. Include:

1. Baseline, pinned target, discovery date and sources.
2. Required-change table and changed operator behavior.
3. Gate/default/settings matrix with explicit recommendations.
4. Optional-feature assessment and deduplicated follow-up issue proposals.
5. Bounded implementation steps, docs/migration work and validation plan.
6. Risks, open decisions and explicit exclusions, including unapproved live validation.

For non-trivial plans, request the repository's oracle trajectory review and incorporate useful feedback before human approval. Summarize findings in chat and link the files; do not paste the entire document. Ask the user to approve implementation/default decisions, publication scope and specific follow-up issues. Do not use Plannotator outside the applicable plan-mode/user-requested workflow.

If the request was assessment-only or consent is absent, stop here.

## 6. Implement only the approved migration

- Work in an isolated provider worktree under the ignored `.worktree/` directory (or another location expressly permitted by current instructions). Never create sibling temporary repositories under `~/Workspace`.
- Read the sibling [unit-testing skill](../unit-testing/SKILL.md) before Go behavior/test changes. Implement narrow required adapters and wiring, preserve approved defaults, and avoid unrelated refactors or speculative feature scaffolding.
- Update the pinned core dependency and necessary transitive dependencies with the current repository workflow. Regenerate `go.sum` and vendor contents rather than editing vendor by hand.
- Inspect `Makefile`, generation scripts and `.github/workflows/` before selecting checks. Run `make update` for generated APIs/CRDs/docs/charts and inspect the result. Current generation copies canonical vendored core CRDs into both chart distributions; preserve intentional external-CRD exclusions. Re-evaluate this mechanism if upstream packaging changed.
- Update chart values/schema/env, conditional RBAC, settings docs and migration guidance together. Explain any behavior change for existing opt-in users and any escape hatch; do not claim unchanged semantics from unchanged defaults alone.
- Add small regressions for provider-owned contracts and actual failures. Test metric emissions with the new label contract. Prefer readable policy/configuration assertions to re-testing upstream matchers/controllers or asserting an unused constant unsupported stub.
- Add or extend behavioral E2E specs when needed for changed operator behavior, but do not execute them without separate live consent. Avoid many provisioning-heavy scenarios when one coherent scenario protects the contract.

## 7. Validate and review

Start with affected packages, then applicable generated/chart/CRD/docs checks and the current full presubmit loop for a broad migration. Record actual commands and outcomes; tool/environment failures are gaps, not passes.

- `make presubmit` currently runs generation verification, lint/deadcode, chart/CRD validation, unit tests and docs checks. Some checks rewrite files or demand a clean diff; inspect changes and distinguish expected migration edits from generator drift. Never bypass checks to publish.
- Compile E2E packages without running their suites when appropriate. Check their bootstrap/TestMain behavior first and use the repository-supported compile-only method; `go test ./...` is not a safe generic compile command for live suites.
- Review changed runtime paths, not just build success. Use a fresh-context review for concrete non-trivial diffs, then compare every approved plan step against the final diff/check evidence. Report deviations and residual risks before publication.
- Read [the E2E skill](../karpenter-gcp-e2e/SKILL.md) only when live validation is requested. Obtain the operation/environment consent it requires. Revalidate the exact tested SHA, controller image, preset and result artifacts; do not attribute an older head's run to the final head. Separate environment incompatibilities from regressions and report both honestly.

## 8. Publish a Draft PR and follow-up issues only as authorized

1. Inspect current PR/issue templates and fill all required fields. Draft issue bodies locally first, with benefit, provider work, acceptance criteria, dependencies and migration context. Link existing issues instead of duplicating them.
2. Before an authorized push, fetch and rebase onto the latest target base; preserve unrelated changes during conflicts, rerun applicable checks and verify signed/DCO commits. Stop for interactive signing help if signing fails.
3. Push only to the explicitly authorized user fork. For an authorized rewrite, verify the old remote head and use an exact force-with-lease, never blind force. No direct canonical `origin` pushes.
4. Open the PR with `--draft`, explicit base repository, base branch and fork head. Complete the template, appropriate `/kind`, honest docs/migration checklist, test evidence, limitations and existing feature-tracking links. Remove dangling `Fixes #`; use `N/A` when no issue is closed.
5. Create only the specifically approved follow-up issues using the enhancement template. Link the real issue URLs in the authorized PR body update; do not post unsolicited comments, review requests or maintainer pings. If issue consent is absent, return local drafts/existing links instead.
6. Verify PR URL/head/base/draft state and issue URLs. Report completed plan steps, deferred features, checks run, unrun live validation and the final commit. Do not merge, promote, deploy or clean infrastructure as an implicit final step.
