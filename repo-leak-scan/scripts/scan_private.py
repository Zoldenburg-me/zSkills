#!/usr/bin/env python3
"""Scan every commit on every ref (branches, tags, fetched PR refs) for private
information that secret scanners do not look for, plus text that discloses a
vulnerability.

What it looks at:
  - every added line of every commit diff (a removed line was added earlier,
    so added lines cover the whole history)
  - every commit message, and author/committer identities
  - optionally a directory of PR/issue text dumped by fetch_pr_text.py

Kinds reported:
  iban, email, personal-path, phone, eth-private-key, mnemonic,
  author-identity, disclosure (candidates for Claude to judge, not verdicts)

Usage: scan_private.py REPO OUT.jsonl [--pr-text DIR] [--allow FILE]
The allow file (default REPO/.leakscan-allow) holds one regex per line matched
against the value; lines starting with "path:" are regexes matched against the
file path. "#" starts a comment.
"""
import argparse, json, os, re, subprocess, sys
from collections import OrderedDict

# ---------------------------------------------------------------- patterns

IBAN_LEN = dict(AD=24, AE=23, AL=28, AT=20, AZ=28, BA=20, BE=16, BG=22, BH=22, BR=29,
                BY=28, CH=21, CR=22, CY=28, CZ=24, DE=22, DK=18, DO=28, EE=20, EG=29,
                ES=24, FI=18, FO=18, FR=27, GB=22, GE=22, GI=23, GL=18, GR=27, GT=28,
                HR=21, HU=28, IE=22, IL=23, IQ=23, IS=26, IT=27, JO=30, KW=30, KZ=20,
                LB=28, LC=32, LI=21, LT=20, LU=20, LV=21, MC=27, MD=24, ME=22, MK=19,
                MR=27, MT=31, MU=30, NL=18, NO=15, PK=24, PL=28, PS=29, PT=25, QA=29,
                RO=24, RS=22, SA=24, SC=31, SE=24, SI=19, SK=24, SM=27, ST=25, SV=28,
                TL=23, TN=24, TR=26, UA=29, VA=22, VG=24, XK=20)
# the IBANs every bank's documentation uses as examples
EXAMPLE_IBANS = {"DE89370400440532013000", "GB82WEST12345698765432", "GB29NWBK60161331926819",
                 "FR1420041010050500013M02606", "NL91ABNA0417164300", "BE68539007547034",
                 "AT611904300234573201", "CH9300762011623852957", "ES9121000418450200051332"}
IBAN_RE = re.compile(r"\b([A-Z]{2}\d{2}(?: ?[A-Z0-9]){11,32})")

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
WEBMAIL = {"gmail.com", "googlemail.com", "yahoo.com", "yahoo.de", "hotmail.com", "hotmail.de",
           "outlook.com", "outlook.de", "live.com", "icloud.com", "me.com", "mac.com", "gmx.de",
           "gmx.net", "gmx.com", "web.de", "t-online.de", "proton.me", "protonmail.com",
           "aol.com", "mail.ru", "yandex.ru", "posteo.de", "mailbox.org", "freenet.de"}
EMAIL_IGNORE_DOMAIN = re.compile(
    r"(^|\.)(example\.(com|org|net)|test|invalid|local|localhost|users\.noreply\.github\.com|"
    r"sentry\.io|domain\.com|email\.com|yourdomain\.com|company\.com)$", re.I)
EMAIL_IGNORE_TLD = {"png", "jpg", "jpeg", "svg", "gif", "webp", "js", "mjs", "ts", "css", "json", "md", "html"}
EMAIL_IGNORE_LOCAL = re.compile(r"^(no-?reply|noreply.*|user|you|your\.?name|name|email|test|foo|bar|"
                                r"someone|john(\.doe)?|jane(\.doe)?|alice|bob|me|hello|info|support)$", re.I)

PATH_RES = [
    (re.compile(r"/Users/([^/\s\"'`$<>{}()]+)/"),
     {"shared", "runner", "user", "username", "you", "me", "name", "john", "jane", "foo", "example"}),
    (re.compile(r"/home/([a-z_][a-z0-9_.-]*)/"),
     {"runner", "node", "user", "ubuntu", "app", "circleci", "vscode", "gitpod", "codespace",
      "username", "you", "me", "example", "linuxbrew", "deno", "pwuser"}),
    (re.compile(r"[A-Za-z]:\\{1,2}Users\\{1,2}([^\\\s\"'`]+)", re.I),
     {"public", "default", "user", "username", "runneradmin", "you"}),
]
TEMP_PATH_RE = re.compile(r"/(?:private/)?var/folders/[\w+]{2}/[\w+]+|/private/tmp/claude-\d+")

PHONE_RE = re.compile(r"(?<![\w./=#-])\+\d{1,3}[ \-]?\(?\d{2,5}\)?(?:[ \-]?\d{2,5}){2,4}(?![\w.])")

ETH_KEY_RE = re.compile(r"(?i)(priv(?:ate)?[_ -]?key|secret|signer[_ -]?key|deployer|\bpk\b)"
                        r"[\"']?\s*[:=,]?\s*[\"'`]?(0x)?([0-9a-f]{64})\b")
# hardhat/anvil default dev accounts: public knowledge, never real money
HARDHAT_KEYS = {
    "ac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
    "59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d",
    "5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a",
    "7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6",
    "47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a",
}
MNEMONIC_RE = re.compile(r"(?i)(mnemonic|seed[ _-]?phrase|recovery[ _-]?phrase|secret[ _-]?phrase)"
                         r"[\"']?\s*[:=]?\s*[\"'`]((?:[a-z]{3,8} ){11,23}[a-z]{3,8})[\"'`]")
TEST_MNEMONIC = "test test test test test test test test test test test junk"

# Strong words carry 2 points, weak ones 1; a candidate needs 2 points, so a
# lone "replay" or "plaintext" (normal vocabulary in a payments codebase) is
# not enough, but "attacker" alone or "leak" + "anyone can" is.
STRONG_RE = re.compile(
    r"(?i)\b(exploit\w*|vulnerab\w*|attacker\w*|attack vector|bypass\w*|CVE-\d{4}-\d+|"
    r"remote code execution|RCE|XSS|SSRF|CSRF|IDOR|sql ?injection|privilege escalation|"
    r"drain(?:s|ed|ing)?|steal(?:s|ing)?|stolen|unauthori[sz]ed|unwrapped|"
    r"hard-?coded (?:key|secret|password|token)|security (?:hole|issue|bug|flaw)|"
    r"reentran\w*|front-?run\w*|zero-?day|0-?day|backdoor|timing attack|"
    r"not (?:yet )?fixed|unpatched|could (?:spend|withdraw|impersonate|forge|steal|drain)|"
    r"anyone (?:could|can) (?:spend|withdraw|read|call|sign|approve|forge|drain|mint))\b")
WEAK_RE = re.compile(
    r"(?i)\b(leak(?:ed|s|ing)?|exposed|insecure\w*|plain ?text|replay\w*|injection|"
    r"race condition|denial of service|anyone (?:can|could)|still open|known issue|"
    r"workaround|security fix)\b")


def disclosure_hits(text):
    strong = {h.lower() for h in STRONG_RE.findall(text)}
    weak = {h.lower() for h in WEAK_RE.findall(text)} - strong
    return (sorted(strong | weak) if 2 * len(strong) + len(weak) >= 2 else [])


PASSWORD_FIELD_RE = re.compile(r"""(?i)type=["']password["'][^>]*?\bvalue=["']([^"'$<{]{8,})["']""")

DOC_EXT = re.compile(r"\.(md|mdx|txt|rst|adoc)$", re.I)
COMMENT_LINE = re.compile(r"^\s*(//|#(?!!)|\*|/\*|<!--|--|;)")

DEFAULT_SKIP_PATHS = re.compile(
    r"(^|/)(node_modules|vendor|\.toolchain|dist|build|coverage)/|"
    r"(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|\.min\.(js|css)|\.map)$")

MAX_LINE = 4000

# ---------------------------------------------------------------- helpers


def iban_valid(raw):
    s = raw.replace(" ", "")
    n = IBAN_LEN.get(s[:2])
    if not n or len(s) < n:
        return None
    s = s[:n]
    r = s[4:] + s[:4]
    digits = "".join(str(int(c, 36)) for c in r)
    return s if int(digits) % 97 == 1 else None


def load_allow(path):
    vals, paths = [], []
    if path and os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            (paths if line.startswith("path:") else vals).append(
                re.compile(line[5:] if line.startswith("path:") else line))
    return vals, paths


class Findings:
    def __init__(self, allow_vals, allow_paths):
        self.items = OrderedDict()
        self.allow_vals, self.allow_paths = allow_vals, allow_paths

    def add(self, kind, severity, value, where, snippet, note=""):
        if any(a.search(value) for a in self.allow_vals):
            return
        if where.get("file") and any(a.search(where["file"]) for a in self.allow_paths):
            return
        key = (kind, value, where.get("file") or where.get("source"))
        f = self.items.get(key)
        if f is None:
            f = self.items[key] = dict(kind=kind, severity=severity, value=value, note=note,
                                       first=where, snippet=snippet[:240], count=0, commits=[])
        f["count"] += 1
        c = where.get("commit")
        if c and c not in f["commits"] and len(f["commits"]) < 8:
            f["commits"].append(c)


def scan_text(F, text, where):
    """Private-info patterns over one line/blob of text."""
    for m in IBAN_RE.finditer(text):
        iban = iban_valid(m.group(1))
        if iban:
            ex = iban in EXAMPLE_IBANS
            F.add("iban", "low" if ex else "high", iban, where, text.strip(),
                  "published example IBAN" if ex else "valid checksum")
    for m in EMAIL_RE.finditer(text):
        e = m.group(0).rstrip(".")
        local, _, dom = e.partition("@")
        dom_l = dom.lower()
        if (EMAIL_IGNORE_DOMAIN.search(dom_l) or dom_l.rsplit(".", 1)[-1] in EMAIL_IGNORE_TLD
                or EMAIL_IGNORE_LOCAL.match(local)):
            continue
        sev = "high" if dom_l in WEBMAIL else "review"
        F.add("email", sev, e, where, text.strip(), "personal webmail" if sev == "high" else "")
    for rx, ignore in PATH_RES:
        for m in rx.finditer(text):
            if m.group(1).lower() not in ignore:
                F.add("personal-path", "review", m.group(0), where, text.strip(),
                      f"home dir of '{m.group(1)}'")
    for m in TEMP_PATH_RE.finditer(text):
        F.add("personal-path", "low", m.group(0), where, text.strip(), "machine-specific temp dir")
    for m in PHONE_RE.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        if 9 <= len(digits) <= 15:
            F.add("phone", "review", m.group(0), where, text.strip())
    for m in ETH_KEY_RE.finditer(text):
        k = m.group(3).lower()
        if k in HARDHAT_KEYS or len(set(k)) < 6:
            continue
        F.add("eth-private-key", "high", "0x" + k, where, text.strip(),
              f"64-hex next to '{m.group(1)}'")
    for m in PASSWORD_FIELD_RE.finditer(text):
        F.add("prefilled-password", "high", m.group(1), where, text.strip(),
              "secret prefilled into an HTML password field")
    for m in MNEMONIC_RE.finditer(text):
        if m.group(2).lower() != TEST_MNEMONIC:
            F.add("mnemonic", "high", m.group(2), where, text.strip())


def scan_disclosure(D, text, where, ctx):
    hits = disclosure_hits(text)
    if hits:
        D.append(dict(kind="disclosure", keywords=hits, where=where, text=ctx[:1500]))


# ---------------------------------------------------------------- git walk

SEP_C, SEP_M = "\x1eCOMMIT ", "\x1dENDMSG"
FMT = f"%x1eCOMMIT %H%x1f%an%x1f%ae%x1f%cn%x1f%ce%x1f%aI%x1f%D%n%B%x1dENDMSG"


def walk(repo, F, D, identities):
    p = subprocess.Popen(["git", "-C", repo, "log", "--all", "--reverse", "--no-color", "-p", "-U0",
                          "--no-ext-diff", "--no-textconv", f"--format={FMT}"],
                         stdout=subprocess.PIPE)
    commit = meta = None
    in_msg, msg = False, []
    path, skip = None, False
    disc_seen = OrderedDict()
    ncommits = 0

    for raw in p.stdout:
        line = raw.decode("utf-8", "replace").rstrip("\n")
        if line.startswith(SEP_C):
            parts = line[len(SEP_C):].split("\x1f")
            commit = parts[0][:12]
            meta = dict(commit=commit, author=f"{parts[1]} <{parts[2]}>", date=parts[5][:10])
            for nm, em in ((parts[1], parts[2]), (parts[3], parts[4])):
                identities.setdefault((nm, em), set()).add(commit)
            in_msg, msg, path = True, [], None
            ncommits += 1
            continue
        if in_msg:
            if line.endswith(SEP_M):
                last = line[: -len(SEP_M)]
                if last:
                    msg.append(last)
                in_msg = False
                body = "\n".join(msg).strip()
                w = dict(meta, source="commit-message")
                for ml in msg:
                    scan_text(F, ml[:MAX_LINE], w)
                scan_disclosure(D, body, w, body)
            else:
                msg.append(line)
            continue
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else None
            skip = path is None or bool(DEFAULT_SKIP_PATHS.search(path))
            continue
        if line.startswith("+") and path and not skip:
            text = line[1:MAX_LINE]
            where = dict(meta, source="diff", file=path)
            scan_text(F, text, where)
            if (DOC_EXT.search(path) or COMMENT_LINE.match(text)) and disclosure_hits(text):
                norm = re.sub(r"\s+", " ", text.strip())
                if norm not in disc_seen:
                    disc_seen[norm] = dict(source="diff", commit=commit, file=path, date=meta["date"])
    p.wait()
    for norm, where in disc_seen.items():
        scan_disclosure(D, norm, where, norm)
    return ncommits


def scan_pr_dir(d, F, D):
    n = 0
    for name in sorted(os.listdir(d)):
        fp = os.path.join(d, name)
        text = open(fp, encoding="utf-8", errors="replace").read()
        head = text.split("\n", 1)[0]
        where = dict(source="pr-text", file=name, ref=head)
        for line in text.splitlines():
            scan_text(F, line[:MAX_LINE], where)
        scan_disclosure(D, text, where, text)
        n += 1
    return n


def in_head(repo, value):
    r = subprocess.run(["git", "-C", repo, "grep", "-q", "-F", "-e", value, "HEAD", "--"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return r.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("out")
    ap.add_argument("--pr-text")
    ap.add_argument("--allow")
    a = ap.parse_args()
    allow = a.allow or os.path.join(a.repo, ".leakscan-allow")
    F = Findings(*load_allow(allow))
    D, identities = [], {}
    nc = walk(a.repo, F, D, identities)
    npr = scan_pr_dir(a.pr_text, F, D) if a.pr_text and os.path.isdir(a.pr_text) else 0

    for (nm, em), commits in identities.items():
        dom = em.rpartition("@")[2].lower()
        if dom in WEBMAIL:
            F.add("author-identity", "high", f"{nm} <{em}>",
                  dict(source="commit-metadata"), f"author/committer on {len(commits)} commits",
                  "personal webmail in commit metadata")
            F.items[("author-identity", f"{nm} <{em}>", "commit-metadata")]["all_commits"] = sorted(commits)
        elif not dom.endswith("noreply.github.com"):
            F.add("author-identity", "low", f"{nm} <{em}>", dict(source="commit-metadata"),
                  f"author/committer on {len(commits)} commits")

    with open(a.out, "w") as out:
        for f in F.items.values():
            if f["first"].get("source") == "diff":
                f["in_head"] = in_head(a.repo, f["value"])
            out.write(json.dumps(f) + "\n")
        for d in D:
            out.write(json.dumps(d) + "\n")
    os.chmod(a.out, 0o600)
    kinds = {}
    for f in F.items.values():
        kinds[f["kind"]] = kinds.get(f["kind"], 0) + 1
    print(f"private scan: {nc} commits, {npr} PR/issue texts; findings {kinds}; "
          f"disclosure candidates {len(D)} -> {a.out}")


if __name__ == "__main__":
    main()
