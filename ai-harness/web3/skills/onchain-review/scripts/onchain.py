#!/usr/bin/env python3
"""Etherscan V2 + Blockscout (public / PRO) + Safe Transaction Service client. Stdlib only.
Prints JSON to stdout.

Usage: python3 onchain.py <command> [--chain eth] [options]
Keys (all optional): ETHERSCAN_API_KEY, BLOCKSCOUT_PRO_API_KEY, SAFE_API_KEY — read from the
environment, else from keys.env in the skill root or ~/.config/onchain-review/keys.env.
Key values are never printed.
"""
import argparse, json, os, sys, time, urllib.parse, urllib.request, urllib.error

CHAINS = {
    "eth":      {"id": 1,     "bs": "eth.blockscout.com",      "safe": "eth"},
    "arbitrum": {"id": 42161, "bs": "arbitrum.blockscout.com", "safe": "arb1"},
    "optimism": {"id": 10,    "bs": "optimism.blockscout.com", "safe": "oeth"},
    "base":     {"id": 8453,  "bs": "base.blockscout.com",     "safe": "base"},
    "gnosis":   {"id": 100,   "bs": "gnosis.blockscout.com",   "safe": "gno"},
}
ES_BASE = "https://api.etherscan.io/v2/api"
PRO_BASE = "https://api.blockscout.com"
SAFE_BASE = "https://api.safe.global/tx-service"
UA = "onchain-review-skill/2.0"
KEY_NAMES = ("ETHERSCAN_API_KEY", "BLOCKSCOUT_PRO_API_KEY", "SAFE_API_KEY")
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY_FILES = (os.path.join(SKILL_ROOT, "keys.env"),
             os.path.expanduser("~/.config/onchain-review/keys.env"))
FORCE_PUBLIC = False
TOPICS = {
    "DelegateChanged": "0x3134e8a2e6d97e929a7e54011ea5485d7d196dd5f0ba4d4ef95803e8e3fc257f",
    "DelegateVotesChanged": "0xdec2bacdd2f05b59de34da9b523dff8be42e5e38e818c82fdb0bae774387a724",
    "VoteCast": "0xb8e138887d0aa13bab447e82de9d5c1777041ecd21ca36ba824ff1e6c07ddda4",
    "VoteCastWithParams": "0xe2babfbac5889a709b63bb7f598b324e08bc5a4fb9ec647fb3cbc9ec07eb8712",
}
FALLBACK_HINTS = ("free api access", "not supported", "rate limit", "max calls", "invalid api key", "missing/invalid")
DRY = False


class ApiError(Exception):
    pass


_KEYS = None


def keys():
    """Env first, then keys.env files. Returns {name: (value, source)}."""
    global _KEYS
    if _KEYS is not None:
        return _KEYS
    found = {}
    for n in KEY_NAMES:
        if os.environ.get(n, "").strip():
            found[n] = (os.environ[n].strip(), "env")
    for path in KEY_FILES:
        if not os.path.isfile(path):
            continue
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            n, v = line.split("=", 1)
            n, v = n.strip(), v.strip().strip('"').strip("'")
            if n in KEY_NAMES and v and n not in found:
                found[n] = (v, path)
    _KEYS = found
    return found


def key(name):
    return keys().get(name, (None, None))[0]


def redact(text):
    for v, _ in keys().values():
        text = text.replace(v, "<KEY>")
    return text


def http_get(url, retries=3, headers=None):
    if DRY:
        return {"dry_run_url": redact(url), "auth_header": bool(headers and "Authorization" in headers)}
    h = {"User-Agent": UA, "Accept": "application/json", **(headers or {})}
    req = urllib.request.Request(url, headers=h)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if (e.code == 429 or e.code >= 500) and attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            hint = " (blocked by sandbox network allowlist?)" if e.code == 403 and e.headers.get("x-deny-reason") else ""
            if e.code == 401:
                hint = " (API key missing or invalid)"
            raise ApiError(f"HTTP {e.code}{hint} for {urllib.parse.urlsplit(url).netloc}{redact(urllib.parse.urlsplit(url).path)}")
        except urllib.error.URLError as e:
            raise ApiError(f"Network error ({e.reason}) — host may be blocked by the sandbox allowlist")


# ---------- Etherscan ----------
def es(chain, **params):
    k = key("ETHERSCAN_API_KEY")
    if not k and not DRY:
        raise ApiError("no ETHERSCAN_API_KEY")
    params = {"chainid": CHAINS[chain]["id"], **params, "apikey": k or "<KEY>"}
    data = http_get(ES_BASE + "?" + urllib.parse.urlencode(params))
    time.sleep(0.25)  # stay under free-tier rate limit
    if DRY or "jsonrpc" in data:
        return data.get("result", data)
    if data.get("status") == "1":
        return data["result"]
    msg = f"{data.get('message')}: {data.get('result')}"
    if "no transactions found" in msg.lower() or "no records found" in msg.lower():
        return []
    raise ApiError("etherscan: " + msg)


# ---------- Blockscout ----------
def bs(chain, path, limit=None, **params):
    """Blockscout v2. Uses the PRO API (api.blockscout.com, Bearer key) when BLOCKSCOUT_PRO_API_KEY
    is available and --public is not set; otherwise the chain's public instance."""
    pro = key("BLOCKSCOUT_PRO_API_KEY")
    if pro and not FORCE_PUBLIC:
        base = f"{PRO_BASE}/{CHAINS[chain]['id']}/api/v2{path}"
        hdr = {"Authorization": f"Bearer {pro}"}
    else:
        base = f"https://{CHAINS[chain]['bs']}/api/v2{path}"
        hdr = None
    items, page_params = [], {}
    while True:
        q = {**params, **page_params}
        data = http_get(base + ("?" + urllib.parse.urlencode(q) if q else ""), headers=hdr)
        if DRY or limit is None or "items" not in data:
            return data
        items.extend(data["items"])
        page_params = data.get("next_page_params") or {}
        if not page_params or len(items) >= limit:
            return {"items": items[:limit], "truncated": bool(page_params) and len(items) >= limit}


def with_fallback(primary, fallback):
    """Try primary; on key/tier/rate errors use fallback. Returns (source, data)."""
    try:
        return primary()
    except ApiError as e:
        if any(h in str(e).lower() for h in FALLBACK_HINTS) or "no etherscan_api_key" in str(e).lower():
            src, data = fallback()
            return src, {"fallback_reason": str(e), "data": data}
        raise


# ---------- commands ----------
def cmd_check(a):
    ks = keys()
    out = {"keys": {n: ({"present": True, "last4": ks[n][0][-4:],
                         "source": "env" if ks[n][1] == "env" else "keys.env"} if n in ks else {"present": False})
                    for n in KEY_NAMES},
           "blockscout_mode": "pro" if ks.get("BLOCKSCOUT_PRO_API_KEY") and not FORCE_PUBLIC else "public",
           "hosts": {}}
    hosts = {"api.etherscan.io": "https://api.etherscan.io/v2/api?chainid=1&module=proxy&action=eth_blockNumber",
             "api.blockscout.com": f"{PRO_BASE}/api/json/plans",
             "mcp.blockscout.com": "https://mcp.blockscout.com/v1/tools",
             "api.safe.global": f"{SAFE_BASE}/eth/api/v1/about/"}
    hosts.update({c["bs"]: f"https://{c['bs']}/api/v2/stats" for c in CHAINS.values()})
    for h, url in hosts.items():
        try:
            http_get(url, retries=1)
            out["hosts"][h] = "reachable"
        except ApiError as e:
            msg = str(e)
            # 401 on Safe /about without key still proves the host is reachable
            out["hosts"][h] = "reachable (auth required)" if "HTTP 401" in msg else msg
    return out


def cmd_whatis(a):
    d = bs(a.chain, f"/addresses/{a.address}")
    if DRY:
        return d
    keys = ("hash", "is_contract", "is_verified", "name", "ens_domain_name", "coin_balance",
            "proxy_type", "implementations", "creator_address_hash", "creation_transaction_hash")
    return {k: d.get(k) for k in keys}


def cmd_discover(a):
    res = {}
    for name in CHAINS:
        try:
            c = bs(name, f"/addresses/{a.address}/counters")
            res[name] = c if DRY else {"transactions": c.get("transactions_count"),
                                       "token_transfers": c.get("token_transfers_count")}
        except ApiError as e:
            res[name] = {"error": str(e)}
    return res


def cmd_summary(a):
    return {"address": cmd_whatis(a), "counters": bs(a.chain, f"/addresses/{a.address}/counters")}


def _es_list(action, a):
    return es(a.chain, module="account", action=action, address=a.address, page=1,
              offset=a.limit, sort="desc")


def cmd_txs(a):
    return with_fallback(lambda: ("etherscan", _es_list("txlist", a)),
                         lambda: ("blockscout", bs(a.chain, f"/addresses/{a.address}/transactions", limit=a.limit)))


def cmd_token_transfers(a):
    # Blockscout first: decoded symbols/decimals included
    try:
        return "blockscout", bs(a.chain, f"/addresses/{a.address}/token-transfers", limit=a.limit)
    except ApiError as e:
        return "etherscan", {"fallback_reason": str(e), "data": _es_list("tokentx", a)}


def cmd_internal(a):
    return with_fallback(lambda: ("etherscan", _es_list("txlistinternal", a)),
                         lambda: ("blockscout", bs(a.chain, f"/addresses/{a.address}/internal-transactions", limit=a.limit)))


def cmd_contract(a):
    out = {}
    try:
        d = bs(a.chain, f"/smart-contracts/{a.address}")
        out["blockscout"] = d if DRY else {k: d.get(k) for k in (
            "name", "is_verified", "compiler_version", "optimization_enabled", "proxy_type",
            "implementations", "abi", "source_code", "verified_at")}
    except ApiError as e:
        out["blockscout_error"] = str(e)
    bs_verified = out.get("blockscout", {}).get("is_verified")
    if not bs_verified or DRY:
        try:
            out["etherscan"] = es(a.chain, module="contract", action="getsourcecode", address=a.address)
        except ApiError as e:
            out["etherscan_error"] = str(e)
    if not a.full:
        for src in ("blockscout",):
            if isinstance(out.get(src), dict) and out[src].get("source_code"):
                out[src]["source_code"] = out[src]["source_code"][:4000] + "\n…[truncated; use --full]"
    return out


def cmd_logs(a):
    return "blockscout", bs(a.chain, f"/addresses/{a.address}/logs", limit=a.limit)


def cmd_tx(a):
    h = a.hash
    out = {}
    for part, path in (("tx", ""), ("token_transfers", "/token-transfers"),
                       ("internal", "/internal-transactions"), ("logs", "/logs")):
        try:
            out[part] = bs(a.chain, f"/transactions/{h}{path}", limit=None if part == "tx" else a.limit)
        except ApiError as e:
            out[part + "_error"] = str(e)
    if "tx_error" in out:
        try:
            out["etherscan_tx"] = es(a.chain, module="proxy", action="eth_getTransactionByHash", txhash=h)
            out["etherscan_receipt"] = es(a.chain, module="proxy", action="eth_getTransactionReceipt", txhash=h)
        except ApiError as e:
            out["etherscan_error"] = str(e)
    return out


def _pad(addr):
    return "0x" + addr.lower().replace("0x", "").rjust(64, "0")


def _getlogs(chain, contract, topic0, topic_n, idx, from_block):
    p = {"module": "logs", "action": "getLogs", "address": contract, "fromBlock": from_block,
         "toBlock": "latest", "topic0": topic0, f"topic{idx}": topic_n, f"topic0_{idx}_opr": "and"}
    return es(chain, **p)


def cmd_governance(a):
    if not (a.token or a.governor):
        raise ApiError("governance needs --token and/or --governor (the DAO's contracts)")
    who = _pad(a.address)
    out = {}
    jobs = []
    if a.token:
        jobs += [("delegations_to", a.token, "DelegateChanged", 3),
                 ("delegations_by", a.token, "DelegateChanged", 1),
                 ("voting_power_changes", a.token, "DelegateVotesChanged", 1)]
    if a.governor:
        jobs += [("votes_cast", a.governor, "VoteCast", 1),
                 ("votes_cast_with_params", a.governor, "VoteCastWithParams", 1)]
    for label, contract, ev, idx in jobs:
        try:
            out[label] = _getlogs(a.chain, contract, TOPICS[ev], who, idx, a.from_block)
        except ApiError as e:
            out[label + "_error"] = str(e)
    out["note"] = ("Raw logs; topics are indexed params, data holds the rest. "
                   "Empty results can mean a non-standard governance system or an Etherscan result cap (1000 logs) — "
                   "narrow --from-block if needed.")
    return out


# ---------- Safe Transaction Service ----------
def safe_get(chain, path, **params):
    k = key("SAFE_API_KEY")
    if not k and not DRY:
        raise ApiError("no SAFE_API_KEY — get one from the Safe developer dashboard (API Keys)")
    url = f"{SAFE_BASE}/{CHAINS[chain]['safe']}/api{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    return http_get(url, headers={"Authorization": f"Bearer {k or '<KEY>'}"})


def cmd_safe_info(a):
    return "safe", safe_get(a.chain, f"/v1/safes/{a.address}/")


def cmd_safe_txs(a):
    p = {"limit": min(a.limit, 100), "ordering": "-nonce"}
    if a.pending:
        p["executed"] = "false"
    d = safe_get(a.chain, f"/v2/safes/{a.address}/multisig-transactions/", **p)
    if DRY or not a.slim:
        return "safe", d
    keep = ("safeTxHash", "nonce", "to", "value", "isExecuted", "isSuccessful", "executionDate",
            "submissionDate", "confirmationsRequired", "transactionHash", "proposer")
    items = []
    for t in d.get("results", []):
        row = {k: t.get(k) for k in keep}
        row["method"] = (t.get("dataDecoded") or {}).get("method")
        row["signers"] = [c.get("owner") for c in t.get("confirmations") or []]
        items.append(row)
    return "safe", {"count": d.get("count"), "next": bool(d.get("next")), "results": items}


def cmd_safe_tx(a):
    return "safe", safe_get(a.chain, f"/v1/multisig-transactions/{a.hash}/")


def cmd_safes_of(a):
    return "safe", safe_get(a.chain, f"/v2/owners/{a.address}/safes/")


def cmd_search(a):
    return bs(a.chain, "/search", q=a.query)


def main():
    global DRY, FORCE_PUBLIC
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true", help="print URLs instead of calling (keys redacted)")
    p.add_argument("--public", action="store_true", help="use public Blockscout instances even if a PRO key is set")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add(name, fn, addr=False, txh=False, limit=False):
        s = sub.add_parser(name)
        s.add_argument("--chain", default="eth", choices=CHAINS)
        if addr:
            s.add_argument("address")
        if txh:
            s.add_argument("hash")
        if limit:
            s.add_argument("--limit", type=int, default=100)
        s.set_defaults(fn=fn)
        return s

    add("check", cmd_check)
    add("whatis", cmd_whatis, addr=True)
    add("discover", cmd_discover, addr=True)
    add("summary", cmd_summary, addr=True)
    add("txs", cmd_txs, addr=True, limit=True)
    add("token-transfers", cmd_token_transfers, addr=True, limit=True)
    add("internal", cmd_internal, addr=True, limit=True)
    add("contract", cmd_contract, addr=True).add_argument("--full", action="store_true")
    add("logs", cmd_logs, addr=True, limit=True)
    add("tx", cmd_tx, txh=True, limit=True)
    g = add("governance", cmd_governance, addr=True)
    g.add_argument("--token"); g.add_argument("--governor"); g.add_argument("--from-block", default="0")
    add("search", cmd_search).add_argument("query")
    add("safe-info", cmd_safe_info, addr=True)
    st = add("safe-txs", cmd_safe_txs, addr=True, limit=True)
    st.add_argument("--pending", action="store_true", help="only not-yet-executed txs")
    st.add_argument("--slim", action="store_true", help="compact rows: nonce, to, method, signers, status")
    add("safe-tx", cmd_safe_tx, txh=True)
    add("safes-of", cmd_safes_of, addr=True)

    a = p.parse_args()
    DRY = a.dry_run
    FORCE_PUBLIC = a.public
    try:
        result = a.fn(a)
        if isinstance(result, tuple):
            result = {"source": result[0], "result": result[1]}
        print(json.dumps(result, indent=2, default=str))
    except ApiError as e:
        print(json.dumps({"error": redact(str(e))}), file=sys.stdout)
        sys.exit(1)


if __name__ == "__main__":
    main()
