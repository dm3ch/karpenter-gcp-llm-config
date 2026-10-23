# Knowledge Base result limits and fallbacks

Inspect current tool schemas; these are interpretation rules, not a replacement for discovery.

- Raw successful MCP JSON may be encoded in `content[0].text`; parse it before accessing fields. Errors can set `isError: true` with plain text. The gateway may already unwrap JSON.
- Both Knowledge Base list tools use `offset`; advance by `returned`, respecting `total` and truncation. Search has no offset/cursor: narrow the query if it exceeds `limit`, and search each repository separately for cross-repository questions.
- Search snippets are lowercased and numbered; fetch full documents for exact casing/context.
- Check `truncated`, `truncationReason`, `contentTruncated`, `documentsFailed`, and `sectionsFailed`. `total > returned` also signals omitted matches. Bounded/failed searches cannot establish absence; scan/response caps may prevent complete results even with paging.
- `sectionVersions` and document `versionId` identify the current published synthesis. Separate calls can see different versions; historical snapshots cannot be requested. Full-document responses can themselves be truncated with no continuation: inspect source or a more focused document for the missing content.
- A listed repository may have no published documents. Empty lists can mean synthesis is disabled or inaccessible, not that code is missing. State the limitation and use local source instead of repeated retries.
- If synthesis is disabled, the user may need their Greptile contact to enable the organization rollout, plus repository access/indexing. Do not change remote configuration or enroll repositories without explicit approval.
