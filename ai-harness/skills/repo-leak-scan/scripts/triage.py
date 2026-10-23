#!/usr/bin/env python3
"""Merge scanner output into one candidate list, score each candidate with a
TypeSafe Noul ("should this be removed from the public history?"), and sort
into three buckets by user cutoffs.

Subcommands
  sanitize-trufflehog  < raw.jsonl > clean.jsonl
      Drops the raw secret from trufflehog JSON lines, keeps a masked form.
  sanitize-gitleaks REPORT.json
      Drops public addresses and hardhat keys, masks the rest, in place.
  merge WORKDIR
      Reads gitleaks*.json, trufflehog*.jsonl, private.jsonl from WORKDIR and
      writes WORKDIR/candidates.jsonl (one normalised candidate per line).
  score WORKDIR [--batch 20]
      Scores candidates via the TypeSafe HTTP API ($TYPESAFE_API_KEY), writing
      WORKDIR/scores.json {id: p}. Without a key it writes
      WORKDIR/to_score.jsonl (id, statement, evidence, yes_means, no_means)
      for scoring through the system1 fast_verify MCP tool instead.
  report WORKDIR [--sure 0.85] [--floor 0.2]
      Buckets candidates with WORKDIR/scores.json and writes WORKDIR/report.md
      and WORKDIR/review.jsonl (the band Claude must judge).

Nothing raw leaves this machine: secret values and IBANs are masked before
they are put into a TypeSafe request or a report.
"""
import argparse, glob, json, os, re, sys, time, urllib.request, urllib.error

TYPESAFE_URL = os.environ.get("TYPESAFE_BASE_URL", "https://api.typesafe.ai").rstrip("/") + "/v1/systemone"
MODEL = os.environ.get("TYPESAFE_DEFAULT_MODEL", "jev-latest")


def mask(s, keep_start=4, keep_end=2):
    s = s or ""
    if len(s) <= keep_start + keep_end + 2:
        return s[:2] + "…" if len(s) > 2 else "…"
    return f"{s[:keep_start]}…{s[-keep_end:]} ({len(s)} chars)"


# ------------------------------------------------------------ sanitize

def sanitize_trufflehog():
    for line in sys.stdin:
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue
        raw = d.get("Raw") or d.get("RawV2") or ""
        d["masked"] = mask(raw)
        for k in ("Raw", "RawV2", "Redacted"):
            d.pop(k, None)
        print(json.dumps(d))


def sanitize_gitleaks(path):
    """Drop public values gitleaks' generic rule mistakes for keys, then mask
    every secret in place. gitleaks runs without --redact so this can see the
    value; the file is rewritten before anything else reads it."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from scan_private import HARDHAT_KEYS
    try:
        rows = json.load(open(path)) or []
    except (ValueError, OSError):
        rows = []
    keep, dropped = [], 0
    for d in rows:
        sec = d.get("Secret", "")
        low = sec.lower().removeprefix("0x")
        if re.fullmatch(r"0x[0-9a-fA-F]{40}", sec) or low in HARDHAT_KEYS:
            dropped += 1  # a public contract/wallet address, or a hardhat dev key
            continue
        m = mask(sec)
        d["Secret"], d["Match"] = m, (d.get("Match") or "").replace(sec, m)
        d.pop("Line", None)
        keep.append(d)
    json.dump(keep, open(path, "w"))
    os.chmod(path, 0o600)
    print(f"gitleaks {os.path.basename(path)}: {len(keep)} kept, {dropped} public addresses/dev keys dropped",
          file=sys.stderr)


# ------------------------------------------------------------ merge

def merge(workdir):
    cands = {}

    def put(c):
        key = c.pop("_key")
        if key in cands:  # same secret again (other tool, other commit): merge
            old = cands[key]
            if c.get("commit") and c["commit"] not in old.setdefault("commits", []):
                old["commits"].append(c["commit"])
            old["detectors"] = sorted(set(old["detectors"]) | set(c["detectors"]))
            if c.get("verified") is not None:
                old["verified"] = c["verified"]
                old["verify_note"] = c.get("verify_note", "")
            return
        cands[key] = c

    for path in glob.glob(os.path.join(workdir, "trufflehog*.jsonl")):
        for line in open(path):
            d = json.loads(line)
            meta = d.get("SourceMetadata", {}).get("Data", {})
            g = meta.get("Git") or meta.get("Filesystem") or {}
            f = g.get("file", "")
            f = os.path.basename(f) if "/pr-text/" in f else f
            commit = (g.get("commit") or "")[:12]
            ve = d.get("VerificationError") or ""
            put(dict(_key=("secret", f, d.get("masked")), commits=[commit] if commit else [], kind="secret", detectors=[d.get("DetectorName", "?")],
                     value=d.get("masked", "…"), file=f, commit=commit, line=g.get("line"),
                     author=g.get("email", ""), date=(g.get("timestamp") or "")[:10],
                     verified=True if d.get("Verified") else (None if ve else False),
                     verify_note=ve[:160], snippet="", source="pr-text" if "-pr." in path else "diff"))
    for path in glob.glob(os.path.join(workdir, "gitleaks*.json")):
        try:
            rows = json.load(open(path))
        except ValueError:
            rows = []
        for d in rows or []:
            f = d.get("File", "")
            f = os.path.basename(f) if "/pr-text/" in f else f
            commit = (d.get("Commit") or "")[:12]
            put(dict(_key=("secret", f, d.get("Secret", "")), commits=[commit] if commit else [], kind="secret", detectors=["gitleaks:" + d.get("RuleID", "?")],
                     value=d.get("Secret", ""), file=f,  # masked by sanitize-gitleaks commit=commit, line=d.get("StartLine"),
                     author=d.get("Email", ""), date=(d.get("Date") or "")[:10], verified=None,
                     verify_note="not checked (no trufflehog detector)",
                     snippet=(d.get("Match") or "")[:200], source="pr-text" if "-pr." in path else "diff"))
    envc = os.path.join(workdir, "envcheck.jsonl")
    if os.path.exists(envc):
        for line in open(envc):
            d = json.loads(line)
            put(dict(_key=("env-value", d["env_key"]), kind="env-value", detectors=["env-crosscheck"],
                     value=d["value"], file=", ".join(d["files"][:3]) or ", ".join(d["pr_text"][:3]),
                     commit=(d["commits"] or [""])[-1], commits=d["commits"], verified=True,
                     verify_note=d["note"], snippet=f"first committed {d['first_date']}; PR text: {len(d['pr_text'])}",
                     source="diff" if d["commits"] else "pr-text"))
    priv = os.path.join(workdir, "private.jsonl")
    if os.path.exists(priv):
        for line in open(priv):
            d = json.loads(line)
            if d["kind"] == "disclosure":
                w = d["where"]
                put(dict(_key=("disclosure", w.get("commit"), w.get("file")), kind="disclosure",
                         detectors=["keywords:" + ",".join(d["keywords"][:6])], value="",
                         file=w.get("file", ""), commit=w.get("commit", ""), source=w.get("source"),
                         snippet=d["text"][:1500]))
                continue
            w = d["first"]
            val = d["value"]
            shown = mask(val, 4, 4) if d["kind"] in ("iban", "eth-private-key", "mnemonic", "prefilled-password") else val
            snip = d["snippet"].replace(val, shown) if shown != val else d["snippet"]
            put(dict(_key=(d["kind"], val, w.get("file") or w.get("source")), kind=d["kind"],
                     all_commits=d.get("all_commits") or d.get("commits"), detectors=["regex"], value=shown, file=w.get("file", ""), commit=w.get("commit", ""),
                     source=w.get("source"), regex_severity=d["severity"], note=d.get("note", ""),
                     in_head=d.get("in_head"), occurrences=d["count"], snippet=snip))
    def reach(name):
        fp = os.path.join(workdir, name)
        return {l[:12] for l in open(fp)} if os.path.exists(fp) else None
    branches, prrefs = reach("reach-branches.txt"), reach("reach-prrefs.txt")
    for c in cands.values():
        cs = {x[:12] for x in (c.get("all_commits") or c.get("commits") or [c.get("commit")]) if x}
        if c.get("source") == "pr-text" or c.get("file", "").startswith(("pr-", "issue-")):
            c["exposure"] = "public (PR/issue text)"
        elif not cs or branches is None:
            c["exposure"] = "unknown"
        elif cs & branches:
            c["exposure"] = f"public branch ({len(cs & branches)} commits)"
        elif prrefs and cs & prrefs:
            c["exposure"] = "PR refs only (needs GitHub Support purge)"
        else:
            c["exposure"] = "local only (not on GitHub)"
        c.pop("all_commits", None)
    out = os.path.join(workdir, "candidates.jsonl")
    with open(out, "w") as fh:
        for i, c in enumerate(cands.values()):
            c["id"] = f"c{i}"
            fh.write(json.dumps(c) + "\n")
    os.chmod(out, 0o600)
    print(f"{len(cands)} candidates -> {out}")


# ------------------------------------------------------------ score

Q_DATA = dict(
    statement="should be removed from this public repository's history because it exposes a real "
              "person's or company's private data or a usable credential",
    yes="Real: a personal email or phone number, a real bank account, a developer's home-directory "
        "path that names them, a real key, token or private key, or a personal webmail address in "
        "commit metadata.",
    no="Harmless: a test fixture, placeholder, documented example or generated dummy value (sequential "
       "or repeated digits such as 1234567 or 700000000 are placeholders); a public "
       "business contact meant to be published (security@, support@ on the project's own domain); "
       "a local-dev-only key such as a hardhat default account; or text that only names a variable.")
Q_DISCLOSURE = dict(
    statement="reveals a security weakness of this project that an attacker could still use, or a "
              "security decision that knowingly leaves a gap, in enough detail that it should not be public",
    yes="Describes an unfixed, accepted or partly fixed weakness, a bypass, or how to attack the live "
        "system: which component, which input or precondition, and what an attacker gains.",
    no="Not about security; generic hardening; or a fixed bug described at the level of an ordinary "
       "changelog line without a recipe for attacking anything still running.")


def evidence_for(c, repo):
    ev = {"repository": f"{repo} (public on GitHub)", "kind": c["kind"],
          "where": c.get("source"), "file": c.get("file"), "detector": c.get("detectors")}
    if c["kind"] == "disclosure":
        ev["text"] = c["snippet"]
    else:
        ev.update(value=c.get("value"), line=c.get("snippet"), note=c.get("note") or c.get("verify_note"),
                  still_in_current_tree=c.get("in_head"), occurrences=c.get("occurrences"))
    return {k: v for k, v in ev.items() if v not in (None, "", [])}


def question_for(c):
    return Q_DISCLOSURE if c["kind"] == "disclosure" else Q_DATA


def load(workdir):
    return [json.loads(l) for l in open(os.path.join(workdir, "candidates.jsonl"))]


def post(body, key):
    data = json.dumps(body).encode()
    for attempt in range(6):
        req = urllib.request.Request(TYPESAFE_URL, data=data, headers={
            "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 529, 500, 502, 503) and attempt < 5:
                time.sleep(2 ** attempt)
                continue
            sys.exit(f"TypeSafe {e.code}: {e.read().decode(errors='replace')[:400]}")


def score(workdir, batch, repo):
    cands = [c for c in load(workdir) if c.get("verified") is not True]
    scores_path = os.path.join(workdir, "scores.json")
    scores = json.load(open(scores_path)) if os.path.exists(scores_path) else {}
    todo = [c for c in cands if c["id"] not in scores]
    key = os.environ.get("TYPESAFE_API_KEY")
    if not key:
        out = os.path.join(workdir, "to_score.jsonl")
        with open(out, "w") as fh:
            for c in todo:
                q = question_for(c)
                fh.write(json.dumps(dict(id=c["id"], statement="This finding " + q["statement"] + ".",
                                         evidence=evidence_for(c, repo), yes_means=q["yes"],
                                         no_means=q["no"])) + "\n")
        print(f"no TYPESAFE_API_KEY: {len(todo)} items -> {out} (score with fast_verify, "
              f"write {{id: probability}} to {scores_path})")
        return
    tokens, answered_by = 0, "none (nothing to score)"
    for i in range(0, len(todo), batch):
        chunk = todo[i:i + batch]
        state = {"findings": {c["id"]: evidence_for(c, repo) for c in chunk}}
        questions = {}
        for c in chunk:
            q = question_for(c)
            questions[c["id"]] = {"type": "noul",
                                  "instructions": f"Does `findings.{c['id']}` contain something that {q['statement']}?",
                                  "criteria": {"true": q["yes"], "false": q["no"]}}
        r = post({"state": state, "model": MODEL, "questions": questions}, key)
        answered_by = r.get("model", "?")
        for qid, ans in r["answers"].items():
            scores[qid] = ans["noul"]
        tokens += r.get("usage", {}).get("input_tokens", 0)
        json.dump(scores, open(scores_path, "w"))
        print(f"  scored {min(i + batch, len(todo))}/{len(todo)}", file=sys.stderr)
    print(f"scored {len(todo)} candidates ({tokens} input tokens, answered by TypeSafe model {answered_by}) -> {scores_path}")


# ------------------------------------------------------------ report

def where(c):
    w = c.get("file") or c.get("source") or ""
    if c.get("commit"):
        w += f" @ {c['commit']}"
    if c.get("line"):
        w += f":{c['line']}"
    return w.replace("|", "\\|")


def row(c):
    v = (c.get("value") or c["snippet"][:80]).replace("|", "\\|").replace("\n", " ")
    extra = ""
    if c["kind"] == "env-value":
        extra = "**CURRENT .env value**"
    elif c["kind"] == "secret":
        extra = {True: "**LIVE**", False: "dead"}.get(c.get("verified"), "unverified")
    elif c.get("in_head") is not None:
        extra = "in HEAD" if c["in_head"] else "history only"
    p = "—" if c.get("p") is None else f"{c['p']:.2f}"
    return f"| {p} | {c['kind']} | `{v}` | {where(c)} | {c.get('exposure', '')} | {extra} |"


def report(workdir, sure, floor):
    cands = load(workdir)
    sp = os.path.join(workdir, "scores.json")
    scores = json.load(open(sp)) if os.path.exists(sp) else {}
    unscored = 0
    for c in cands:
        if c.get("verified") is True:
            c["p"] = 1.0
        elif c["id"] in scores:
            c["p"] = scores[c["id"]]
        else:
            c["p"] = None
            unscored += 1
    sure_l = [c for c in cands if c["p"] is not None and c["p"] >= sure]
    band = sorted([c for c in cands if c["p"] is not None and floor <= c["p"] < sure], key=lambda c: -c["p"])
    low = [c for c in cands if c["p"] is not None and c["p"] < floor]
    none = [c for c in cands if c["p"] is None]
    with open(os.path.join(workdir, "review.jsonl"), "w") as fh:
        for c in band + none:
            fh.write(json.dumps(c) + "\n")
    hdr = "| score | kind | value | where | exposure | status |\n|---|---|---|---|---|---|"
    rank = lambda c: (0 if c.get("exposure", "").startswith("public") else 1 if c.get("exposure", "").startswith("PR") else 2)
    md = [f"# Leak scan report\n",
          f"Cutoffs: **≥ {sure}** confirmed · **{floor}–{sure}** Claude review · **< {floor}** dismissed\n",
          f"{len(cands)} candidates: {len(sure_l)} confirmed, {len(band)} to review, "
          f"{len(low)} dismissed, {unscored} unscored.\n",
          f"## Confirmed: not meant to be public ({len(sure_l)})\n",
          "Sorted by exposure: what a stranger can download today first.\n", hdr,
          *map(row, sorted(sure_l, key=lambda c: (rank(c), -c["p"]))),
          f"\n## Claude review ({len(band) + len(none)})\n",
          "<!-- Claude: replace this comment with a verdict table (leak / fine + one-line reason). -->\n",
          hdr, *map(row, band + none),
          f"\n## Dismissed ({len(low)})\n",
          "Kept in candidates.jsonl with their scores; counts by kind: " +
          ", ".join(f"{k} {sum(1 for c in low if c['kind'] == k)}" for k in sorted({c['kind'] for c in low}))]
    out = os.path.join(workdir, "report.md")
    open(out, "w").write("\n".join(md) + "\n")
    os.chmod(out, 0o600)
    print(f"confirmed {len(sure_l)}, review {len(band) + len(none)}, dismissed {len(low)} -> {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["sanitize-trufflehog", "sanitize-gitleaks", "merge", "score", "report"])
    ap.add_argument("workdir", nargs="?")
    ap.add_argument("--batch", type=int, default=20)
    ap.add_argument("--repo", default="this repository")
    ap.add_argument("--sure", type=float, default=0.85)
    ap.add_argument("--floor", type=float, default=0.2)
    a = ap.parse_args()
    if a.cmd == "sanitize-trufflehog":
        sanitize_trufflehog()
    elif a.cmd == "sanitize-gitleaks":
        sanitize_gitleaks(a.workdir)
    elif a.cmd == "merge":
        merge(a.workdir)
    elif a.cmd == "score":
        score(a.workdir, a.batch, a.repo)
    else:
        report(a.workdir, a.sure, a.floor)


if __name__ == "__main__":
    main()
