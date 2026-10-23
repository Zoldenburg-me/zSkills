# Lead and worker sessions

The rules for running board tasks across sessions. The `session-loop` skill has the step-by-step version.

## Roles

- **The lead** reads the board, starts one worker session per task by priority, and keeps the board current. Tasks that touch the same files go to one worker. The lead doesn't write code, run the routers or launch review agents.
- **The worker** owns its task until it's merged. Its brief ends with "Run /session-loop worker."

## The worker's loop for each task

1. Fix and test.
2. Before every commit, no exceptions: run `/skill-router`, then `/agent-router`, after each piece of work, including review fixes.
3. Open the PR, plus a docs PR if users will notice the change.
4. Run `/git-workflow` once, after the PR is open and before merging.
5. Wait for Devin: the "Devin Review" status must be `success` on the final head commit, and every Devin comment fixed or answered. Pending doesn't count as passing, and every push restarts the wait.
6. Merge, then prove the merge: the head commit matches the last push, `origin/main` contains the merge commit, and a grep finds the change.
7. Send one report to the lead: the PR link, the merge commit, how review findings were handled, and anything still open.

## Rules around the loop

- Only the lead writes to the board. A worker's report is only a claim. The lead checks `origin/main` before marking a task done.
- Decisions only the user can make come to the user as one question, from whichever session needs them. The lead records the answer on the board.
- Two workers never edit the same files at the same time.
- Every report and session summary starts with a **TL;DR**: two or three plain sentences saying what happened, where it stands and what's still open, so anyone can follow the session at a glance. Details go below it.
