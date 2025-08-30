#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import re
import json

# Test scraper to debug parsing
URL = "https://www.kicktipp.de/wurstliga/tippuebersicht?tippsaisonId=3944954&spieltagIndex=1"
NUM_RE = re.compile(r"^\s*(\d+)\s*:\s*(\d+)\s*$")

def test_parsing():
    print(f"Fetching: {URL}")
    r = requests.get(URL, headers={"User-Agent": "test-scraper"})
    soup = BeautifulSoup(r.text, "lxml")
    
    print("\n=== LOOKING FOR MATCHES TABLE ===")
    matches = []
    for i, tbl in enumerate(soup.find_all("table")):
        headers = [th.get_text(strip=True) for th in tbl.find_all("th")]
        print(f"Table {i}: Headers = {headers[:5]}...")
        
        if {"Termin", "Heim", "Gast", "Ergebnis"}.issubset(set(headers)):
            print(f"✅ FOUND MATCHES TABLE {i}")
            tbody = tbl.find("tbody") or tbl
            rows = tbody.find_all("tr")
            print(f"Rows found: {len(rows)}")
            
            for j, tr in enumerate(rows):
                tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
                if len(tds) >= 4:
                    termin, heim, gast, ergebnis = tds[0], tds[1], tds[2], tds[3]
                    print(f"  Match {j+1}: {heim} vs {gast} = '{ergebnis}'")
                    matches.append({"home": heim, "away": gast, "result": ergebnis})
                else:
                    print(f"  Row {j+1}: Only {len(tds)} columns, skipping")
            break
    
    print(f"\nTotal matches parsed: {len(matches)}")
    
    print("\n=== LOOKING FOR PLAYER TABLE ===")
    players = []
    for i, tbl in enumerate(soup.find_all("table")):
        header_text = " ".join(th.get_text(strip=True) for th in tbl.find_all("th"))
        if "Name" in header_text and "P" in header_text:
            print(f"✅ FOUND PLAYER TABLE {i}")
            headers = [th.get_text(strip=True) for th in tbl.find_all("th")]
            print(f"Headers: {headers}")
            
            tbody = tbl.find("tbody") or tbl
            rows = tbody.find_all("tr")
            print(f"Player rows found: {len(rows)}")
            
            # Find name and P column indices
            try:
                name_idx = headers.index("Name")
            except ValueError:
                name_idx = 2 if len(headers) > 2 else 0
            
            p_indices = [i for i, h in enumerate(headers) if h == "P"]
            p_idx = p_indices[-1] if p_indices else max(0, len(headers) - 3)
            
            print(f"Name column: {name_idx}, P column: {p_idx}")
            
            for j, tr in enumerate(rows):
                tds = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
                if len(tds) > max(name_idx, p_idx):
                    name = tds[name_idx].strip() if name_idx < len(tds) else "?"
                    p_raw = tds[p_idx].strip() if p_idx < len(tds) else "0"
                    if name and name != "?" and not name.startswith("endOfBlock"):
                        print(f"  Player {j+1}: {name} = {p_raw} points")
                        try:
                            p_val = int(p_raw)
                            players.append({"name": name, "kicktipp_P": p_val})
                        except:
                            print(f"    Warning: Could not parse points '{p_raw}' for {name}")
                else:
                    print(f"  Row {j+1}: Only {len(tds)} columns, need {max(name_idx, p_idx)+1}")
            break
    
    print(f"\nTotal players parsed: {len(players)}")
    
    # Write results
    result = {
        "matches": matches,
        "players": players,
        "total_matches": len(matches),
        "total_players": len(players)
    }
    
    with open("test_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\nResults written to test_result.json")

if __name__ == "__main__":
    test_parsing()