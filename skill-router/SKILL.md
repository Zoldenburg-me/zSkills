---
name: skill-router
description: Pick and run the skills that fit what the user is doing right now. Builds a catalog of every reachable skill (the loaded listing, ~/.claude/skills, commands, plugins, and the uninstalled ECC library), shortlists it with BM25 against the task and the repo, scores the shortlist with TypeSafe Jev (does it fit the task, does the repo have what it works on), then runs the top picks. Use when the user says "which skills should I use", "run the relevant skills", "route this", "what skill fits", /skill-router, or starts a task and wants the right skills applied without naming them.
---

# Skill router

Turns "what should I use for this?" into a ranked, scored list and then runs
the winners. Code does the catalog, the shortlist and the cutoffs; Jev answers
two yes/no questions per shortlisted skill; you judge the uncertain band and
do the running.

## 1. Describe the task

Write one or two sentences of what the user is doing **now**: the goal, the
part of the system, and the stage (planning, writing, reviewing, debugging,
shipping). Use the arguments if given; otherwise summarise the conversation.
Name concrete things ("Express routes in services/api", "GDPR data map"), not
adjectives. This text is what everything is scored against.

## 2. Run the router with your skill listing

From the repository root (it reads `git` and `package.json` there), pipe the
skills listing from your context (the "skills available for use with the
Skill tool" block) in on stdin, one line per skill exactly as listed:
`- name: description` (a line without a description is fine). This is the
only way plugin and claude.ai skills that are not on disk enter the catalog,
and it marks what is invokable right now. Use stdin, not a shared file:
parallel sessions overwrite each other's files.

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/route.py run \
  --task "<the task from step 1>" --listing - <<'LISTING'
- name: description
...
LISTING
```

Options: `--top 3` (most to run), `--sure 0.6` (auto-run cutoff), `--floor 0.25`
(below this is dropped), `--shortlist N` (how many BM25 picks Jev scores:
40 with an API key, 12 without), `--no-score` (BM25 only), `--workdir DIR`.

## 3. Score

Scoring needs a TypeSafe key. The script looks in `TYPESAFE_API_KEY`, then
the system1 MCP server's `~/.system1/config.json` (the key `fast_verify`
uses), then the checkout's `.env`, then the main checkout's `.env`. The script reads the key;
you never read `.env` or print the key yourself.

Without a key the script writes `to_score.jsonl` in the workdir it prints
(task fit only, one line per shortlisted skill). Then:
- Call the system1 MCP's `fast_verify` (`mcp__system1__fast_verify`, or
  `mcp__plugin_ai-harness_system1__fast_verify` from the ai-harness plugin) once for **every** line, with its
  `statement`, `evidence`, `yes_means` and `no_means` unchanged. Don't pick a
  subset, reword the statement, or score skills that are not in the file.
- Write `{"<id>": {"task": probability}}` to `scores.json` in that workdir.
  Don't write scores for the baseline skills; they run regardless.
- Run `route.py report` from the same checkout. A report that still lists
  "Unscored" skills is incomplete: score them or say so.

With neither a key nor the tool, use `--no-score`, judge the BM25 list
yourself and say that Jev did not score it.

What goes to TypeSafe: the task text, file-extension counts, dependency names,
changed file paths, recent commit subjects, and skill names and descriptions.
No file contents, no diffs. Mention this if the task text names a person or
something confidential, and offer `--no-score`.

## 4. Decide

**Baseline for a change.** When the task is a code change (it mentions a PR,
diff, commit, push, merge, branch, staged or uncommitted changes, or a
`/pull/N` link; force with `--change`, suppress with `--no-change`), the report
opens with **Always run for a change**: `security-review`, `tidy-context` and
`leak-check`. These run every time, whatever their score, and do not count
against `--top`. A missed review costs more than a needless one. Set
`SKILL_ROUTER_ALWAYS` (comma-separated) to change the list.

How each one runs on a change:
- `security-review`: over the diff (`git diff <base>...HEAD`), every changed
  route, input, secret, signature and outbound fetch.
- `tidy-context`: over the context files the change touches (AGENTS.md,
  CLAUDE.md, `docs/`, memory, notes). If it touches none, say so in one line.
- `leak-check`: on a PR or branch, check out its head (a worktree if the
  checkout is shared) and run it with `--range origin/<base>...HEAD`; on local
  work, over the staged diff.

The rest of the report has three parts. `p` is `task × repo`: both have to be true.

- **Run**: p ≥ sure, capped at `--top`. Run these unless one plainly
  contradicts the task (Jev reads descriptions, not the skill bodies).
- **Judge yourself**: the uncertain band, plus anything over the cap. Read
  the description; add one only if you can say in a sentence what it changes.
- Everything below the floor is dropped. Don't bring it back.

Prefer one skill that does the job over three that overlap. If two picks do
the same thing (`security-review` and `security-scan`, say), keep the one
whose description matches the task better.

## 5. Show the plan, then run

Before running anything, show the user a short table: skill, p, why (one
clause), how it runs. Then run them in a sensible order (plan → build →
review → verify):

- `Skill(<name>)` sources (loaded, installed, command, plugin): call the
  Skill tool with that name.
- `Read ~/…/SKILL.md` (library): read that file and follow it for this task
  only. Don't install it unless the user asks.

Each skill's own rules still apply. A skill that commits, pushes, publishes,
sends or deletes gets the user's confirmation at that step, as it would if
called directly. Being picked by the router is not permission.

If the user only asked "which skills fit?", stop after the table.

## Notes

- The workdir is one per checkout, `~/.cache/skill-router/<repo>-<hash>/`
  (printed on every run). It keeps `context.json`, `catalog.json`,
  `shortlist.json`, `scores.json`, `report.md`. Each run replaces the scores,
  so they never mix tasks; two sessions in the same checkout still share it.
- A skill named in the task text is always shortlisted, whatever BM25 says.
- `gdpr-compliance` is always shortlisted too, so Jev scores it on every run;
  it still has to clear the cutoff to run. Set `SKILL_ROUTER_SCORE`
  (comma-separated) to change that list.
- The shortlist weighs the task text over repo signals; repo fit is Jev's
  second question, not the keyword step's job.
- Deprecated skills (description starts with DEPRECATED) and this router are
  never candidates.
- The library path defaults to `~/Documents/everything-claude-code/skills`;
  set `SKILL_ROUTER_LIBRARY` to change it.
