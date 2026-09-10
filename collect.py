#!/usr/bin/env python3
"""
Hyperliquid Market-State Tape — Phase 1 collector (Market Intelligence Research Report).

Collects REST snapshots from Hyperliquid's public info API every run:
  - metaAndAssetCtxs: mark, funding, open interest for every perp
  - allMids: mid prices (filtered to the tracked set)
  - candleSnapshot: last 1m candle for majors (BTC, ETH, SOL, HYPE)

Appends one JSON line per run to data/snapshots/YYYY-MM-DD.jsonl, then commits
and pushes — a durable, replayable market-state tape for research.

HONEST SCOPE (per the report's own framing): this is Layer A (market
discovery) at REST-snapshot resolution. TRUE L2 order-book depth and
order-flow imbalance need websocket streaming from a persistent host —
that is the next phase, not claimed here.
"""
import json
import os
import urllib.request
from datetime import datetime, timezone

API = "https://api.hyperliquid.xyz/info"
MAJORS = ["BTC", "ETH", "SOL", "HYPE"]
TOP_N = 30          # track top-N perps by open interest
CANDLE_LOOKBACK_MS = 120_000  # last ~2 minutes of 1m candles

def post(body):
    req = urllib.request.Request(
        API, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())

def main():
    now = datetime.now(timezone.utc)
    snap = {"ts": now.isoformat()}

    # perp contexts: universe + funding/OI/mark
    meta = post({"type": "metaAndAssetCtxs"})
    universe, ctxs = meta[0]["universe"], meta[1]
    perps = []
    for u, c in zip(universe, ctxs):
        try:
            oi = float(c.get("openInterest") or 0)
        except (TypeError, ValueError):
            continue
        perps.append({
            "coin": u["name"], "mark": c.get("markPx"),
            "funding": c.get("funding"), "oi": oi,
            "day_vol": c.get("dayNtlVlm"),
        })
    perps.sort(key=lambda p: p["oi"], reverse=True)
    tracked = perps[:TOP_N]
    snap["perps"] = tracked

    # mids for the tracked coins only (allMids returns the whole venue)
    names = {p["coin"] for p in tracked} | set(MAJORS)
    mids = post({"type": "allMids"}).get("mids", {})
    snap["mids"] = {k: v for k, v in mids.items() if k in names}

    # last 1m candle for majors
    candles = {}
    start = int(now.timestamp() * 1000) - CANDLE_LOOKBACK_MS
    for coin in MAJORS:
        try:
            c = post({"type": "candleSnapshot",
                      "req": {"coin": coin, "interval": "1m", "startTime": start}})
            if c:
                candles[coin] = c[-1]
        except Exception:
            continue
    snap["candles_1m"] = candles

    # append to the daily tape
    os.makedirs("data/snapshots", exist_ok=True)
    path = f"data/snapshots/{now:%Y-%m-%d}.jsonl"
    with open(path, "a") as f:
        f.write(json.dumps(snap, separators=(",", ":")) + "\n")
    print(f"snapshot appended: {len(tracked)} perps, {len(candles)} candles -> {path}")

if __name__ == "__main__":
    main()
