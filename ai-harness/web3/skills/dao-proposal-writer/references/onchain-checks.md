# On-chain checks by proposal type

Run these with the `onchain-review` skill before the proposal is written,
so the proposal states facts rather than instructions to check them.

Record the chain, the block number and the UTC timestamp of the reads.
That line appears **once** in the proposal, under the table or paragraph
the figures belong to ("Data as of Ethereum block 23,412,880,
2026-10-07 14:02 UTC"). Every address gets an explorer link. Nothing gets
a "verified" tag: the link is the verification.

## Who checks what

| Kind of fact | Example | Who decides it |
| --- | --- | --- |
| On-chain state | balances, owners, ticks, current parameter values, Safe signers | The chain. If the member's figure is wrong, use the chain's value and flag the difference in the reply. |
| Intent | the recipient, the amount to send, the new parameter value | The member. If it disagrees with what the chain suggests (e.g. the recipient is an EOA, not the treasury Safe), don't change it. Ask in Open questions. |
| Execution-time state | the exact amounts at signing, the simulation result | The signers, at execution. One sentence in the Specification, never a checklist. |

## Checks by type

**Treasury transfer, grant, or stream**
- Source treasury: is it a Safe? Owners, threshold, modules (a Reality/SafeSnap
  or Zodiac module decides whether a vote executes on its own), guard.
- Source balance of the asset at the reads block. Is it enough to cover the ask?
- Recipient: EOA, Safe or contract. If a Safe: owners and threshold. If it
  is the member's own address, it goes in the Disclosure.
- Stream or vesting contract: verified source, the admin and revoker
  addresses, and whether a proxy is upgradeable.

**LP position or other DeFi position held by the DAO**
- Owner of the position (e.g. `ownerOf(tokenId)` on the Uniswap V3
  NonfungiblePositionManager), or the approved operator.
- Position state: `positions(tokenId)` → token0, token1, fee, tickLower,
  tickUpper, liquidity, tokensOwed0/1.
- Pool identity: the pool address that the factory derives from
  token0/token1/fee, compared with the address the proposal cites.
- In or out of range: the pool's `slot0()` tick compared with the
  position's tick range.
- What is claimable: the DecreaseLiquidity and Collect event history,
  which tells you whether tokensOwed is fees only or includes principal
  that was never collected.

**Parameter change** (risk parameters, fees, caps, rates)
- The current value read from the contract, for the "current" column of
  the current → proposed table.
- The contract and function that change it, plus who is allowed to call
  that function (owner, timelock, role).

**Contract upgrade or new deployment**
- Verified source, compiler version, proxy type and admin.
- The implementation the proxy currently points to, and the address of
  the new implementation.
- New roles or permissions granted, and who can revoke them.

**Delegate, council or committee program**
- Voting power and delegation of the named addresses at the reads block.
- Members' past on-chain voting record, if the proposal makes claims
  about it.

**Calldata in the proposal**
- Decode it and check it does exactly what the text says, and nothing
  more: the same targets, functions, amounts and recipients.
- Any mismatch is reported to the member as blocking.

## When a check can't be run

Reasons include: no Blockscout connector, a blocked host, a missing API
key, an unsupported chain, or a fact that is off-chain only.

Put the fact in the reply's **Open questions** with the exact read that
would settle it (contract, function, argument, chain). Don't put it in the
proposal as "to be confirmed" or "must be verified". Until it is
answered, the matching value stays a `[TBD: …]` marker.
