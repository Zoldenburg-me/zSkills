---
name: security-fix
description: Work the findings of a finished security-audit run one at a time, one session per finding. `queue` turns the run's findings.json into a fix queue (FIX-PROGRESS.md) and offers a one-click task chip for the first finding; `next` (run in that new session) claims the row, proves the bug with a failing test, makes the smallest fix that enforces the invariant at the last trusted decision point, has an independent checker judge it, opens a PR, and offers the chip for the next finding. Use after a security-audit run completes, when the user says "fix the findings", "start the fix queue", "next finding", /security-fix, or opens a session from a security-fix chip.
---

# Security fix

The fixing half of `security-audit`. The audit stays read-only and ends by pointing here.
This skill changes code, so its whole design is about not running away:

- **One finding per session.** A session claims one row, ships one PR, offers the next chip, and stops.
- **The table is the state machine** and only `scripts/fixqueue.py` moves rows. Claims are guarded
  (`--expect todo`), so two sessions never own one row.
- **The judge is not the fixer.** `scripts/judge.py` (deterministic: red on the merge base, green on
  the fix, nothing deleted) plus an independent checker subagent ([CHECKER.md](CHECKER.md)) decide
  whether a fix or a "not a bug" verdict stands. The fixer never grades its own work.
- **The owner flips the last switch.** The loop only reaches `pr-open` or `reject-proposed`.
  `fixed` comes from the owner's merge (`fixqueue.py refresh` reads it from git); `rejected` only
  from the owner in chat. The skill never merges.
- **Decisions are front-loaded.** `queue` marks rows whose blockers need product intent as
  `needs-decision`; the chain skips them and lists them for the owner instead of guessing.

## Modes

Arguments: `/security-fix <mode> [run-dir]`. `run-dir` defaults to the newest
`~/security-audit-skill/<repo-name>/run-<N>/` that has a `findings.json` and `run_status: "complete"`.

### `queue`: after an audit run completes

1. Read the run's `run-metadata.json`. Refuse if `run_status` is not `complete`: an incomplete run's
   queue would silently miss findings. Say which fingerprints are unvalidated and stop.
2. **Front-load the repo setup** into `<run-dir>/fix-config.json`, read from the target repo's
   `AGENTS.md`/`CLAUDE.md`/`README` (never from `.env*` or secrets), and show it to the owner once:
   ```json
   {"repo": "<abs path of the main checkout>", "base": "origin/main", "branch_prefix": "x/",
    "check_cmd": "npm run check", "suite_cmd": "<run ONE test file; {file} is repo-relative>",
    "link_dirs": ["node_modules", "<every other gitignored dir the tests need, e.g. a vendored toolchain>"],
    "env_setup": "<shell line the repo docs require before tests, relative to the worktree, or empty>",
    "pr_how": "<how PRs are opened here: gh, or REST + per-session token>",
    "docs_repo": "<repo that needs a PR for user-visible changes, or empty>"}
   ```
   Ask only what the docs do not say. This file is how later sessions avoid asking mid-run.
   **Prove it before the first chip:** in a fresh detached worktree of `base` with `link_dirs`
   symlinked, run `env_setup && suite_cmd` on one existing test file. It must pass. A config that
   cannot run a test on base turns every reproduction into a harness failure.
3. `python3 scripts/fixqueue.py build <run-dir>` (add `--order FILE`, a JSON list or object of
   fingerprints, to order the needs-validation leads; `x-priority.json` in the run dir is used when
   present). Confirmed findings come first by severity, then needs-validation leads. An existing
   FIX-PROGRESS.md keeps every row, status and order; new fingerprints are appended, and `todo`
   rows with an empty note whose blockers need product intent become `needs-decision`.
4. Show the owner the queue summary: rows, `needs-decision` rows with their questions, and the
   first `todo` row. Ask the `needs-decision` questions now; record each answer in that row's note
   and set it to `todo` (`fixqueue.py set <n> todo --expect needs-decision --note "owner: …"`) or leave it.
5. Offer the chip for the first `todo` row (see **Chips**).

### `next`: in a session opened from a chip

Follow [NEXT.md](NEXT.md) exactly. It ends by offering the next chip and stopping.

### `status`

`python3 scripts/fixqueue.py refresh <run-dir> --repo <repo>` (merged PRs become `fixed`), then
`fixqueue.py next` and show: table counts, open PRs, everything waiting on the owner, and
`stale_in_progress` rows (claimed over 6 hours ago: the session probably died). For a stale row,
ask the owner; on their yes, `fixqueue.py set <n> todo --expect in-progress --human --note "reset: <reason>"`.
If no fresh `in-progress` row exists and a `todo` row does, offer its chip.

## Chips

Use `mcp__ccd_session__spawn_task` (the desktop app's background-task chip; one click opens a new
session). If that tool is not available, print the same prompt in a fenced block for the owner to
paste into a new session.

- `title`: `Fix #<n>: <first ~45 chars of the row title>`
- `tldr`: one or two plain sentences, what the finding lets someone do, plus any overlap warning
  from `fixqueue.py next` ("touches files that the open fix PR for #<m> also changes").
- `cwd`: `fix-config.json` `repo`.
- `prompt`: self-contained:
  ```
  /security-fix next <abs run-dir>
  Finding #<n> `<fingerprint>`: <title>. Follow the security-fix skill's NEXT.md exactly.
  ```

Offer at most one chip per session. Never offer a chip for a row that is not `todo`.

## Hard rules (every mode)

- The target repo's `AGENTS.md`/`CLAUDE.md` binds: branch prefix, protected branches, what may not
  be read, how checks run, how PRs open, commit message rules.
- No features, refactors, renames, tidy-ups or hardening notes. Only the smallest change that
  enforces the finding's invariant, plus the tests that prove it.
- No live endpoints, deployments, real keys or real money. Reproduce locally with dummy data.
- A credential the owner gives for PRs is used for that session only, never written to a file,
  commit, log or command echo, and the owner is reminded to revoke it at the end.
- Never set `fixed` or `rejected` without the owner (the script refuses without `--human`).

## Files

- [NEXT.md](NEXT.md): the per-finding procedure.
- [CHECKER.md](CHECKER.md): the independent checker subagent's prompt.
- `scripts/fixqueue.py`: build / refresh / next / set over FIX-PROGRESS.md.
- `scripts/judge.py`: red-on-base, green-on-fix, boundary report; exit code is final.
