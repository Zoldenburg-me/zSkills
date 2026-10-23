#!/usr/bin/env python3
"""Lint a governance proposal draft for AI-writing tells.

Usage:
    python3 slop_check.py DRAFT.md [--dao uniswap|ens|arbitrum|1inch|aave|compound|optimism|maker|lido|gitcoin|generic]

Checks:
  * restatement        - phrases that re-announce or re-summarise what was already said
  * reverification     - the draft vouching for itself ("verified", "double-checked", checkmarks)
  * context-bleed      - leftovers from the drafting conversation or earlier versions
  * filler             - vocabulary that carries no information in a proposal
  * structure          - missing sections, oversized summary, duplicated sentences,
                         summary repeated in a closing section, emoji headings,
                         dash and bold density, open placeholders
  * numbers            - table "Total" rows that do not equal the rows above

Exit status: 1 if any ERROR, 2 if the only blockers are open [TBD]
placeholders (fine for a draft, not for posting), else 0. Stdlib only.
"""
import argparse
import re
import sys
from collections import Counter

# (regex, category, severity, advice)
PATTERNS = [
    # --- restatement / reaffirmation -------------------------------------
    (r"\bto (?:reiterate|recap|summari[sz]e)\b", "restatement", "ERROR", "Say it once, in the section where it belongs."),
    (r"\bin (?:summary|conclusion|short|closing)\b", "restatement", "ERROR", "Drop the wrap-up; the Summary section already exists."),
    (r"\bas (?:mentioned|noted|stated|discussed|outlined|described|highlighted) (?:above|earlier|previously|before)\b", "restatement", "ERROR", "Link the section or delete the back-reference."),
    (r"\b(?:it is|it's) (?:important|worth|crucial|essential) (?:to note|noting|to highlight|to emphasi[sz]e|to remember)\b", "restatement", "ERROR", "State the fact directly."),
    (r"\b(?:to be clear|let me be clear|to clarify|simply put|put simply|in other words|that is to say)\b", "restatement", "WARN", "Usually precedes a restatement; write the clear version once."),
    (r"\b(?:key takeaways?|tl;?dr of the above|bottom line)\b", "restatement", "WARN", "A takeaway block repeats the Summary."),
    (r"\bthis proposal (?:aims|seeks|intends|is designed) to\b", "restatement", "WARN", "Use the verb: 'This proposal funds/changes/deploys ...'."),
    (r"\bonce again\b|\bagain,\s", "restatement", "WARN", "Signals repetition."),
    # --- reverification / self-vouching ----------------------------------
    (r"\b(?:we|i) (?:have )?(?:double|triple)[- ]checked\b", "reverification", "ERROR", "Readers check; cite the source instead."),
    (r"\b(?:verified|confirmed|validated|fact-checked)\s*(?:above|below|again|twice|as accurate|for accuracy)\b", "reverification", "ERROR", "Replace with a link to the data or the transaction."),
    (r"\(\s*(?:verified|confirmed|checked)\s*\)", "reverification", "ERROR", "Inline 'verified' tags are noise; link the source."),
    (r"[✅✔☑]", "reverification", "ERROR", "Checkmark emoji; remove."),
    (r"\b(?:to be (?:confirmed|verified|checked)|must (?:be )?(?:confirm|verif)\w*|(?:appears|believed|assumed) to (?:be|consist|hold|sit)\b)", "reverification", "WARN", "Readable on-chain? Check it with onchain-review and state the result; otherwise move it to Open questions."),
    (r"\b(?:to the best of (?:our|my) knowledge|as far as (?:we|i) (?:can tell|know)|if (?:we|i) understand correctly)\b", "reverification", "WARN", "Either you know it (cite it) or say exactly what is unknown."),
    (r"\b(?:please (?:verify|double-check|note)|note that|note:)\b", "reverification", "WARN", "Usually filler. If it matters, make it a sentence of its own."),
    (r"\b(?:accurate|correct) as of (?:the time of )?writing\b", "reverification", "WARN", "Give the date or block number once, in the data source line."),
    # --- context bleed (drafting history leaking into the post) ----------
    (r"\b(?:as (?:you|we) (?:requested|asked|discussed)|per your (?:request|instructions|feedback))\b", "context-bleed", "ERROR", "Conversation residue; the reader was not in that conversation."),
    (r"\b(?:previous|earlier|prior|original|last) (?:draft|version|iteration|revision)\b", "context-bleed", "ERROR", "The post describes the current proposal only. Put changes in a forum reply."),
    (r"\b(?:updated|revised|changed) (?:from|since) (?:v\d|version|the draft)\b", "context-bleed", "ERROR", "Move version history to a 'Changes since vN' forum reply."),
    (r"\b(?:here(?:'s| is) (?:the|a|your) (?:updated|revised|final|draft))\b", "context-bleed", "ERROR", "Chat preamble; delete."),
    (r"\b(?:i hope this helps|let me know if|feel free to|happy to (?:adjust|revise|help))\b", "context-bleed", "ERROR", "Chat sign-off; delete."),
    (r"\b(?:as an ai|language model|i cannot browse)\b", "context-bleed", "ERROR", "Delete."),
    (r"\b(?:no longer|instead of the previously|now (?:reduced|increased|changed|removed))\b[^.]{0,40}?\b(?:proposed|suggested|planned|budget)?", "context-bleed", "WARN", "Check whether this compares against an older draft the reader never saw."),
    (r"\bbefore (?:publication|publishing|posting|(?:this|it) is (?:published|posted|formali[sz]ed|submitted))\b", "context-bleed", "ERROR", "A note to the author left in the post. Do the step, then delete the note."),
    (r"\b(?:see|in|on) the [^.\n]{0,50}?\btab\b", "context-bleed", "ERROR", "Refers to a tab in the drafting document; the forum reader has no tabs. Link or inline it."),
    (r"\[(?:timeline|date|source|note|ref)\s*:[^\]]*\]", "context-bleed", "WARN", "Bracketed drafting note. State the date or block plainly, once."),
    # --- filler vocabulary ------------------------------------------------
    (r"\b(?:delve|delving|tapestry|testament to|realm|landscape|paradigm|synerg(?:y|ies|istic)|holistic|game[- ]changer|cutting[- ]edge|groundbreaking|revolutioni[sz]e|unlock(?:s|ing)? (?:the )?(?:full )?potential|seamless(?:ly)?|robust|pivotal|transformative|empower(?:s|ing)?|foster(?:s|ing)?|spearhead|bolster|elevate|navigate the|ever[- ]evolving|fast[- ]paced|vibrant|thriving|in today's)\b", "filler", "WARN", "Replace with the concrete claim or delete."),
    (r"\b(?:leverag(?:e|es|ing)|utili[sz](?:e|es|ing))\b", "filler", "WARN", "Use 'use'."),
    (r"\b(?:not (?:just|only|merely) [^.]{1,60}?,? but (?:also )?)", "filler", "WARN", "'Not just X but Y' framing; state Y."),
    (r"\b(?:isn't|is not|aren't|are not) (?:just |merely |simply )?(?:about )?[^.]{1,40}?\s[—-]{1,2}\s?(?:it's|it is|they're|they are)\b", "filler", "WARN", "'It's not X - it's Y' framing; state Y."),
    (r"\b(?:why (?:this|it) matters|the bottom line|here's (?:why|the thing|what))\b", "filler", "WARN", "Blog-style signposting; let the section heading do this."),
    (r"\b(?:we are (?:excited|thrilled|delighted|pleased|proud) to)\b", "filler", "WARN", "Tone; start with the action."),
]

REQUIRED = {
    "generic":  ["summary|abstract|tl;?dr", "motivation|rationale|problem|background", "specification|implementation|proposal|details|scope|deliverables", "cost|budget|ask|funding|financ"],
    "uniswap":  ["summary|tl;?dr", "background|motivation|purpose|problem", "specification|proposal|solution|details"],
    "ens":      ["summary|description", "abstract", "specification"],
    "arbitrum": ["abstract", "motivation", "rationale", "specifications?", "steps to implement", "timeline", "overall cost|cost", "conflicts? of interest"],
    "1inch":    ["simple summary", "abstract", "motivation", "specification", "rationale", "considerations"],
    "aave":     ["simple summary|summary", "motivation", "specification", "disclaimer|copyright|next steps"],
    "compound": ["simple summary|summary|tl;?dr", "abstract|motivation|background|purpose", "specification|proposal|recommendation", "next steps"],
    "optimism": ["project|proposal overview", "distribution|use of funds|budget|allocation", "milestones?|kpis?|success"],
    "maker":    ["sentence summary", "paragraph summary", "motivation", "specification|proposal details"],
    "lido":     ["simple summary", "abstract", "motivation", "specification"],
    "gitcoin":  ["summary", "abstract", "motivation", "specification", "benefits", "drawbacks", "vote"],
}

SUMMARY_HEADINGS = re.compile(r"^#{1,4}\s*(?:simple summary|summary|abstract|tl;?dr|sentence summary)\b", re.I)
CLOSING_HEADINGS = re.compile(r"^#{1,4}\s*(?:conclusion|closing|summary of|final thoughts|wrap[- ]?up|recap|key takeaways)\b", re.I)
HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿\U0001F000-\U0001F2FF]")
PLACEHOLDER = re.compile(r"\[(?:TBD|TODO|XX+|INSERT[^\]]*|PLACEHOLDER)\]|\bTBD\b|\bXX+\b|0x\.\.\.|<[A-Z_ ]{3,}>|<[A-Za-z][^<>\n]*\s[^<>\n]*>")


def words(text):
    return re.findall(r"[A-Za-z0-9']+", text)


def sentences(text):
    flat = re.sub(r"\s+", " ", text)
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", flat) if len(words(s)) >= 6]


def shingles(text, n=4):
    w = [x.lower() for x in words(text)]
    return {tuple(w[i:i + n]) for i in range(max(0, len(w) - n + 1))}


def sections(lines):
    """Return list of (heading_text, start_line_no, body_text)."""
    out, cur, start, buf = [], "(preamble)", 1, []
    in_code = False
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_code = not in_code
        m = HEADING.match(line) if not in_code else None
        if m:
            out.append((cur, start, "\n".join(buf)))
            cur, start, buf = line.strip(), i, []
        else:
            buf.append(line)
    out.append((cur, start, "\n".join(buf)))
    return out


def strip_code(lines):
    res, in_code = [], False
    for line in lines:
        if line.strip().startswith("```"):
            in_code = not in_code
            res.append("")
            continue
        res.append("" if in_code else re.sub(r"`[^`]*`", "", line))
    return res


NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def table_totals(raw):
    """Yield (line_no, column, stated, computed) for Total rows that don't add up."""
    rows, start = [], None
    for i, line in enumerate(raw + [""], 1):
        if line.strip().startswith("|"):
            if start is None:
                start = i
            rows.append((i, [c.strip() for c in line.strip().strip("|").split("|")]))
            continue
        if rows:
            body = [(n, r) for n, r in rows if not all(re.fullmatch(r":?-{2,}:?", c or "--") for c in r)][1:]
            items = []
            for n, r in body:
                if r and re.search(r"\btotal\b", r[0].replace("*", ""), re.I):
                    for col in range(1, len(r)):
                        m = NUM.search(r[col].replace("*", ""))
                        if not m:
                            continue
                        vals = []
                        for _, ir in items:
                            if col < len(ir):
                                im = NUM.search(ir[col].replace("*", ""))
                                if im:
                                    vals.append(float(im.group(0).replace(",", "")))
                        stated = float(m.group(0).replace(",", ""))
                        tol = max(0.5, abs(stated) * 0.001)
                        # a total may cover all rows above it or only the last k (a subtotal)
                        runs = [sum(vals[-k:]) for k in range(2, len(vals) + 1)]
                        if len(vals) >= 2 and not any(abs(r - stated) <= tol for r in runs):
                            yield n, col, stated, sum(vals)
                    items = []
                else:
                    items.append((n, r))
        rows, start = [], None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("draft")
    ap.add_argument("--dao", default="generic", choices=sorted(REQUIRED))
    args = ap.parse_args()

    raw = open(args.draft, encoding="utf-8").read().splitlines()
    lines = strip_code(raw)
    findings = []

    def add(sev, line, cat, msg):
        findings.append((sev, line, cat, msg))

    # phrase patterns
    compiled = [(re.compile(p, re.I), c, s, a) for p, c, s, a in PATTERNS]
    for i, line in enumerate(lines, 1):
        for rx, cat, sev, advice in compiled:
            for m in rx.finditer(line):
                add(sev, i, cat, f'"{m.group(0).strip()}" - {advice}')

    body = "\n".join(lines)
    n_words = len(words(body)) or 1

    # dash density
    dashes = len(re.findall(r"—|\s--\s", body))
    per_k = dashes * 1000 / n_words
    if per_k > 4:
        add("WARN", 0, "structure", f"{dashes} em dash(es) ({per_k:.1f} per 1000 words). Use full stops, commas or parentheses.")

    # deferred verification: the proposal tells someone else to check its facts
    verif = len(re.findall(r"\b(?:verif\w*|confirm\w*|double[- ]check\w*|byte[- ]for[- ]byte)\b", body, re.I))
    if verif * 1000 / n_words > 8:
        add("WARN", 0, "reverification", f"{verif} verify/confirm words ({verif * 1000 / n_words:.0f} per 1000). Run the on-chain reads before posting (onchain-review skill) and state the results with a block number and links; keep one execution-time check, not a running instruction.")

    # bold density
    bolds = len(re.findall(r"\*\*[^*]+\*\*", body))
    if bolds > 3 and bolds * 1000 / n_words > 12:
        add("WARN", 0, "structure", f"{bolds} bold spans. Bold only the few values a voter must not miss.")

    # headings: emoji, required sections
    heads = [(i, HEADING.match(l)) for i, l in enumerate(lines, 1)]
    heads = [(i, m.group(2)) for i, m in heads if m]
    for i, h in heads:
        if EMOJI.search(h):
            add("ERROR", i, "structure", f'Emoji in heading "{h.strip()}".')
    head_text = " | ".join(h.lower() for _, h in heads)
    for req in REQUIRED[args.dao]:
        if not re.search(req, head_text):
            add("ERROR", 0, "structure", f"No section heading matching /{req}/ (template: {args.dao}).")

    # placeholders
    for i, line in enumerate(lines, 1):
        for m in PLACEHOLDER.finditer(line):
            add("TODO", i, "pending", f'Open placeholder "{m.group(0)}" - needs a value from the author before posting.')

    # budget arithmetic
    for n, col, stated, computed in table_totals(raw):
        add("ERROR", n, "numbers", f"Total in column {col + 1} is {stated:,.2f} but the rows above sum to {computed:,.2f}.")

    secs = sections(lines)
    # summary length
    summary = None
    for head, start, text in secs:
        if SUMMARY_HEADINGS.match(head):
            summary = (head, start, text)
            wc = len(words(text))
            limit = 40 if re.search(r"simple|sentence|tl;?dr", head, re.I) else 120
            if wc > limit:
                add("WARN", start, "structure", f"{head.strip()} is {wc} words; aim for <= {limit}.")
            break

    # closing section that repeats the summary
    for head, start, text in secs:
        if CLOSING_HEADINGS.match(head):
            add("WARN", start, "restatement", f'Closing section "{head.strip()}". Keep it only if it adds something new (a commitment, a sunset, a next step); otherwise end on the last actionable section.')
            if summary:
                a, b = shingles(summary[2]), shingles(text)
                if a and b and len(a & b) / min(len(a), len(b)) > 0.25:
                    add("ERROR", start, "restatement", "Closing section re-uses the Summary's wording.")

    # duplicated / near-duplicated sentences across the document
    prose = "\n".join(l for l in lines if not HEADING.match(l) and not EMOJI.fullmatch(l.strip() or "x"))
    sents = sentences(prose)
    seen = {}
    for s in sents:
        key = frozenset(shingles(s, 3))
        if not key:
            continue
        for prev, pkey in seen.items():
            overlap = len(key & pkey) / min(len(key), len(pkey))
            if overlap > 0.6:
                add("WARN", 0, "restatement", f'Near-duplicate sentences:\n      a) "{prev[:110]}"\n      b) "{s[:110]}"')
                break
        else:
            seen[s] = key

    # repeated content words (same claim hammered)
    stop = set("the a an and or of to in for on with by is are be this that it as at from we our will can its their which these those was were has have not".split())
    common = Counter(w.lower() for w in words(body) if len(w) > 3 and w.lower() not in stop)

    # report
    order = {"ERROR": 0, "WARN": 1, "TODO": 2}
    findings.sort(key=lambda f: (order[f[0]], f[1]))
    if not findings:
        print(f"clean: {n_words} words, no findings")
        return 0
    for sev, line, cat, msg in findings:
        loc = f"L{line}" if line else "doc"
        print(f"{sev:5} {loc:>5}  [{cat}] {msg}")
    errs = sum(1 for f in findings if f[0] == "ERROR")
    warns = sum(1 for f in findings if f[0] == "WARN")
    todos = sum(1 for f in findings if f[0] == "TODO")
    print(f"\n{errs} error(s), {warns} warning(s), {todos} open placeholder(s) in {n_words} words. Top terms: " +
          ", ".join(f"{w}({c})" for w, c in common.most_common(6)))
    if errs:
        return 1
    return 2 if todos else 0


if __name__ == "__main__":
    sys.exit(main())
