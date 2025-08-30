from __future__ import annotations
import json, os
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo
from config import SEASON, TZ

BASE = os.path.join("data", f"season-{SEASON}")
SPIEL_DIR = os.path.join(BASE, "spieltage")
OUT = os.path.join(BASE, "standings.json")


def load_spieltage():
    files = sorted(f for f in os.listdir(SPIEL_DIR) if f.endswith('.json'))
    for fn in files:
        with open(os.path.join(SPIEL_DIR, fn), encoding="utf-8") as f:
            yield json.load(f)


def main():
    totals = defaultdict(lambda: {"kicktipp_sum_P":0, "wurstliga_sum":0, "tv_sum":0, "null_sum":0, "sts_sum":0})
    counted = []

    for doc in load_spieltage():
        if doc.get("status") == "not_started":
            continue
        
        # Skip if this looks like meaningless pre-season data (all players have 0 points)
        all_zero = all(p.get("kicktipp_P", 0) == 0 for p in doc.get("players", []))
        if all_zero and len(doc.get("players", [])) > 0:
            continue
        counted.append(doc["spieltag"])
        for p in doc.get("players", []):
            t = totals[p["name"]]
            t["kicktipp_sum_P"] += int(p.get("kicktipp_P", 0))
            t["wurstliga_sum"] += int(p.get("wurstliga_pts", 0))
            t["tv_sum"] += int(p.get("tv", 0))
            t["null_sum"] += int(p.get("null_wurst", 0))
            t["sts_sum"] += int(p.get("sts", 0))

    out = {
        "season": SEASON,
        "spieltage_counted": sorted(counted),
        "updated_at": datetime.now(ZoneInfo(TZ)).isoformat(),
        "players": [
            {"name": name, **vals}
            for name, vals in sorted(
                totals.items(),
                key=lambda kv: (kv[1]["wurstliga_sum"], kv[1]["kicktipp_sum_P"]),
                reverse=True
            )
        ]
    }

    os.makedirs(BASE, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("standings written", OUT)

if __name__ == "__main__":
    main()