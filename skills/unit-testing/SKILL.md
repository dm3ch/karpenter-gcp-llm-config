---
name: unit-testing
description: Write, change, or review Go unit tests for karpenter-provider-gcp. Read before Go behavior changes, bug fixes, or test-quality reviews. Prefer contract confidence and maintainability over coverage targets, implementation-coupled assertions, and excessive mocks.
---

# Unit tests

Build the smallest understandable suite that protects the contract. Coverage is diagnostic, not a target; neither an uncovered line nor a test line-count quota justifies another case.

## Choose behaviors and boundaries

1. Read the requirement, callers, changed behavior, and nearby tests. Establish the intended contract, not merely what the implementation currently does. Existing scaffolding is not automatically worth copying.
2. Choose a coherent boundary: a decision function, provider method, or reconciliation. Meaningful unexported logic is fine; do not export helpers or test every helper separately just for coverage.
3. Name the incorrect outcome each case catches. Cover distinct behaviors, important boundaries, and realistic failures without manufacturing a happy/error/nil matrix or equivalent permutations.
4. For bugs, prefer a focused regression that fails before the fix and passes afterward. Establish intent before mock infrastructure; a short behavior list suffices for routine tests.

## Keep assertions and setup maintainable

- Follow nearby `testing`/`testify` or Ginkgo/Gomega conventions; do not introduce frameworks or rewrite neighboring tests for consistency.
- Keep important inputs visible with minimal fixtures and small existing helpers. Avoid generic builders or configurable fake frameworks for a few cases.
- Assert observable values, errors, state, and meaningful side effects. Multiple assertions are fine for one behavior; compare only relevant fields unless the whole value is the contract.
- Derive expectations independently, not with the production algorithm/helper.
- Avoid private call graphs, cache layout, incidental ordering, exact SDK sequences, or complete error text unless contractual. Conversely, caller-visible ordering, caching, retries, and idempotency deserve protection.
- Use tables when setup/assertions genuinely match; do not force unrelated stories into one table or multiply every input dimension.
- Keep unit tests isolated and deterministic: no live cloud/Kubernetes calls or credentials; avoid real sleeps and process-global changes.
- Do not redesign production code with new interfaces/wrappers solely for mocking. Explain awkward seams and tradeoffs instead.

## GCP doubles

Prefer real domain/API structs and existing small fakes supplying only scenario-relevant behavior. Do not emulate the cloud or test Google's SDK.

HTTP doubles are justified for **our adapter contract**: requests/resource identifiers, pagination, error translation, or retries. They are not justified merely to reach unrelated selection/filtering/metadata logic through SDK calls. Do not ban useful adapter regressions because they use HTTP.

For example, version selection can pass a real `ServerConfig` to `ResolveVersionForChannel`; it does not need a fake GKE endpoint. The semantic-order regression uses compatible `1.34.9`/`1.34.10` versions while forcing fallback from a different-minor default.

Examples (skill-relative): [version-selection tests](../../../pkg/providers/gke/version_test.go), [small instance-type collaborators](../../../pkg/providers/instancetype/fakeproviders_test.go). Reuse the relevant pattern, not every setup detail.

If a service guarantee cannot be established locally, state the limitation. Local integration tests are separate; live tests require explicit operation/environment consent.

## Validate and prune

From the provider root, run the focused test/package, then relevant `AGENTS.md`/CI checks. Examples: `go test ./pkg/providers/gke/... -run '^TestResolveVersionForChannel_'`, `go test -race ./pkg/providers/gke/...`, or `make ut-test` when broad validation is warranted.

Review each case: what plausible wrong behavior fails it? Would a behavior-preserving refactor break it? Is setup obscuring intent? Combine redundancy without deleting meaningful regressions or weakening assertions merely to shorten tests; explain legitimate expectation changes.

Report protected behaviors, actual commands/results, and validation gaps—not coverage percentage or test volume as proof of quality.
