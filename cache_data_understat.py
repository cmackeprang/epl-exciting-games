#!/usr/bin/env python3
"""
Cache data fetcher - Run this locally to fetch and cache match data
This avoids API blocking issues on Render by using pre-fetched data
"""

import asyncio
import json
from datetime import datetime
from exciting_games_understat import ExcitingGameFinder

async def cache_matches(days_back: int = 30):
    """Fetch and cache match data locally."""
    print(f"Fetching matches for the last {days_back} days...")
    
    finder = ExcitingGameFinder(days_back=days_back, debug=True)
    exciting_games = await finder.find_exciting_games()
    
    # Save to JSON
    cache_data = {
        'cached_at': datetime.now().isoformat(),
        'days_back': days_back,
        'games': exciting_games
    }
    
    with open('match_cache_understat.json', 'w') as f:
        json.dump(cache_data, f, indent=2)
    
    print(f"\n✅ Cached {len(exciting_games)} exciting matches to match_cache_understat.json")
    print(f"Cache will be used on Render deployment")
    print(f"\nRemember to:")
    print("1. git add match_cache_understat.json")
    print("2. git commit -m 'Update match cache'")
    print("3. git push")

if __name__ == "__main__":
    asyncio.run(cache_matches(30))
