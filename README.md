# Wurstliga – Zero‑Cost Astro + Tailwind Starter

Drop‑in blueprint to replace Streamlit + CSV with a zero‑cost stack:

* **Scrape Kicktipp** on a schedule via **GitHub Actions**
* Store normalized **JSON** in the repo (`/data`) and commit only when data actually changes
* **Astro + Tailwind** static site (GitHub Pages) with charts & tables
* Robust Spieltag lifecycle: `not_started` → `in_progress` → `complete`. Only completed Spieltage count toward season standings
* Fully configurable **Wurstliga points ladder** + tie handling

## Quick Start

1. **Update configuration**: Edit `scraper/config.py` with your Kicktipp group details
2. **Update site URL**: Edit `site/astro.config.mjs` with your GitHub Pages URL
3. **Install dependencies**: 
   ```bash
   cd scraper && pip install -r requirements.txt
   cd ../site && pnpm install
   ```
4. **Test locally**:
   ```bash
   cd scraper && python scrape_kicktipp.py && python compute_wurstliga.py
   cd ../site && pnpm dev
   ```
5. **Deploy**: Push to GitHub, enable GitHub Pages and Actions

## Architecture

- **Scraper** (`/scraper`): Python scripts that fetch Kicktipp data
- **Data** (`/data`): JSON files with Spieltag data and computed standings
- **Site** (`/site`): Astro + Tailwind frontend that reads the JSON data
- **Workflows** (`/.github/workflows`): Automated scraping and deployment

## Features

- ✅ Automated Kicktipp scraping with schedule
- ✅ Dense ranking system with configurable points ladder
- ✅ Robust status tracking (not_started/in_progress/complete)
- ✅ Interactive charts showing rank evolution
- ✅ Individual Spieltag detail pages
- ✅ Zero hosting costs (GitHub Pages)
- ✅ Only commits when data actually changes

## Configuration

Key settings in `scraper/config.py`:
- `KICKTIPP_GROUP`: Your Kicktipp group name
- `TIPPSEASON_ID`: Season ID from your Kicktipp URL
- `WURSTLIGA_LADDER`: Points distribution [10, 8, 6, 5, 4, 3, 2, 1]

## GitHub Setup

1. Enable GitHub Actions in repository settings
2. Enable GitHub Pages → Deploy from GitHub Actions
3. Actions will run automatically on the defined schedule

## Local Development

```bash
# Run scraper once to create /data
cd scraper && pip install -r requirements.txt
python scrape_kicktipp.py && python compute_wurstliga.py

# Dev the site
cd ../site && pnpm install && pnpm dev
```

Visit `http://localhost:4321` to see your site.

## Customization

- **Points system**: Modify `WURSTLIGA_LADDER` in `config.py`
- **Scraping schedule**: Edit cron expressions in `.github/workflows/scrape.yml`
- **Styling**: Customize Tailwind theme in `site/tailwind.config.mjs`
- **Branding**: Update colors, logo, and text throughout the site