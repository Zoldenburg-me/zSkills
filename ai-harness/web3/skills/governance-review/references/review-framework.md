# Review framework

Work through each lens. For each, record findings with severity (Blocking / Major / Minor) and the question the author must answer.

## Contents
1. Mandate and problem
2. Mechanism
3. Economics and incentives
4. Assumptions and sensitivity
5. Risk, failure modes and exit paths
6. Execution and security
7. Accountability
8. Conflicts of interest and capture
9. Process compliance
10. Precedent and second-order effects
11. Draft quality (author mode)

## 1. Mandate and problem
- Is the problem real and evidenced (data, not assertion)? Whose problem is it — the DAO's or the proposer's?
- Is this within the DAO's mandate and authority, or does it belong to a foundation, a company, or a different body?
- What happens if the DAO does nothing? If the answer is "not much", the bar rises.

## 2. Mechanism
- Can you explain in two sentences exactly what changes if this passes? If not, the proposal is under-specified.
- Does the mechanism actually cause the claimed outcome, or just correlate with it?
- Are there simpler or cheaper ways to get the same outcome (existing programs, parameter change, no-cost alternative)?

## 3. Economics and incentives
- Total cost, including token emissions at a stated price, vesting overhang, operational and audit costs. Recompute all totals.
- Cost per outcome (per user, per $ volume, per $ revenue to the DAO). Compare with alternatives or prior programs when known.
- Who gets paid, when, and whether payment is tied to delivery. Upfront payments without clawback = Major at least.
- Incentive programs: can participants farm and leave (mercenary liquidity/volume)? Wash-trading or self-dealing possible? Is there a sybil defence?
- Revenue or fee-share claims: gross or net? Denominated in what? Who verifies?
- Treasury impact: share of liquid treasury, runway effect, concentration in one token.

## 4. Assumptions and sensitivity
- List the 3–5 assumptions that carry the economics (flow, adoption, price, utilisation).
- For each: what evidence supports it, and what happens to the outcome at half the assumed value? If the proposal breaks at half, Major; if it becomes net-harmful, Blocking.
- Look for ratchets: mechanisms that move one way easily and are hard to reverse (inventory accumulation, permanent permissions, one-way parameter drift).

## 5. Risk, failure modes and exit paths
- Market stress: what happens in a liquidity crisis, depeg, oracle failure, or 50%+ drawdown of the incentive token?
- Counterparty and key-person risk: what if the service provider disappears, is hacked, or is sanctioned?
- Smart-contract risk: audits (by whom, scope, date, fixes applied), bug bounty, upgradeability.
- Exit path: how is the program wound down, funds returned, permissions revoked — and does the exit still work under the stress scenario? Missing or stress-broken exit = Blocking for anything holding DAO funds.
- Legal and regulatory exposure for the DAO, delegates, or signers (securities-like promises, sanctioned jurisdictions, custody). Flag, don't opine as a lawyer.

## 6. Execution and security
- On-chain actions: target contracts, function calls, parameters, amounts, recipients. Calldata must match the text exactly.
- Contracts verified? Proxies: implementation verified and admin known? New permissions granted — to whom, revocable by whom?
- Multisig or council execution: signers named, threshold, independence of signers, timelock.
- Off-chain execution (foundation acts on DAO signal): is there a binding commitment, or only a signal?

## 7. Accountability
- Milestones: specific, measurable, dated, externally verifiable. "Community growth" is not a milestone.
- Reporting cadence, who reviews, and what happens on a missed milestone (pause, clawback, re-vote).
- Stop conditions and kill switch: who can halt it, under what criteria.

## 8. Conflicts of interest and capture
- Proposer's delegation, token holdings, other active grants, roles (signer, council, service provider), related entities.
- Does the proposer or a related party vote on their own funding? Is abstention committed?
- Does the proposal concentrate power (new committee, long mandate, discretionary budget) with the proposer?

## 9. Process compliance
- Correct proposal type and template per the DAO's current rules (fetched, not remembered).
- Required temp check / discussion period / audit / KYC steps done?
- Fast-track or emergency path: are its criteria actually met, or is it used to skip scrutiny? Misuse = Major.
- Snapshot/on-chain parameters: voting options, quorum, duration match the rules.

## 10. Precedent and second-order effects
- What does passing this make easier to pass next time?
- Effects on other programs, partners, tokenholders, and the DAO's reputation.

## 11. Draft quality (author mode only)
- TL;DR in the first five lines: what, how much, why, what voters approve.
- Every number sourced; every address linked; calldata or execution spec included.
- Conflicts disclosed up front; risks section names the real risks rather than boilerplate.
- Anticipate the three hardest questions a sceptical delegate will ask and answer them in the text.
- Consistent figures across sections (totals, dates, token amounts) — check mechanically.
