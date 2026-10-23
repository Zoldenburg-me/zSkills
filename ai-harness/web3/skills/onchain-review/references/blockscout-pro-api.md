# Blockscout PRO API (condensed from blockscout/agent-skills `web3-dev` v0.1.0)

Full upstream text: `upstream/web3-dev-SKILL-0.1.0.md`.

Use when: the MCP server is unavailable, a script needs higher limits than public instances, or a chain has no public `*.blockscout.com` host. One key, 100+ chains.

- Base: `https://api.blockscout.com` + path verbatim from `pro-api-index.md`, e.g. `/1/api/v2/blocks/10000000`. Do not add extra prefixes.
- Auth: `Authorization: Bearer $BLOCKSCOUT_PRO_API_KEY` (key starts `proapi_`). Also send `User-Agent: onchain-review-skill/2.0` and `Accept: application/json` — bare urllib UA gets a Cloudflare 403 (error 1010), which is not an auth problem.
- Parameter detail: `pro-api.json` is ~24k lines — never read it whole. Query with jq, e.g.
  `jq '.paths["/{chain_id}/api/v2/addresses/{address_hash_param}/transactions"].get.parameters' references/pro-api.json`
  (use `oastools walk parameters -path '<PATH>'` if installed).
- Contract state at a block: `POST https://api.blockscout.com/{chain_id}/json-rpc` with `eth_call`, same Bearer header. No separate RPC needed.
- Timestamp → block: `/{chain_id}/api/legacy/block/get-block-number-by-time` (don't bisect).
- Pagination: `next_page_params` → pass back as query params.
- Billing: every response has `x-credits-remaining`; stop batch jobs when it runs low. Live plans/costs/chain list (no key): `/api/json/plans`, `/api/json/config`.
- Errors: 401/403 JSON → bad key, stop. 402 → credits exhausted. 429 → exponential backoff. 5xx → capped retry.
- Key missing → get one at https://dev.blockscout.com (free tier, no card).
