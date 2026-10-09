#!/usr/bin/env python3
"""fixqueue.py: the fix queue for one security-audit run (FIX-PROGRESS.md).

The table is the state machine. Code moves rows; prose never does.

  build   <run-dir> [--order FILE] [--dry-run]   create the queue, append new fingerprints, mark
                                                 todo rows whose blockers need the owner's decision
  refresh <run-dir> --repo PATH                  pr-open -> fixed when the recorded head is on <base>
  next    <run-dir> --repo PATH [--stale-hours H]
                                                 JSON: first todo row, its record, files, overlaps,
                                                 rows waiting on the owner, stale in-progress rows
  set     <run-dir> N STATUS --expect STATUS [--branch S] [--sha SHA] [--pr URL] [--note S] [--human]

Statuses (loop-written): todo, in-progress, pr-open, reject-proposed, blocked, needs-decision.
Statuses (owner-written): fixed, rejected. Allowed moves are in TRANSITIONS; anything else, and any
move into or out of fixed/rejected, needs --human (pass it only when the owner said so in chat).
`refresh` writes fixed only when the PR's head commit is on the base branch: the owner's merge.
Nothing here reorders rows or deletes one. A row line that does not parse is an error, not a skip.
"""
import argparse, datetime, fcntl, json, os, re, subprocess, sys

PROGRESS = "FIX-PROGRESS.md"
CONFIG = "fix-config.json"
COLS = ["#", "Status", "Fingerprint", "Title", "Branch / PR", "Notes"]
LOOP_STATUSES = {"todo", "in-progress", "pr-open", "reject-proposed", "blocked", "needs-decision"}
HUMAN_STATUSES = {"fixed", "rejected"}
TRANSITIONS = {
    "todo": {"in-progress"},
    "in-progress": {"pr-open", "reject-proposed", "blocked", "needs-decision"},
    "blocked": {"todo"},
    "needs-decision": {"todo"},
}
SEVERITY = ["critical", "high", "medium", "low", "informational"]
DECISION = re.compile(r"product intent|owner decision|owner must (confirm|decide)|owner-only|decision is the owner", re.I)
CLAIM = re.compile(r"claimed (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z)")

HEADER = """# Fix progress — {run}

One row per finding, worked strictly in order; never reorder or delete a row. Rows move only
through `scripts/fixqueue.py` of the security-fix skill.

- Loop-written: `todo` → `in-progress` → `pr-open` (PR open, awaiting the owner's merge),
  `reject-proposed` (the reproduction test showed no bug; awaiting the owner's sign-off),
  `blocked` (a fact outside source decides it; the note holds the question),
  `needs-decision` (product intent is the owner's call; the note holds the question).
- Owner-written: `fixed` (also set by `refresh` once the PR's head commit is on the base branch),
  `rejected`.
"""


def esc(s):
    return str(s).replace("|", "\\|").replace("\n", " ").strip()


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def read_rows(path):
    rows = []
    if not os.path.exists(path):
        return rows
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        s = line.strip()
        if not s.startswith("|") or s.startswith("| # ") or re.fullmatch(r"\|(-+\|)+", s):
            continue
        cells = [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s)[1:-1]]
        if len(cells) != len(COLS) or not cells[0].isdigit():
            sys.exit(f"{path}:{n}: table row does not parse; fix it by hand before running fixqueue.py:\n{s[:200]}")
        row = dict(zip(COLS, cells))
        row["Fingerprint"] = row["Fingerprint"].strip("`")
        rows.append(row)
    nums = [int(r["#"]) for r in rows]
    if nums != list(range(1, len(rows) + 1)):
        sys.exit(f"{path}: row numbers are not 1..{len(rows)} in order: {nums}")
    return rows


def render(run, rows):
    out = [HEADER.format(run=run), "| " + " | ".join(COLS) + " |", "|" + "---|" * len(COLS)]
    for r in rows:
        cells = [r["#"], r["Status"], f"`{r['Fingerprint']}`", r["Title"], r["Branch / PR"], r["Notes"]]
        out.append("| " + " | ".join(esc(c) for c in cells) + " |")
    return "\n".join(out) + "\n"


def write_rows(run_dir, rows):
    path = os.path.join(run_dir, PROGRESS)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(render(os.path.basename(os.path.normpath(run_dir)), rows))
    os.replace(tmp, path)


def locked(run_dir):
    f = open(os.path.join(run_dir, ".fix-progress.lock"), "w")
    fcntl.flock(f, fcntl.LOCK_EX)
    return f


def records(run_dir):
    return json.load(open(os.path.join(run_dir, "findings.json"), encoding="utf-8"))


def ordered(recs, order_file):
    """Confirmed first, by severity (unknown severity last); then needs_validation in the order
    of the optional order file (fingerprints as JSON object keys or list items), then by
    fingerprint. Rejected records are not queued."""
    rank = {}
    if order_file and os.path.exists(order_file):
        rank = {fp: i for i, fp in enumerate(json.load(open(order_file, encoding="utf-8")))}
    sev = lambda r: (r.get("severity") or {}).get("overall_severity")
    conf = sorted((r for r in recs if r["verdict"] == "confirmed"),
                  key=lambda r: (SEVERITY.index(sev(r)) if sev(r) in SEVERITY else len(SEVERITY), r["fingerprint"]))
    nv = sorted((r for r in recs if r["verdict"] == "needs_validation"),
                key=lambda r: (rank.get(r["fingerprint"], len(rank)), r["fingerprint"]))
    return conf + nv


def decision_note(r):
    hits = [b for b in r.get("blockers", []) if DECISION.search(b)]
    return ("needs-decision: " + hits[0][:220]) if hits else ""


def files_of(r):
    seen = []
    for t in (r or {}).get("trace", []) + (r or {}).get("evidence", []):
        f = t.get("file")
        if f and f not in seen:
            seen.append(f)
    return seen


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)


def config(run_dir):
    p = os.path.join(run_dir, CONFIG)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


# The Branch / PR cell is written only by `set`: "`<branch>` · sha:<sha> · <PR URL>"
def branch_of(cell):
    m = re.search(r"`([^`]+)`", cell or "")
    return m.group(1) if m else None


def sha_of(cell):
    m = re.search(r"\bsha:([0-9a-f]{7,40})\b", cell or "")
    return m.group(1) if m else None


def branch_cell(branch, sha, pr):
    return " · ".join(x for x in [f"`{branch}`" if branch else "", f"sha:{sha}" if sha else "", pr or ""] if x)


# ---------------------------------------------------------------- commands

def cmd_build(a):
    run = os.path.normpath(a.run_dir)
    order = a.order or os.path.join(run, "x-priority.json")
    recs = ordered(records(run), order)
    by_fp = {r["fingerprint"]: r for r in recs}
    with locked(run):
        rows = read_rows(os.path.join(run, PROGRESS))
        known = {r["Fingerprint"] for r in rows}
        added, marked = [], []
        for row in rows:  # front-load decisions on rows queued before this check existed
            note = decision_note(by_fp.get(row["Fingerprint"], {}))
            if row["Status"] == "todo" and not row["Notes"] and note:
                row["Status"], row["Notes"] = "needs-decision", note
                marked.append(row["#"])
        for r in recs:
            if r["fingerprint"] in known:
                continue
            note = decision_note(r)
            rows.append({"#": str(len(rows) + 1), "Status": "needs-decision" if note else "todo",
                         "Fingerprint": r["fingerprint"], "Title": r["title"], "Branch / PR": "", "Notes": note})
            added.append(r["fingerprint"])
        gone = [r["Fingerprint"] for r in rows if r["Fingerprint"] not in by_fp]
        if a.dry_run:
            sys.stdout.write(render(os.path.basename(run), rows))
        else:
            write_rows(run, rows)
    print(json.dumps({"rows": len(rows), "added": added, "marked_needs_decision": marked, "not_in_findings": gone,
                      "needs_decision": [r["#"] for r in rows if r["Status"] == "needs-decision"]}, indent=1),
          file=sys.stderr)


def merged(repo, base, row):
    sha = sha_of(row["Branch / PR"])
    if sha and git(repo, "cat-file", "-e", sha + "^{commit}").returncode == 0:
        if git(repo, "merge-base", "--is-ancestor", sha, base).returncode == 0:
            return sha
    # squash/rebase merges: the base log names the branch or the fingerprint
    for needle in filter(None, [branch_of(row["Branch / PR"]), row["Fingerprint"]]):
        hit = git(repo, "log", base, "-n1", "--format=%h", "--fixed-strings", "--grep", needle).stdout.strip()
        if hit:
            return hit
    return None


def cmd_refresh(a):
    run = os.path.normpath(a.run_dir)
    base = config(run).get("base", "origin/main")
    git(a.repo, "fetch", "--quiet", "origin")
    flipped = []
    with locked(run):
        rows = read_rows(os.path.join(run, PROGRESS))
        for r in rows:
            if r["Status"] != "pr-open":
                continue
            hit = merged(a.repo, base, r)
            if hit:
                r["Status"] = "fixed"
                r["Notes"] = (r["Notes"] + f"; merged ({hit} on {base})").strip("; ")
                flipped.append(r["#"])
        write_rows(run, rows)
    print(json.dumps({"fixed": flipped}))


def cmd_next(a):
    run = os.path.normpath(a.run_dir)
    base = config(run).get("base", "origin/main")
    rows = read_rows(os.path.join(run, PROGRESS))
    by_fp = {r["fingerprint"]: r for r in records(run)}
    row = next((r for r in rows if r["Status"] == "todo"), None)
    waiting = [{"#": r["#"], "status": r["Status"], "note": r["Notes"]} for r in rows
               if r["Status"] in ("needs-decision", "blocked", "reject-proposed")]
    stale, cutoff = [], datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=a.stale_hours)
    for r in rows:
        if r["Status"] != "in-progress":
            continue
        m = CLAIM.search(r["Notes"])
        when = datetime.datetime.strptime(m.group(1), "%Y-%m-%dT%H:%MZ").replace(tzinfo=datetime.timezone.utc) if m else None
        if when is None or when < cutoff:
            stale.append({"#": r["#"], "claimed": m.group(1) if m else None})
    out = {"next": row, "waiting_on_owner": waiting, "stale_in_progress": stale}
    if row:
        rec = by_fp.get(row["Fingerprint"])
        files = files_of(rec)
        overlaps = []
        for r in rows:
            b = branch_of(r["Branch / PR"])
            if r["Status"] not in ("pr-open", "in-progress") or not b:
                continue
            changed = git(a.repo, "diff", "--name-only", f"{base}...origin/{b}").stdout.split()
            hit = sorted({c for c in changed for f in files if c == f or c.endswith("/" + f)})
            if hit:
                overlaps.append({"#": r["#"], "branch": b, "files": hit})
        out.update(record=rec, files=files, overlaps=overlaps)
    print(json.dumps(out, indent=1, ensure_ascii=False))


def cmd_set(a):
    run = os.path.normpath(a.run_dir)
    if a.status not in LOOP_STATUSES | HUMAN_STATUSES:
        sys.exit(f"unknown status {a.status}")
    with locked(run):
        rows = read_rows(os.path.join(run, PROGRESS))
        row = next((r for r in rows if r["#"] == str(a.n)), None)
        if not row:
            sys.exit(f"no row {a.n}")
        cur = row["Status"]
        if cur not in a.expect.split(","):
            sys.exit(f"row {a.n} is {cur}, expected {a.expect}; another session may own it")
        owner_move = a.status in HUMAN_STATUSES or cur in HUMAN_STATUSES or a.status not in TRANSITIONS.get(cur, set())
        if owner_move and not a.human:
            sys.exit(f"{cur} -> {a.status} is the owner's move; pass --human only when the owner said so in chat")
        row["Status"] = a.status
        if a.branch is not None or a.sha is not None or a.pr is not None:
            row["Branch / PR"] = branch_cell(a.branch or branch_of(row["Branch / PR"]),
                                             a.sha or sha_of(row["Branch / PR"]), a.pr)
        note = a.note
        if a.status == "in-progress":
            note = f"claimed {now()}" + (f"; {a.note}" if a.note else "")
        if note is not None:
            row["Notes"] = note
        write_rows(run, rows)
    print(json.dumps(row))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)
    b = s.add_parser("build"); b.add_argument("run_dir"); b.add_argument("--order"); b.add_argument("--dry-run", action="store_true")
    r = s.add_parser("refresh"); r.add_argument("run_dir"); r.add_argument("--repo", required=True)
    n = s.add_parser("next"); n.add_argument("run_dir"); n.add_argument("--repo", required=True)
    n.add_argument("--stale-hours", type=float, default=6)
    t = s.add_parser("set"); t.add_argument("run_dir"); t.add_argument("n", type=int); t.add_argument("status")
    t.add_argument("--expect", required=True); t.add_argument("--branch"); t.add_argument("--sha"); t.add_argument("--pr")
    t.add_argument("--note"); t.add_argument("--human", action="store_true")
    a = p.parse_args()
    {"build": cmd_build, "refresh": cmd_refresh, "next": cmd_next, "set": cmd_set}[a.cmd](a)


if __name__ == "__main__":
    main()
