# DAO templates and pre-2023 reference proposals

These per-DAO formats were researched from the official process docs and
from the original forum posts (Discourse raw markdown, GitHub template
repos). Quotes are verbatim. Items marked *(unverified)* could not be
checked against a primary source.

Forums change their templates. Before drafting, look for a pinned
"template" or "how to propose" post in the DAO's forum. If it differs from
this file, follow the forum.

## Contents
- [Patterns shared by good pre-2023 proposals](#patterns-shared-by-good-pre-2023-proposals)
- [Uniswap](#uniswap) · [ENS](#ens) · [Arbitrum](#arbitrum) · [1inch](#1inch)
- [Aave](#aave) · [Compound](#compound) · [Optimism](#optimism)
- [MakerDAO](#makerdao) · [Lido](#lido) · [Gitcoin](#gitcoin)
- [Openers worth imitating](#openers-worth-imitating)

---

## Patterns shared by good pre-2023 proposals

- **The ask comes first.** The first sentence names the actor, the action
  and the scale: "A proposal to adjust five (5) total risk parameters …
  across four (4) Aave V2 assets."
- **Length scales with stakes.** Parameter and technical changes ran about
  450–750 words. Programs and budgets ran about 1,500–2,250 words. Nothing
  was padded to look thorough.
- **Parameters appear as current → proposed.** Writers used a three-column
  table (`Parameter | Current | Recommended`), arrow notation
  ("Reserve Factor 20% → 100%"), or "will be increased from 50 million DAI
  to 500 million DAI".
- **Addresses are full and labelled.** Each one carries its contract role
  and an explorer link (`aToken = [0x…](etherscan)`, "LendingPoolConfigurator
  (0x311B…)"). ENS names were used where they exist (`controller.ens.eth`).
- **Calldata was rarely written in the forum post.** It lived in the
  on-chain proposal or a GitHub PR, and the post linked to it.
- **Budgets give a bold headline figure, line items and a total.**
  - They use two denominations (token and USD) and say how the conversion
    price is set.
  - Unspent funds are returned. Caps, sunsets and milestone tranches are
    stated.
- **Prior discussion is linked, not retold.** At a later stage, feedback is
  summarised as "incorporated / not incorporated" and commenters are
  credited by @handle.
- **Disclosure is plain.** Committee members are listed with their
  affiliation and "holds UNI", and compensated authors say they are
  compensated.
- **Hedging is specific.** A proposal is framed as a "pilot" with a 120-day
  sunset, and writers say "we will cancel the vote should simulations
  change". Vague softeners are absent.
- **Voice is "we propose" or institutional.** Writers use "Gauntlet
  recommends …" or "This proposal …".
- **There are no emoji, no hype and no closing recap.** Where a Conclusion
  exists (Uniswap's and Compound's grants programs), it adds a commitment
  such as "the burden of proof will be on UGP to renew". It does not
  repeat the summary.

---

## Uniswap
**Forum:** gov.uniswap.org

**Process.**
- 2020-10-26 version: Temperature Check → Consensus Check → Governance
  Proposal ([process post](https://gov.uniswap.org/t/community-governance-process/7732)).
- Simplified on 2022-01-21 to **RFC → Temperature Check (Snapshot) → Formal
  Vote** ([revision](https://gov.uniswap.org/t/proposed-simplifications-to-the-uniswap-governance-process/15906)).
- The current stage names are in the latest process post. Check it.

**Title prefixes.** `[RFC] …`, `[Temperature Check] …`,
`[Consensus Check] …`, `Governance Proposal [UP###] — …`

**Required content.**
- There are no mandated headings.
- Snapshot polls must include a **"Make no change"** option.
- The process asks authors to "remain as impartial as possible" in the
  poll wording.
- A formal vote post links the polls, the earlier threads, and the code
  audit if there is one.

**Typical structure:** Summary → Background or Motivation → Proposal or
Specification → Budget, where there is one → Vote options → Next steps.
A later-stage post adds "Feedback incorporated" and "Feedback not
incorporated, and why".

**Examples.**
- [`[RFC] Uniswap Grants Program v0.1`](https://gov.uniswap.org/t/rfc-uniswap-grants-program-v0-1/9081)
  (2020-12-03):
  - Opens with a bold one-sentence purpose.
  - Hard budget cap ("$750K per quarter … limit of 2 quarters").
  - Hourly rate with a weekly cap.
  - Committee members listed with affiliation and holdings.
- [`[Consensus Check] "Fee Switch" Pilot`](https://gov.uniswap.org/t/consensus-check-fee-switch-pilot/17384)
  (2022-08-04):
  - Sections: Feedback incorporated / Responses to feedback not
    incorporated / Final specification / Vote.
  - The exact pools are listed, with a 120-day sunset.
- [`[Consensus Check] Fix the Cross Chain Messaging Bridge on Arbitrum`](https://gov.uniswap.org/t/18547)
  (2022-11-29):
  - Sections: Background / Problem / Solution.
  - Full addresses with Arbiscan links, and the alias arithmetic written
    out.

## ENS
**Forum:** discuss.ens.domains.
**Process docs:** https://docs.ens.domains/v/governance/process (current
version; the 2021–22 wording is *(unverified)*).

**Proposal types.**
- Executable
- Social
- Constitutional Amendment, which must include a diff of the constitution
  and needs two-thirds approval.

**Stages.** Temperature Check (forum, optional) → Draft Proposal (a PR to
`governance-docs` plus a forum post) → Active Proposal (Snapshot, or the
on-chain governor for executable proposals).

**Title format.** `[EPn] [Executable|Social] Title`. EP numbering became
term-based (EP2.1, EP3.4 …) after August 2022.

**Headings used in EPs.**
- A Status line, or a metadata table (Status, Discussion Thread, Votes).
- Then **Summary** (or Description), **Abstract**, **Specification**, and
  **Code** (for executable proposals).
- Motivation is folded into the Abstract.

**Examples.**
- [`[EP5] [Executable] Set the temporary premium start price to $100,000`](https://discuss.ens.domains/t/9336)
  (2022-01-06), about 440 words:
  - Summary in one sentence: "Increases the start price for the temporary
    premium added when names expire from $2,000 to $100,000."
  - A short bulleted data block.
  - Specification as numbered contract calls ("Call `setPriceOracle` on
    `controller.ens.eth` …").
- [`[EP14][Executable] Funding True Names Ltd`](https://discuss.ens.domains/t/13391)
  (2022-06-27):
  - The budget is given both annually and daily ($4,197,500 a year =
    $11,500 a day).
  - Cites the constitution article.
  - The specification names the recipient and the streaming contract
    address.

## Arbitrum
**Forum:** forum.arbitrum.foundation.
**Docs:** https://docs.arbitrum.foundation/how-tos/create-submit-dao-proposal
The DAO launched in March 2023, so every example is from 2023. The
template itself is sound.

**Types.**
- **Constitutional**: changes to the Constitution, chain software, or
  anything needing chain-owner permission. Core governor.
- **Non-Constitutional**: funds, grants, guidelines. Treasury governor.

**Stages.** Forum (at least 7 days) → Snapshot temperature check (1 week)
→ Tally on-chain vote.

**Title format.** No mandated prefix. Posts commonly lead with the type
or the stage, e.g. `[Non-Constitutional] …` or `[Proposal] AIP-x: …`
*(unverified as a rule)*. Match the most recent posts in the forum's
Proposals category.

**Headings, in order (the Constitution "encourages" these):**
1. **Abstract**: "Two or three sentences that summarize the AIP."
2. **Motivation**
3. **Rationale**: how the AIP fits the mission and the community values.
4. **Key Terms** (optional)
5. **Specifications**: platforms and technologies, alternate designs,
   related work.
6. **Steps to Implement**: cost, manpower and resources per step, plus
   legal documents for third-party payments.
7. **Timeline**
8. **Overall Cost**: fixed and recurring.
9. **Conflicts of Interest**

A resubmitted AIP adds: a link to the previous AIP, why it failed, what
changed, and new information. This is the one sanctioned place for version
history.

**Examples.**
- [AIP-1.1 Lockup, Budget, Transparency](https://forum.arbitrum.foundation/t/proposal-aip-1-1-lockup-budget-transparency/13360):
  - The abstract numbers the three actions.
  - The budget table has a bold total ($36,000,000) and a denomination
    note.
- [STIP](https://forum.arbitrum.foundation/t/arbitrums-short-term-incentive-program-arbitrum-improvement-proposal/16131):
  - "distribute up to 50,000,000 ARB …"
  - The Overall Cost is one line: "50,094,000 ARB."
  - Timeline lines are dated.
  - KPIs are bold-labelled bullets.

## 1inch
**Template:** https://gov.1inch.community/docs/governance/improvement-proposal-template
**Lifecycle:** https://gov.1inch.community/docs/governance/proposal-lifecycle

**Stages.**
1. Discussion
2. 1IP Formalization: the forum title takes the `[1RC]` prefix, and "a
   single 1IP contains a single proposal".
3. Temperature Check: a 3-day forum poll, with options "(Yes) In favor of
   this proposal." / "(No) Against this proposal.". **The text cannot be
   edited after this point** except to fix errata.
4. Snapshot (5 days)
5. Implementation

The 1IP number is assigned at stage 4.

**Headings, in order.**
1. **Simple Summary**: "a single sentence, or a bulleted list".
2. **Abstract**: "very terse and human-readable … Someone should be able
   to read only the abstract to get the gist."
3. **Motivation**
4. **Specification**: "detailed enough to allow for implementation by a
   development team".
5. **Rationale**: alternate designs considered, and the net benefit.
6. **Considerations** (mandatory):
   - Security: threats, risks, pitfalls.
   - Governance: revenue, treasury cost, voting, staking, tokenomics.
   - The qualifications of any third-party team being paid.

**Examples.**
- [1IP-08 Simple diversification mechanism for the DAO Treasury](https://gov.1inch.network/t/28)
  (2022-06-21)
- [1IP-09 Collect Treasury Revenue in 1INCH](https://gov.1inch.network/t/22)
  (2022-06-22)

Both are under about 800 words and embed the poll at the top. They use
"shall" in the specification and state exact price thresholds.

## Aave
**Forum:** governance.aave.com. **AIP repo:** github.com/aave/aip.

**Stages.**
- Before mid-2023: ARC (forum) → AIP (on-chain).
- After mid-2023: `[TEMP CHECK]` → `[ARFC]` → AIP (the framework post
  /t/13828 is dated 2023-06-27).

**ARFC / TEMP CHECK headings.**
- Header: Title, Author, Date (YYYY-MM-DD).
- Then **Summary**, **Motivation**, **Specification**, **Disclaimer**
  (compensation and conflicts), **Next Steps**, **Copyright** ("CC0").

**AIP front-matter.** `title` (44 characters or fewer), `author`,
`shortDescription`, `discussions`, `created`.
**AIP sections:** Simple Summary, Motivation, Specification, References,
Copyright. Older AIPs (2021–22) also had Abstract, Rationale, Test Cases
and Implementation.

**Examples.**
- [Gauntlet, ARC: Risk Parameter Updates 2022-04-22](https://governance.aave.com/t/arc-risk-parameter-updates-2022-04-22/7911):
  - Simple summary in one sentence.
  - `Parameter | Current Value | Recommended Value` table.
  - A volatility data table and a link to the risk dashboard.
  - "Next Steps: Targeting an AIP on 2022-04-26".
- AIP "Add CVX to Aave V2" (2022-05-12):
  - Opens "Llama proposes listing CVX … The risk parameters detailed
    within have been provided by Gauntlet."
  - Every contract is given as `role = [0x…](etherscan)`.

## Compound
**Forum:** comp.xyz.

**Template.**
- There was no fixed template before late 2022. CIP-1
  (https://www.comp.xyz/t/3722, 2022-10-20) introduced the header fields
  `Author / Status / Type / Created`.
- Before that, writers used the EIP-style sections that Gauntlet made
  standard.

**Common headings.** Simple Summary, Abstract, Motivation, Specification,
Dashboard or Data, Next Steps.

**Stages.** Temperature Check and Consensus Check polls (for example
"Asset Listing Temperature Check: …") → Governor Bravo on-chain vote.

**Examples.**
- [Gauntlet, Risk Parameter Updates 2022-04-20](https://www.comp.xyz/t/3183):
  - Simple Summary: "A proposal to adjust two (2) parameters for two (2)
    Compound assets."
  - A Current/Recommended table.
  - Next Steps gives the on-chain submission date and says the vote will
    be cancelled if simulations change.
- [Compound Grants Program](https://www.comp.xyz/t/1292) (2021-03-01):
  - The tl;dr names every author.
  - The budget is itemised in COMP ("4,444 COMP grants, 444 COMP ops, 184
    COMP lead … All unspent funds will be returned").
  - Success metrics are split into measurable and qualitative.
  - Links Uniswap's grants program as precedent.

## Optimism
**Forum:** gov.optimism.io. The 2022 Governance Fund used **field-based
forms, not essay sections**.

**Phase 0 (May 2022).**
- Title format: `[GF:Phase 0 Proposal] PROJECT_NAME`
  ([how-to](https://gov.optimism.io/t/governance-fund-phase-0-how-to-create-a-proposal/215)).
- Fields:
  - Project Name, Author Name
  - DefiLlama TVL, Transactions/day, Tier, Optimism native (Y/N)
  - Number of OP tokens to claim, L2 Recipient Address
  - "Proposal for token distribution (under 1000 words)", which answers:
    how the OP will be distributed, how it incentivises usage and
    liquidity, why users stay after incentives end, over what period, and
    any co-incentives.

**Phase 1 / Season 1–2.**
- [Template](https://gov.optimism.io/t/grant-proposal-template/3233);
  the current text is a later revision.
- It adds: team, project links, competitors, open source (Y/N), ecosystem
  value proposition, previous OP grants, and "Optimism alignment (up to
  200 words)".
- It also asks for the % allocation per initiative, trackable milestones,
  and accountability addresses.
- "Shorter timelines are preferable."

**Title tags:** `[DRAFT]` → `[REVIEW]` → `[READY]`.

**Examples.**
- [GYSR](https://gov.optimism.io/t/2463) (2022-06-04):
  - Fields first, with the recipient address in backticks.
  - The allocation is a numbered breakdown with OP and %.
  - Unused OP is returned.
  - KPIs are on-chain.
- [Across](https://gov.optimism.io/t/3401) (2022-08-30): metrics are
  linked to Dune and DefiLlama.

For Optimism, keep the form's labels verbatim and answer each in place.
Don't convert the form to essay sections.

## MakerDAO
**Forum:** forum.makerdao.com (now forum.skyeco.com). **MIP templates:**
github.com/makerdao/mips, `MIP0/`.

**Preamble** (code block): MIP#, Title, Author(s), Contributors, Tags,
Type, Status, Date Proposed, Date Ratified, Dependencies, Replaces.

**Sections, with the template's own length limits.**
- References
- **Sentence Summary**: "Suggest 30 words max."
- **Paragraph Summary**: "Suggest 100 words max."
- **Component Summary**: "Suggest 30 words max per component."
- Motivation
- Specification / Proposal Details
- Technical MIPs add: Proposed Code, Test Cases, Security Considerations,
  Auditor Information, Licensing.

**Other formats.**
- **Signal requests** have short context and a Discourse poll with
  discrete options ("No change / 2% / 4%").
- **Executive summaries** use conditional framing: "If this executive
  proposal passes, the following changes will occur", then one item per
  change, phrased "will be increased from X to Y", with links to the
  poll and the thread.

## Lido
**Forum:** research.lido.fi. **LIP template:**
github.com/lidofinance/lido-improvement-proposals.

**LIP front-matter:** lip, title (44 characters or fewer), status, author,
discussions-to, created, requires.

**LIP sections.**
- **Simple Summary**: "non-technical and accessible to a casual community
  member"
- **Abstract**: about 200 words, "*what* will be done … not *why* … or
  *how*"
- **Motivation**: "the *why* … This is not the place to describe how"
- **Specification**: Overview, Rationale, Technical Specification, Test
  Cases
- **Security Considerations** and **Failure Modes**: these may postdate
  2022 *(unverified)*.

There was no enforced forum template before 2023. Example:
[Protocol Guild Pilot grant](https://research.lido.fi/t/2016)
(2022-04-08), which opens "This is a signaling proposal for a grant which
will direct funding to …" and states the ask in bold.

## Gitcoin
**Forum:** gov.gitcoin.co.
**Template:** [GCP template](https://gov.gitcoin.co/t/gitcoin-community-proposal-gcp-template/134)
(2021-05-16).

**Title format:** `[Proposal] - Title`. Don't assign a number.

**Sections.**
- **Summary**: "2–3 sentences … without going into deep detail"
- **Abstract**
- **Motivation**
- **Specification**: "the more detail, the better"
- **Benefits**
- **Drawbacks**
- **Vote**: "Clearly outline what voting 'yes' and 'no' entails"

**Process v3 (2022-04-14).**
- Budgets are denominated in GTC, with the USD conversion stated.
- At least 5 days on the forum.
- No edits once the proposal is on Snapshot.

**Example.** [DAO Ops S14 Budget Request](https://gov.gitcoin.co/t/10447)
(2022-04-28):
- TL;DR, then a bold ask: "we request $948k USD or 276k GTC".
- A footnote explains the GTC pricing.
- A budget table: Category | Assumptions | USD | GTC.

---

## Openers worth imitating

These are verbatim. Note how each tells you what a For vote does in its
first sentence.

- "Increases the start price for the temporary premium added when names
  expire from $2,000 to $100,000." (ENS EP5)
- "A proposal to adjust two (2) parameters for two (2) Compound assets."
  (Compound, Gauntlet)
- "This proposal is a batch update of risk parameters to align with the
  Moderate risk level chosen by the Aave community." (Aave, Gauntlet)
- "Llama proposes listing CVX, the governance token of the Convex Finance
  protocol, on Aave v2 mainnet as collateral with borrowing enabled."
  (Aave)
- "This is a renewal proposal for the DAO Ops workstream requesting
  budgetary funds for Season 14 (May 1, 2022 through July 31, 2022)."
  (Gitcoin)
- "This proposal outlines a one-time, community-created consensus
  framework to distribute up to 50,000,000 ARB of DAO-funded incentives
  targeting active Arbitrum protocols." (Arbitrum STIP)
