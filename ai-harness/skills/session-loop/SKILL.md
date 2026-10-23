---
name: session-loop
description: How the lead session and its worker sessions run board tasks end to end. Lead picks tasks from the agent-tracker board by priority, starts one worker session per task and keeps the board current; the worker fixes, tests, runs /skill-router and /agent-router, opens the PR (and the docs PR), waits for Devin on the final head SHA, merges and reports in one message. Use when the user says "you are the lead", "work the board", "spin up sessions", "/session-loop lead", or when a brief says "/session-loop worker".
---

# Session loop

Two roles. Run the part for yours: `/session-loop lead` or `/session-loop worker`.
The rule file `sessions-rules.md` next to this file holds the hard limits; this is the how.

## Lead

The lead keeps its context small: it dispatches and records, it does not code,
review or run routers.

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
4. **Mark the board** in the same turn: `in_progress`, assignee = lead's
   agent name, note = worker name.
5. **On a report:** check it on `origin/main` (`git fetch`, `git branch -r
   --contains <merge sha>`, one grep for the change). Then set the task
   `done` with the PR, merge commit and the open items. New follow-ups become
   board tasks; owner decisions become `blocked` tasks phrased as one question.
6. **On a failed or stalled worker** (network error, idle mid-loop), send it
   one message: resume where it stopped, same rules. Never finish its work in
   the lead.
7. Tell the user one or two lines per change of state, with PR links.

## Worker

You own the task from code to merge. The lead only reads your final report.

1. **Start current.** `git fetch && git rebase origin/main`. Read the repo's
   `AGENTS.md` (or `CLAUDE.md`); its rules win over this skill.
2. **Branch** `x/<slug>`. Rename the worktree's branch if it is not.
3. **Fix** the smallest complete change. Money, identity, a parser or a route
   gets a test that fails before the fix. Finish callers, tests and grep suites.
4. **Check** with the repo's offline check (for example `npm run check`).
   UI change: look at it in the browser pane at phone and desktop width and
   keep before/after screenshots for the PR.
5. **Routers before EVERY commit, no matter what.** After each piece of work
   (first fix, review fixes, Devin fixes, any change at all) run
   `/skill-router`, then `/agent-router` with the agents it picks, before you
   commit. Fix every Critical, High and Medium finding; answer the rest in the
   PR body. No change is too small to skip this, and a self-run
   `/ponytail-review` does not replace them.
6. **Commit, push, PR.** Conventional message, no Co-Authored-By or
   "Generated with" lines. No `gh` CLI: use the GitHub API with the PAT read
   inline (for example `security find-generic-password -s <your-pat-item> -w`), never
   printed. PR body: what changed, the tests, what you did not check.
   **Run `/git-workflow` once**, after the PR is open and before the merge,
   and fix what it flags (branch name, message format, history, base).
7. **Docs.** A user-visible change gets a PR on the docs repo in the same task
   (`<owner>/<docs-repo>`; its AGENTS.md sets the voice). Check that checkout's branch first or use a worktree.
8. **Always wait for Devin. Merge gate, all must hold on the FINAL head SHA:**
   - `GET /repos/<owner>/<repo>/commits/<sha>/statuses`: the "Devin Review"
     status is `success`, i.e. Devin has FINISHED reviewing that SHA. Pending
     or not started is not passing.
   - Every Devin review comment is addressed: fixed (routers, commit, push)
     or answered on its thread.
   - Any other CI on that SHA is green.
   - `/git-workflow` has run (once, step 6).
   Every push restarts the wait for Devin. If Devin has not reviewed after a
   long wait, tell the lead; never merge without it.
9. **Merge**, then prove it: the PR head equals your last push, `git fetch`
   and `git branch -r --contains <merge sha>` shows `origin/main`, and one grep
   of `origin/main` finds the change. "merged: true" alone is not proof.
10. **Report** to the lead with `SendMessage` (to = the lead's session id), ONE
    short message that opens with a **TL;DR** (two or three plain sentences:
    what happened, where it stands, what's open), then PR link(s), merge commit,
    what Devin found and how it was handled, open items. Then stop. Do not touch the board.

If you need an owner decision mid-task, ask the user in your own session
(one question), not the lead.
