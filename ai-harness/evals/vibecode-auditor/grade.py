#!/usr/bin/env python3
"""Grade vibecode-auditor reports against the answer key.

usage: grade.py answer-key.json seeded-report.md clean-report.md
       grade.py --self-test
Recall = planted flaws found in the seeded report. False positives = Critical/High
findings in the clean report, which has no known flaws.
"""
import json, re, sys

LEVELS = ["Low", "Medium", "High", "Critical"]

def findings(report):
    """Rows of the findings table: (severity, lowercased row text)."""
    rows = []
    for line in report.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip().strip("*").strip() for c in line.strip().strip("|").split("|")]
        sev = next((c.capitalize() for c in cells if c.capitalize() in LEVELS), None)
        if sev:
            rows.append((sev, line.lower()))
    return rows

def verdict_check(report):
    """Does the stated verdict follow the agent's rule from the severities it reported?"""
    sevs = {s for s, _ in findings(report)}
    want = "no" if "Critical" in sevs else "after fixing" if "High" in sevs else "yes"
    m = re.search(r"safe to launch:\s*(.+)", report, re.I)
    said = m.group(1).strip().lower() if m else ""
    return {"expected": want, "stated": said[:80], "ok": said.startswith(want)}

def matches(flaw, text):
    return all(any(term in text for term in group) for group in flaw["match"])

def grade(key, seeded, clean):
    rows = findings(seeded)
    found, used = {}, set()
    for flaw in key["flaws"]:
        hits = [i for i, (_, text) in enumerate(rows) if matches(flaw, text)]
        # Prefer a row no other flaw has claimed; one row may still cover two flaws.
        i = next((h for h in hits if h not in used), hits[0] if hits else None)
        if i is not None:
            found[flaw["id"]] = rows[i][0]
            used.add(i)
    flaws = key["flaws"]
    by_level = {lvl: [f for f in flaws if f["severity"] == lvl] for lvl in LEVELS}
    agree = sum(1 for f in flaws if f["id"] in found
                and abs(LEVELS.index(found[f["id"]]) - LEVELS.index(f["severity"])) <= 1)
    clean_rows = findings(clean)
    return {
        "recall": f"{len(found)}/{len(flaws)}",
        "recall_by_level": {lvl: f"{sum(f['id'] in found for f in fs)}/{len(fs)}"
                            for lvl, fs in by_level.items() if fs},
        "severity_agrees_within_one": f"{agree}/{len(found)}",
        "missed": [f"{f['id']} ({f['severity']}) {f['title']}" for f in flaws if f["id"] not in found],
        "seeded_extra_findings": [t[:160] for i, (_, t) in enumerate(rows) if i not in used],
        "clean_false_positives_critical_high": [f"{s}: {t[:160]}" for s, t in clean_rows if s in ("Critical", "High")],
        "clean_findings_medium_low": len([1 for s, _ in clean_rows if s in ("Medium", "Low")]),
        "verdict_seeded": verdict_check(seeded),
        "verdict_clean": verdict_check(clean),
    }

def self_test():
    key = {"flaws": [
        {"id": "A", "severity": "Critical", "title": "a", "match": [["webhook"], ["signature"]]},
        {"id": "B", "severity": "Low", "title": "b", "match": [["lovable"]]},
    ]}
    seeded = ("| # | Severity | Finding | Where |\n|---|---|---|---|\n"
              "| 1 | **High** | Webhook lacks signature check | app/api/stripe/webhook/route.ts:5 |\n"
              "| 2 | Medium | Something else | x.ts:1 |\n")
    clean = "Safe to launch: no\n| 1 | Critical | bad | y.ts |\n| 2 | Low | meh | z.ts |\n"
    r = grade(key, seeded, clean)
    assert r["recall"] == "1/2" and r["missed"][0].startswith("B"), r
    assert r["severity_agrees_within_one"] == "1/1", r
    assert len(r["seeded_extra_findings"]) == 1, r
    assert len(r["clean_false_positives_critical_high"]) == 1 and r["clean_findings_medium_low"] == 1, r
    assert r["verdict_clean"]["ok"] and not r["verdict_seeded"]["ok"], r
    assert verdict_check("Safe to launch: yes\n| 1 | Low | x | y |")["ok"]
    assert not verdict_check("Safe to launch: no\n| 1 | Medium | x | y |")["ok"]
    print("self-test ok")

if __name__ == "__main__":
    if sys.argv[1:] == ["--self-test"]:
        self_test()
    else:
        key, seeded, clean = sys.argv[1:4]
        print(json.dumps(grade(json.load(open(key)), open(seeded).read(), open(clean).read()), indent=2))
