from __future__ import annotations

# Kicktipp group + season
KICKTIPP_BASE = "https://www.kicktipp.de"
KICKTIPP_GROUP = "wurstliga"
TIPPUEBERSICHT_PATH = f"/{KICKTIPP_GROUP}/tippuebersicht"
TIPPSEASON_ID = 3944954        # from your URL
SEASON = "2025-26"
SPIELTAGE = list(range(1, 35)) # Bundesliga has 34

# Wurstliga points ladder per dense rank group (extend as you like)
# Example: 1st group=10, 2nd=8, 3rd=6, then 5,4,3,2,1,...
WURSTLIGA_LADDER = [10, 8, 6, 5, 4, 3, 2, 1]

# A Spieltag is considered COMPLETE only if all 9 matches have a result like "a:b"
MATCHES_PER_SPIELTAG = 9

# Scraper politeness
USER_AGENT = "wurstliga-scraper/1.0 (+github actions)"
TIMEOUT = 30
RETRY = 2
SLEEP_BETWEEN = 1.0

# Timezone
TZ = "Europe/Berlin"