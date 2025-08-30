# Wurstliga Scraper

Scrapes Kicktipp data and computes Wurstliga standings.

## Files

- `config.py` - Configuration (Kicktipp URLs, scoring ladder, etc.)
- `scrape_kicktipp.py` - Main scraper that fetches Spieltag data
- `compute_wurstliga.py` - Computes season standings from complete Spieltage
- `requirements.txt` - Python dependencies

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run scraper once
python scrape_kicktipp.py

# Compute standings
python compute_wurstliga.py
```

## Configuration

Edit `config.py` to:
- Change Kicktipp group/season URLs
- Adjust Wurstliga points ladder
- Modify scraper behavior (delays, retries, etc.)

## Data Model

The scraper outputs JSON files with Spieltag status tracking:
- `not_started` - No results yet
- `in_progress` - Some but not all results available  
- `complete` - All 9 matches have results

Only `complete` Spieltage count toward season standings.