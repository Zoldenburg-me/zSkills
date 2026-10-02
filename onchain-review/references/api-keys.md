# API keys

| Service | Env var | Get it | Used for |
|---|---|---|---|
| Etherscan V2 | `ETHERSCAN_API_KEY` | https://etherscan.io/myapikey | verified source/ABI fallback, getLogs for governance |
| Blockscout PRO | `BLOCKSCOUT_PRO_API_KEY` (`proapi_…`) | https://dev.blockscout.com | higher limits, 100+ chains via one host |
| Safe Transaction Service | `SAFE_API_KEY` (JWT) | Safe developer dashboard → API Keys | Safe owners, threshold, queued/executed multisig txs |

## How the script finds keys (first hit wins)
1. Environment variable of the same name.
2. `keys.env` in the skill root (next to SKILL.md), then `~/.config/onchain-review/keys.env`. Format: `NAME=value`, one per line, `#` comments allowed. Template: `keys.env.example`.

`python3 scripts/onchain.py check` reports each key as present (last 4 chars only) or missing.

## Rules for Claude
- Never print, echo, quote or log a key value. Refer to keys by variable name; when confirming, show at most the last 4 characters.
- Never ask the user to paste a key into chat. If they do anyway, use it for this session only via an env var in the command, don't write it to any file unasked, and recommend rotating it.
- A key in `keys.env` inside the skill travels with the skill: anyone the skill is shared with (or an org, if installed org-wide) can read it. Mention this once if the user asks to bake keys in; the user decides.
- Missing key → say which one, where to get it, and fall back (Blockscout MCP / public instances need no key). Only Safe has no keyless fallback worth using.
