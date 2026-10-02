#!/usr/bin/env python3
"""Look for the repo's OWN secret values (from .env-style files that are not
tracked) anywhere in history and in PR/issue text. This catches what pattern
scanners cannot: a custom token with no known shape, pasted somewhere odd
(e.g. prefilled into an HTML password field). A hit is the real value;
public config (addresses, hostnames, numbers, *_URL/_ADDRESS/...) is skipped.

Values stay in memory; output names the variable, commits and files only.

Usage: env_crosscheck.py REPO OUT.jsonl [--pr-text DIR]
"""
import argparse, glob, json, os, re, subprocess

# names that are configuration, not secrets
NOT_SECRET = ("_URL", "_URI", "_CHAIN", "_ENV", "_PORT", "_HOST", "_NETWORK", "_ID", "_MODE",
              "_ADDRESS", "_DOMAIN", "_USDC", "_EURE", "_TOKEN_ADDRESS", "_CONTRACT")
PUBLIC_VALUE = re.compile(r"^(0x[0-9a-fA-F]{40}|[a-z0-9-]+(\.[a-z0-9-]+)+|\d+)$")  # address, hostname, number


def env_files(repo):
    tracked = set(subprocess.run(["git", "-C", repo, "ls-files"], capture_output=True, text=True).stdout.split())
    for p in sorted(set(glob.glob(os.path.join(repo, ".env*")) + glob.glob(os.path.join(repo, "**/.env*"), recursive=True))):
        rel = os.path.relpath(p, repo)
        if os.path.isfile(p) and rel not in tracked and "node_modules" not in rel and not rel.endswith((".example", ".sample", ".template")):
            yield rel, p


def parse(path):
    for line in open(path, errors="replace"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.replace("export ", "").strip()
        v = v.strip().strip('"').strip("'")
        yield k, v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("out")
    ap.add_argument("--pr-text")
    a = ap.parse_args()
    found = []
    for rel, path in env_files(a.repo):
        for k, v in parse(path):
            # client ids are checked too (they can be private), only plain config is skipped
            if len(v) < 12 or v.lower() in ("true", "false") or v.startswith(("http://", "https://")) or PUBLIC_VALUE.match(v) or \
                    (k.endswith(NOT_SECRET) and not k.endswith("CLIENT_ID")):
                continue
            commits = subprocess.run(["git", "-C", a.repo, "log", "--all", "-S" + v, "--format=%H %ad", "--date=short"],
                                     capture_output=True, text=True).stdout.split("\n")
            commits = [c for c in commits if c]
            files = []
            for c in commits[:5]:
                show = subprocess.run(["git", "-C", a.repo, "show", c.split()[0]], capture_output=True, text=True).stdout
                f = None
                for line in show.splitlines():
                    if line.startswith("+++ "):
                        f = line[6:]
                    elif v in line and f and f not in files:
                        files.append(f)
            prs = []
            if a.pr_text and os.path.isdir(a.pr_text):
                prs = [n for n in sorted(os.listdir(a.pr_text))
                       if v in open(os.path.join(a.pr_text, n), errors="replace").read()]
            if commits or prs:
                found.append(dict(kind="env-value", severity="high", value=f"{k} (from {rel})", env_key=k,
                                  commits=[c.split()[0] for c in commits], first_date=commits[-1].split()[1] if commits else "",
                                  files=files, pr_text=prs,
                                  note="the CURRENT value of a local secret appears in public history: rotate it"))
    with open(a.out, "w") as fh:
        for f in found:
            fh.write(json.dumps(f) + "\n")
    os.chmod(a.out, 0o600)
    print(f"env cross-check: {len(found)} local secret values found in history/PR text -> {a.out}")
    for f in found:
        print(f"  {f['env_key']}: commits {' '.join(c[:9] for c in f['commits'][:4])} files {', '.join(f['files'][:3])} pr {', '.join(f['pr_text'][:3])}")


if __name__ == "__main__":
    main()
