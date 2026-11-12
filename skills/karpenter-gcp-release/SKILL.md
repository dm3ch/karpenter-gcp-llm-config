---
name: karpenter-gcp-release
description: Help a maintainer prepare, publish, verify, or resume a karpenter-provider-gcp release step by step, following RELEASE.md from the latest fetched origin/main. Use for minor or patch release assistance and release-readiness checks; not merely for deploying an existing release or upgrading karpenter-core.
---

# Assist a maintainer with a release

Be an interactive navigator, not a second release runbook. Do not duplicate release policy, commands, naming conventions, or step sequences here.

## Read the authoritative procedure

- Locate the **provider checkout** and read its applicable repository instructions. `.pi/` is a separate Git repository; do not fetch its origin by mistake.
- Inspect the provider's remotes and local status, then fetch `origin`. Resolve `origin/main` to an immutable commit SHA and read that commit's `RELEASE.md` in full, without switching branches or resetting local files.
- Use that document as the source of truth for the release procedure. If fetching or reading fails, stop and explain; do not silently fall back to a stale local copy or claim it is current.
- Record the runbook SHA and keep it pinned for this session. On resume, fetch again, compare revisions, and reconcile any changed instructions before continuing. The runbook revision is distinct from the code being released, which may come from a release branch.

## Help one step at a time

- Confirm missing inputs: intended version, release type, source branch/commit, and whether the maintainer wants guidance only or help executing steps.
- Derive a concise checklist from the applicable runbook sections and cross-references. Cite their headings rather than maintaining a separate release sequence.
- Inspect existing local and remote state read-only to establish completed work, especially when resuming. Do not repeat writes based only on a previous conversation.
- For each next incomplete step, explain the goal, propose the action with confirmed inputs, and identify side effects, including downstream workflows. Ask for required approval or provide the command for the maintainer to run.
- Verify the outcome before marking the step complete and moving on. Distinguish observed evidence from maintainer-reported results. Stop on failure, ambiguity, or an unmet gate; do not silently skip steps or retry mutations.
- For longer sessions, keep progress, evidence, runbook SHA, release source, blockers, and the next action in an ignored `.pi/plans/release-<version>.md`. Exclude credentials and sensitive environment identifiers. Saved progress is not continuing authorization.

## Respect execution boundaries

- Follow repository safety, worktree, signing, remote, and publication rules. Runbook commands do not override them. Preserve unrelated local work; do not blindly execute destructive examples or use literal URLs to bypass push restrictions.
- Obtain explicit scoped approval before remote mutations, publication, announcements, or live operations. Invoking this skill or asking to prepare a release is not blanket consent. Explain indirect effects before approval; hand prohibited operations to the maintainer and verify their results read-only.
- If the runbook conflicts with safety rules or current tooling, omits a necessary transition, or leaves a requirement ambiguous, cite the issue and ask the maintainer rather than inventing a procedure or silently changing scope.
- For deployment or E2Es, read the [E2E skill](../karpenter-gcp-e2e/SKILL.md), inspect the scripts, and obtain operation/environment approval including embedded cleanup. Resolve any discrepancy with the runbook's required test scope before proceeding.
- Verify the exact release commit and existing tag/release state before writes; preserve signing and never overwrite an existing tag/release as a retry. Source changes can invalidate previous validation. Publication alone does not prove artifact builds or propagation succeeded.

Finish with verified progress, version/source, public artifact links where appropriate, unresolved gates, and the next maintainer action. Do not call the release complete until the runbook's required outcomes are verified; do not announce, deploy, or clean up as an implicit final step.
