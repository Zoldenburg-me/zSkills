# zSkills

Agent skills from Zoldenburg, for Claude Code, Codex CLI, OpenCode and any
agent that reads the `SKILL.md` format: a folder with a `SKILL.md` (name,
description, instructions) plus the scripts and references it uses.
Also one subagent (`vibecode-auditor`) and one Claude Code plugin
(`ai-harness`) that bundles skills, agents and commands.

## Install

### Claude Code

Copy a skill folder into `~/.claude/skills/` (all projects) or
`<repo>/.claude/skills/` (one project):

```bash
git clone git@github.com:Zoldenburg-me/zSkills.git
cp -r zSkills/repo-leak-scan ~/.claude/skills/
```

An agent file goes into `~/.claude/agents/`:

```bash
cp zSkills/vibecode-auditor/vibecode-auditor.md ~/.claude/agents/
```

`ai-harness` installs as a plugin:

```bash
claude plugin marketplace add ./zSkills/ai-harness
claude plugin install ai-harness@ai-harness
```

### Codex CLI

Codex discovers skills from `.agents/skills/` directories. Clone the repo
into your project or link it:

```bash
git clone git@github.com:Zoldenburg-me/zSkills.git
# Symlink the skills into your repo so Codex finds them
ln -sfn "$PWD/zSkills/.agents/skills" .agents/
```

Or copy individual skills:

```bash
cp -r zSkills/repo-leak-scan .agents/skills/
```

Codex loads the skills automatically on next launch. Use `$skill-name` to
invoke one, or let Codex pick the right skill from the description.

For an agent definition, place the file in your project:

```bash
cp zSkills/vibecode-auditor/vibecode-auditor.md .agents/agents/
```

### OpenCode

OpenCode discovers skills from `.opencode/skills/` and agents from
`.opencode/agents/`. Clone the repo and symlink the discovery directories:

```bash
git clone git@github.com:Zoldenburg-me/zSkills.git
ln -sfn "$PWD/zSkills/.opencode/skills" .opencode/
ln -sfn "$PWD/zSkills/.opencode/agents" .opencode/
ln -sfn "$PWD/zSkills/.opencode/commands" .opencode/
```

Or reference individual skills in `opencode.jsonc`:

```jsonc
{
  "plugins": ["./zSkills/ai-harness"]
}
```

The `opencode.jsonc` at the repo root also ships MCP server config for
Context7 and system1 (TypeSafe scoring).

## Skills

| Skill | What it does |
|---|---|
| [repo-leak-scan](repo-leak-scan/SKILL.md) | Scans every commit, branch, PR head and PR/issue text for leaked secrets (and checks with the provider whether they still work), private data (IBANs, emails, phone numbers, home paths, wallet keys, commit identities) and vulnerability disclosures. Compares the repo's own `.env` values against history. Scores each candidate with TypeSafe, confirms those above a cutoff, and leaves the uncertain band to the agent. Labels each finding by exposure: public branch, PR refs only, or local only. |
| [onchain-review](onchain-review/SKILL.md) | Reviews wallets, contracts, transactions and Safe multisigs on any EVM chain through the Blockscout MCP server, the Blockscout PRO API, Etherscan V2 and the Safe Transaction Service: balances and activity, DAO delegation and votes, verified source and state at a past block, transaction traces, Safe owners, threshold and pending proposals with who has signed. Read-only; every number comes from a fetched response. |
| [skill-router](skill-router/SKILL.md) | Picks the skills that fit the current task and runs them. Catalogs every reachable skill (loaded listing, `~/.claude/skills`, commands, plugins, the uninstalled ECC library), shortlists with BM25, then scores each shortlisted skill with two TypeSafe Jev Nouls: does it serve the task, and does the repo have what it works on. Runs the top picks, hands the uncertain band to the agent, and shows the plan before running anything. |
| [gdpr-compliance](gdpr-compliance/SKILL.md) | Audits a codebase for GDPR / DSGVO and produces an Art. 30 data map: every place the app collects, stores, logs or sends personal data, the recipients, controller vs processor role, proposed legal basis and retention, data-subject-rights coverage, and a ranked gap list (Blocker / Fix / Tidy) with fixes and questions for counsel. Also reviews a diff for new personal-data exposure and drafts an Art. 13 notice. German specifics included (DDG Impressum, TDDDG, BDSG DPO, §147 AO retention). Engineering inventory, not legal advice. |
| [security-fix](security-fix/SKILL.md) | Works the findings of a finished security-audit run one per session. `queue` turns `findings.json` into a fix queue (`FIX-PROGRESS.md`) and marks findings that need a product decision; `next` claims one row, writes the reproduction test, makes the smallest fix at the last trusted decision point, and opens a PR. A deterministic judge (test red on the merge base, green on the fix, no deleted or weakened tests) and an independent checker subagent with a mutation check decide whether the fix stands. The fixer never grades itself and never merges; the owner's merge marks the row fixed. Each session offers a one-click chip for the next finding. |
| [session-loop](session-loop/SKILL.md) | Runs board tasks across Claude Code sessions. The lead reads the agent-tracker board by priority, starts one worker session per task and keeps the board current; it never codes. Each worker fixes and tests, runs `/skill-router` and `/agent-router` before every commit, opens the PR (and a docs PR for user-visible changes), runs `/git-workflow` once, waits for Devin to pass on the final head SHA, merges, proves the merge on `origin/main` and reports in one message. Hard limits in `sessions-rules.md`. |

## Agents

| Agent | What it does |
|---|---|
| [vibecode-auditor](vibecode-auditor/vibecode-auditor.md) | Read-only audit of apps built with Lovable, Bolt, v0, Replit, Cursor and similar. Looks for what these builds ship with: keys in the client, missing server-side checks, open database policies, unbounded AI spend, placeholder data, generic UI. Returns a ranked report and a launch verdict. Its eval (seeded and clean fixture apps, answer key, grader) is in `ai-harness/evals/vibecode-auditor/`. |

## Plugins

| Plugin | What it does |
|---|---|
| [ai-harness](ai-harness/README.md) | Claude Code plugin for building AI apps: evals first, smallest complete change, reviewed and verified before merge. Bundles about 30 skills (from ECC, Ponytail, andrej-karpathy-skills and this repo), 15 agents, 4 commands, an `AGENTS.md` template with `/ai-harness:harness-init`, and a separate `ai-harness-web3` add-on. Third-party licences in `NOTICE.md`. |

## Multi-agent compatibility

This repo ships discovery directories for three agent platforms:

| Platform | Skills | Agents | Commands | Config |
|---|---|---|---|---|
| **Claude Code** | `~/.claude/skills/` or plugin | `~/.claude/agents/` or plugin | Plugin `/commands` | `ai-harness/` plugin |
| **Codex CLI** | `.agents/skills/` | `.agents/agents/` (AGENTS.md) | N/A (slash commands) | `.codex/config.toml` |
| **OpenCode** | `.opencode/skills/` | `.opencode/agents/` | `.opencode/commands/` | `opencode.jsonc` |

The same `SKILL.md` format works across all three. Symlinked directories
(`.agents/skills/`, `.opencode/skills/`) let you use the repo's skills without
copying them. |

### repo-leak-scan requirements

- git, curl, Python 3.9+ (standard library only)
- gitleaks and TruffleHog: `repo-leak-scan/scripts/install-tools.sh` downloads
  the latest releases and verifies them against the published checksums
- `TYPESAFE_API_KEY` in the environment or the scanned repo's `.env` for
  scoring; without it the agent scores through the TypeSafe MCP tool or
  reviews everything itself
- `GITHUB_TOKEN` only for private repos (PR text is read through the GitHub API)

### onchain-review requirements

- Python 3.9+ (standard library only) for `scripts/onchain.py`, or the
  Blockscout MCP connector (no key needed)
- Optional keys, read from the environment or `onchain-review/keys.env`
  (gitignored; template in `keys.env.example`): `ETHERSCAN_API_KEY`,
  `BLOCKSCOUT_PRO_API_KEY`, `SAFE_API_KEY` (needed for Safe multisig review)
- Includes Blockscout's MIT-licensed agent-skills material under
  `references/upstream/` with its licence

### skill-router requirements

- Python 3.9+ (standard library only), git
- `TYPESAFE_API_KEY` in the environment or the repo's `.env` for scoring;
  without it the agent scores through the system1 `fast_verify` MCP tool or
  judges the BM25 shortlist itself
- Optional: a local clone of the ECC skills library; set
  `SKILL_ROUTER_LIBRARY` to its `skills/` folder
- Sends the task text, file-type counts, dependency names, changed file paths
  and recent commit subjects to TypeSafe; no file contents or diffs

### gdpr-compliance requirements

- bash and grep for `scripts/pii_scan.sh` (no other dependencies)
- An agent that can run parallel read-only sub-agents for the four sweeps;
  without it, run the sweeps one after another
- Sends nothing anywhere: the scan and sweeps read the local repo only

### security-fix requirements

- Python 3.9+ (standard library only), git
- A run directory written by a `security-audit` style workflow: `findings.json`
  (records with `verdict`, `fingerprint`, `title`, `trace`, `evidence`,
  `blockers`, `validation_plan`) and `run-metadata.json` with `run_status`
- The target repo's own test runner; `fix-config.json` in the run dir records
  how to run one test file and which gitignored dirs to link into worktrees
- Optional: the Claude desktop app's task chips (`spawn_task`) to open the next
  session; without them the skill prints the prompt to paste
- Optional: `agent-router` and `skill-router` for the review pass
- Runs the repo's tests locally only; sends nothing anywhere except the PR

### session-loop requirements

- The `agent-tracker` MCP (the board), the Claude desktop app's session tools
  (`start_session`, `SendMessage`), a GitHub repo with Devin review, and an
  authenticated `gh` CLI
- `skill-router`, `agent-router` and `git-workflow` for the worker loop;
  `agent-router` and `git-workflow` ship inside `ai-harness`

### ai-harness requirements

- Claude Code with plugin support; `uv` for the bundled system1 MCP, `npx`
  for Context7
- The per-skill requirements above apply to the copies inside it. The
  copies inside `ai-harness` can be newer than the standalone folders

## License

MIT, see [LICENSE](LICENSE); `ai-harness/` carries its own copy. Third-party
material keeps its own licence, listed in `ai-harness/NOTICE.md`,
`ai-harness/web3/NOTICE.md` and `onchain-review/references/upstream/`.
