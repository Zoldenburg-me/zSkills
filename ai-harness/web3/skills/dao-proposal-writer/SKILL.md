---
name: "dao-proposal-writer"
description: Write and tighten DAO governance proposals to the professional standard of pre-2023 forum proposals (Uniswap, ENS, Arbitrum, Aave, Compound, 1inch, Optimism, Maker, Lido, Gitcoin), using the target DAO's own template and with no AI padding — no restating, no self-verification, no leftovers from earlier drafts or chats. Use this whenever a DAOplomats member wants to draft, rewrite, shorten, clean up or format a governance proposal, temp check, RFC, AIP/EP/1IP/ARFC, grant or funding request, delegate program, parameter change, or a forum post to a DAO, even if they only paste notes, bullet points, an old draft or a call transcript. Checks addresses, balances, positions and Safe setups on-chain with onchain-review before writing, so the proposal states facts instead of asking readers to verify them. For critiquing someone else's proposal or deciding a vote, use governance-review instead; this skill writes, governance-review red-teams.
---

# DAO proposal writer (DAOplomats standard)

Proposals that passed and aged well before the AI boom read like
engineering change requests: a one-line ask, the evidence, the exact
actions, the money, the dates. Nothing said twice. This skill produces
that, in the target DAO's own format.

The three failure modes this skill exists to prevent:

1. **Reaffirmation** — the summary restated in the motivation, sections that
   re-sell themselves, a closing recap.
2. **Reverification** — "verified", "double-checked", ✅, "to the best of our
   knowledge" in place of a link to the source.
3. **Context bleed** — chat residue ("here's the updated draft"), comparisons
   to earlier drafts the reader never saw, and stale facts carried over from
   old proposals or previous versions.

`references/anti-slop.md` explains each with before/after rewrites. Read it
the first time you use this skill in a conversation.

## Workflow

### 1. Pin down the target and the stage

You need: the DAO, the stage (idea / temp check / RFC / on-chain), and the
proposal type (funding, parameter change, contract upgrade, delegate or
council program, social/constitutional). Infer them from what the member
gave you; ask only for what you can't infer.

Then open `references/dao-templates.md` and use that DAO's headings, in its
order, with its title format and metadata. If the DAO isn't listed, use the
DAOplomats default skeleton below and tell the member to check the forum's
pinned template (most Discourse forums pin one in "Proposals" or "Governance").

### 2. Collect facts, not prose

Pull every fact out of the member's material into a working list: the ask,
amounts, recipient addresses, parameters (current → proposed), dates,
milestones, people/entities and their roles, prior votes and forum links,
data and its source.

Treat old drafts, prior proposals and transcripts as **source material**,
not as text to carry forward. For each fact, check it belongs to the
current version. If a number, date, address or name appears only in older
material, or two sources disagree, don't guess and don't silently pick one:
put it in an "Open questions" list for the member (step 5).

Never invent figures, addresses, endorsements, audit results or
precedents. Where a value is missing, leave a visible `[TBD: what is
needed]` marker so the draft can't be posted by accident.

### 2b. Verify on-chain facts before writing

If the proposal rests on anything that lives on-chain, check it now with
the `onchain-review` skill. Don't write it into the proposal as a task
for someone else. This applies to:

- addresses (treasury, recipient, executor Safe, contracts)
- balances or positions (LP NFTs, vaults, streams)
- current parameter values
- Safe signers and modules
- calldata
- claims about past transactions or votes

A proposal that says "to be confirmed", "must verify", "appears to be" or
"believed to be" about something readable on a block explorer reads as
unfinished, and it hands the reader work the author should have done.

Invoke `onchain-review` (installed as `anthropic-skills:onchain-review` on
claude.ai). Then follow `references/onchain-checks.md`, which covers:

- what to read for each proposal type,
- how to cite the reads: one "Data as of block N, UTC time" line, with
  explorer links and no "verified" tags,
- who decides when the chain and the member disagree: the chain decides
  on-chain state; the member decides intent (recipient, amount), and you
  ask them.

If a check can't run (no connector, blocked host, off-chain fact), the
fact goes to Open questions with the exact read that would settle it. The
value stays a `[TBD]` in the draft.

Signers still re-check amounts and simulate at execution. That is one
sentence in the Specification, never a checklist inside the proposal.

### 3. Write each section once

Assign every fact to exactly one section (Summary is the only place a fact
may appear in brief). Then write:

- **Title**: the DAO's prefix format + a verb phrase naming the action and
  the scale. `[Temp Check] Deploy Uniswap v3 to Celo`, not
  `Proposal: An Exciting Opportunity for Growth`.
- **Summary / Abstract**: 1–3 sentences. What is being done, by whom, for
  how much, by when. Someone who reads only this knows what a "For" vote does.
- **Motivation**: the problem with evidence (numbers with sources, links to
  prior discussion). Start with the evidence, not a paraphrase of the summary.
- **Rationale** (where the template has it): the alternatives considered and
  why this one. Short. This is where objections are pre-empted, plainly.
- **Specification**: exact and checkable. Full addresses in code
  formatting with explorer links, parameter tables (current → proposed),
  calldata or a link to it, who executes, which multisig/timelock.
- **Budget / Cost**: a table: line, amount, basis. Token, chain, and the
  conversion date if USD-denominated. Vesting/streaming and clawback terms.
- **Timeline / Milestones / KPIs**: dated, measurable, tied to payments.
- **Vote options / Next steps**: what each option does, and the next stage.

If the template has no vote-options or next-steps heading, put what each
option does in the last implementation section (Arbitrum: Steps to
Implement) rather than adding a heading.

Link prior forum threads and votes instead of re-summarising them. Name the
author's interests once, in a Disclosure line if the template has none
(DAOplomats is a delegate; if the author is compensated by, delegates for,
or is a recipient under this proposal, say so).

Substance a delegate will look for (the same lenses `governance-review`
applies, so a draft that covers them survives review). Each goes in the
section the template gives it, stated once:

- **What a For vote changes**, explainable in two sentences.
- **Why the DAO and why now**, and what happens if it does nothing.
- **Payment tied to delivery**: tranches or streams, milestones that are
  dated and externally checkable, clawback or return of unspent funds.
- **Exit path**: who can stop it, under what condition, and how funds and
  permissions come back.
- **Execution**: executor, multisig signers and threshold, or the calldata
  link. The text must describe exactly what the calldata does.
- **The three hardest questions** a sceptical delegate will ask, answered
  in Rationale or Considerations as plain statements, not as a FAQ. E.g.
  the question "Why not fold this into the existing delegate program?"
  becomes "The Delegate Incentive Program pays existing delegates for
  participation; it has no onboarding budget. This program covers that gap
  only."

Style: short declarative sentences, active voice with named actors, "we"
for the authors, no emoji, no hype vocabulary, bold only for the amount and
the vote options. Write in the register of a technical memo.

### 4. Check the draft

Run the linter. Fix every ERROR, and fix WARNs unless you can say why one
is fine. Open `[TBD]` placeholders are reported as TODO (exit code 2): they
stay until the member supplies the value, and the draft isn't ready to post
until the linter exits 0.

```bash
python3 <skill-dir>/scripts/slop_check.py draft.md --dao <uniswap|ens|arbitrum|1inch|aave|compound|optimism|maker|lido|gitcoin|generic>
```

Then the judgment pass the script can't do. For each, re-read the draft:

- Delete any sentence whose information already appeared earlier.
- Read the Summary alone. Does it say what a For vote does and costs?
- Every number and address: is it from the member's current inputs, a
  cited source, or an on-chain read from step 2b, and does it match
  everywhere it's referenced?
- Any "confirm", "verify", "to be confirmed", "appears", "believed" left
  about on-chain state means step 2b was skipped. Go back and run it.
- Anything comparing to "before", "previously", "now", "no longer": is the
  comparison against something the forum actually saw?
- Would cutting this paragraph lose a fact? If not, cut it.

Then offer the member a red-team pass with the `governance-review` skill in
author mode (its "Draft feedback" format). Don't run it unasked: it is a
separate, adversarial read and the member should choose it. If its
findings lead to edits, apply them with this skill's rules, so fixes don't
reintroduce restatement or self-verification.

Target length: most pre-2023 proposals that passed ran 400–1,200 words
before tables and code. Longer only when the specification needs it.

### 5. Hand it back

Give the member:

1. The proposal in Markdown, ready to paste into Discourse. Nothing above
   or below it inside the code/quote block.
2. Outside the proposal, a short **Open questions** list: every `[TBD]`,
   every conflict between sources, every fact you couldn't confirm for
   this version.
3. If they gave you an earlier version **that was posted publicly**: a
   **Changes since vN** list they can
   post as a forum reply. This list never goes into the proposal body.

Don't append a recap of what you did or offers to adjust beyond one line.

## DAOplomats default skeleton

Use when the DAO has no template or the member asks for a generic one.

```markdown
# [Stage] Verb phrase naming the action and its scale

**Author:** DAOplomats (forum handle)  ·  **Date:** YYYY-MM-DD  ·  **Stage:** Temp Check | RFC | On-chain
**Related:** [prior thread](link), [prior vote](link)

## Summary
One to three sentences.

## Motivation
Problem and evidence, with sources.

## Rationale
Alternatives considered; why this one.

## Specification
Exact actions. Addresses, parameters (current → proposed), executor, calldata link.

## Budget
| Line | Amount | Basis |
| --- | --- | --- |
| ... | ... | ... |
| **Total** | **...** | |

## Timeline and milestones
| Milestone | Deliverable / KPI | Date | Payment |
| --- | --- | --- | --- |

## Risks
Each risk and its mitigation, one line each. Omit if none are material.

## Disclosure
Authors' relevant interests.

## Vote options
- **For**: what happens.
- **Against**: what happens.
- **Abstain**
```

Drop sections that would be empty (e.g. Budget on a no-cost parameter
change becomes one line: "No cost to the treasury."). Don't add sections the
template doesn't have.

## Reference files

- `references/dao-templates.md` — per-DAO title formats, stages, headings and
  metadata, with links to the official templates and well-written pre-2023
  examples. Read the section for the target DAO.
- `references/anti-slop.md` — the three failure modes in detail, vocabulary
  table, formatting tells, before/after rewrites.
- `references/onchain-checks.md` — what to read on-chain per proposal
  type, how to cite it, and what to do when chain and member disagree.
  Used with the `onchain-review` skill in step 2b.
- `scripts/slop_check.py` — linter for the mechanical cases: restatement,
  self-verification and chat/version residue phrases, missing template
  sections, oversized summary, duplicated sentences, emoji, open
  placeholders, and budget-table totals that don't add up.
