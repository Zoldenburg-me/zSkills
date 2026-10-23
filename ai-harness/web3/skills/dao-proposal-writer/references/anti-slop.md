# Anti-slop rules for governance proposals

Delegates read dozens of posts a week. The proposals that got passed and
remembered from 2020–2022 (Uniswap's Arbitrum deployment, Compound's
Gauntlet parameter changes, ENS's EP series, Aave's asset listings) share
one habit: **every sentence carries a fact the reader didn't have yet.**
AI drafts break that habit in three predictable ways, plus a vocabulary
problem. This file explains each so you can recognise it, not just grep for it.

`scripts/slop_check.py` catches the mechanical cases. The judgment cases
below it can't catch; those are on you.

## Contents
1. Reaffirmation (saying it again)
2. Reverification (the draft vouching for itself)
3. Context bleed (old drafts and the chat leaking in)
4. Vocabulary and framing
5. Formatting tells
6. Before/after rewrites

---

## 1. Reaffirmation

**What it looks like.** The Summary states the ask. The Motivation opens by
restating the ask. Each section ends with a sentence that re-explains why
the section matters. A "Conclusion" or "Key takeaways" block repeats the
Summary. Phrases: *as mentioned above, to reiterate, in summary, it is
important to note, to be clear, once again, this proposal aims to*.

**Why it hurts.** Delegates skim. Repetition makes them think they missed
something, then makes them stop reading. It also hides the real content:
a 1,200-word post with 400 words of signal reads as weak.

**Rule.** Each fact lives in exactly one section:

| Fact | Its one home |
| --- | --- |
| What is being asked, how much, from whom | Summary / Abstract (1–3 sentences) |
| Why now, what problem, evidence | Motivation |
| Why this design over the alternatives | Rationale |
| Exact actions, addresses, parameters, calldata | Specification |
| Money and its breakdown | Budget / Cost |
| Dates | Timeline |

The Summary is the only place a fact appears in brief. Nothing restates it
afterwards. The post ends on its last actionable section (Cost, Timeline,
Vote options, or Next steps), never on a recap.

Judgment cases the linter misses:
- A Motivation paragraph whose first sentence paraphrases the Summary. Delete
  the sentence; start with the evidence.
- A section closing on "This ensures that the DAO ..." which re-sells the
  section. Delete it.
- The same number given in three places. Keep it in Budget; elsewhere refer
  by name ("the budget below").

## 2. Reverification

**What it looks like.** "All figures have been verified." "(confirmed)"
"We double-checked the addresses." Checkmark emoji next to items. "To the
best of our knowledge." "Accurate as of writing" sprinkled per section.

**Why it hurts.** The author's assurance is worth nothing to a delegate;
the source is. Self-vouching reads as defensive and, if anything is wrong,
as dishonest.

**Rule.** Replace every assurance with the thing that makes it checkable:
- a link to the dashboard, Dune query, Etherscan/Arbiscan page, Tally/Snapshot
  vote, or audit report;
- a block number or date for every on-chain figure, stated **once** in a
  "Data as of block N / YYYY-MM-DD" line under the table it belongs to;
- for an address: the address in full, in code formatting, with the
  explorer link. No "verified" tag.

If something is genuinely unknown, say exactly what and when it will be
known: "Final audit cost depends on the auditor's quote, expected 14 Nov;
the cap is 40,000 USDC." Not "to the best of our knowledge".

## 3. Context bleed

**What it looks like.**
- Chat residue: "Here's the updated draft", "as you requested", "let me
  know if you'd like changes", "happy to adjust".
- Version residue: "Unlike the previous draft, the budget is now 30k",
  "we no longer propose X", "updated from v1".
- Stale facts: a number, date, team member or scope item that was in an
  earlier draft or an earlier proposal and was never re-checked.
- Inherited framing: re-arguing an objection that was raised in a call or
  DM the forum never saw.

**Why it hurts.** The reader never saw the conversation or the earlier
drafts. Comparisons against them are noise at best and confusing at worst
(they invite "what changed and why?" threads). Stale facts are how a
proposal ends up asking for the wrong amount on-chain.

**Rule.** The proposal body describes the current proposal only, as if
written fresh today.
- History belongs in a forum reply titled "Changes since vN" with a short
  bulleted diff, or in a single "Revision history" line at the very bottom
  if the DAO's template asks for one (Arbitrum and Maker sometimes do).
- When the author gives you an old draft or prior proposal, treat it as
  **source material, not as text to carry over**. Re-derive every number,
  date and address from the author's current inputs; if the author hasn't
  confirmed a fact for this version, list it under "Open questions for the
  author" in your reply to them, outside the proposal.
- Objections from private conversations get addressed only if the forum
  will plausibly raise them, and then as a plain Rationale point ("We
  considered X; it costs Y more because Z"), never as "some have asked".

## 4. Vocabulary and framing

Replace or delete:

| Instead of | Write |
| --- | --- |
| leverage, utilise | use |
| robust, seamless, cutting-edge, best-in-class | the measurable property (99.9% uptime, audited by X, 3s finality) |
| empower, foster, unlock potential, drive growth | what changes and for whom, with a number |
| ecosystem, landscape, space (as filler) | name the protocols, users or market |
| holistic, synergy, paradigm, transformative | delete |
| "We are excited to propose" | start with the action |
| "It's not just X — it's Y" | Y |
| "Why this matters:" signposts | a heading, or nothing |
| rhetorical questions ("What if delegates could…?") | the statement |
| triplets for rhythm ("transparent, accountable and efficient") | the one that is true and evidenced |

Prefer active voice with a named actor: "The Foundation multisig sends
150,000 ARB to …" beats "Funds will be transferred …".

Hedges: allow one where uncertainty is real, and quantify it. Delete
"potentially", "may help to", "could contribute towards" when no
uncertainty is being communicated.

## 5. Formatting tells

- **Emoji** in headings or bullets: none. (Pre-2023 professional proposals
  essentially never used them.)
- **Em dashes**: fine occasionally. More than ~4 per 1,000 words reads as
  generated; use full stops.
- **Bold**: for the few values a voter must not miss (the amount, the vote
  options). Not for every list lead-in.
- **Nested bullets**: one level. If you need two, it's a table or a
  paragraph.
- **Headings**: the DAO template's headings, in its order, in its case.
  Don't invent "Overview", "Introduction", "Executive Summary" on top of
  "Summary".
- **Tables**: for parameters (current → proposed), budgets (line, amount,
  rationale) and milestones (deliverable, date, payment). Not for prose.

## 6. Before/after rewrites

Figures in these rewrites are illustrative. In a real draft every number
comes from the author or a cited source.

**Summary**

> Before: This proposal aims to empower the Arbitrum ecosystem by
> leveraging a robust grants framework that fosters innovation and drives
> sustainable growth. It's not just funding — it's an investment in the
> future of the DAO.

> After: Fund a 6-month grants program for Arbitrum-native analytics
> tools: 300,000 ARB, released in three milestone tranches by a 3-of-5
> multisig. Grants are capped at 25,000 ARB each.

**Motivation opener**

> Before: As mentioned above, analytics tooling is pivotal. It's
> important to note that the current landscape is fragmented.

> After: Of the 41 dashboards linked from the DAO docs, 17 no longer
> load (checked 2022-09-12). Delegates currently rely on two
> community-maintained Dune dashboards with no funding.

**Specification with context bleed**

> Before: Compared to the previous draft, we have reduced the budget to
> 30k (verified) and removed the marketing line item as requested.

> After: | Line | Amount (USDC) |
> | --- | --- |
> | Engineering, 2 FTE × 3 months | 24,000 |
> | Hosting and RPC | 3,000 |
> | Audit | 3,000 |
> | **Total** | **30,000** |
>
> (The removed marketing line goes in a "Changes since v1" forum reply,
> not here.)

**Ending**

> Before: ## Conclusion — In summary, this proposal will empower
> delegates… We look forward to your feedback!

> After: end on the last real section, e.g.
> ## Next steps — Temp Check on Snapshot from 3 Oct to 8 Oct. If it
> passes with a "For" majority, an on-chain proposal follows on 15 Oct.
