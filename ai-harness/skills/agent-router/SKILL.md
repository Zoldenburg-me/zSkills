---
name: agent-router
description: Pick and launch the subagents that fit what the user is doing right now. Builds a catalog of every reachable agent (the session's agent listing, ~/.claude/agents, plugin agents, and the uninstalled ECC agent library), shortlists it with BM25 against the task and the repo, scores the shortlist with TypeSafe Jev (does it fit the task, does the repo have what it works on), then launches the top picks in parallel. Use when the user says "which agents should I use", "run the relevant agents", "route this to agents", "what agent fits", /agent-router, or wants the right subagents applied without naming them.
---

# Agent router

The subagent counterpart of `skill-router`. It turns "which agents should look
at this?" into a ranked, scored list and then launches the winners. Code builds
the catalog and the shortlist and applies the cutoffs. Jev answers two yes/no
questions per shortlisted agent. You judge the uncertain band and do the
launching. The script reuses `skill-router`'s repo context, BM25 and TypeSafe
client, so the `skill-router` skill must sit next to this one.

## 1. Describe the task

Write one or two sentences about what the user is doing **now**: the goal, the
part of the system, and the stage (planning, writing, reviewing, debugging,
shipping). Use the arguments if any were given; otherwise summarise the
conversation. Name concrete things ("rate-limit middleware in host/src"), not
adjectives.

## 2. Run the router with the agent listing

From the repository root, pipe the "Available agent types for the Agent tool"
block from your context in on stdin, one line per agent, in the form
`- name: description`. The trailing `(Tools: …)` may stay; the script strips it.
This is the only way plugin and built-in agents enter the catalog, and it marks
what `Agent(subagent_type=…)` accepts right now. Use stdin, not a shared file:
parallel sessions overwrite each other's files.

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/route.py run \
  --task "<the task from step 1>" --listing - <<'LISTING'
- name: description
...
LISTING
```

Options:
- `--top 3`: the most agents to launch.
- `--sure 0.6`: the auto-launch cutoff.
- `--floor 0.25`: anything scoring below this is dropped.
- `--shortlist 30`: how many BM25 picks Jev scores.
- `--no-score`: rank with BM25 only.
- `--change` / `--no-change`: force the code-change baseline on or off.
- `--workdir DIR`: defaults to one per checkout, printed on every run.

**Scoring.** Scoring needs a TypeSafe key. The script (skill-router's key
lookup) tries `TYPESAFE_API_KEY`, then the system1 MCP server's
`~/.system1/config.json` (the key `fast_verify` uses), then the checkout's
`.env`, then the main checkout's `.env`. The script reads the key; you never
read `.env` or print the key yourself.

If there's no key, the script writes `to_score.jsonl` in the workdir it prints,
covering the top `--mcp-shortlist` agents (default 12, which means 24
questions) and leaving out the baseline, which launches regardless. Then:
1. Score **every** line with the system1 MCP's `fast_verify` (`mcp__system1__fast_verify`, or `mcp__plugin_ai-harness_system1__fast_verify` from the ai-harness plugin), if that tool is
   available. Pass its `statement`, `evidence`, `yes_means` and `no_means`
   fields unchanged, and send all the calls in one message so they run in
   parallel. Don't pick a subset or score agents that aren't in the file.
2. Write the results to `scores.json` in that workdir as
   `{"<name>": {"task": p, "repo": p}}`.
3. Run `route.py report` from the same checkout. A report that still lists
   "Unscored" agents is incomplete: score them or say so.

If neither the key nor the tool is available, judge the BM25 list yourself and
tell the user that Jev did not score it.

**What goes to TypeSafe:** the task text, file-extension counts, dependency
names, changed file paths, recent commit subjects, and agent names and
descriptions. No file contents and no diffs. If the task text names a person or
something confidential, say so and offer `--no-score`.

## 3. Decide

**Baseline for a change.** A task counts as a code change when it mentions a PR,
diff, commit, push, merge, branch, or staged or uncommitted changes. For a
change, the report opens with **Always launch for a change**:
`code-reviewer` and `security-reviewer`. They run whatever their score and
don't count toward `--top`. Set `AGENT_ROUTER_ALWAYS` (comma-separated) to
change the list.

Below the baseline, the report has three parts. `p` is `task × repo`, so an
agent only ranks high if both answers are yes.
- **Launch**: agents with p ≥ sure, up to `--top`. Launch these unless one
  plainly contradicts the task. Jev reads descriptions, not the agent bodies.
- **Judge yourself**: the uncertain band, plus anything over the cap. Add an
  agent only if you can say in one sentence what it will find that the others
  won't.
- Agents below the floor are dropped. Don't bring them back.

Prefer agents that don't overlap. If a language reviewer (such as
`typescript-reviewer`) and `code-reviewer` both qualify, keep both only for a
real change. For a quick question, the language reviewer is enough. Agents that
only plan or review (`planner`, `architect` and the `*-reviewer` agents) are
safe to run in parallel. Agents that edit files (`*-build-resolver`,
`refactor-cleaner`, `code-simplifier`, `tdd-guide`, `doc-updater`) should run
one at a time, or with `isolation: "worktree"`.

`general-purpose`, `claude`, `Explore`, `Plan` and `statusline-setup` are never
candidates. Set `AGENT_ROUTER_NEVER` to change that list.

## 4. Show the plan, then launch

Before launching anything, show the user a short table with these columns:
agent, p, why (one clause), and what it will be asked. Then:

- **`Agent(<name>)` sources** (loaded, installed, plugin): call the Agent tool
  with `subagent_type: <name>`. Give it a self-contained prompt that includes
  the task, the files or diff range, and what to return. Launch independent
  agents in one message so they run in parallel.
- **`Agent(general-purpose) + <path>` sources** (library): read that agent file
  and launch `general-purpose` with the file's body as the brief, followed by
  the task. Don't install the agent unless the user asks.

Wait for every launched agent and merge the results into one answer, most
severe first. Never end a turn while agents are still running. An agent's
report isn't shown to the user, so relay what matters.

Being picked by the router is not permission. Any agent that would commit,
push, publish, send or delete still needs the user's confirmation at that step.

If the user only asked "which agents fit?", stop after the table.

## Notes

- The workdir is one per checkout, `~/.cache/agent-router/<repo>-<hash>/`. It
  holds `context.json`, `catalog.json`, `shortlist.json`, `scores.json`,
  `report.md` and `run.json`. Each run replaces the scores, so results from
  different tasks never mix; two sessions in the same checkout still share it.
- An agent named in the task text is always shortlisted, whatever its BM25
  score.
- The library path defaults to `~/Documents/everything-claude-code/agents`.
  Set `AGENT_ROUTER_LIBRARY` to change it.
