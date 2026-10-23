# Governance events

Topic0 hashes (keccak256 of the signature, verified):

- DelegateChanged(address delegator, address fromDelegate, address toDelegate)
  0x3134e8a2e6d97e929a7e54011ea5485d7d196dd5f0ba4d4ef95803e8e3fc257f
  Emitted by ERC20Votes / Comp-style tokens. delegator, from, to are indexed (topics 1–3).
- DelegateVotesChanged(address delegate, uint256 previousVotes, uint256 newVotes)
  0xdec2bacdd2f05b59de34da9b523dff8be42e5e38e818c82fdb0bae774387a724
  delegate indexed (topic1); votes in data.
- VoteCast(address voter, uint256 proposalId, uint8 support, uint256 weight, string reason)
  0xb8e138887d0aa13bab447e82de9d5c1777041ecd21ca36ba824ff1e6c07ddda4
  Emitted by OpenZeppelin Governor and Governor Bravo (Compound). voter indexed.
- VoteCastWithParams(address,uint256,uint8,uint256,string,bytes)
  0xe2babfbac5889a709b63bb7f598b324e08bc5a4fb9ec647fb3cbc9ec07eb8712

`support`: 0 = against, 1 = for, 2 = abstain (Bravo and OZ counting simple).

## How to review a delegate

1. Identify the governance token and governor contracts for the DAO (ask the user or check the DAO's docs — don't guess addresses).
2. `governance --token <token> --governor <governor> --address <delegate>`.
3. Report: delegations received over time (from DelegateChanged where toDelegate = address), voting power trajectory (DelegateVotesChanged), votes cast with proposal IDs, support, weight, and reason text.
4. Voting participation rate requires the proposal list (ProposalCreated on the governor) — compute it only if fetched, otherwise say it's missing.

Caveats: non-standard DAOs (e.g. 1inch's own staking-based delegation, Aragon, Snapshot-only DAOs) don't emit these events. If governance returns nothing, say the DAO may use a different mechanism rather than concluding the address never voted.
