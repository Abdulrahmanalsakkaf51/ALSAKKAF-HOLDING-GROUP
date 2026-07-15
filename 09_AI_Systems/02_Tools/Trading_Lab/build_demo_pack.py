# -*- coding: utf-8 -*-
"""Generate a fully SYNTHETIC OHLCV series into TRL-PACK-DEMO.json.

Deterministic (fixed seed) so results are reproducible. NOT real market
data - fictional symbol, generated locally, no network access.
"""
import datetime
import json
import os
import random

BASE = os.path.dirname(os.path.abspath(__file__))
PACK_PATH = os.path.join(BASE, "sample_data", "TRL-PACK-DEMO.json")


def generate_ohlcv(days=60, start_price=100.0, seed=17):
    rnd = random.Random(seed)
    price = start_price
    start_date = datetime.date(2026, 4, 1)
    bars = []
    for i in range(days):
        # A gentle up-cycle then a sharp synthetic drawdown then partial
        # recovery, so the demo can show both a normal trade and (if
        # thresholds are crossed) a risk-policy event without needing to
        # hand-craft numbers.
        if i < 25:
            drift = 0.6
        elif i < 35:
            drift = -2.2
        else:
            drift = 0.4
        change = drift + rnd.uniform(-1.0, 1.0)
        open_p = price
        close_p = max(1.0, price + change)
        high_p = max(open_p, close_p) + rnd.uniform(0, 0.5)
        low_p = min(open_p, close_p) - rnd.uniform(0, 0.5)
        volume = rnd.randint(1000, 5000)
        date = (start_date + datetime.timedelta(days=i)).isoformat()
        bars.append({"date": date, "open": round(open_p, 4),
                      "high": round(high_p, 4), "low": round(low_p, 4),
                      "close": round(close_p, 4), "volume": volume})
        price = close_p
    return bars


if __name__ == "__main__":
    with open(PACK_PATH, encoding="utf-8") as handle:
        pack = json.load(handle)
    pack["instruments"][0]["ohlcv"] = generate_ohlcv()
    with open(PACK_PATH, "w", encoding="utf-8") as handle:
        json.dump(pack, handle, indent=2)
    print("Wrote %d synthetic bars to %s" % (
        len(pack["instruments"][0]["ohlcv"]), PACK_PATH))
