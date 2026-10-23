# Repository guidance

This is the GCP provider for Karpenter: a Go/Kubernetes controller with Helm charts, generated CRDs, and Ginkgo E2Es against real GKE infrastructure.

Root `AGENTS.md` symlinks here, in the separate `.pi/` Git repository. Commands and paths below are relative to the **provider root**, not `.pi/`. Check which repository a Git command will affect.

## Hard constraints

- Never push to canonical `origin`. Push only to an explicitly authorized user fork; no push or publication without user approval. Open PRs as **draft**.
- Never post comments, issues, review requests, maintainer pings, or other human-directed messages without explicit approval. An E2E request alone is not permission to post its report.
- Live GCP/Kubernetes/IAM/Terraform changes require explicit approval for the operation and target environment. Implementation/PR approval is not deployment, cleanup, reconciliation, or E2E approval. Deployment scripts can include cleanup: inspect their side effects before requesting consent.
- Never print, copy, summarize publicly, or commit credentials, service-account JSON, kubeconfigs, or sensitive environment identifiers/project IDs.
- Preserve GPG signing and hooks/checks. Stop for interactive signing help if needed; never bypass them without exact user authorization.
- Implement in an ignored `.worktree/` unless the user explicitly approves in-place edits. Preserve unrelated changes; no temporary sibling workspaces under `~/Workspace`.

## Code map and working style

- `cmd/controller/`: entrypoint; `pkg/cloudprovider/`: core integration.
- `pkg/apis/v1alpha1/`: provider APIs; `pkg/controllers/`: reconcilers.
- `pkg/providers/`: GCP/GKE adapters, instance types, pricing, images, disks, metadata, and node pool templates.
- `charts/`, `docs/`, `examples/`, `MIGRATION.md`: packaging and operator guidance.
- `test/suites/`, `test/pkg/`, `hack/`: E2Es, helpers, and generation/tooling.

Inspect nearby patterns first. Prefer small, idiomatic Go changes over new abstractions or broad refactors. Preserve controller-runtime/Karpenter conventions; consider nil/empty cloud responses, eventual consistency, typed errors, retries, and idempotency.

## Load the relevant skill

Paths are provider-root-relative:

| Task                                                | Skill                                                                 |
|-----------------------------------------------------|-----------------------------------------------------------------------|
| Unfamiliar architecture/subsystem context           | `.pi/skills/knowledge-base/SKILL.md`; verify synthesis against source |
| Go behavior changes or writing/reviewing unit tests | `.pi/skills/unit-testing/SKILL.md`                                    |
| Core upgrade/migration assessment                   | `.pi/skills/karpenter-core-upgrade/SKILL.md`                          |
| Explicitly authorized live E2Es                     | `.pi/skills/karpenter-gcp-e2e/SKILL.md`                               |

## Validation

Inspect current `Makefile` and `.github/workflows/`; run the smallest applicable CI subset before claiming readiness or committing.

| Change                           | Checks                                                                                                         |
|----------------------------------|----------------------------------------------------------------------------------------------------------------|
| Go logic                         | Focused `go test` first; `make ut-test` for race-enabled `./pkg/...` tests; `make verify` for lint/format      |
| Generated APIs/CRDs/charts/data  | `make update`, inspect output, then `make verify-codegen`, `make verify-crds`, `make chart-lint` as applicable |
| Prose in `docs/` or `proposals/` | `make docs-lint` (`make docs-fix` rewrites); not a check for `.pi/` files                                      |
| Broad changes                    | `make presubmit`: toolchain, verify, and CI checks                                                             |

`make update` also tidies/downloads modules; do not run it for ordinary prose-only edits. `make verify` auto-fixes formatting; it and `verify-codegen` require the **entire tracked diff** clean, so distinguish expected edits from generated drift. Never bypass checks to publish. Go version lives in `go.mod`; `.golangci.yaml` defines import/format rules. `make toolchain` installs managed tools, not golangci-lint.

E2E infrastructure is persistent: `make e2e-setup` and `e2e-teardown` are retired. Maintenance/retirement procedures: `deploy/terraform-e2e/README.md`, with separate live consent. Make requires project/location; service-account keys are optional with appropriate gcloud/ADC authentication. `e2e-tests` defaults to `standard` (excludes GPU and extended local SSD), with Make concurrency 4; the agent E2E skill explicitly uses 20. Do not substitute unlocked `e2e-test` for that workflow.

## Design and publication

Significant architecture/API/operator-visible changes need a proposal using `proposals/0000-template.md` and `CONTRIBUTING.md`. Align docs, examples, charts, and `MIGRATION.md` with approved behavior.

Before authorized publication, rebase onto the latest target branch and rerun applicable checks. Follow `.github/PULL_REQUEST_TEMPLATE.md` and issue templates exactly: all required fields, appropriate `/kind`, honest docs/migration checklist, and `N/A` rather than a dangling `Fixes #`. No unsolicited comments or maintainer pings.
