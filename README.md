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
