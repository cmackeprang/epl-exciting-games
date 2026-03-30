#!/usr/bin/env python3
"""
Cache data fetcher for API-Football
Run this locally to fetch and cache match data for EPL and Champions League
This avoids API rate limits on Render by using pre-fetched data
"""

import asyncio
import json
from datetime import datetime
from exciting_games import ExcitingGameFinder


async def cache_league(league: str, days_back: int = 30):
    """
    Fetch and cache match data for a specific league.
    
    Args:
        league: 'EPL' or 'UCL'
        days_back: Number of days to fetch (default 30)
    """
    print(f"\n{'='*70}")
    print(f"Fetching {league} matches for the last {days_back} days...")
    print(f"{'='*70}\n")
    
    try:
        finder = ExcitingGameFinder(days_back=days_back, leagues=[league], debug=True)
        exciting_games = await finder.find_exciting_games()
        
        # Determine cache filename
        cache_filename = f'match_cache_{league.lower()}.json'
        
        # Save to JSON
        cache_data = {
            'cached_at': datetime.now().isoformat(),
            'days_back': days_back,
            'league': league,
            'games': exciting_games
        }
        
        with open(cache_filename, 'w') as f:
            json.dump(cache_data, f, indent=2)
        
        print(f"\n✅ Cached {len(exciting_games)} exciting {league} matches to {cache_filename}")
        return True
        
    except Exception as e:
        print(f"\n❌ Error caching {league} data: {e}")
        return False


async def cache_all_leagues(days_back: int = 30):
    """
    Fetch and cache match data for all supported leagues.
    
    Args:
        days_back: Number of days to fetch (default 30)
    """
    leagues = ['EPL', 'UCL']
    
    results = {}
    for league in leagues:
        success = await cache_league(league, days_back)
        results[league] = success
    
    print(f"\n{'='*70}")
    print("CACHE GENERATION SUMMARY")
    print(f"{'='*70}")
    for league, success in results.items():
        status = "✅ Success" if success else "❌ Failed"
        print(f"{league}: {status}")
    
    print(f"\nCache files will be used on Render deployment")
    print(f"\nRemember to:")
    print("1. git add match_cache_epl.json match_cache_ucl.json")
    print("2. git commit -m 'Update match caches'")
    print("3. git push")
    print(f"{'='*70}\n")


async def main():
    """Main execution with user choice."""
    print("="*70)
    print("API-Football Cache Generator")
    print("="*70)
    print("\nThis will fetch match data and save it locally.")
    print("Choose what to cache:")
    print("1. EPL only")
    print("2. Champions League only")
    print("3. Both leagues")
    print()
    
    try:
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == '1':
            await cache_league('EPL', days_back=30)
        elif choice == '2':
            await cache_league('UCL', days_back=30)
        elif choice == '3':
            await cache_all_leagues(days_back=30)
        else:
            print("Invalid choice. Please run again and select 1, 2, or 3.")
            
    except KeyboardInterrupt:
        print("\n\nOperation cancelled.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
