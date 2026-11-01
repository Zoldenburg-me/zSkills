# Lead, worker and reviewer sessions

The rules for running board tasks across sessions. The `session-loop` skill has the step-by-step version.

## Roles

- **The lead** reads the board, starts one worker session per task by priority, and creates and closes tasks. On the board it is the master agent (`AGENT_TRACKER_ROLE=master`, named `taskmaster`) and runs `tracker_check_rules` every pass. Tasks that touch the same files go to one worker. When a worker's PR is ready, the lead starts one reviewer session for it. The lead doesn't write code, run the routers or launch review agents. A session is the lead only when the user says so, and there is one lead at a time.
- **The worker** owns its task until it's merged. On the board it is a Main agent: it claims its own task, logs progress, reports to the lead with `parent`, and sets the task to `review` when its PR is ready. Its brief ends with "Run /session-loop worker."
- **The reviewer** reviews one PR, read-only. It never edits, commits, pushes or merges, and as a sub-session it makes no tracker calls. Its brief ends with "Run /session-loop reviewer."

## The worker's loop for each task

1. Fix and test.
2. Before every commit: the repo's check passes and `/leak-check` is clean. No routers or reviewer agents on your own work.
3. Open the PR, plus a docs PR if users will notice the change. Run `/git-workflow` once. Tell the lead the PR is ready for review, with its head SHA.
4. Fix every Critical, High and Medium finding from the reviewer and answer the rest. After each fix push, send the reviewer the new head SHA.
5. Merge gate, on the final head SHA: the reviewer's verdict is `clear`, the "Devin Review" status is `success`, and every Devin comment is fixed or answered. Pending doesn't count as passing, and every push restarts the wait.
6. Merge, then prove the merge: the head commit matches the last push, `origin/main` contains the merge commit, and a grep finds the change.
7. Send one report to the lead: the PR link, the merge commit, how review findings were handled, and anything still open.

## The reviewer's loop

1. Check out the PR head and confirm its SHA.
2. Run `/skill-router`, then `/agent-router`, on the PR's diff against its base. On a later head, review the new commits and what they touch.
3. Post one PR comment per head: findings ranked by severity with file:line and the fix, and a verdict, `clear` (no open Critical, High or Medium) or `changes needed`.
4. Send the verdict to the worker and one line to the lead.

## Milestone audits

At each milestone the repo's plan names (a scope freeze, before going public), the lead adds a board task for a read-only audit of the whole codebase at that commit: `security-audit` with the quick profile, plus `rust-review` and `spec-to-code-compliance` against the plan where they fit. Its findings become board tasks.

## Rules around the loop

- Only the lead creates, closes or reassigns tasks. A worker writes only to its own task (claim, progress, todos, `review`). A worker's report is only a claim. The lead checks `origin/main` before marking a task done.
- Decisions only the user can make come to the user as one question, from whichever session needs them. The lead records the answer on the board.
- Two workers never edit the same files at the same time. Reviewers and audits edit nothing.
- Every report and session summary starts with a **TL;DR**: two or three plain sentences saying what happened, where it stands and what's still open, so anyone can follow the session at a glance. Details go below it.
