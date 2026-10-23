# What to do about each finding

Order matters: **contain first, clean up second.** A public secret has to be
assumed copied; rewriting history only stops future readers.

## Secrets

1. Revoke or rotate at the provider. Do this even for "dead" verification
   results if the key was ever real.
2. Check the provider's access logs for use since the commit date.
3. Move the value to the secret store / `.env` (gitignored) and reference it.
4. Optionally remove it from history (below). Not a substitute for 1.

## Private data in history

- Still in HEAD → delete or replace it in a normal commit first.
- History rewrite: `git filter-repo --replace-text expressions.txt`
  (`literal==>***REMOVED***` per line) or `--invert-paths --path <file>`; BFG
  works too. Every branch and tag needs the rewrite; then force-push all refs
  and tell collaborators to re-clone (old clones still have it).
- **Author identity** (personal webmail in commits): `git filter-repo
  --mailmap mailmap.txt` with `New Name <new@domain> <old@gmail.com>`. Set
  `git config user.email` to the project address, or GitHub's noreply address,
  so it does not recur.
- **If the committer is `noreply@github.com`**, the commits are PR merges or
  web edits made on github.com, and GitHub takes the author email from the
  account, not from git config. Fix it in GitHub → Settings → Emails: make the
  project address primary or tick "Keep my email addresses private" (and the
  default commit email for web-based operations). Otherwise every merge
  re-leaks the address after a rewrite.

## Things a force-push does not remove

- **PR refs** (`refs/pull/N/head`) are read-only for you and keep the old
  commits reachable. Also cached commit views and forks. Ask GitHub Support to
  purge them (Support → "Remove sensitive data", list the commit SHAs and PR
  numbers). GitHub's "Removing sensitive data from a repository" docs describe
  the exact request.
- **PR/issue text** — edit or delete the comment; GitHub keeps edit history
  visible to anyone who can see the comment, so delete the edit revision as well
  (comment menu → "edited" → delete revision) or ask Support.
- Forks and other people's clones: out of your control; this is why step 1
  for secrets is rotate.

## Disclosure text

- Unfixed weakness → fix it first, then decide whether to rewrite the message.
  Rewriting old commit messages needs a full history rewrite, so for most
  cases fixing the weakness is the remediation and the text becomes a
  changelog entry.
- Living docs (AGENTS.md, docs/*.md) that describe an open gap: move the
  detail to a private place (private repo, issue tracker with restricted
  access, or a GitHub security advisory draft) and leave a neutral rule in
  the public file.
- Set up a `SECURITY.md` with a private reporting route so the next
  finding goes there instead of into a commit message.

## Prevent recurrence

- Pre-commit: `gitleaks protect --staged` (or `gitleaks git --pre-commit`
  in newer versions) as a hook.
- GitHub: enable secret scanning and **push protection** (Settings → Code
  security), free on public repos.
- CI: run this scan (or `gitleaks git --log-opts=<base>..HEAD`) on every PR.
