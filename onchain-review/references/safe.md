# Safe Transaction Service API

Docs: https://docs.safe.global/core-api/how-to-use-api-keys and the Transaction Service swagger per chain.

- Base: `https://api.safe.global/tx-service/{shortName}` with EIP-3770 short names:
  eth (1), arb1 (42161), oeth (10), base (8453), gno (100). Other chains: check docs.
- Auth: `Authorization: Bearer $SAFE_API_KEY` (a JWT from the Safe developer dashboard, API Keys section). Unauthenticated access is heavily rate-limited; 401 = missing/invalid key, 429 = rate or quota exceeded.
- Endpoints the script uses (verified in docs: the v2 multisig-transactions one; the others are standard Transaction Service routes — if one 404s, check the chain's swagger before concluding anything):
  - `/api/v1/safes/{safe}/` — owners, threshold, nonce, modules, guard, version
  - `/api/v2/safes/{safe}/multisig-transactions/` — queued and executed multisig txs, confirmations, decoded data
  - `/api/v1/multisig-transactions/{safeTxHash}/` — one proposal incl. confirmations
  - `/api/v2/owners/{owner}/safes/` — Safes where an address is an owner
- Addresses in paths must be checksummed on some deployments; if a lowercase address returns 404/422, retry checksummed (Blockscout `get_address_info` returns the checksummed hash).

## Review a Safe
1. `safe-info` → owners, threshold, modules, guard. Flag modules and guards explicitly — they can bypass or restrict the owner threshold.
2. `safe-txs` → pending (not executed, sorted by nonce) vs executed. For pending: who has signed, who hasn't, nonce gaps/conflicts (two txs with the same nonce).
3. Cross-check executed txs against Blockscout (`get_transaction_info`) when value or target matters.
4. This API only sees Safe-level data. It cannot tell you who controls an owner key.

Read-only: never propose, sign, confirm or delete Safe transactions from this skill.
