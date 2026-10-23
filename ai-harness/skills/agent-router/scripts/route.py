#!/usr/bin/env python3
"""Pick the subagents worth launching now: build a catalog of every agent the
session can reach, shortlist it with BM25 against the task and the repo, then
score the shortlist with TypeSafe (Jev) and bucket it.

The agent counterpart of skill-router. Repo context, BM25, the TypeSafe client
and the frontmatter parser are imported from skill-router's route.py, so the
two routers rank the same way.

Subcommands
  run --task TEXT [--listing FILE|-] [--workdir DIR] [--shortlist 30]
      [--sure 0.6] [--floor 0.25] [--top 3] [--no-score] [--change|--no-change]
      Writes WORKDIR/context.json, catalog.json, shortlist.json, then scores
      via the TypeSafe HTTP API ($TYPESAFE_API_KEY, or the repo's .env) into
      scores.json and prints the report. Without a key it writes
      to_score.jsonl for the system1 fast_verify MCP tool instead.
  report [--workdir DIR] [--sure 0.6] [--floor 0.25] [--top 3]
      Prints the report from an existing scores.json (after MCP scoring).

Only the task text, file-extension counts, dependency names, changed file
paths, recent commit subjects and agent names/descriptions go to TypeSafe.
"""
import argparse, json, os, re, sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

HOME = os.path.expanduser("~")
# sibling install: works in ~/.claude/skills and inside a plugin
SKILL_ROUTER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "skill-router", "scripts")
sys.path.insert(0, SKILL_ROUTER)
try:
    import route as sr   # skill-router's route.py
except ImportError:
    sys.exit(f"agent-router needs skill-router's route.py in {SKILL_ROUTER}")

AGENTS_DIR = os.path.join(HOME, ".claude", "agents")
PLUGIN_CACHE = os.path.join(HOME, ".claude", "plugins", "cache")
LIBRARY_DIR = os.environ.get("AGENT_ROUTER_LIBRARY",
                             os.path.join(HOME, "Documents", "everything-claude-code", "agents"))
BATCH, THREADS = 10, 4


def env_list(var, default):
    return [n.strip() for n in os.environ.get(var, default).split(",") if n.strip()]


# Launched on every code change whatever Jev says: a missed review costs more than a needless one.
ALWAYS_ON_CHANGE = env_list("AGENT_ROUTER_ALWAYS", "code-reviewer,security-reviewer")
# Generic fallbacks and harness utilities: never candidates, they fit everything and say nothing.
NEVER = set(env_list("AGENT_ROUTER_NEVER", "claude,general-purpose,statusline-setup,Explore,Plan"))


# ------------------------------------------------------------ catalog

def add(cat, name, desc, source, how):
    if not name or name in NEVER or "DEPRECATED" in (desc or "")[:40]:
        return
    cur = cat.get(name)
    if cur is None:
        cat[name] = {"name": name, "description": desc or "", "source": source, "how": how}
    elif len(desc or "") > len(cur["description"]):
        cur["description"] = desc   # keep the first source's `how`, take the fuller text


def agent_files(root):
    if not os.path.isdir(root):
        return []
    return [os.path.join(root, f) for f in sorted(os.listdir(root)) if f.endswith(".md")]


def build_catalog(listing_path):
    cat = {}
    # 1. The session's own agent listing: authoritative for what Agent(subagent_type=...) accepts now.
    if listing_path:
        for line in (sys.stdin if listing_path == "-" else open(listing_path, encoding="utf-8")):
            m = re.match(r"^\s*-\s*([\w:.\-/]+)\s*(?::\s*(.*))?$", line.rstrip())
            if m:
                n = m.group(1)
                desc = re.sub(r"\s*\(Tools:.*?\)\s*$", "", (m.group(2) or "").strip())
                add(cat, n, desc, "loaded", f"Agent({n})")
    # 2. Installed user agents and plugin agents (fill in full descriptions).
    for p in agent_files(AGENTS_DIR):
        fm = sr.frontmatter(p)
        n = fm.get("name") or os.path.basename(p)[:-3]
        add(cat, n, fm.get("description", ""), "installed", f"Agent({n})")
    for root, _, files in os.walk(PLUGIN_CACHE):
        if os.path.basename(root) != "agents":
            continue
        for f in files:
            if f.endswith(".md"):
                fm = sr.frontmatter(os.path.join(root, f))
                if fm.get("name"):
                    add(cat, fm["name"], fm.get("description", ""), "plugin", f"Agent({fm['name']})")
    # 3. Library agents: not registered, launched as general-purpose with the file as the brief.
    for p in agent_files(LIBRARY_DIR):
        fm = sr.frontmatter(p)
        n = fm.get("name") or os.path.basename(p)[:-3]
        add(cat, n, fm.get("description", ""), "library",
            f"Agent(general-purpose) + {p.replace(HOME, '~')}")
    return cat


# ------------------------------------------------------------ TypeSafe

Q_TASK = dict(
    instructions="Would launching the subagent `agents.{id}` now materially help with `context.task`?",
    true="The agent's specialty directly serves the task as stated: delegating to it now would produce a review, "
         "plan, fix or finding the task needs.",
    false="The agent specialises in a different task, only shares a keyword with it, duplicates what the main "
          "agent would do anyway, or would only matter at a later stage the task does not include.")
Q_REPO = dict(
    instructions="Does the repository described in `context.repo` and `context.working_tree` have what the "
                 "subagent `agents.{id}` works on?",
    true="The repository uses the language, framework, service or file type the agent is for, or the agent is "
         "language-neutral and applies to any repository.",
    false="The agent targets a language, framework, database, platform or domain (e.g. healthcare, networking, "
          "email triage) that `context.repo` shows no sign of.")


def score_chunk(ctx, chunk, key):
    state = {"context": ctx, "agents": {sr.sid(a["name"]): {"name": a["name"], "description": a["description"]}
                                        for a in chunk}}
    qs = {}
    for a in chunk:
        i = sr.sid(a["name"])
        qs[f"{i}__task"], qs[f"{i}__repo"] = sr.question(Q_TASK, i), sr.question(Q_REPO, i)
    r = sr.post({"state": state, "model": sr.MODEL, "questions": qs}, key)
    out = {a["name"]: {"task": r["answers"][f"{sr.sid(a['name'])}__task"]["noul"],
                       "repo": r["answers"][f"{sr.sid(a['name'])}__repo"]["noul"]} for a in chunk}
    return out, r.get("model", "?"), r.get("usage", {}).get("input_tokens", 0)


def score(workdir, ctx, short, key):
    chunks = [short[i:i + BATCH] for i in range(0, len(short), BATCH)]
    scores, models, tok = {}, set(), 0
    with ThreadPoolExecutor(THREADS) as ex:
        for out, model, t in ex.map(lambda c: score_chunk(ctx, c, key), chunks):
            scores.update(out)
            models.add(model)
            tok += t
    json.dump(scores, open(os.path.join(workdir, "scores.json"), "w"), indent=1)
    print(f"scored {len(short)} agents with TypeSafe {', '.join(sorted(models))} ({tok} input tokens)",
          file=sys.stderr)


def write_mcp_batch(workdir, ctx, short, cap, baseline):
    # fast_verify answers one question per call: score only the head of the shortlist. The baseline launches
    # regardless, so it gets no calls.
    short = [a for a in short if a["name"] not in baseline][:cap]
    path = os.path.join(workdir, "to_score.jsonl")
    with open(path, "w") as fh:
        for a in short:
            ev = {"task": ctx["task"], "repo": ctx["repo"], "agent": {"name": a["name"], "description": a["description"]}}
            for kind, q in (("task", Q_TASK), ("repo", Q_REPO)):
                fh.write(json.dumps({"id": f"{a['name']}::{kind}",
                                     "statement": q["instructions"].replace("`agents.{id}`", f"`{a['name']}`")
                                         .replace("`context.task`", "the task")
                                         .replace("`context.repo` and `context.working_tree`", "the repository"),
                                     "evidence": ev, "yes_means": q["true"], "no_means": q["false"]}) + "\n")
    print(f"no TYPESAFE_API_KEY: {2 * len(short)} questions -> {path}\n"
          f"score EVERY line with mcp__system1__fast_verify (or mcp__plugin_ai-harness_system1__fast_verify when the MCP comes from the ai-harness plugin) (fields as given, all calls in one message) and write "
          f'{{"<name>": {{"task": p, "repo": p}}}} to {os.path.join(workdir, "scores.json")}, then run `report`.',
          file=sys.stderr)


# ------------------------------------------------------------ report

def load(workdir, name, default):
    p = os.path.join(workdir, name)
    return json.load(open(p)) if os.path.exists(p) else default


def report(workdir, sure, floor, top):
    short = load(workdir, "shortlist.json", None)
    if short is None:
        sys.exit(f"no shortlist in {workdir}: run `run` first")
    baseline = load(workdir, "baseline.json", [])
    scores = load(workdir, "scores.json", {})
    stray = sorted(set(scores) - {a["name"] for a in short})
    if stray:
        print(f"warning: scores.json has names not on the shortlist (ignored): {', '.join(stray)}", file=sys.stderr)
    rows = []
    for a in short:
        sc = scores.get(a["name"])
        repo = None if sc is None else sc.get("repo")
        rows.append(dict(a, p=None if sc is None else sc["task"] * (1.0 if repo is None else repo),
                         task=sc and sc["task"], repo=repo))
    rows.sort(key=lambda r: (r["p"] is None, -(r["p"] or 0), -r["bm25"]))
    base = [r for r in rows if r["name"] in baseline]
    rows = [r for r in rows if r["name"] not in baseline]
    scored = [r for r in rows if r["p"] is not None]
    run = [r for r in scored if r["p"] >= sure][:top]
    band = [r for r in scored if r["p"] >= floor and r not in run]
    unscored = [r for r in rows if r["p"] is None]

    def line(r):
        repo = "" if r["repo"] is None else f" · repo {r['repo']:.2f}"
        p = "—" if r["p"] is None else f"{r['p']:.2f} (task {r['task']:.2f}{repo})"
        return f"| {p} | `{r['name']}` | {r['source']} | {r['how']} | {r['description'][:110].replace('|', '/')} |"

    head = "| p | agent | source | how to launch | what it does |\n|---|---|---|---|---|"
    out = []
    if baseline:
        missing = [n for n in baseline if n not in {r["name"] for r in base}]
        out += ["## Always launch for a change (baseline, not scored against the cutoff)", head]
        out += [line(r) for r in base] + [f"| — | `{n}` | missing | not installed | — |" for n in missing]
        out.append("")
    out += [f"## Launch (p ≥ {sure}, at most {top})", head] + [line(r) for r in run]
    out += [f"\n## Judge yourself (p ≥ {floor}, not in Launch)", head] + [line(r) for r in band]
    if unscored:
        out += [f"\n## Unscored (BM25 order) — {len(unscored)} of {len(rows)} not scored; the report is incomplete",
                head] + [line(r) for r in unscored[:15]]
    out.append(f"\n{len(rows)} shortlisted; {len(scored) - len(run) - len(band)} below {floor} dropped.")
    text = "\n".join(out)
    open(os.path.join(workdir, "report.md"), "w").write(text + "\n")
    json.dump([r["name"] for r in base] + [r["name"] for r in run], open(os.path.join(workdir, "run.json"), "w"))
    print(text)


# ------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--task", required=True)
    r.add_argument("--listing", help="file with the session's agent listing, one '- name: description' per line; - for stdin")
    r.add_argument("--shortlist", type=int, default=30)
    r.add_argument("--no-score", action="store_true")
    r.add_argument("--mcp-shortlist", type=int, default=12,
                   help="without an API key, how many shortlisted agents to send to fast_verify (2 calls each)")
    r.add_argument("--change", dest="change", action="store_true", default=None,
                   help="treat the task as a code change: add the baseline agents (auto-detected from the task text)")
    r.add_argument("--no-change", dest="change", action="store_false")
    rep = sub.add_parser("report")
    for p in (r, rep):
        p.add_argument("--workdir", help="default: one per checkout under ~/.cache/agent-router")
        p.add_argument("--sure", type=float, default=0.6)
        p.add_argument("--floor", type=float, default=0.25)
        p.add_argument("--top", type=int, default=3)
    a = ap.parse_args()
    a.workdir = a.workdir or sr.default_workdir("agent-router")
    os.makedirs(a.workdir, exist_ok=True)
    if a.cmd == "report":
        return report(a.workdir, a.sure, a.floor, a.top)
    task = a.task.strip()
    if not task:
        sys.exit("--task is empty: describe what the user is doing right now")
    cat = build_catalog(a.listing)
    if not cat:
        sys.exit("empty catalog: pass --listing or install agents in ~/.claude/agents")
    ctx = sr.repo_context(task)
    change = a.change if a.change is not None else bool(sr.CHANGE_RE.search(task))
    baseline = [n for n in ALWAYS_ON_CHANGE if n in cat] if change else []
    short = sr.shortlist(cat, ctx, a.shortlist, baseline)
    for name, obj in (("context", ctx), ("catalog", cat), ("shortlist", short), ("baseline", baseline)):
        json.dump(obj, open(os.path.join(a.workdir, f"{name}.json"), "w"), indent=1)
    by_src = Counter(x["source"] for x in cat.values())
    print(f"catalog {len(cat)} agents ({', '.join(f'{k} {v}' for k, v in by_src.most_common())}); "
          f"shortlist {len(short)}", file=sys.stderr)
    print(f"workdir {a.workdir}", file=sys.stderr)
    sp = os.path.join(a.workdir, "scores.json")
    if os.path.exists(sp):
        os.remove(sp)   # scores belong to one task; never mix them with the previous run
    if not a.no_score:
        key = sr.api_key()
        if key:
            score(a.workdir, ctx, short, key)
        else:
            write_mcp_batch(a.workdir, ctx, short, a.mcp_shortlist, baseline)
    report(a.workdir, a.sure, a.floor, a.top)


if __name__ == "__main__":
    main()
