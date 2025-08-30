# Data Directory

This directory contains scraped Kicktipp data and computed standings.

## Structure

- `season-2024-25/spieltage/` - Individual Spieltag JSON files (01.json, 02.json, etc.)
- `season-2024-25/standings.json` - Computed season standings from complete Spieltage
- `season-2024-25/metadata.json` - Scraper metadata (last run, statuses)

## Data Flow

1. GitHub Actions runs scraper on schedule
2. Scraper fetches Kicktipp data and writes Spieltag JSON files
3. compute_wurstliga.py aggregates complete Spieltage into standings.json
4. Astro site reads these JSON files at build time
5. Only files that actually changed get committed