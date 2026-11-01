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
- From Cloudflare's security-audit-skill: security-audit (plus a hand-off line to `security-fix`).
- Zoldenburg skills: skill-router, agent-router, session-loop, security-fix, repo-leak-scan, gdpr-compliance, deep-research, plus the new `harness-init` and its templates.
- Commands: `/loop-start`, `/loop-status`, `/santa-loop`, `/leak-check`.
- Agents (17): planner, architect, code/security/TS/Python/Rust/RAG/ML reviewers, silent-failure-hunter, TDD, TS and Rust build fixers, e2e, docs lookup, loop-operator, and the read-only `vibecode-auditor` for AI-built apps.
- `.mcp.json`: Context7 for current library docs (used by `docs-lookup`) and system1 for TypeSafe scoring when there's no API key.

**`ai-harness-web3`** (add-on, in `web3/`)
- web3-dev (Blockscout), onchain-review, governance-review, dao-proposal-writer.
- It's a separate plugin so the web3 skill descriptions don't take up context in projects that don't need them.

**`ai-harness-board`** (add-on, in `board/`)
- The agent-tracker board for `session-loop`: the MCP server (`tracker_*` tools) and the token-usage hooks (Stop, SessionEnd), talking to a hosted [dashboard-ai](https://github.com/Zoldenburg-me/dashboard-ai) board.
- On enable it asks for the **Board URL** and **Board token** (the token goes to the system keychain). With no URL the server refuses to start instead of falling back to a local database.
- **More boards:** run `board/bin/board add <name> <url>` yourself in a terminal (hidden token prompt, checked against `/api/whoami`). Each extra board is its own user-scope MCP server, `agent-tracker-<name>`, with its own agent names. `board list`, `board remove <name>`.
- **Codex CLI and OpenCode:** `board/bin/board add <name> <url> --tool codex` merges `[mcp_servers.agent-tracker-<name>]` into `~/.codex/config.toml`; `--tool opencode` merges `mcp.agent-tracker-<name>` into `~/.config/opencode/opencode.json`. Other entries are kept. The entry runs the copied `launch.py` with `AGENT_DASH_URL`, `AGENT_TRACKER_NAMES` and `AGENT_DASH_TOKEN_FILE`, never the token. Then a human runs `board token <name>` in a terminal: hidden prompt, checks the token against `/api/whoami`, and only if the board accepts it writes `~/.config/agent-tracker/<name>.token` (mode 600). It prints OK or the error, and refuses to run without a terminal, since getpass would echo piped input. On Python below 3.11 (no `tomllib`) the merged `config.toml` can't be validated, so the old one is kept as `config.toml.board-bak`. The server refuses a token file that group or others can read. `--token-file PATH` picks another file, and works with `--tool claude` too, which otherwise keeps the token in Claude Code's config as before. `list` and `remove` take `--tool` and exit non-zero on failure.
- Roles still come from `AGENT_TRACKER_ROLE` in the shell that starts Claude Code (`master` for the lead, `sub` for reviewers).
- Replaces the old `install.sh` setup: remove the user-scope `agent-tracker` MCP entry, its per-folder copies and the `claude_hook.py` hooks in `~/.claude/settings.json`, or the board gets two servers and double hook calls.
- Install: `claude plugin install ai-harness-board@ai-harness`.

**Security add-on** (in `security/`, CC BY-SA 4.0, not MIT)
- Nine Trail of Bits plugins, copied unchanged and installed one by one: rust-review, spec-to-code-compliance, sharp-edges, differential-review, property-based-testing, testing-handbook-skills, audit-context-building, entry-point-analyzer, supply-chain-risk-auditor.
- They stay separate plugins because their paths (`${CLAUDE_PLUGIN_ROOT}/prompts`, `scripts/`, `workflows/`) would collide if merged. License and credit: `security/LICENSE`, `security/NOTICE.md`.
- Install: `claude plugin install <name>@ai-harness`.

## Needs

- `skill-router`, `agent-router`, `repo-leak-scan` score with TypeSafe. With a `TYPESAFE_API_KEY` (environment, `~/.system1/config.json` or `.env`) the scripts call the API directly. Without one they write `to_score.jsonl` and Claude scores each line with the system1 MCP's `fast_verify` tool, which this plugin ships in `.mcp.json` (`system1-mcp` 0.2.1, needs `uv`). With neither, they fall back to unscored BM25 and say so.
- `session-loop`, `security-fix`: the `agent-tracker` MCP and Devin review. The lead/worker rules are in `skills/session-loop/sessions-rules.md`; the worker loop also uses the `git-workflow` skill.
- `onchain-review`: API keys go in `~/.config/onchain-review/keys.env`, not inside the plugin, because plugin updates replace that folder.

## Notes

- Claude Code loads `AGENTS.md` by itself only when there's no `CLAUDE.md`. The `@AGENTS.md` import makes it load in both cases, and other agents (Codex, Cursor) read the same file.
- If ECC or Ponytail are also installed, the same skills show up twice (under different namespaces). Turn one copy off.
- To update a copied skill, copy it again from upstream and update `NOTICE.md`.
- If you already have `system1` in your own MCP config, you'll get it twice; either copy works.
- The two MCP servers in `.mcp.json` start when the plugin loads. Context7 sends library-docs queries to Upstash; system1 sends what the skills score (task text, skill and agent descriptions, masked leak candidates) to TypeSafe; with a `TYPESAFE_API_KEY` the scripts send the same data to TypeSafe directly. Remove either entry if you don't want that.
