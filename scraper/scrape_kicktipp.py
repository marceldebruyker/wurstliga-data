#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Wurstliga Kicktipp scraper (full rewrite)

- Auto-discovers all Spieltage (no hard-coded list)
- Parses matches (Termin/Heim/Gast/Ergebnis) for each Spieltag
- Parses player table (Name + P) and assigns Wurstliga points by dense rank
- Derives Spieltag status: not_started / in_progress / complete
- Writes one JSON file per Spieltag and a season-level metadata.json
- Always overwrites files on each run

Requires:
  - requests, beautifulsoup4, lxml, zoneinfo (Py3.9+)
  - a config.py providing the symbols imported below
"""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Tuple
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo

from config import (
    KICKTIPP_BASE,         # e.g. "https://www.kicktipp.de"
    TIPPUEBERSICHT_PATH,   # e.g. "/wurstliga/tippuebersicht"
    TIPPSEASON_ID,         # e.g. 3944954 (new season)
    SEASON,                # e.g. "2025-26"
    MATCHES_PER_SPIELTAG,  # e.g. 9
    USER_AGENT,
    TIMEOUT,
    RETRY,
    SLEEP_BETWEEN,
    WURSTLIGA_LADDER,      # list of wurstliga points by dense rank (index 0 = rank 1)
    TZ,                    # e.g. "Europe/Berlin"
)

# ---------- Configuration of output paths ----------

DATA_DIR = os.path.join("..", "data", f"season-{SEASON}", "spieltage")
META_PATH = os.path.join("..", "data", f"season-{SEASON}", "metadata.json")
os.makedirs(DATA_DIR, exist_ok=True)

# ---------- HTTP helpers ----------

HDRS = {"User-Agent": USER_AGENT}

def get(url: str) -> requests.Response:
    """
    Fetch a URL with basic retry/backoff using the configured RETRY/ TIMEOUT.
    Raises for non-200 after retries.
    """
    for i in range(RETRY + 1):
        r = requests.get(url, headers=HDRS, timeout=TIMEOUT)
        if r.status_code == 200:
            return r
        # Linear backoff (1, 2, 3, ...)
        time.sleep(1 + i)
    r.raise_for_status()  # never reached if we returned above
    return r  # for type checkers

# ---------- Parsing helpers ----------

NUM_RE = re.compile(r"^\s*(\d+)\s*:\s*(\d+)\s*$")
DATE_RE = re.compile(r"(\d{2}\.\d{2}\.\d{2})\s+(\d{2}:\d{2})")

def discover_spieltage(tippsaison_id: int) -> List[int]:
    """
    Discover all available spieltagIndex values by scanning the season navigation.
    Falls back to a reasonable [1..34] if none are found.
    """
    url = f"{KICKTIPP_BASE}{TIPPUEBERSICHT_PATH}?tippsaisonId={tippsaison_id}&spieltagIndex=1"
    r = get(url)
    soup = BeautifulSoup(r.text, "lxml")

    idxs: set[int] = set()
    for a in soup.select("a[href*='spieltagIndex=']"):
        href = a.get("href", "")
        abs_url = urljoin(KICKTIPP_BASE, href)
        q = parse_qs(urlparse(abs_url).query)
        if "spieltagIndex" in q:
            try:
                idx = int(str(q["spieltagIndex"][0]).strip())
                if idx > 0:
                    idxs.add(idx)
            except Exception:
                continue

    # Fallback: typical Bundesliga 34 matchdays
    if not idxs:
        return list(range(1, 35))
    return sorted(idxs)

def parse_matches(soup: BeautifulSoup) -> Tuple[List[Dict[str, Any]], int]:
    """
    Parse the first table containing headers Termin/Heim/Gast/Ergebnis.
    Returns (matches, total_match_slots_detected)
    """
    matches: List[Dict[str, Any]] = []

    # Find the matches table by its headers
    match_table = None
    for tbl in soup.find_all("table"):
        headers = [t.get_text(strip=True) for t in tbl.find_all("th")]
        if {"Termin", "Heim", "Gast", "Ergebnis"}.issubset(set(headers)):
            match_table = tbl
            break

    if not match_table:
        # No table found: return empty list and zero slots
        return matches, 0

    tz = ZoneInfo(TZ)
    body = match_table.find("tbody") or match_table
    rows = body.find_all("tr")

    for i, tr in enumerate(rows, start=1):
        tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        if len(tds) < 4:
            continue
        termin, heim, gast, ergebnis = tds[0], tds[1], tds[2], tds[3]

        # Parse datetime "DD.MM.YY HH:MM" into local ISO
        dt_iso = None
        m = DATE_RE.search(termin)
        if m:
            try:
                dt = datetime.strptime(
                    f"{m.group(1)} {m.group(2)}", "%d.%m.%y %H:%M"
                ).replace(tzinfo=tz)
                dt_iso = dt.isoformat()
            except Exception:
                dt_iso = None

        # Normalize result: only keep real scores like "2:0"
        res = ergebnis.strip()
        res = res if NUM_RE.match(res) else ""

        matches.append(
            {
                "kicktipp_row": i,
                "datetime_local": dt_iso,
                "home": heim,
                "away": gast,
                "result": res,
            }
        )

    return matches, len(rows)

def parse_players(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    Parse the player table containing 'Name' and 'P' headers.
    Returns a list of players with kicktipp_P and derived fields later.
    """
    players: List[Dict[str, Any]] = []

    player_table = None
    for tbl in soup.find_all("table"):
        header_text = " ".join(th.get_text(strip=True) for th in tbl.find_all("th"))
        if "Name" in header_text and "P" in header_text:
            player_table = tbl
            break

    if not player_table:
        return players

    headers = [th.get_text(strip=True) for th in player_table.find_all("th")]

    # Column indices with robust fallbacks
    try:
        name_idx = headers.index("Name")
    except ValueError:
        # Often 'Pos | +/- | Name | ...'
        name_idx = 2 if len(headers) > 2 else 0

    # Prefer the last "P" if multiple occur
    p_indices = [i for i, h in enumerate(headers) if h == "P"]
    if p_indices:
        p_idx = p_indices[-1]
    else:
        # Frequently P,S,G at the end -> pick third from last if available
        p_idx = max(0, len(headers) - 3)

    tbody = player_table.find("tbody") or player_table
    for tr in tbody.find_all("tr"):
        tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
        if not tds or len(tds) <= max(name_idx, p_idx):
            continue

        name = tds[name_idx].strip()
        p_raw = tds[p_idx].strip()

        try:
            p_val = int(p_raw)
        except Exception:
            p_val = 0  # tolerate blanks/non-ints as 0

        if name:
            players.append({"name": name, "kicktipp_P": p_val})

    return players

def apply_wurstliga_scoring(players: List[Dict[str, Any]]) -> None:
    """
    Mutates player dicts in place:
      - dense_rank (1=best)
      - wurstliga_pts (from WURSTLIGA_LADDER)
      - sts: 1 if rank 1 else 0
      - tv: 1 if kicktipp_P == 0 else 0
      - null_wurst: 1 if wurstliga_pts == 0 else 0
    """
    # Dense rank from Kicktipp P (higher is better)
    bucket: Dict[int, List[Dict[str, Any]]] = {}
    for p in players:
        bucket.setdefault(p["kicktipp_P"], []).append(p)

    unique_scores = sorted(bucket.keys(), reverse=True)
    score_to_dense_rank = {score: i + 1 for i, score in enumerate(unique_scores)}

    for p in players:
        dense_rank = score_to_dense_rank.get(p["kicktipp_P"], 999)
        p["dense_rank"] = dense_rank

        ladder_idx = dense_rank - 1
        wurst = (
            WURSTLIGA_LADDER[ladder_idx]
            if 0 <= ladder_idx < len(WURSTLIGA_LADDER)
            else 0
        )
        p["wurstliga_pts"] = int(wurst)
        p["sts"] = 1 if dense_rank == 1 else 0
        p["tv"] = 1 if p["kicktipp_P"] == 0 else 0
        p["null_wurst"] = 1 if p["wurstliga_pts"] == 0 else 0

def derive_spieltag_status(matches: List[Dict[str, Any]], total_slots: int, players: List[Dict[str, Any]]) -> str:
    """
    Decide not_started / in_progress / complete using results and (as a hint) player points.
    """
    results_done = sum(1 for m in matches if NUM_RE.match(m.get("result", "")))
    total = total_slots if total_slots > 0 else (len(matches) or MATCHES_PER_SPIELTAG)

    if results_done == 0:
        status = "not_started"
    elif results_done < total:
        status = "in_progress"
    else:
        status = "complete"

    # If everyone has 0 points and there are no results, treat it as not started
    if players and all(p.get("kicktipp_P", 0) == 0 for p in players) and results_done == 0:
        status = "not_started"

    return status

def parse_spieltag(html: str, spieltag: int) -> Dict[str, Any]:
    """
    Parse a Spieltag HTML document into structured JSON-friendly dict.
    """
    soup = BeautifulSoup(html, "lxml")

    matches, total_slots = parse_matches(soup)
    players = parse_players(soup)
    apply_wurstliga_scoring(players)
    status = derive_spieltag_status(matches, total_slots, players)

    return {
        "season": SEASON,
        "spieltag": spieltag,
        "status": status,
        "matches": matches,
        "players": players,
    }

# ---------- I/O helpers ----------

def write_json(path: str, obj: Dict[str, Any]) -> None:
    """Always overwrite JSON (UTF-8, pretty, keep umlauts)."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

# ---------- Main ----------

def main() -> None:
    tz = ZoneInfo(TZ)
    meta: Dict[str, Any] = {
        "season": SEASON,
        "spieltage": {},
        "updated_at": datetime.now(tz).isoformat(),
    }

    # Discover all Spieltage for this season
    spieltage = discover_spieltage(TIPPSEASON_ID)

    for stg in spieltage:
        url = (
            f"{KICKTIPP_BASE}{TIPPUEBERSICHT_PATH}"
            f"?tippsaisonId={TIPPSEASON_ID}&spieltagIndex={stg}"
        )
        resp = get(url)
        doc = parse_spieltag(resp.text, stg)

        # Write per-Spieltag JSON (always overwrite)
        out_path = os.path.join(DATA_DIR, f"{stg:02d}.json")
        write_json(out_path, doc)

        # Build metadata summary
        meta["spieltage"][str(stg)] = {
            "status": doc["status"],
            "players": len(doc["players"]),
        }

        time.sleep(SLEEP_BETWEEN)

    # Write metadata (always overwrite)
    write_json(META_PATH, meta)

    # For downstream jobs that look at this process output, we announce that we wrote files
    print("changed=true")

if __name__ == "__main__":
    main()
