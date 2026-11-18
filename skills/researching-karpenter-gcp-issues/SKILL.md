---
name: researching-karpenter-gcp-issues
description: Investigates karpenter-gcp/karpenter-provider-gcp GitHub issues by number or URL using the report, affected release, current source, upstream Karpenter, official GCP documentation, and other primary evidence. Use when asked to research, verify, triage, or pre-review an issue; determine whether code confirms it; identify an evidence-backed cause and fix direction; decide whether reporter details or reproduction are needed; and draft a concise issue reply without posting it.
compatibility: Requires a trusted karpenter-provider-gcp checkout, git, GitHub CLI access, and optional read-only web or cloud tooling.
---

# Researching karpenter-provider-gcp Issues

Investigate one issue without mutating GitHub, the repository, Kubernetes, or GCP.

## Input

Accept an issue number or GitHub issue URL. The repository is always:

```text
karpenter-gcp/karpenter-provider-gcp
```

If no unambiguous issue number is present, ask for it. Otherwise start without additional questions.

## Non-negotiable boundaries

- Do not comment on, edit, label, close, or otherwise mutate the issue or any PR.
- Do not change tracked source, create commits, push, deploy, or run e2e tests.
- Do not create, update, or delete cloud or Kubernetes resources.
- Read-only commands such as `gcloud ... describe/list` are allowed only when they are necessary, scoped, and side-effect free.
- Do not call an API's create/insert method merely to reproduce a report, even if a CLI claims to offer a dry run, unless the user separately approves it.
- Do not turn the investigation into an implementation plan unless asked.
- Leave pre-existing working-tree changes untouched.

## Evidence standard

Operate on facts, not a list of possible causes.

Classify important conclusions as one of:

- **Confirmed by code** — the reported input deterministically reaches the observed behavior.
- **Consistent with the report** — evidence supports it, but the incident itself was not reproduced.
- **Not reproduced** — source behavior is understood, but an external/runtime claim was not independently observed.
- **Unknown; needs evidence** — the missing fact changes the diagnosis.

Rules:

1. Support every causal claim with a primary source: tagged/current code, an exact structured error, an official API document, a test, or a read-only observation.
2. Do not treat issue prose as independent confirmation; identify what came only from the reporter.
3. Do not infer permanence, retryability, or capacity semantics from an HTTP status alone. Prefer structured reason/code fields and documented behavior.
4. Do not claim that source inspection proves exact retry counts, elapsed time, memory growth, or production impact unless those values follow directly from code.
5. If evidence is insufficient, say so and request only the smallest artifact that can decide the question.

## Workflow

### 1. Read and normalize the issue

Use a read-only query that includes comments:

```bash
gh issue view <number> \
  --repo karpenter-gcp/karpenter-provider-gcp \
  --json number,title,body,author,createdAt,updatedAt,state,labels,comments,url
```

Extract:

- affected provider/chart and Kubernetes/GKE versions;
- environment and constraints;
- exact observed and expected behavior;
- structured error codes and messages;
- reproduction steps and supplied artifacts;
- claims that require independent verification.

Check for linked or existing fixes without mutating anything:

```bash
gh search prs '<distinctive term> repo:karpenter-gcp/karpenter-provider-gcp' \
  --json number,title,state,url,updatedAt
```

### 2. Establish exact source boundaries

Inspect both:

1. the release or commit named in the issue;
2. the current upstream `main` commit.

Confirm remote `main` with the GitHub API. Fetch only the needed branch or tag when the local ref is stale. Never checkout or rewrite the working tree; prefer:

```bash
git show <ref>:<path>
git grep -n '<term>' <ref> -- <paths>
git diff <release>..<main> -- <paths>
```

Record relevant dependency boundaries, especially the vendored Karpenter version. Never extrapolate behavior inspected in one release to another.

### 3. Trace the complete behavior

Follow the narrow execution path end to end:

```text
reported input/error
→ provider discovery or API call
→ error/type classification
→ cache or availability update
→ Karpenter lifecycle/reconcile behavior
→ retry, timeout, deletion, or scheduler fallback
```

Inspect focused tests to learn the intended contract. Search current `main` for an existing fix before recommending work.

When relevant, compare established behavior in Karpenter AWS/Azure/IBM providers, cluster-autoscaler, or kOps. Use built-in URL/repository fetching for read-only external source research; do not clone repositories manually. Treat analogous implementations as design evidence, not proof of GCP behavior.

### 4. Verify external claims safely

Prefer official GCP API documentation and error catalogs. Read-only `list`, `get`, or `describe` commands may verify catalog or configuration claims.

Keep two conclusions separate:

- whether the external service actually emitted the reported response;
- whether this provider mishandles that response if it occurs.

Do not perform a mutating reproduction under this skill. If mutation is the only way to establish the external fact, mark it **Not reproduced** and decide whether the issue's exact logs are sufficient.

### 5. Decide whether more evidence is required

No additional reproduction is needed when an exact reported input or structured error maps deterministically to a confirmed code path and the provider defect can be tested locally.

Request more information only when it changes attribution or fix design. Ask for a minimal artifact, for example:

- one complete structured API/controller error;
- exact image digest or provider version;
- two comparable post-GC profiles for a memory-growth claim;
- the smallest relevant resource spec with secrets removed.

Avoid generic requests for “more logs,” entire cluster dumps, credentials, kubeconfigs, or a reproduction guide that merely repeats the issue.

### 6. Assess whether it should be fixed

State:

- the external trigger, if established;
- the provider-side mechanism, if confirmed;
- whether the behavior belongs in this provider;
- the narrowest safe fix direction;
- semantic constraints the fix must preserve;
- whether existing cache/error/lifecycle mechanisms should be reused.

Do not present a speculative implementation as a fix. For error handling, classify the exact structured code, preserve unrelated errors, scope cache invalidation precisely, and distinguish temporary suppression from permanent exclusion.

### 7. Produce the answer

Match the user's language. Draft the issue reply in the language already used in the issue.

Use exactly these sections:

```markdown
## Смог ли подтвердить проблему по коду?
<Да / Частично / Нет, with the decisive evidence and affected refs.>

## Что вызывает проблему и стоит ли это исправлять?
<External trigger vs provider mechanism, fix assessment, and whether more details or reproduction are needed.>

## Короткий черновик комментария в issue
> <Paste-ready, concise reply. Do not claim the issue was reproduced unless it was.>
```

Keep the draft comment focused on conclusion, evidence, next action, and any single blocking request. Do not include routine command logs.

End with a one-line confirmation that no GitHub comment, code change, commit, push, deployment, or cloud mutation was performed.

## Durable report threshold

For a small deterministic issue, answer directly in chat. For a multi-version, profiling, security, or multi-component investigation, save the detailed evidence to:

```text
.pi/research/issue-<number>/research.md
```

Keep the chat answer concise and link the report. Never place research artifacts in tracked `docs/` or `proposals/`.

## Completion checklist

Before answering, verify:

- affected release and current upstream `main` were distinguished;
- causal claims have primary evidence;
- reporter evidence and independent confirmation are separated;
- unsupported theories were omitted;
- the need for more data or reproduction is explicit;
- the proposed fix direction is narrow and does not classify broad error categories accidentally;
- the issue reply is paste-ready and was not posted;
- no mutation occurred.

