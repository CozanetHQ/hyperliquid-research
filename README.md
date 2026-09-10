# hyperliquid-research

Phase 1 of the Market Intelligence Trading System (research report, 2026-09-10):
the primary research venue is **Hyperliquid** — on-chain order book, perp
metadata (mark, funding, open interest), and accessible market-data endpoints.

## What this repo IS

A **market-state tape**: `collect.py` runs every 10 minutes on GitHub Actions,
snapshots Hyperliquid's public REST info API —

- top 30 perps by open interest: mark price, funding rate, OI, day volume
- mid prices for the tracked set
- the latest 1m candle for BTC / ETH / SOL / HYPE

— appends one JSON line per run to `data/snapshots/YYYY-MM-DD.jsonl`, and
commits the tape. This is the report's **Layer A (market discovery)** at
REST-snapshot resolution: a durable, replayable record of funding/OI/price
state that later phases (funding/basis signals, regime measurement,
cross-venue comparisons with dYdX/Drift) are built on.

## What this repo is NOT (honest scope)

No L2 order-book depth, no order-flow imbalance, no trade-tick capture —
those need **websocket streaming from a persistent host**, which GitHub
Actions' short-lived runners cannot provide. That is Phase 2 (a small
always-on collector on a VPS / fly.io), explicitly not claimed here.
No trading, no orders, no keys — read-only public endpoints.

## Data layout

```
data/snapshots/2026-09-10.jsonl   # one line per 10-min snapshot
```

Each line: `{"ts": ..., "perps": [{coin, mark, funding, oi, day_vol} x30],
"mids": {...}, "candles_1m": {BTC: {...}, ...}}`
