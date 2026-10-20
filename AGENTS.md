# AGENTS.md

Guidance for AI coding agents working in the karpenter-provider-gcp repository.

This file is maintained in the separate `.pi/` Git repository. Root-level
`AGENTS.md` symlinks to this file. All repository paths and commands below are
relative to the karpenter-provider-gcp root, not `.pi/`.

## Repository overview

This repository is the GCP cloud provider for Karpenter. It is a Go/Kubernetes controller with Helm charts, generated CRDs, provider integrations, and Ginkgo-based e2e tests against real GKE clusters.

Key areas:

- `cmd/controller/` — controller entrypoint.
- `pkg/apis/v1alpha1/` — public API types for GCP provider resources.
- `pkg/cloudprovider/` — Karpenter cloud provider integration.
- `pkg/controllers/` — reconcilers and controller logic.
- `pkg/providers/` — GCP/GKE provider implementations, pricing, offerings, instance types, images, disk types, metadata, and node pool templates.
- `charts/` — Helm charts and CRDs.
- `docs/`, `examples/`, `MIGRATION.md` — user-facing documentation and upgrade guidance.
- `test/suites/` and `test/pkg/` — e2e suites and test helpers.
- `hack/` — generation, docs, CRD, pricing, and e2e helper scripts.
- `proposals/` — design proposals for significant/API/operator-visible changes.

## Hard rules

- Never push directly to `origin`. If the user explicitly asks for a push/PR workflow, push only to the user's own fork remote and create a draft PR back to this repository.
- Do not push branches, tags, commits, or this instructions file unless the user explicitly asks you to push.
- Never write comments, messages, review requests, maintainer pings, PR comments, issue comments, or other calls to action directed at humans without explicit user request or approval.
- Treat service account JSON files, kubeconfigs, GCP project IDs, and credentials as sensitive. Do not print, commit, summarize, or copy secrets.
- Do not disable GPG signing or bypass commit hooks/checks unless the user explicitly authorizes the exact action.
- Open PRs as draft unless the user explicitly requests otherwise.

## Development commands

Common commands:

```bash
make help                 # list documented targets
make toolchain            # install repo-managed developer tools
make tidy                 # go mod tidy
make download             # go mod download
make update               # regenerate headers, generated code, docs, Helm docs, PDCSI compatibility data
make verify               # golangci-lint with auto-fix enabled, then require clean diff
make ci                   # CI verification subset
make presubmit            # full developer loop: toolchain + verify + ci
make ut-test              # race-enabled unit tests for ./pkg/...
make chart-lint           # helm lint charts/karpenter and charts/karpenter-crd
make verify-crds          # validate generated CRDs
make docs-lint            # mdox markdown formatting check
make docs-fix             # mdox markdown formatting fix
```

When changing generated APIs, CRDs, docs, Helm values, or compatibility data, run `make update` and inspect the generated diff.

For a focused Go test, prefer the narrowest useful command first, for example:

```bash
go test ./pkg/providers/instance/...
go test ./pkg/controllers/nodeclaim/... -run TestName
```

Before claiming a change is ready, run the relevant subset of CI locally. For broad changes, use `make presubmit` if the environment has the required tools.

## Formatting and linting

- Go version is declared in `go.mod`.
- `golangci-lint` configuration is in `.golangci.yaml` and enables auto-fix formatters (`gci`, `goimports`).
- Imports should be grouped as standard library, third-party, then local module (`github.com/cloudpilot-ai/karpenter-provider-gcp`).
- CI runs `make toolchain`, golangci-lint, and `make ci`.
- `make verify` may rewrite files; always check `git diff` afterward.

## Unit-testing policy

- Before implementing Go behavior changes or writing/reviewing unit tests, read the [unit-testing skill](.pi/skills/unit-testing/SKILL.md).
- Prioritize regression confidence, readability, and maintainability. Coverage is diagnostic, not a target; neither 100% coverage nor a test line-count quota is required.
- Test contracts through observable results, state, and meaningful side effects, not incidental helper calls, internal structure, or call order. Behavior-preserving refactors should not require rewriting tests.
- Choose representative cases for distinct behaviors, realistic failure paths, and important boundaries. Avoid redundant permutations and tests added only to execute uncovered lines.
- Prefer real domain values and existing small fakes. Use GCP HTTP mocks only when the provider/SDK adapter contract itself is under test, not to reach unrelated business logic.
- Do not redesign production code just for mock convenience or remove existing regression protection merely to make tests shorter.

## E2E workflow

E2E tests run against real GKE infrastructure and require explicit environment variables:

```bash
export E2E_PROJECT_ID=<gcp-project-id>
export E2E_SA_PATH=/path/to/service-account-key.json
export E2E_LOCATION=<zone-or-region>
# Optional:
export E2E_PREFIX=karpenter-e2e
export E2E_REGION=us-central1
```

Targets:

```bash
make e2e-setup        # create/reuse cluster and supporting infra
make e2e-deploy       # build and deploy controller
make e2e-tests        # run all e2e suites; GINKGO_PROCS defaults to 4
make e2e-test SUITE=provisioning FOCUS="amd64 on-demand"
make e2e-check-clean  # report orphaned resources without deleting
make e2e-teardown     # delete e2e infrastructure
```

Do not run e2e setup, deploy, teardown, or broad e2e suites unless the user explicitly asks and confirms the target project/environment. Use the repository e2e skill or existing e2e docs/scripts for quota-aware work.

## Design and API changes

For significant changes, prefer a proposal before implementation. This includes:

- architectural redesigns or replacement of major subsystems;
- new `GCENodeClass` fields, CRDs, or changes to existing API fields;
- operator-visible behavior changes;
- upgrade/migration requirements;
- multi-phase work spanning several PRs.

Use `proposals/0000-template.md` and follow `CONTRIBUTING.md`. Keep docs, examples, charts, and `MIGRATION.md` aligned with API/operator-visible changes.

## PR and issue hygiene

- Follow `.github/PULL_REQUEST_TEMPLATE.md` and issue templates exactly when creating PRs/issues.
- Fill required template sections; use `N/A` where a section does not apply.
- For PRs, include the appropriate `/kind ...` line and update docs/MIGRATION checklist honestly.
- Do not leave `Fixes #` dangling if there is no issue.
- Rebase onto the latest target branch before pushing/opening a PR if the user asks for that workflow.

## Working style

- Do implementation work in a git worktree under `.worktree/` unless the user explicitly asks to work in the main checkout.
- Inspect existing patterns before introducing new abstractions.
- Keep changes small and idiomatic; prefer straightforward Go over clever generalization.
- Preserve Kubernetes/controller-runtime and Karpenter conventions already used in nearby code.
- For provider behavior, ensure errors, eventual consistency, nil/empty cloud responses, and retry/idempotency behavior match neighboring providers.
- Avoid broad refactors unless they are necessary for the requested change.
- When editing tests, prefer realistic Ginkgo/Gomega assertions and fixtures consistent with adjacent suites.
- If a command would mutate live GCP, Kubernetes, GitHub, or git remote state, stop and ask unless the user already authorized that exact action.

## Useful local checks before finishing

Use the smallest set that covers the change:

- Go-only logic: `go test ./pkg/...` or a narrower package test.
- Controller/provider changes: relevant package tests plus `make verify` if tooling is available.
- API/CRD/chart changes: `make update`, `make verify-codegen`, `make verify-crds`, `make chart-lint`.
- Docs/proposals: `make docs-lint` or `make docs-fix`.
- Broad changes: `make presubmit`.
