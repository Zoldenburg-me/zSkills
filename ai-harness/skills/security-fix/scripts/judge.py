#!/usr/bin/env python3
"""judge.py: the deterministic part of the fix judge. Exit code is final.

  judge.py --run-dir RUN --row N --repo FIX_WORKTREE --work-dir SCRATCH
           [--expect-green-on-base] [--owner-approved-test-edit] [--timeout SECONDS]

The fixer chooses nothing here. The test command comes from RUN/fix-config.json
(env_setup, suite_cmd with {file}, link_dirs), the test files are the test files the
branch adds or changes, and the allowed source files are the ones the finding's record names.

Requires a clean worktree: the judge judges the committed HEAD, never a dirty tree.

1. Boundary (diff HEAD against merge-base(HEAD, base), renames off): fails on any deleted file,
   on an edited pre-existing test and on removed assertion lines, unless the owner approved
   the test edit (--owner-approved-test-edit). Source files outside the record are reported.
2. Base run: a detached worktree at the merge base, with the branch's test files copied in.
   Fix mode: it must FAIL on an assertion. Exit 124/126/127 (timeout, not executable, not
   found) or an import/syntax/type error is a harness failure, not a reproduction.
   --expect-green-on-base (rejection mode): it must PASS.
3. Head run: a detached worktree at HEAD. It must PASS.
"""
import argparse, json, os, re, shutil, signal, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fixqueue  # noqa: E402

ASSERTISH = re.compile(r"\b(assert|expect|equal|deepEqual|strictEqual|ok\(|throws|rejects|status\b)")
HARNESS_FAIL = re.compile(
    r"Cannot find module|ERR_MODULE_NOT_FOUND|SyntaxError|error TS\d+|is not exported|"
    r"ReferenceError: \w+ is not defined|TypeError: [\w.$]+ is not a (function|constructor)|"
    r"command not found|No such file or directory|EADDRINUSE")
HARNESS_EXITS = {124, 126, 127}


def is_test(f):
    return bool(re.search(r"(^|/)(test|tests|__tests__)/|[-_.]test\.|\.spec\.", f))


def sh(cmd, cwd, timeout):
    p = subprocess.Popen(["bash", "-c", cmd], cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, start_new_session=True)
    try:
        out, _ = p.communicate(timeout=timeout)
        return p.returncode, out[-4000:]
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        out, _ = p.communicate()
        return 124, f"timeout after {timeout}s\n" + (out or "")[-2000:]


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)


def worktree(repo, rev, work_dir, common, links, prefix):
    wt = tempfile.mkdtemp(prefix=prefix, dir=work_dir)
    os.rmdir(wt)
    add = git(repo, "worktree", "add", "--detach", wt, rev)
    if add.returncode:
        sys.exit("worktree add failed: " + add.stderr)
    for d in links:
        src = os.path.join(common, d)
        if os.path.exists(src) and not os.path.lexists(os.path.join(wt, d)):
            os.symlink(src, os.path.join(wt, d))
    return wt


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--run-dir", required=True)
    p.add_argument("--row", type=int, required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--work-dir", required=True)
    p.add_argument("--expect-green-on-base", action="store_true")
    p.add_argument("--owner-approved-test-edit", action="store_true")
    p.add_argument("--timeout", type=int, default=900)
    a = p.parse_args()
    repo = os.path.abspath(a.repo)
    cfg = fixqueue.config(a.run_dir)
    if not cfg.get("suite_cmd") or "{file}" not in cfg["suite_cmd"]:
        sys.exit("fix-config.json needs suite_cmd containing {file}")
    base = cfg.get("base", "origin/main")
    rows = fixqueue.read_rows(os.path.join(a.run_dir, fixqueue.PROGRESS))
    row = next((r for r in rows if r["#"] == str(a.row)), None)
    if not row:
        sys.exit(f"no row {a.row}")
    rec = {r["fingerprint"]: r for r in fixqueue.records(a.run_dir)}.get(row["Fingerprint"])
    allow = set(fixqueue.files_of(rec)) if rec else set()

    dirty = git(repo, "status", "--porcelain", "--untracked-files=normal").stdout.strip()
    if dirty:
        sys.exit("worktree is dirty; commit first (amend after a send-back). The judge judges HEAD:\n" + dirty)
    mb = git(repo, "merge-base", "HEAD", base).stdout.strip()
    if not mb:
        sys.exit(f"no merge base between HEAD and {base}")
    common = os.path.dirname(os.path.abspath(os.path.join(repo, git(repo, "rev-parse", "--git-common-dir").stdout.strip())))

    # 1. boundary
    status = [l.split("\t") for l in git(repo, "diff", "--no-renames", "--name-status", mb, "HEAD").stdout.splitlines() if l]
    deleted = [s[-1] for s in status if s[0].startswith("D")]
    added = {s[-1] for s in status if s[0].startswith("A")}
    changed = [s[-1] for s in status if not s[0].startswith("D")]
    tests = [f for f in changed if is_test(f)]
    if not tests:
        sys.exit("the branch adds or changes no test file")
    edited_existing = [f for f in tests if f not in added]
    removed_asserts = []
    for f in tests:
        for line in git(repo, "diff", mb, "HEAD", "--", f).stdout.splitlines():
            if line.startswith("-") and not line.startswith("---") and ASSERTISH.search(line):
                removed_asserts.append(f"{f}: {line[1:].strip()[:160]}")
    outside = [f for f in changed if not is_test(f) and not any(f == x or f.endswith("/" + x) or x.endswith("/" + f) for x in allow)]
    # an edited existing test is normal when the new case goes into the suite the plan names;
    # what is not normal is losing assertions from it
    weakened = bool(removed_asserts) and not a.owner_approved_test_edit

    env = cfg.get("env_setup", "").strip()
    cmd = " && ".join(([env] if env else []) + [cfg["suite_cmd"].replace("{file}", t) for t in tests])
    links = cfg.get("link_dirs", [])
    os.makedirs(a.work_dir, exist_ok=True)

    # 2. base run
    wt = worktree(repo, mb, a.work_dir, common, links, "judge-base-")
    try:
        for t in tests:
            dst = os.path.join(wt, t)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(os.path.join(repo, t), dst)
        base_code, base_tail = sh(cmd, wt, a.timeout)
    finally:
        git(repo, "worktree", "remove", "--force", wt)
    harness = base_code in HARNESS_EXITS or bool(base_code and HARNESS_FAIL.search(base_tail))

    # 3. head run
    wt = worktree(repo, "HEAD", a.work_dir, common, links, "judge-head-")
    try:
        head_code, head_tail = sh(cmd, wt, a.timeout)
    finally:
        git(repo, "worktree", "remove", "--force", wt)

    if a.expect_green_on_base:
        base_ok = base_code == 0
    else:
        base_ok = base_code != 0 and not harness
    ok = base_ok and head_code == 0 and not deleted and not weakened
    verdict = {
        "mode": "rejection" if a.expect_green_on_base else "fix",
        "row": a.row, "fingerprint": row["Fingerprint"], "head": git(repo, "rev-parse", "HEAD").stdout.strip()[:12],
        "merge_base": mb[:12], "command": cmd, "tests": tests,
        "base": {"exit": base_code, "as_required": base_ok, "harness_failure": harness, "tail": base_tail},
        "head": {"exit": head_code, "as_required": head_code == 0, "tail": head_tail},
        "boundary": {"deleted": deleted, "edited_existing_tests": edited_existing,
                     "removed_assertion_lines": removed_asserts[:40], "weakened_fails": weakened,
                     "outside_record": outside},
        "pass": ok,
    }
    print(json.dumps(verdict, indent=1))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
