---
name: governance-review
description: Review DAO governance proposals and proposal drafts — red-team analysis, funding and grant applications, incentive programs, parameter or contract changes, security council and treasury actions, and pre-submission feedback on your own drafts. Produces a structured critique, a forum-ready reviewer reply, a vote rationale, or line-level draft edits. Use this skill whenever the user shares a governance forum post, Snapshot/Tally proposal, AIP/1IP/CIP-style document, grant pitch, or a draft they intend to post to a DAO, or asks how to vote, whether a proposal holds up, or to "red-team", "review", "rev", or "tear apart" a proposal — even if they don't say "governance".
---

# Governance proposal review

The job is to find what would make this proposal fail, harm the DAO, or be rejected — before voters or attackers do. Be specific and adversarial, but fair: every criticism names the passage, the mechanism of failure, and a fix or a question the author must answer.

## 1. Establish context first

Get these before judging; ask only for what cannot be found:

- **Mode.** *External review* (someone else's proposal: user is a delegate/reviewer) or *author review* (user's own draft, pre-submission). Mode changes the output, not the rigor.
- **The full text.** Fetch forum/Snapshot/Tally links. If only a summary is given, say the review is limited to it.
- **DAO and process.** Which DAO, which proposal type (e.g. fast-track vs standard, temp check vs on-chain), and the *current* process rules. Fetch the DAO's governance docs or forum process post; do not rely on remembered rules — thresholds, quorums and timelines change.
- **Stake of the user.** Does the user, their organisation, or an affiliate delegate, receive funds, hold roles (signer, council, service provider) or compete with the proposer? If yes, conflict-of-interest handling (section 4) is mandatory, not optional.

## 2. Run the review

Read `references/review-framework.md` and work through every lens. Skip a lens only by stating why it doesn't apply. Rank findings:

- **Blocking** — the proposal should not pass as written (e.g. unverifiable execution, unbounded spend, missing exit path, undisclosed conflict).
- **Major** — passes only with changes (weak milestones, optimistic assumptions carrying the economics, unclear accountability).
- **Minor** — clarity, formatting, missing links.

Quantify wherever the proposal gives numbers: recompute totals, cost per outcome, runway, share of treasury, emissions vs expected revenue. Show the arithmetic. If a number cannot be checked, say so.

## 3. Verify on-chain claims

When the proposal includes addresses, calldata, contract upgrades, treasury balances or prior-performance claims, verify rather than trust. If the `onchain-review` skill is available, use it (contract verification, proxy implementation, Safe signers, historical transfers). Decode calldata and check that it does exactly what the text says — nothing more. Mismatches between text and calldata are always Blocking.

## 4. Conflicts of interest

If the user or anyone the proposal benefits has an interest: state it in the first paragraph of any output meant for publication, separate the user's financial interest from the analysis, and note whether the user should abstain on the vote. In author mode, check the draft itself discloses every conflict of the proposer (delegation held, other grants, roles, related entities).

## 5. Produce the output

Pick the format from `references/output-templates.md` that matches what the user asked for; default to the **structured review**. Rules for every format:

- Lead with the verdict and the single strongest objection.
- Quote proposal text sparingly (short fragments) and point to section names.
- Separate facts (from the proposal, docs, or chain) from judgement; label guesses and contested points as such.
- Tone for public posts: direct, not hostile, no sarcasm; criticise mechanisms, not people.
- End with concrete asks: what must change for the user to support it.

## Guardrails

- Don't invent DAO rules, precedents, prior votes, or delegate positions. Fetch or say unknown.
- Don't give a "for" recommendation just because issues are minor-only if a blocking question is still unanswered.
- Reviewing a competitor's proposal: apply the same bar you'd apply to the user's own.
