# `next`: fix one finding, then stop

`Q` = `python3 ~/.claude/skills/security-fix/scripts/fixqueue.py`,
`J` = `python3 ~/.claude/skills/security-fix/scripts/judge.py`,
`RUN` = the run dir, `CFG` = `RUN/fix-config.json`, `<repo>` = `CFG.repo`, `<base>` = `CFG.base`.
Work autonomously. The only questions to the owner are in step 1; after that, a question that comes
up becomes a row status with the question in the note, never a wait. Every exit path updates the
row and ends the session.

## 0. Rules (they override convenience)

- Read the target repo's `AGENTS.md`/`CLAUDE.md` first and follow it. Read `CFG`.
- **One finding.** Do not start, fix or touch another row's finding, even if you see it.
- **Smallest change** that enforces the invariant at the last trusted decision point. No features,
  refactors, renames, tidying, or hardening notes. Where a sibling path already enforces the check,
  copy that check; do not invent a mechanism.
- **The test is the contract.** Once the reproduction test is red on base, you may not weaken it,
  delete it, or change what it asserts to get green. The judge fails removed assertions.
- **Execution.** The audit could not run target code (no OS sandbox on its host). Here the owner's
  own test suite runs as the repo's docs describe it: locally, dummy data, local stubs and local
  chains only. No live endpoints, deployments, real keys or real money, ever.
- **Attempts.** Every judge failure, checker `send-back`, and edit after the checker's `accept`
  counts. On the 4th → `Q set RUN <n> blocked --expect in-progress --note "3 attempts: <last failure>"`, stop.

## 1. Claim (all owner questions happen here)

1. `git -C <repo> fetch origin`, then `Q refresh RUN --repo <repo>`.
2. `Q next RUN --repo <repo>` → the first `todo` row, its record, the files it names, overlaps with
   open fix branches, rows waiting on the owner, stale `in-progress` rows. No `todo` row → report
   `waiting_on_owner` and `stale_in_progress` and stop.
3. `Q set RUN <n> in-progress --expect todo` (stamps the claim time). Refused → another session
   took it; run `Q next` once more; refused again → stop.
4. If `CFG.pr_how` needs a per-session token, ask for it **now**. No token → continue anyway; step 6
   pushes the branch and records it without a PR.

## 2. Workspace

- If the session runs in a worktree the app made, use it; otherwise create a sibling worktree
  `<repo>-fix-<n>`. Either way: `git switch -c <CFG.branch_prefix>fix-<short-slug> <base>`.
- Symlink each `CFG.link_dirs` entry from the main checkout if it is missing. Apply `CFG.env_setup`.

## 3. Already fixed? Understand, then reproduce (before touching source)

Read, in this order, from `RUN`:
- the `findings.json` record (printed by `Q next`): `trace`, `evidence`, `root_cause` or
  `claimed_root_cause`, `blockers`, `validation_plan.local`. **That local plan is your test.**
- `FINDINGS-DETAIL.md` (confirmed) or `NEEDS-VALIDATION.md` (lead): the same record in prose.
- `HARDENING.md`: only notes on the same file or route, so you do not conflict with them. Do not implement them.
- `coverage-ledger.json` units whose `result_fingerprints` include yours: which controls already hold.

Line numbers drift: re-read every cited file at `<base>` and find the code by function name.
Check `git log <base> --oneline -50` for a commit that already addresses it.

Write the test from `validation_plan.local` into the existing suite it names, entering through the
trace's **entrypoint** (the route or public function) as the lower-trust principal, not by calling an
inner helper with the check already bypassed. Dummy data, local stubs only. Run just that suite
(`CFG.suite_cmd`) on your branch, which still equals base:
- **Red, on the asserted vulnerable behaviour** (not an import, compile or harness error) → the bug
  is real. Commit the test alone (`test: reproduce <fingerprint>`), go to 4.
- **Green** → no bug on base (never reproduced, or already fixed). Commit the test, go to 6 "no bug".
- **Cannot be settled locally** (the decisive fact is a deployment or partner fact in `blockers`) →
  `Q set RUN <n> blocked --expect in-progress --note "<exact question for the owner>"`, stop.
- **What "correct" means is a product decision** (or an existing test asserts the vulnerable
  behaviour as intended) → `Q set RUN <n> needs-decision --expect in-progress --note "<the question,
  the two options, file:line>"`, stop.

## 4. Smallest fix

Before editing, write down three lines (they go in the PR body):
- **Invariant**, one sentence.
- **Last trusted decision point**: file and function.
- **Why narrowest**: what a smaller change would miss, and what a larger one would add.

Edit only what that needs. Match the surrounding style. Comments state what is true now; no
"fixed"/"used to" notes. Add the regression cases the validation plan names (the refusal, plus the
legitimate path still working). Commit (`fix: <what is now refused>`, per the repo's commit rules).
After any later change: amend, so the branch is always one test commit plus one fix commit, or squash
them into one if the repo wants one commit per PR.

## 5. Judge (you do not judge yourself)

1. `J --run-dir RUN --row <n> --repo <worktree> --work-dir <your scratchpad>/judge`. The judge builds
   the command from `CFG`, takes the test files from your diff, refuses a dirty tree, runs base and
   HEAD in fresh worktrees, and fails on harness errors, deletions and removed assertions.
   Exit 0 required. `--owner-approved-test-edit` only with a recorded owner answer in the row's note.
2. `CFG.check_cmd` fully green in the worktree (the repo's gate). Fix only what your change broke.
3. Launch the **checker** subagent with [CHECKER.md](CHECKER.md) in fix mode (fresh context, the
   strongest available model). It returns `accept` or `send-back` with reasons.
4. After `accept`, run `/agent-router` and then `/skill-router` **once**, and launch only read-only
   reviewers from what they pick (code, security, type, test-coverage review). Do not launch agents
   that write code. Fix only real issues inside this finding's scope (each fix = an attempt, and
   back to 5.1); list everything else as notes for the PR body.

## 6. Ship and record

**Fixed** (judge exit 0, checker `accept`):
- Push the branch. Open the PR as `CFG.pr_how` says, with the token from step 1, never echoed.
  Body: fingerprint, invariant, root cause, last trusted decision point, why narrowest, the judge's
  base tail and head result, the checker's JSON verdict, router notes, "No other behaviour changed."
  Confirm the PR head SHA equals the commit you pushed.
- A user-visible change (new prompt, error text, page content) with `CFG.docs_repo` set → a docs PR
  in the same task, per that repo's rules. Otherwise "No user-visible change." in the PR body.
- `Q set RUN <n> pr-open --expect in-progress --branch <branch> --sha <pushed sha> --pr <PR URL or
  omit> --note "<one line>"`. No token → no `--pr`, and the note says "branch pushed, PR not opened".

**No bug** (the test was green on base):
- `J --run-dir RUN --row <n> --repo <worktree> --work-dir … --expect-green-on-base` must exit 0.
- Checker in rejection mode. It must show the test goes red when the claimed flaw is injected.
  Disagrees → the test was wrong: rewrite it (an attempt) and redo step 3.
- Agrees → push the test branch as a regression guard (PR if the checker called the test meaningful),
  then `Q set RUN <n> reject-proposed --expect in-progress --branch <branch> --sha <sha> [--pr <url>]
  --note "<test name>: <why no bug>; checker: <verdict>"`.

## 7. Hand off and stop

1. `Q next RUN --repo <repo>`. If a `todo` row exists, offer its chip (SKILL.md **Chips**), with any
   overlap warning in the tldr.
2. Final message to the owner: finding number and fingerprint; outcome; the base-then-head output;
   files changed with line counts; the checker verdict; router agents and skills that ran and what
   they said; `check_cmd` result; PR URL(s) or the pushed branch; rows waiting on the owner and stale
   rows; a reminder to revoke the token if one was used.
3. Stop. Do not start the next finding in this session.
