#!/usr/bin/env python3
"""Self-check for precommit.py: python3 -I scripts/test_precommit.py (exits non-zero on failure)."""
import os, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import precommit as pc  # noqa: E402

LINE = "home = " + os.path.join("/", "Users", "alice", "notes")  # built at runtime so this file has no home path


def staged_repo(*config):
    repo = tempfile.mkdtemp()
    git = lambda *a: subprocess.run(["git", "-C", repo, *a], check=True, capture_output=True)
    git("init", "-q")
    for kv in config:
        git("config", *kv.split("=", 1))
    for name in ("plain.txt", "with space.txt", "naïve.txt"):
        with open(os.path.join(repo, name), "w") as fh:
            fh.write(LINE + "\n")
    git("add", ".")
    return repo


# Added lines are found whatever diff prefix or path quoting the user's git config sets.
for config in ([], ["diff.mnemonicPrefix=true"], ["diff.noprefix=true"], ["core.quotepath=on"]):
    got = sorted(pc.staged_added_lines(staged_repo(*config)))
    want = [(n, LINE) for n in ("naïve.txt", "plain.txt", "with space.txt")]
    assert got == want, (config, got)

# A gitleaks crash or config error (exit > 1) blocks instead of passing as clean.
bindir = tempfile.mkdtemp()
for code in (1, 2, 126):
    exe = os.path.join(bindir, "gitleaks")
    with open(exe, "w") as fh:
        fh.write(f"#!/bin/sh\nexit {code}\n")
    os.chmod(exe, 0o755)
    pc.BIN = bindir
    assert pc.run_gitleaks(bindir) == 1, code
with open(exe, "w") as fh:
    fh.write("#!/bin/sh\nexit 0\n")
assert pc.run_gitleaks(bindir) == 0

print("precommit self-check ok")
