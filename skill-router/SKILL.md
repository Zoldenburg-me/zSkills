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

## 2. Save your skill listing

Copy the skills listing from your context (the "skills available for use with
the Skill tool" block) into `~/.cache/skill-router/listing.md`, one line per
skill exactly as listed: `- name: description` (a line without a description
is fine). This is the only way plugin and claude.ai skills that are not on
disk enter the catalog, and it marks what is invokable right now.

## 3. Run the router

From the repository root (it reads `git` and `package.json` there):

```bash
python3 ~/.claude/skills/skill-router/scripts/route.py run \
  --task "<the task from step 1>" \
  --listing ~/.cache/skill-router/listing.md
```

Options: `--top 3` (most to run), `--sure 0.6` (auto-run cutoff), `--floor 0.25`
(below this is dropped), `--shortlist 40` (how many BM25 picks Jev scores),
`--no-score` (BM25 only).

Scoring needs `TYPESAFE_API_KEY` in the environment or the repo's `.env`. The
key is read, never printed. Without it the script writes `to_score.jsonl`:
score those questions with `mcp__system1__fast_verify` if that tool is
available, write `{"<name>": {"task": p, "repo": p}}` to
`~/.cache/skill-router/last/scores.json`, and run `route.py report`. With
neither, judge the BM25 list yourself and say that Jev did not score it.

What goes to TypeSafe: the task text, file-extension counts, dependency names,
changed file paths, recent commit subjects, and skill names and descriptions.
No file contents, no diffs. Mention this if the task text names a person or
something confidential, and offer `--no-score`.

## 4. Decide

The report has three parts. `p` is `task × repo`: both have to be true.

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

- Workdir `~/.cache/skill-router/last/` keeps `context.json`, `catalog.json`,
  `shortlist.json`, `scores.json`, `report.md`. Each run replaces the scores,
  so they never mix tasks.
- A skill named in the task text is always shortlisted, whatever BM25 says.
- The shortlist weighs the task text over repo signals; repo fit is Jev's
  second question, not the keyword step's job.
- Deprecated skills (description starts with DEPRECATED) and this router are
  never candidates.
- The library path defaults to `~/Documents/everything-claude-code/skills`;
  set `SKILL_ROUTER_LIBRARY` to change it.
