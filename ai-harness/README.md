# ai-harness

A Claude Code plugin for building AI apps: evals first, smallest complete change, reviewed and verified before merge.
It's put together from skills and agents in [ECC](https://github.com/affaan-m/everything-claude-code) and [Ponytail](https://github.com/DietrichGebert/ponytail) (both MIT, see `NOTICE.md`), plus an `AGENTS.md` template for projects.

## Install

```bash
claude plugin marketplace add ./zSkills/ai-harness   # from a clone of zSkills
claude plugin install ai-harness@ai-harness
claude plugin install ai-harness-web3@ai-harness   # optional web3 add-on
```

Then, in a project: `/ai-harness:harness-init` writes `AGENTS.md` and a `CLAUDE.md` that imports it (`@AGENTS.md`). Fill in the TODOs.

## What's inside

**`ai-harness`** (core)
- Skills from ECC: eval-harness, ai-regression-testing, tdd-workflow, verification-loop, security-review, api-design, error-handling, search-first, iterative-retrieval, cost-aware-llm-pipeline, agent-harness-construction, mcp-server-patterns, regex-vs-llm-structured-text, loop-design-check, continuous-agent-loop, git-workflow.
- Skills from Ponytail: ponytail, ponytail-review, ponytail-audit.
- From andrej-karpathy-skills: karpathy-guidelines (think before coding, simplicity first, surgical changes, goal-driven execution).
- Zoldenburg skills: skill-router, agent-router, session-loop, security-audit, security-fix, repo-leak-scan, gdpr-compliance, deep-research, plus the new `harness-init` and its templates.
- Commands: `/loop-start`, `/loop-status`, `/santa-loop`, `/leak-check`.
- Agents (15): planner, architect, code/security/TS/Python/RAG/ML reviewers, silent-failure-hunter, TDD, build fixer, e2e, docs lookup, loop-operator, and the read-only `vibecode-auditor` for AI-built apps.
- `.mcp.json`: Context7 for current library docs (used by `docs-lookup`) and system1 for TypeSafe scoring when there's no API key.

**`ai-harness-web3`** (add-on, in `web3/`)
- web3-dev (Blockscout), onchain-review, governance-review, dao-proposal-writer.
- It's a separate plugin so the web3 skill descriptions don't take up context in projects that don't need them.

## Needs

- The two MCP servers in `.mcp.json` start when the plugin loads. Context7 sends library-docs queries to Upstash; system1 sends what the skills score (task text, skill and agent descriptions, masked leak candidates) to TypeSafe; with a `TYPESAFE_API_KEY` the scripts send the same data to TypeSafe directly. Remove either entry if you don't want that.
- `skill-router`, `agent-router`, `repo-leak-scan` score with TypeSafe. With a `TYPESAFE_API_KEY` (environment, `~/.system1/config.json` or `.env`) the scripts call the API directly. Without one they write `to_score.jsonl` and Claude scores each line with the system1 MCP's `fast_verify` tool, which this plugin ships in `.mcp.json` (`system1-mcp` 0.2.1, needs `uv`). With neither, they fall back to unscored BM25 and say so.
- `session-loop`, `security-fix`: the `agent-tracker` MCP and Devin review. The lead/worker rules are in `skills/session-loop/sessions-rules.md`; the worker loop also uses the `git-workflow` skill.
- `onchain-review`: API keys go in `~/.config/onchain-review/keys.env`, not inside the plugin, because plugin updates replace that folder.

## Notes

- Claude Code loads `AGENTS.md` by itself only when there's no `CLAUDE.md`. The `@AGENTS.md` import makes it load in both cases, and other agents (Codex, Cursor) read the same file.
- If ECC or Ponytail are also installed, the same skills show up twice (under different namespaces). Turn one copy off.
- To update a copied skill, copy it again from upstream and update `NOTICE.md`.
- If you already have `system1` in your own MCP config, you'll get it twice; either copy works.
