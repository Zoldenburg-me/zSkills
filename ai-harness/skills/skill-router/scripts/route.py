#!/usr/bin/env python3
"""Pick the skills worth running now: build a catalog of every skill the agent
can reach, shortlist it with BM25 against the task and the repo, then score
the shortlist with TypeSafe (Jev) and bucket it.

Subcommands
  run --task TEXT [--listing FILE|-] [--workdir DIR] [--shortlist N]
      [--sure 0.6] [--floor 0.25] [--top 3] [--no-score]
      Writes WORKDIR/context.json, catalog.json, shortlist.json, then scores
      via the TypeSafe HTTP API ($TYPESAFE_API_KEY, ~/.system1/config.json, or .env) into
      scores.json and prints the report. Without a key it writes
      to_score.jsonl (task fit only, 12 skills) for the system1 fast_verify MCP tool.
  report [--workdir DIR] [--sure 0.6] [--floor 0.25] [--top 3]
      Prints the report from an existing scores.json (after MCP scoring).

Two Nouls per skill, kept separate on purpose: `fits_task` (does it serve
what the user is doing) and `fits_repo` (does this repo have what it works
on). The rank is their product, so a perfect task match for a stack the repo
does not use still ranks low.

Only the task text, file-extension counts, dependency names, changed file
paths and recent commit subjects go to TypeSafe. No file contents, no diffs.
"""
import argparse, hashlib, json, math, os, re, subprocess, sys, time, urllib.error, urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

TYPESAFE_URL = os.environ.get("TYPESAFE_BASE_URL", "https://api.typesafe.ai").rstrip("/") + "/v1/systemone"
MODEL = os.environ.get("TYPESAFE_DEFAULT_MODEL", "jev-latest")
HOME = os.path.expanduser("~")
SKILLS_DIR = os.path.join(HOME, ".claude", "skills")
COMMANDS_DIR = os.path.join(HOME, ".claude", "commands")
PLUGIN_CACHE = os.path.join(HOME, ".claude", "plugins", "cache")
LIBRARY_DIR = os.environ.get("SKILL_ROUTER_LIBRARY",
                             os.path.join(HOME, "Documents", "everything-claude-code", "skills"))
SELF = "skill-router"
BATCH = 10            # skills per request; two questions each
SHORTLIST_API, SHORTLIST_MCP = 40, 12   # MCP scoring is one tool call per question
THREADS = 4
TASK_WEIGHT, REPO_WEIGHT = 1.0, 0.15
# Run on every code change (PR, diff, commit, push) whatever Jev says: a missed
# security review or leak costs more than a needless one.
ALWAYS_ON_CHANGE = [n.strip() for n in os.environ.get(
    "SKILL_ROUTER_ALWAYS", "security-review,tidy-context,leak-check").split(",") if n.strip()]
# Always shortlisted, so Jev scores them on every run; unlike the baseline they
# still have to clear the cutoff to run.
ALWAYS_SCORE = [n.strip() for n in os.environ.get(
    "SKILL_ROUTER_SCORE", "gdpr-compliance").split(",") if n.strip()]
CHANGE_RE = re.compile(r"\b(pr|pull request|diff|commits?|push|merge|branch|uncommitted|staged|changes)\b"
                       r"|/pull/\d+|#\d+", re.I)
EXT_WORDS = {".ts": "typescript", ".tsx": "typescript react", ".js": "javascript", ".jsx": "javascript react",
             ".py": "python", ".go": "golang go", ".rs": "rust", ".sol": "solidity", ".java": "java",
             ".kt": "kotlin", ".swift": "swift", ".rb": "ruby rails", ".php": "php laravel", ".vue": "vue",
             ".dart": "dart flutter", ".cs": "csharp dotnet", ".cpp": "cpp", ".sql": "sql database",
             ".html": "html frontend", ".css": "css frontend", ".md": "docs markdown"}
STOP = set("the and for with that this from into when use used using your you are not any all can will "
           "its it's skill skills should does what which who how about over under also only more most".split())


# ------------------------------------------------------------ catalog

def frontmatter(path):
    try:
        text = open(path, encoding="utf-8", errors="replace").read(6000)
    except OSError:
        return {}
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return {}
    fm, key = {}, None
    for line in m.group(1).splitlines():
        kv = re.match(r"^([A-Za-z_-]+):\s*(.*)$", line)
        if kv:
            key, val = kv.group(1), kv.group(2).strip()
            fm[key] = "" if val in (">", "|", ">-", "|-") else val.strip("\"'")
        elif key and line.startswith(" "):
            fm[key] = (fm[key] + " " + line.strip()).strip()
    return fm


def add(cat, name, desc, source, how):
    if not name or name == SELF or "DEPRECATED" in (desc or "")[:40]:
        return
    cur = cat.get(name)
    if cur is None:
        cat[name] = {"name": name, "description": desc or "", "source": source, "how": how}
    elif len(desc or "") > len(cur["description"]):
        cur["description"] = desc   # keep the first source's `how`, take the fuller text


def skill_dirs(root):
    if not os.path.isdir(root):
        return []
    return [(d, os.path.join(root, d, "SKILL.md")) for d in sorted(os.listdir(root))
            if os.path.isfile(os.path.join(root, d, "SKILL.md"))]


def build_catalog(listing_path):
    cat = {}
    # 1. What the agent's own skill listing says is invokable right now (authoritative).
    if listing_path:
        for line in (sys.stdin if listing_path == "-" else open(listing_path, encoding="utf-8")):
            m = re.match(r"^\s*-\s*([\w:.\-/]+)\s*(?::\s*(.*))?$", line.rstrip())
            if m:
                add(cat, m.group(1), (m.group(2) or "").strip(), "loaded", f"Skill({m.group(1)})")
    # 2. Installed user skills, commands and plugin skills (fill in full descriptions).
    for d, p in skill_dirs(SKILLS_DIR):
        fm = frontmatter(p)
        add(cat, fm.get("name") or d, fm.get("description", ""), "installed", f"Skill({fm.get('name') or d})")
    if os.path.isdir(COMMANDS_DIR):
        for f in sorted(os.listdir(COMMANDS_DIR)):
            if f.endswith(".md"):
                n = f[:-3]
                add(cat, n, frontmatter(os.path.join(COMMANDS_DIR, f)).get("description", ""), "command", f"Skill({n})")
    for root, _, files in os.walk(PLUGIN_CACHE):
        if "SKILL.md" in files:
            fm = frontmatter(os.path.join(root, "SKILL.md"))
            if fm.get("name"):
                add(cat, fm["name"], fm.get("description", ""), "plugin", f"Skill({fm['name']})")
    # 3. Library skills: not installed, used by reading their SKILL.md.
    for d, p in skill_dirs(LIBRARY_DIR):
        fm = frontmatter(p)
        add(cat, fm.get("name") or d, fm.get("description", ""), "library", f"Read {p.replace(HOME, '~')}")
    return cat


# ------------------------------------------------------------ repo context

def sh(*args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=20).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def dep_names():
    deps = []
    for f in ("package.json", "services/api/package.json"):
        try:
            pj = json.load(open(f))
        except (OSError, ValueError):
            continue
        for k in ("dependencies", "devDependencies"):
            deps += list((pj.get(k) or {}).keys())
    for f in ("requirements.txt", "go.mod", "Cargo.toml", "pyproject.toml", "Gemfile", "composer.json"):
        if os.path.exists(f):
            deps.append(f)
    return sorted(set(deps))[:60]


def repo_context(task):
    files = sh("git", "ls-files").split()
    exts = Counter(os.path.splitext(f)[1].lower() for f in files if os.path.splitext(f)[1])
    markers = [m for m in ("Dockerfile", "docker-compose.yml", "hardhat.config.js", "hardhat.config.ts",
                           "foundry.toml", "next.config.js", "vite.config.ts", ".github/workflows",
                           "AGENTS.md", "CLAUDE.md", "openapi.yaml") if os.path.exists(m)]
    changed = [l[3:] for l in sh("git", "status", "--porcelain").splitlines()][:30]
    return {
        "task": task,
        "repo": {
            "name": os.path.basename(sh("git", "rev-parse", "--show-toplevel").strip()) or os.path.basename(os.getcwd()),
            "branch": sh("git", "branch", "--show-current").strip(),
            "file_types": dict(exts.most_common(10)),
            "dependencies": dep_names(),
            "markers": markers,
        },
        "working_tree": {
            "changed_files": changed,
            "recent_commits": sh("git", "log", "-5", "--format=%s").splitlines(),
        },
    }


# ------------------------------------------------------------ shortlist (BM25)

def tokens(text):
    return [t for t in re.findall(r"[a-z0-9][a-z0-9+#.-]{1,}", text.lower().replace("_", "-")) if t not in STOP]


def shortlist(cat, ctx, size, forced=()):
    # The task decides relevance; repo signals only break ties (repo fit is Jev's second question).
    langs = " ".join(EXT_WORDS.get(e, "") for e in ctx["repo"]["file_types"])
    q = Counter({t: TASK_WEIGHT * n for t, n in Counter(tokens(ctx["task"])).items()})
    for t in tokens(langs + " " + " ".join(ctx["repo"]["markers"])):
        q[t] += REPO_WEIGHT
    # The name counts twice: it is the densest statement of what a skill is for.
    docs = {n: tokens((n.replace("-", " ") + " ") * 2 + s["description"]) for n, s in cat.items()}
    N, avg = len(docs), sum(map(len, docs.values())) / max(len(docs), 1)
    df = Counter(t for d in docs.values() for t in set(d))
    scores = {}
    for n, d in docs.items():
        tf, s = Counter(d), 0.0
        for t, qn in q.items():
            if t in tf:
                idf = math.log(1 + (N - df[t] + 0.5) / (df[t] + 0.5))
                s += qn * idf * tf[t] * 2.2 / (tf[t] + 1.2 * (0.25 + 0.75 * len(d) / avg))
        scores[n] = s
    named = [n for n in cat if re.search(r"(?<![\w-])" + re.escape(n) + r"(?![\w-])", ctx["task"], re.I)]
    named += [n for n in forced if n in cat and n not in named]
    ranked = [n for n in sorted(cat, key=lambda n: -scores[n]) if n not in named and scores[n] > 0]
    picked = named + ranked[:max(size - len(named), 0)]
    return [dict(cat[n], bm25=round(scores[n], 2)) for n in picked]


# ------------------------------------------------------------ TypeSafe

Q_TASK = dict(
    instructions="Would running the skill `skills.{id}` now materially help the agent with `context.task`?",
    true="The skill's purpose directly serves the task as stated: following it now would change what the agent "
         "does or make the result better for this task.",
    false="The skill is about a different task, only shares a keyword with it, restates a general habit the agent "
          "already follows, or would only matter at a later stage the task does not include.")
Q_REPO = dict(
    instructions="Does the repository described in `context.repo` and `context.working_tree` have what the skill "
                 "`skills.{id}` works on?",
    true="The repository uses the language, framework, service or file type the skill is for, or the skill is "
         "language-neutral and applies to any repository.",
    false="The skill targets a language, framework, database or platform that `context.repo` shows no sign of, "
          "or needs a tool or service this repository does not use.")


def api_key():
    key = os.environ.get("TYPESAFE_API_KEY")
    if key:
        return key
    # The system1 MCP server's own store: the same key the fast_verify tool uses.
    cfg = os.path.join(os.environ.get("SYSTEM1_CONFIG_DIR") or os.path.join(HOME, ".system1"), "config.json")
    try:
        key = (json.load(open(cfg)).get("api_key") or "").strip()
    except (OSError, ValueError, AttributeError):
        key = ""
    if key:
        return key
    common = sh("git", "rev-parse", "--path-format=absolute", "--git-common-dir").strip()
    for env in [".env"] + ([os.path.join(os.path.dirname(common), ".env")] if common else []):
        try:
            for line in open(env):
                m = re.match(r"^\s*(?:export\s+)?TYPESAFE_API_KEY\s*=\s*['\"]?([^'\"\s#]+)", line)
                if m:
                    return m.group(1)
        except OSError:
            pass
    return None


def default_workdir(tool=SELF):
    # One workdir per checkout: parallel sessions in different worktrees must not overwrite each other's scores.
    top = sh("git", "rev-parse", "--show-toplevel").strip() or os.getcwd()
    return os.path.join(HOME, ".cache", tool,
                        os.path.basename(top) + "-" + hashlib.sha1(top.encode()).hexdigest()[:6])


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
        except urllib.error.URLError as e:
            if attempt < 5:
                time.sleep(2 ** attempt)
                continue
            sys.exit(f"TypeSafe unreachable: {e.reason}")


def sid(name):
    return re.sub(r"[^A-Za-z0-9_]", "_", name)


def question(q, i):
    return {"type": "noul", "instructions": q["instructions"].format(id=i),
            "criteria": {"true": q["true"], "false": q["false"]}}


def score_chunk(ctx, chunk, key):
    state = {"context": ctx, "skills": {sid(s["name"]): {"name": s["name"], "description": s["description"]}
                                        for s in chunk}}
    qs = {}
    for s in chunk:
        i = sid(s["name"])
        qs[f"{i}__task"], qs[f"{i}__repo"] = question(Q_TASK, i), question(Q_REPO, i)
    r = post({"state": state, "model": MODEL, "questions": qs}, key)
    out = {}
    for s in chunk:
        i = sid(s["name"])
        out[s["name"]] = {"task": r["answers"][f"{i}__task"]["noul"], "repo": r["answers"][f"{i}__repo"]["noul"]}
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
    print(f"scored {len(short)} skills with TypeSafe {', '.join(sorted(models))} ({tok} input tokens)", file=sys.stderr)


def write_mcp_batch(workdir, ctx, short, baseline):
    path = os.path.join(workdir, "to_score.jsonl")
    short = [s for s in short if s["name"] not in baseline]   # the baseline runs regardless; don't spend calls on it
    with open(path, "w") as fh:
        for s in short:
            # Task fit only: one tool call per question, and the shortlist already leans on the repo's stack.
            ev = {"task": ctx["task"], "repo": ctx["repo"], "skill": {"name": s["name"], "description": s["description"]}}
            fh.write(json.dumps({"id": s["name"],
                                 "statement": f"Would running the skill `{s['name']}` now materially help the agent "
                                              f"with `task`?",
                                 "evidence": ev, "yes_means": Q_TASK["true"], "no_means": Q_TASK["false"]}) + "\n")
    print(f"no TYPESAFE_API_KEY: {len(short)} questions -> {path}\n"
          f"score EVERY line with mcp__system1__fast_verify (or mcp__plugin_ai-harness_system1__fast_verify when the MCP comes from the ai-harness plugin) (statement, evidence, yes_means, no_means as given) and "
          f'write {{"<id>": {{"task": probability}}}} to {os.path.join(workdir, "scores.json")}, then run `report`.',
          file=sys.stderr)


# ------------------------------------------------------------ report

def report(workdir, sure, floor, top):
    short = json.load(open(os.path.join(workdir, "shortlist.json")))
    bp = os.path.join(workdir, "baseline.json")
    baseline = json.load(open(bp)) if os.path.exists(bp) else []
    sp = os.path.join(workdir, "scores.json")
    scores = json.load(open(sp)) if os.path.exists(sp) else {}
    names = {s["name"] for s in short}
    stray = sorted(set(scores) - names)
    if stray:
        print(f"warning: scores.json has names not on the shortlist (ignored): {', '.join(stray)}", file=sys.stderr)
    rows = []
    for s in short:
        sc = scores.get(s["name"])
        repo = None if sc is None else sc.get("repo")
        p = None if sc is None else sc["task"] * (1.0 if repo is None else repo)
        rows.append(dict(s, p=p, task=sc and sc["task"], repo=repo))
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

    head = "| p | skill | source | how to run | what it does |\n|---|---|---|---|---|"
    out = []
    if baseline:
        missing = [n for n in baseline if n not in {r["name"] for r in base}]
        out += ["## Always run for a change (baseline, not scored against the cutoff)", head]
        out += [line(r) for r in base] + [f"| — | `{n}` | missing | not installed | — |" for n in missing]
        out.append("")
    out += [f"## Run (p ≥ {sure}, at most {top})", head] + [line(r) for r in run]
    out += [f"\n## Judge yourself (p ≥ {floor}, not in Run)", head] + [line(r) for r in band]
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
    r.add_argument("--listing", help="file with the agent's skill listing, one '- name: description' per line; - for stdin")
    r.add_argument("--shortlist", type=int, help=f"default {SHORTLIST_API} with an API key, {SHORTLIST_MCP} without")
    r.add_argument("--no-score", action="store_true")
    r.add_argument("--change", dest="change", action="store_true", default=None,
                   help="treat the task as a code change: add the baseline skills (auto-detected from the task text)")
    r.add_argument("--no-change", dest="change", action="store_false")
    rep = sub.add_parser("report")
    for p in (r, rep):
        p.add_argument("--workdir", help="default: one per checkout under ~/.cache/skill-router")
        p.add_argument("--sure", type=float, default=0.6)
        p.add_argument("--floor", type=float, default=0.25)
        p.add_argument("--top", type=int, default=3)
    a = ap.parse_args()
    a.workdir = a.workdir or default_workdir()
    os.makedirs(a.workdir, exist_ok=True)
    if a.cmd == "report":
        return report(a.workdir, a.sure, a.floor, a.top)
    task = a.task.strip()
    if not task:
        sys.exit("--task is empty: describe what the user is doing right now")
    cat = build_catalog(a.listing)
    ctx = repo_context(task)
    change = a.change if a.change is not None else bool(CHANGE_RE.search(task))
    baseline = ALWAYS_ON_CHANGE if change else []
    key = None if a.no_score else api_key()
    size = (a.shortlist or (SHORTLIST_API if key or a.no_score else SHORTLIST_MCP)) + len(baseline)
    short = shortlist(cat, ctx, size, baseline + [n for n in ALWAYS_SCORE if n not in baseline])
    for name, obj in (("context", ctx), ("catalog", cat), ("shortlist", short), ("baseline", baseline)):
        json.dump(obj, open(os.path.join(a.workdir, f"{name}.json"), "w"), indent=1)
    by_src = Counter(s["source"] for s in cat.values())
    print(f"catalog {len(cat)} skills ({', '.join(f'{k} {v}' for k, v in by_src.most_common())}); "
          f"shortlist {len(short)}", file=sys.stderr)
    sp = os.path.join(a.workdir, "scores.json")
    if os.path.exists(sp):
        os.remove(sp)   # scores belong to one task; never mix them with the previous run
    print(f"workdir {a.workdir}", file=sys.stderr)
    if key:
        score(a.workdir, ctx, short, key)
    elif not a.no_score:
        write_mcp_batch(a.workdir, ctx, short, baseline)
    report(a.workdir, a.sure, a.floor, a.top)


if __name__ == "__main__":
    main()
