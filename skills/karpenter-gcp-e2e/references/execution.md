# E2E launcher, cleanup, and cancellation

Read before launching long tests. Inspect this revision's helper and wrappers: historical behavior is not a guarantee.

## Launch and observe

Use a detached tmux session rather than a long abortable agent Bash call. Write a run-local script that loads the approved environment, records stage before each operation, and captures deployment, runner, and overall statuses separately.

For pipelines, enable `pipefail` and capture `${PIPESTATUS[0]}` **immediately** after the runner/Make command piped to `tee`, before another command overwrites it. Ensure shell error handling still writes the status/`exit-code` file on failure. Report-generation success must not mask runner failure. Preserve the interrupted/failed stage rather than replacing it with a generic `finished` marker.

Use fresh artifact paths and provide the user absolute logs/report paths and session name. Monitor in short calls; never start a duplicate after a monitoring timeout. Missing session/exit marker is not success.

`make`/`go run` can exit on Ctrl-C before reporting or Lease release. If they cannot preserve the signal path, build the inspected helper into the artifact directory and launch it directly with exactly the wrapper's environment/arguments. Record this launcher-only change; retain selection, concurrency, locking, and reporting.

## Cancellation

Cancel only when requested: `tmux send-keys -t <session> C-c` requests shutdown. Do not use `tmux kill-session` or agent-tool abort for normal cancellation; successful key delivery does not establish graceful shutdown.

Inspect the helper itself: current runner cancellation kills its isolated child process group, even though the parent handles interrupts. Check surviving runner/Ginkgo/test-binary processes, Lease ownership/renewal, and residual resources read-only. Lease expiry alone does not prove tests stopped. Do not steal/delete/clear the Lease or kill leftovers without approval, and do not claim clean shutdown without supporting evidence.

If no report/controller log was produced, collect logs read-only and write a clearly cancelled/incomplete fallback report with known stage/status and no invented totals.

## Cleanup races

Deployment currently performs cleanup before it acquires any runner Lease. Check for active runs first and obtain explicit cleanup approval before invoking it. A runner Lease is not a deployment lock.

Deletion by selector is a snapshot: a live controller can create NodeClaims while old workloads/NodePools remain. After approved cleanup verify objects and backing instances are gone, not merely that deletion printed names. If new claims still reference previous pools, stop before testing and report them. Follow-up deletion requires approval covering that scope and another active-run check. Never force-remove finalizers to hide incomplete cleanup.

After failed/interrupted tests, report residual resources and suggested follow-up; do not silently clean, repair, rerun, or redeploy.
