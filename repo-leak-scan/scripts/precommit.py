#!/usr/bin/env python3
"""Pre-commit gate: the repo-leak-scan detectors over the STAGED changes only.

The full scan (run.sh) walks all history, every PR ref and PR text, and scores
with TypeSafe: minutes per run, and it would block every commit on old
findings this commit cannot fix. This checks only the lines being added now:

  - gitleaks --staged                     (secret rules)
  - scan_private.scan_text                (IBAN, webmail, home paths, wallet keys,
                                           mnemonics, prefilled password fields)
  - local .env secret values              (env_crosscheck's filter, verbatim match)

  - the commit identity git will use      (blocks when user.email is unset, so
                                           git would guess user@<hostname>, or
                                           when it is a hostname or webmail)
  - Claude session links (claude.ai/code/session_…, /chat/, /share/)

Blocks on: any gitleaks hit, any high-severity private finding (incl. Claude
session links), any home-dir path, any local .env value, a guessed, hostname
or webmail commit identity. Warns (does not block) on other emails, phones and
non-noreply identities. Values are printed masked. Allowlist:
REPO/.leakscan-allow (same format as the full scan). Bypass once:
git commit --no-verify.

Usage: precommit.py [REPO=.] [--range BASE...HEAD] [--commit-msg FILE]
  --range checks the lines a branch or PR adds over its merge base instead of
  the staged diff (gitleaks then scans those commits), plus the messages and
  author/committer identities of those commits.
  --commit-msg checks only the message being committed (the commit-msg hook).
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import scan_private as sp  # noqa: E402
import env_crosscheck as ec  # noqa: E402

BIN = os.environ.get("LEAKSCAN_BIN", os.path.expanduser("~/.cache/repo-leak-scan/bin"))
BLOCK_KINDS = {"personal-path"}  # blocked even at "review" severity: never public


def mask(kind, v):
    if kind in ("email", "personal-path", "phone"):
        return v
    return v[:4] + "…" + v[-3:] if len(v) > 10 else "…"


def staged_added_lines(repo, rng=None):
    """Yield (file, line) for every added line in the staged diff, or in RANGE."""
    which = [rng] if rng else ["--cached"]
    diff = subprocess.run(["git", "-C", repo, "diff", *which, "-U0", "--no-color",
                           "--no-ext-diff", "--diff-filter=ACMR"],
                          capture_output=True, text=True, errors="replace", check=True).stdout
    f = None
    for line in diff.splitlines():
        if line.startswith("+++ "):
            f = line[6:] if line.startswith("+++ b/") else None
        elif f and line.startswith("+") and not sp.DEFAULT_SKIP_PATHS.search(f):
            yield f, line[1:][:sp.MAX_LINE]


def run_gitleaks(repo, rng=None):
    exe = os.path.join(BIN, "gitleaks")
    if not os.access(exe, os.X_OK):
        print("leak-scan: gitleaks not installed, secret rules NOT checked "
              "(scripts/install-tools.sh in the repo-leak-scan skill)", file=sys.stderr)
        return 0
    scope = ["--log-opts", rng.replace("...", "..")] if rng else ["--pre-commit", "--staged"]
    r = subprocess.run([exe, "git", repo, *scope, "--redact", "--no-banner", "-v",
                        "--log-level", "warn", "--exit-code", "1"])
    return 1 if r.returncode == 1 else 0


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, errors="replace")


def identity_problem(email):
    """(block, reason) for a commit email, or None when it is fine."""
    host = sp.hostname_identity(email)
    if host:
        return True, host
    dom = email.rpartition("@")[2].lower()
    if dom in sp.WEBMAIL:
        return True, "personal webmail"
    if not dom.endswith("noreply.github.com") and not email.lower().startswith("noreply@"):
        return False, "not a no-reply address"
    return None


def check_identity(repo):
    """Messages for the identity the next commit will use: [(block, text)]."""
    out = []
    unset = False
    configured = git(repo, "config", "--get", "user.email").stdout.strip()
    from_env = os.environ.get("GIT_AUTHOR_EMAIL") or os.environ.get("EMAIL")
    for var in ("GIT_AUTHOR_IDENT", "GIT_COMMITTER_IDENT"):
        r = git(repo, "var", var)
        if r.returncode != 0:
            out.append((True, f"{var}: git has no identity ({r.stderr.strip()[:120]})"))
            continue
        email = r.stdout.rpartition("<")[2].partition(">")[0]
        if unset:
            continue  # same guessed address; already reported for the author
        if not configured and not from_env:
            unset = True
            out.append((True, f"no user.email configured: git would commit as <{email}>, built from this "
                              "machine's hostname. Set git config --global user.email "
                              "<id>+<user>@users.noreply.github.com"))
            continue
        p = identity_problem(email)
        if p:
            out.append((p[0], f"{var}: <{email}> ({p[1]})"))
    return list(dict.fromkeys(out))


def message_lines(text):
    """Commit message lines as git will store them (comments and scissors part dropped)."""
    for line in text.splitlines():
        if line.startswith("# ------------------------ >8"):
            break
        if not line.startswith("#"):
            yield line


def range_commits(repo, rng):
    """(sha, author email, committer email, message) for every commit in RANGE."""
    r = git(repo, "log", "--no-color", "--format=%x1e%h%x1f%ae%x1f%ce%x1f%B", rng.replace("...", ".."))
    for rec in r.stdout.split("\x1e")[1:]:
        sha, ae, ce, body = (rec.split("\x1f") + ["", "", "", ""])[:4]
        yield sha, ae, ce, body


def local_secrets(repo):
    for rel, path in ec.env_files(repo):
        for k, v in ec.parse(path):
            if ec.is_secret(k, v):
                yield f"{k} (from {rel})", v


def main():
    args = sys.argv[1:]
    rng = msg_file = None
    if "--commit-msg" in args:
        i = args.index("--commit-msg")
        if i + 1 >= len(args):
            sys.exit("leak-scan: --commit-msg needs FILE")
        msg_file = args[i + 1]
        del args[i:i + 2]
    if "--range" in args:
        i = args.index("--range")
        if i + 1 >= len(args):
            sys.exit("leak-scan: --range needs BASE...HEAD")
        rng = args[i + 1]
        del args[i:i + 2]
    repo = subprocess.run(["git", "-C", args[0] if args else ".", "rev-parse",
                           "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip()
    F = sp.Findings(*sp.load_allow(os.path.join(repo, ".leakscan-allow")))
    if msg_file:
        return check_message(F, msg_file)
    secrets = list(local_secrets(repo))
    env_hits = []
    for f, text in staged_added_lines(repo, rng):
        sp.scan_text(F, text, dict(source="diff", file=f))
        env_hits += [(name, f) for name, v in secrets if v in text]

    blocked = run_gitleaks(repo, rng)
    if rng:
        for sha, ae, ce, body in range_commits(repo, rng):
            for line in message_lines(body):
                sp.scan_text(F, line[:sp.MAX_LINE], dict(source="commit-message", file=f"commit {sha} message"))
            for who, email in (("author", ae), ("committer", ce)):
                p = identity_problem(email)
                if p:
                    print(f"leak-scan: {'BLOCK' if p[0] else 'warn '} commit {sha} {who} <{email}> ({p[1]})", file=sys.stderr)
                    blocked += p[0]
    else:
        for block, text in check_identity(repo):
            print(f"leak-scan: {'BLOCK' if block else 'warn '} identity: {text}", file=sys.stderr)
            blocked += block
    for name, f in dict.fromkeys(env_hits):
        print(f"leak-scan: BLOCK local secret {name} is in {f}", file=sys.stderr)
        blocked += 1
    for x in F.items.values():
        block = x["severity"] == "high" or x["kind"] in BLOCK_KINDS
        print(f"leak-scan: {'BLOCK' if block else 'warn '} {x['kind']}: {mask(x['kind'], x['value'])}"
              f" in {x['first']['file']}{' (' + x['note'] + ')' if x['note'] else ''}", file=sys.stderr)
        blocked += block
    if blocked:
        print(f"leak-scan: {'range ' + rng + ' has findings' if rng else 'commit refused'}. Remove the value, allowlist a false positive in "
              ".leakscan-allow, or bypass once with git commit --no-verify.", file=sys.stderr)
        return 1
    return 0


def check_message(F, msg_file):
    """commit-msg hook: the message itself (Claude session links, keys, webmail, …)."""
    with open(msg_file, encoding="utf-8", errors="replace") as fh:
        for line in message_lines(fh.read()):
            sp.scan_text(F, line[:sp.MAX_LINE], dict(source="commit-message", file="commit message"))
    blocked = 0
    for x in F.items.values():
        block = x["severity"] == "high" or x["kind"] in BLOCK_KINDS
        print(f"leak-scan: {'BLOCK' if block else 'warn '} {x['kind']}: {mask(x['kind'], x['value'])}"
              f" in the commit message{' (' + x['note'] + ')' if x['note'] else ''}", file=sys.stderr)
        blocked += block
    if blocked:
        print("leak-scan: commit refused. Edit the message (e.g. drop the Claude-Session: line), or bypass "
              "once with git commit --no-verify.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
