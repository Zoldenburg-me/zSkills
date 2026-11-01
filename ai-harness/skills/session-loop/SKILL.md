---
name: session-loop
description: Lead dispatches agent-tracker board tasks to worker sessions; a worker owns its task to the merge; a read-only reviewer session reviews each PR head. Use for "you are the lead", "work the board", "/session-loop lead", or a brief saying "/session-loop worker" or "/session-loop reviewer".
---

# Session loop

Three roles. Run the part for yours: `/session-loop lead`, `/session-loop worker` or `/session-loop reviewer`.
A session is the lead only when the user says so; there is one lead at a time.
The rule file `sessions-rules.md` next to this file holds the hard limits; this is the how.

## Lead

The lead keeps its context small: it dispatches and records, it does not code,
review or run routers. On the board it is the master agent: started with
`AGENT_TRACKER_ROLE=master`, registered as `taskmaster` (or the server's
`AGENT_DASH_MASTER`). It creates and closes tasks; workers claim and log
their own.

0. **Check the rules.** `tracker_check_rules` at the start of every pass; send
   each break to the worker that owns it.
1. **Read the board.** `tracker_list_tasks` for the project, status
   `todo,in_progress,review,blocked`. Order: urgent → high → medium → low.
2. **Pick what fits now.** Skip tasks that need an owner decision (say which
   question), a deploy step only the owner may approve, or files another
   worker is in. Pair tasks that touch the same files into one worker.
3. **Start one worker per task** with `start_session` (`user_asked` when the
   user asked for it in this turn, otherwise `own_initiative` cards),
   `use_worktree: true`, `wake_when_done: true`. The brief is short:
   - task id(s), the bug or feature in one or two sentences, where (files,
     line numbers with their date), the fix if known, what the tests prove;
   - files other workers are in, to avoid;
   - any owner decision already made, quoted;
   - last line: `Run /session-loop worker. Report to the lead (<lead session id>).`
4. **Leave the claim to the worker.** Don't set `in_progress` or the assignee
   yourself; the worker claims the task when it starts.
5. **On "PR ready for review"** from a worker (its task is now `review`): start one reviewer session for
   that PR (`use_worktree: true`), brief = repo, PR number, head SHA, the
   task, the worker's session id; last line: `Run /session-loop reviewer.
   Report to the worker (<worker id>) and the lead (<lead session id>).`
   One reviewer per PR, reused for its later heads. Give the worker its id.
6. **Milestone audits.** At each milestone the repo's plan names (a scope
   freeze, before going public) add a board task: read-only audit of the
   whole codebase at that commit (`security-audit` quick profile, plus
   `rust-review` and `spec-to-code-compliance` against the plan where they
   fit). Dispatch it like any task; the audit session edits nothing and its
   report's findings become board tasks.
7. **On a report:** check it on `origin/main` (`git fetch`, `git branch -r
   --contains <merge sha>`, one grep for the change). Then set the task
   `done` with the PR, merge commit and the open items. New follow-ups become
   board tasks; owner decisions become `blocked` tasks phrased as one question.
   Only the lead sets `done`.
8. **On a failed or stalled worker or reviewer** (network error, idle
   mid-loop), send it one message: resume where it stopped, same rules. Never
   finish its work in the lead.
9. Tell the user one or two lines per change of state, with PR links.

## Worker

You own the task from code to merge. The lead only reads your final report.
On the board you are a Main agent (the default role).

0. **Claim it.** `tracker_register` with a short name for the task, then
   `tracker_heartbeat` status `working`, `parent` = the lead's tracker name.
   Set your task `in_progress` with yourself as assignee. Log one line per
   meaningful step with `tracker_log_progress`. Touch only your own task:
   new work becomes a todo on it, or goes to the lead to create. Never
   create, close or reassign tasks.
1. **Start current.** `git fetch && git rebase origin/main`. Read the repo's
   `AGENTS.md` (or `CLAUDE.md`); its rules win over this skill.
2. **Branch** `x/<slug>`. Rename the worktree's branch if it is not.
3. **Fix** the smallest complete change. Money, identity, a parser or a route
   gets a test that fails before the fix. Finish callers, tests and grep suites.
4. **Check** with the repo's offline check (Zold: `npm run check`, node PATH
   from its AGENTS.md).
   UI change: look at it in the browser pane at phone and desktop width and
   keep before/after screenshots for the PR.
5. **Before every commit:** the step-4 check passes and `/leak-check` is clean.
   You do not run the routers or reviewer agents on your own work; the
   reviewer session does that on the PR head.
6. **Commit, push, PR.** Conventional message; open the PR with `gh`. PR body: what changed, the tests, what you did not check.
   **Run `/git-workflow` once**, after the PR is open and before the merge,
   and fix what it flags (branch name, message format, history, base).
   Then set your task `review` and send the lead: `PR ready for review: <url> at <head sha>`.
6b. **Review fixes.** Fix every Critical, High and Medium finding from the
   reviewer; answer the rest on the PR. After each fix push, send the
   reviewer the new head SHA and wait for its verdict on it.
7. **Docs.** A user-visible change gets a PR on the docs repo in the same task
   (Zold: `Zoldenburg-me/zold-docs`, `~/Documents/zold-docs`, its AGENTS.md
   sets the voice). Check that checkout's branch first or use a worktree.
8. **Always wait for Devin. Merge gate, all must hold on the FINAL head SHA:**
   - The reviewer's verdict on that SHA is `clear` (no open Critical, High or
     Medium).
   - `gh api repos/<owner>/<repo>/commits/<sha>/statuses`: the "Devin Review"
     status is `success`, i.e. Devin has FINISHED reviewing that SHA. Pending
     or not started is not passing.
   - Every Devin review comment is addressed: fixed (commit, push, reviewer
     re-check) or answered on its thread.
   - Any other CI on that SHA is green.
   Every push restarts the wait for Devin. If Devin has not reviewed after a
   long wait, tell the lead; never merge without it.
9. **Merge**, then prove it: the PR head equals your last push, `git fetch`
   and `git branch -r --contains <merge sha>` shows `origin/main`, and one grep
   of `origin/main` finds the change. "merged: true" alone is not proof.
10. **Report** to the lead with `SendMessage` (to = the lead's session id), ONE
    short message that opens with a **TL;DR** (two or three plain sentences:
    what happened, where it stands, what's open), then PR link(s), merge commit,
    what Devin found and how it was handled, open items. Heartbeat `idle`,
    then stop. Leave `done` to the lead.

If you need an owner decision mid-task, ask the user in your own session
(one question), not the lead.

## Reviewer

You review one PR, read-only: you never edit, commit, push or merge. On the
board you are a sub-session: make no tracker calls (start with
`AGENT_TRACKER_ROLE=sub` where you can).

1. **Check out the head** in your worktree: `gh pr checkout <n>`, confirm
   `git rev-parse HEAD` equals the SHA you were given.
2. **Routers on the PR.** Run `/skill-router`, then `/agent-router` with the
   agents it picks, both on the range `origin/<base>...HEAD`. On a later head,
   review the commits since the last SHA you cleared, plus anything they touch.
3. **Post one PR comment** (`gh pr comment`) per head: the SHA, findings
   ranked Critical → Low with file:line and the smallest fix, and the verdict
   `clear` or `changes needed`. `clear` means no open Critical, High or Medium.
4. **Report** with `SendMessage` to the worker (the verdict, the comment link)
   and one line to the lead. Then wait for the next head SHA from the worker.
   Stop when the PR is merged or closed.
