# zSkills

Agent skills from Zoldenburg, for Claude Code and any agent that reads the
`SKILL.md` format: a folder with a `SKILL.md` (name, description, instructions)
plus the scripts and references it uses.

## Install

Copy a skill folder into `~/.claude/skills/` (all projects) or
`<repo>/.claude/skills/` (one project):

```bash
git clone git@github.com:Zoldenburg-me/zSkills.git
cp -r zSkills/repo-leak-scan ~/.claude/skills/
```

## Skills

| Skill | What it does |
|---|---|
| [repo-leak-scan](repo-leak-scan/SKILL.md) | Scans every commit, branch, PR head and PR/issue text for leaked secrets (and checks with the provider whether they still work), private data (IBANs, emails, phone numbers, home paths, wallet keys, commit identities) and vulnerability disclosures. Compares the repo's own `.env` values against history. Scores each candidate with TypeSafe, confirms those above a cutoff, and leaves the uncertain band to the agent. Labels each finding by exposure: public branch, PR refs only, or local only. |
| [onchain-review](onchain-review/SKILL.md) | Reviews wallets, contracts, transactions and Safe multisigs on any EVM chain through the Blockscout MCP server, the Blockscout PRO API, Etherscan V2 and the Safe Transaction Service: balances and activity, DAO delegation and votes, verified source and state at a past block, transaction traces, Safe owners, threshold and pending proposals with who has signed. Read-only; every number comes from a fetched response. |
| [skill-router](skill-router/SKILL.md) | Picks the skills that fit the current task and runs them. Catalogs every reachable skill (loaded listing, `~/.claude/skills`, commands, plugins, the uninstalled ECC library), shortlists with BM25, then scores each shortlisted skill with two TypeSafe Jev Nouls: does it serve the task, and does the repo have what it works on. Runs the top picks, hands the uncertain band to the agent, and shows the plan before running anything. |
| [gdpr-compliance](gdpr-compliance/SKILL.md) | Audits a codebase for GDPR / DSGVO and produces an Art. 30 data map: every place the app collects, stores, logs or sends personal data, the recipients, controller vs processor role, proposed legal basis and retention, data-subject-rights coverage, and a ranked gap list (Blocker / Fix / Tidy) with fixes and questions for counsel. Also reviews a diff for new personal-data exposure and drafts an Art. 13 notice. German specifics included (DDG Impressum, TDDDG, BDSG DPO, §147 AO retention). Engineering inventory, not legal advice. |
| [security-fix](security-fix/SKILL.md) | Works the findings of a finished security-audit run one per session. `queue` turns `findings.json` into a fix queue (`FIX-PROGRESS.md`) and marks findings that need a product decision; `next` claims one row, writes the reproduction test, makes the smallest fix at the last trusted decision point, and opens a PR. A deterministic judge (test red on the merge base, green on the fix, no deleted or weakened tests) and an independent checker subagent with a mutation check decide whether the fix stands. The fixer never grades itself and never merges; the owner's merge marks the row fixed. Each session offers a one-click chip for the next finding. |

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
