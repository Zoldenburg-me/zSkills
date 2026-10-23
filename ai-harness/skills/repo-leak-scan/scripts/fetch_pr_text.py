#!/usr/bin/env python3
"""Dump every PR's title/body, PR+issue conversation comments and review comments
of a GitHub repo into one text file per item, so the secret and private-info
scanners can read them like files.

Usage: fetch_pr_text.py OWNER/REPO OUT_DIR
Auth: uses $GITHUB_TOKEN if set (sent only to api.github.com). Without it the
public-repo rate limit is 60 requests/hour, enough for a few hundred PRs.
"""
import json, os, re, sys, urllib.request, urllib.error

API = "https://api.github.com"


def get_all(path):
    url = f"{API}{path}{'&' if '?' in path else '?'}per_page=100"
    out = []
    while url:
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                                   "User-Agent": "repo-leak-scan"})
        tok = os.environ.get("GITHUB_TOKEN")
        if tok:
            req.add_header("Authorization", f"Bearer {tok}")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                out.extend(json.load(r))
                m = re.search(r'<([^>]+)>;\s*rel="next"', r.headers.get("Link", ""))
                url = m.group(1) if m else None
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:300]
            sys.exit(f"GitHub API {e.code} on {url}: {body}\n"
                     "(404 on a private repo or 403 rate limit -> set GITHUB_TOKEN)")
    return out


def write(out_dir, name, header, text):
    with open(os.path.join(out_dir, name), "w") as f:
        f.write(header + "\n\n" + (text or "") + "\n")


def main():
    repo, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    pulls = get_all(f"/repos/{repo}/pulls?state=all")
    for p in pulls:
        write(out_dir, f"pr-{p['number']}-body.txt",
              f"PR #{p['number']} {p['html_url']}\nauthor: {p['user']['login']}\ntitle: {p['title']}",
              p.get("body"))
    pr_numbers = {p["number"] for p in pulls}
    # conversation comments on PRs and issues (issues can leak too; kept, labelled)
    for c in get_all(f"/repos/{repo}/issues/comments"):
        n = int(c["issue_url"].rsplit("/", 1)[1])
        kind = "pr" if n in pr_numbers else "issue"
        write(out_dir, f"{kind}-{n}-comment-{c['id']}.txt",
              f"{kind.upper()} #{n} comment {c['html_url']}\nauthor: {c['user']['login']}", c.get("body"))
    # inline review comments
    for c in get_all(f"/repos/{repo}/pulls/comments"):
        n = int(c["pull_request_url"].rsplit("/", 1)[1])
        write(out_dir, f"pr-{n}-review-{c['id']}.txt",
              f"PR #{n} review comment {c['html_url']}\nauthor: {c['user']['login']}\nfile: {c.get('path')}",
              c.get("body"))
    print(f"{len(pulls)} PRs, {len(os.listdir(out_dir))} text items -> {out_dir}")


if __name__ == "__main__":
    main()
