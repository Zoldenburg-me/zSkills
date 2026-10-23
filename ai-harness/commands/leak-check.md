---
description: Quick leak check of the STAGED changes and the commit identity (same check the global pre-commit hook runs), or of a branch/PR with --range BASE...HEAD (diff, commit messages and author/committer emails). Blocks Claude session links and hostname/unset git emails. For a full-history audit use /repo-leak-scan.
argument-hint: "[repo path, default: current repo] [--range origin/main...HEAD]"
allowed-tools: Bash(python3 ${CLAUDE_PLUGIN_ROOT}/skills/repo-leak-scan/scripts/precommit.py:*), Bash(git diff --cached --stat:*), Bash(git diff --stat:*)
---

Run the repo-leak-scan pre-commit check on the staged changes of `$ARGUMENTS` (or the current repo if empty):

```bash
git diff --cached --stat
python3 ${CLAUDE_PLUGIN_ROOT}/skills/repo-leak-scan/scripts/precommit.py ${ARGUMENTS:-.}
```

For a branch or PR (what it adds over its merge base), check out its head and pass the range:

```bash
git diff --stat origin/main...HEAD
python3 ${CLAUDE_PLUGIN_ROOT}/skills/repo-leak-scan/scripts/precommit.py . --range origin/main...HEAD
```

Then report briefly:
- If nothing is staged (and no `--range`), say so: the check only looks at staged lines (`git add` first).
- Exit 0: clean, list any `warn` lines (other emails, phones) in one line.
- `identity` / `commit … author` BLOCKs: git has no `user.email` (it guessed `user@<hostname>`, which leaks the machine and network) or the address is a hostname or webmail. Fix: `git config --global user.email <id>+<user>@users.noreply.github.com`; already-pushed commits need an author rewrite (ask first: force-push).
- `claude-session-link` BLOCKs: a `claude.ai/code/session_…` (or `/chat/`, `/share/`) link in a file or commit message. Fix: drop the line (usually a `Claude-Session:` trailer).
- Exit 1: each `BLOCK` finding with its file and kind, using the masked value exactly as printed. Never print an unmasked secret, IBAN or key. Say what to do: remove the value, add a regex to `.leakscan-allow` for a real false positive (let the user decide), or rotate it if it is a local `.env` secret.

Do not edit files, unstage, or commit unless asked.
