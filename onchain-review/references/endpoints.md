# Endpoints and chains

Verify against the official docs when something fails; explorer APIs change.
- Etherscan V2: https://docs.etherscan.io/
- Blockscout: https://docs.blockscout.com/devs/apis

## Chains supported by the script

| Chain     | chainid | Blockscout host            | Safe shortName |
|-----------|---------|----------------------------|----------------|
| Ethereum  | 1       | eth.blockscout.com         | eth            |
| Arbitrum  | 42161   | arbitrum.blockscout.com    | arb1           |
| Optimism  | 10      | optimism.blockscout.com    | oeth           |
| Base      | 8453    | base.blockscout.com        | base           |
| Gnosis    | 100     | gnosis.blockscout.com      | gno            |

Add a chain by extending `CHAINS` in `scripts/onchain.py`.

With `BLOCKSCOUT_PRO_API_KEY` set, the script sends Blockscout calls to `https://api.blockscout.com/{chainid}/api/v2/...` instead (see `blockscout-pro-api.md`). Any chain in `pro-api-index.md` / `/api/json/config` works there; the MCP connector covers all Blockscout chains too.

Other hosts: `mcp.blockscout.com` (MCP REST mirror), `api.safe.global` (Safe, see `safe.md`), `chains.blockscout.com` (Chainscout).

## Etherscan V2

Single base URL, chain selected by `chainid`, one API key for all chains:
`https://api.etherscan.io/v2/api?chainid=<id>&module=<m>&action=<a>&...&apikey=<key>`

Used actions: `account/balance`, `account/txlist`, `account/tokentx`, `account/txlistinternal`,
`contract/getsourcecode`, `contract/getabi`, `logs/getLogs`, `proxy/eth_getTransactionByHash`,
`proxy/eth_getTransactionReceipt`, `proxy/eth_getCode`.

Responses: `{"status":"1","message":"OK","result":...}`. `status:"0"` with a message like
"No transactions found" is empty, not an error. Messages about free-tier access or rate limits
trigger Blockscout fallback. Free tier is rate-limited (a few calls/sec); the script sleeps between calls.

## Blockscout REST API v2 (no key needed on public instances)

- `/api/v2/addresses/{addr}` — balance, is_contract, ENS, proxy info
- `/api/v2/addresses/{addr}/counters`
- `/api/v2/addresses/{addr}/transactions`
- `/api/v2/addresses/{addr}/token-transfers`
- `/api/v2/addresses/{addr}/internal-transactions`
- `/api/v2/addresses/{addr}/logs`
- `/api/v2/smart-contracts/{addr}` — source, ABI, verification
- `/api/v2/transactions/{hash}` plus `/token-transfers`, `/internal-transactions`, `/logs`
- `/api/v2/search?q=...` — ENS names, tokens, addresses

Pagination: responses include `next_page_params`; pass those keys back as query params.
