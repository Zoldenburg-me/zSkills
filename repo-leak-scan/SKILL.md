---
name: repo-leak-scan
description: Scan a git repo's ENTIRE history — every commit on every branch, every PR head (merged, closed or abandoned) and every PR/issue title, body and comment — for leaked API keys and secrets (and check with the provider whether each still works), private data (IBANs, personal emails, phone numbers, home-directory paths, wallet private keys, mnemonics, personal webmail in commit metadata) and text that discloses an exploitable vulnerability or a security decision that leaves a gap. Scores every candidate with TypeSafe for "should not be public", confirms those above a user-chosen cutoff, and has Claude judge the uncertain band. Use this whenever the user wants to audit a repo before making it public, check commits or PRs for leaks, find leaked keys/tokens/passwords, check if secrets still work, look for personal data or IBANs in git history, or asks "did we leak anything", "is this repo safe to open source", "scan for secrets", "gitleaks", "trufflehog" — even if they only mention one of these.
---

# Repo leak scan

Finds what should never have been pushed, anywhere it can still be read: old
commits, branches, PR heads GitHub keeps forever, and PR conversation text.

The pipeline, and why each part exists:

1. **Collect** — `git log --all` plus `refs/pull/*/head` (a closed PR's commits
   stay downloadable even after the branch is deleted) plus PR/issue text via the
   GitHub API (people paste keys into PR comments).
2. **Detect** — gitleaks (broad secret rules), TruffleHog (secrets + **live
   verification**: it calls the provider to see if the key still works), and
   `scan_private.py` (IBAN with checksum, emails, phone numbers, home paths,
   wallet keys, mnemonics, commit identities, and security-disclosure keywords).
   Regex is cheap and over-reports; that is fine because step 3 sorts it.
   Plus `env_crosscheck.py`: the repo's own untracked `.env*` values searched
   for verbatim in all history and PR text. This is the check that catches a
   custom token no pattern knows (it found an operator token prefilled into an
   HTML password field that gitleaks and TruffleHog both missed). A hit is the
   real current value, scores 1.0, and means **rotate**.
3. **Score** — one TypeSafe Noul per candidate: the probability it should be
   removed from public history. A verified-live secret scores 1.0 without asking.
4. **Bucket** — `≥ sure` is confirmed, `floor…sure` goes to you (Claude) for a
   verdict, `< floor` is dismissed but kept in `candidates.jsonl`.

## Steps

### 1. Ask for the cutoffs (unless the user gave them)

Ask once: "Confidence cutoff for 'definitely shouldn't be public'? (default
0.85; items between 0.2 and that get my review)". Lower cutoffs mean fewer
items to review and more trust in the scorer. Accept the defaults if the user
doesn't care.

### 2. Make sure the tools exist

Run `scripts/install-tools.sh --dry-run`. If gitleaks/trufflehog are missing
from `~/.cache/repo-leak-scan/bin`, show the user the file names, sources and
sizes it printed and **ask before downloading** (it is a download of an
executable). On yes, run `scripts/install-tools.sh`; it verifies each archive
against the release's checksums file and refuses on mismatch.

If the user declines, the scan still runs: private info and disclosures are
covered, secrets only by what `scan_private.py` sees (wallet keys) — say so in
the report.

### 3. Run

```bash
~/.claude/skills/repo-leak-scan/scripts/run.sh <repo> --sure <cutoff> --floor <floor>
```

The last line printed is the workdir (a 0700 temp dir, outside the repo so a
report full of leaks can't get committed). Flags: `--no-pr` skips PR refs and
PR text (no network), `--no-score` stops before TypeSafe.

PR text uses the GitHub API unauthenticated (fine for public repos, 60
requests/hour). For a private repo or a 403, the user can export
`GITHUB_TOKEN`; never ask them to paste one into chat.

### 4. Scoring path

- **`TYPESAFE_API_KEY` in the environment or in `<repo>/.env`** → `run.sh`
  already scored everything (batched, ~20 findings per request) and printed the
  model that answered (e.g. `jev-1.13.0`). Pass `--require-typesafe` when the
  user wants a guarantee: the run then stops instead of skipping scoring.
  Go to step 5.
- **No key, but the `mcp__system1__fast_verify` tool is available** → `run.sh`
  wrote `<workdir>/to_score.jsonl`. For each line call `fast_verify` with its
  `statement`, `evidence`, `yes_means`, `no_means`; collect
  `{id: probability}` into `<workdir>/scores.json` (write it as you go, it is
  resumable), then run `scripts/triage.py report <workdir> --sure … --floor …`.
  Independent calls can go in parallel in one message. For hundreds of items,
  tell the user the count first and offer `TYPESAFE_API_KEY` as the faster path.
- **Neither** → skip scoring; every candidate lands in the review band. Review
  `high` regex severity first.

Only masked values go to TypeSafe (secrets and IBANs show 4 leading and 2–4
trailing characters). Emails and paths are sent as-is because the judgment
depends on the domain or username; mention this if the user is sensitive about it.

### 5. Review the uncertain band

`<workdir>/review.jsonl` holds the candidates between floor and cutoff. For
each, decide **leak** or **fine** with a one-line reason. Read
`references/judging.md` first: it lists what counts and the traps (test
fixtures, published contact addresses, fixed-and-described bugs). When the
snippet is not enough, look at the source: `git show <commit> -- <file>` or the
PR text file in `<workdir>/pr-text/`.

Replace the `<!-- Claude: … -->` marker in `<workdir>/report.md` with a table
of your verdicts.

### 6. Report to the user

Every candidate carries an **exposure**: `public branch`, `public (PR/issue
text)`, `PR refs only` (downloadable from GitHub but not on any branch, e.g.
after a history rewrite; needs a GitHub Support purge), or `local only` (stale
local branches; not public, but would be if pushed). Never call something
public without checking this column. Within each point below, order by
exposure.

Lead with what needs action now, in this order:

1. **Live secrets** (verified) and **current `.env` values found in history**
   — rotate immediately; history rewriting does not un-leak a key that was
   public. Never echo or sed a secret value while investigating (a `/` in the
   value breaks `sed s///` and the error prints it); use the masked output or
   Python with the value passed through an env var.
2. Confirmed private data and disclosures, and whether each is still in HEAD
   or history-only.
3. Your verdicts on the review band (leaks only; the count of "fine").
4. Dismissed count, and anything not scanned (tool missing, PR text skipped).

Never print a full secret, IBAN or private key in chat — use the masked form.
Point to `<workdir>/report.md` for the full table. For what to do about each
finding (rotate, rewrite history, GitHub cached PR refs, disclosure text) read
`references/remediation.md` and give the steps that apply; don't rewrite
history or force-push yourself unless the user explicitly asks.

## Allowlist

Known-harmless values can go in `<repo>/.leakscan-allow`, one regex per line
(matched against the value), or `path:<regex>` to skip files. Suggest entries
for recurring false positives you dismissed, but let the user decide — an
allowlist in a public repo also documents what you chose not to worry about.

## Files

- `scripts/run.sh` — the whole pipeline
- `scripts/install-tools.sh` — fetch + checksum-verify gitleaks and trufflehog
- `scripts/fetch_pr_text.py` — PR/issue titles, bodies, comments, review comments
- `scripts/scan_private.py` — private data + disclosure candidates
- `scripts/env_crosscheck.py` — local `.env` secret values vs history and PR text
- `scripts/triage.py` — merge / score / report
- `references/judging.md` — how to decide leak vs fine
- `references/remediation.md` — what to do about each kind of finding
