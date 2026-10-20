---
name: unit-testing
description: Write, change, or review Go unit tests for karpenter-provider-gcp. Read before implementing Go behavior changes, fixing bugs, adding tests, or reviewing test quality. Prioritize contract confidence, readability, and maintainability over coverage, implementation-coupled assertions, excessive cases, and GCP HTTP mocks.
---

# Unit tests

Build the smallest understandable suite that protects the contract. Coverage can reveal a missed behavior, but an uncovered line is not by itself a reason to add a test. Do not target 100% coverage or a fixed number of test lines.

## Before writing tests

1. Read the changed behavior and nearby tests. Identify the contract from the requirement, issue, or caller expectations, not just what the implementation currently does. Existing tests show local conventions, not automatic justification for copying their scaffolding.
2. Choose a useful boundary: a pure decision function, provider method, or controller reconciliation. A unit is a coherent behavior, not necessarily one Go function. Testing meaningful unexported logic is fine; do not export helpers just for tests or test every helper separately.
3. Select a small set of distinct behaviors. For each proposed case, be able to name the incorrect outcome it catches. Include relevant failure paths and boundaries, but do not manufacture a happy/error/nil matrix for every function or enumerate equivalent permutations.
4. For a bug fix, prefer a focused regression that fails for the original defect and passes with the fix. Establish the test intent before adding mock infrastructure. A short behavior list is enough; no separate approval ceremony is needed for routine tests.

## Keep tests maintainable

- Follow the surrounding `testing`/`testify` or Ginkgo/Gomega style. Do not introduce another framework or rewrite neighboring tests for consistency.
- Use minimal fixtures with the important inputs visible in the test. Reuse small existing helpers when they clarify intent; avoid generic builders, configurable fake frameworks, and layers of indirection for a few cases.
- Assert returned values, errors, resulting state, or meaningful side effects. Multiple assertions are fine when they describe the same behavior. Assert only the fields that matter, unless the entire value is the contract.
- Compute expectations independently of the code under test. Do not reproduce its algorithm or use the same production helper to derive the expected result.
- Avoid assertions about private call graphs, cache layout, exact SDK call sequences, incidental ordering, or complete error text unless that detail is part of the contract. Conversely, idempotency, ordering, retries, and caching behavior deserve tests when callers rely on them.
- Use table-driven tests when the cases share setup and assertions. Do not force different stories into a large table or multiply every input dimension. A case must protect something distinct, not merely have a different name.
- Keep unit tests deterministic and isolated: no live GCP/Kubernetes calls or real credentials. Prefer a local dependency or existing fake over real sleeps and process-global state changes.
- Do not add production interfaces, wrappers, or broad refactors solely to make mocking easier. If the existing seam is awkward, explain the tradeoff rather than hiding it behind a test framework.

## GCP boundaries and test doubles

Prefer real API/domain structs for pure logic and existing small provider fakes for collaborators. A fake should supply the minimum behavior needed by the scenario, not emulate the cloud service.

Do not build an `httptest.Server`, custom transport, or JSON response matrix merely to get through SDK calls and reach unrelated selection, filtering, or metadata logic. Do not test Google's SDK implementation.

HTTP-level doubles are appropriate when our adapter behavior is the subject: request construction, resource identifiers, pagination, error translation, or retries. Keep these tests narrow and verify what our code promises. Do not ban a justified adapter test merely because it uses HTTP.

If a realistic service guarantee cannot be established by a unit test, state that limitation instead of manufacturing a larger fake. Local integration tests are a separate option; live integration/e2e runs require the repository's explicit environment authorization.

## Example: version selection without GCP emulation

Illustrative simplification, not a historical before/after diff:

- **Avoid for a pure version-selection change:** fake the GKE `GetServerConfig` endpoint, instantiate an SDK client, assert request paths/call counts, and repeat the setup for many equivalent version strings.
- **Prefer:** pass a real `ServerConfig` to `ResolveVersionForChannel` and assert the selected version. Separate adapter tests can protect fetching the configuration if that behavior changes.

This focused regression catches lexicographic sorting instead of semantic version ordering:

```go
func TestResolveVersionForChannel_SemverOrderNotLexicographic(t *testing.T) {
	sc := &containerv1.ServerConfig{
		Channels: []*containerv1.ReleaseChannelConfig{{
			Channel:        "REGULAR",
			DefaultVersion: "1.35.3-gke.1389000",
			ValidVersions:  []string{"1.34.9-gke.900000", "1.34.10-gke.1000000"},
		}},
	}

	got, err := ResolveVersionForChannel(sc, "regular", "1.34.5")

	require.NoError(t, err)
	require.Equal(t, "1.34.10-gke.1000000", got)
}
```

The fixture deliberately forces fallback from a different minor version. It makes the regression visible without asserting which sorting helper is used. Other contract behaviors, such as no compatible version, still need their own tests when relevant.

Repository examples (paths below are relative to this skill directory):

- [Version-selection tests](../../../pkg/providers/gke/version_test.go): distinct selection rules and failure outcomes, using API structs without HTTP scaffolding.
- [Instance-type provider fakes](../../../pkg/providers/instancetype/fakeproviders_test.go): small fixed GKE/pricing collaborators. Reuse the relevant fake pattern, not necessarily every detail of the provider setup.

## Validate and prune

Run commands from the repository root. Start with the affected test/package, then run the relevant broader checks required by `CLAUDE.md` and CI. For example:

```bash
go test ./pkg/providers/gke/... -run '^TestResolveVersionForChannel_'
go test -race ./pkg/providers/gke/...
# Full unit-test target, when the change calls for it:
make ut-test
```

Before finishing, review the test diff:

- What plausible wrong behavior makes each new test fail? Remove or combine cases that add no distinct regression protection.
- Would a behavior-preserving refactor break the assertions? If so, are they testing a real contract or incidental implementation?
- Is setup obscuring the behavior? Simplify fixtures and doubles before adding more helpers.
- Have important regressions and realistic failures remained protected? Do not delete or weaken tests just to reduce line count; explain legitimate expectation changes.

Report which behaviors are protected, the commands actually run, and any meaningful validation gaps. Do not report coverage percentage or test volume as proof of quality.
