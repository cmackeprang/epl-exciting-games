#!/usr/bin/env python3
"""
Cached version of ExcitingGameFinder that works with pre-fetched data
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path


class CachedExcitingGameFinder:
    """Uses cached match data instead of live API calls."""
    
    def __init__(self, days_back: int, debug: bool = False):
        """
        Initialize the finder with cache support.
        
        Args:
            days_back: Number of days to look back for matches
            debug: If True, shows xG and goals in output
        """
        self.days_back = days_back
        self.debug = debug
        self.cutoff_date = datetime.now() - timedelta(days=days_back)
        self.cache_file = Path(__file__).parent / "match_cache_understat.json"
    
    def is_cache_stale(self) -> bool:
        """
        Check if the cache is from earlier than today.
        
        Returns:
            True if cache doesn't exist or is not from today, False otherwise
        """
        if not self.cache_file.exists():
            print("Cache file does not exist - needs refresh")
            return True
        
        try:
            with open(self.cache_file, 'r') as f:
                cache = json.load(f)
            
            cached_at_str = cache.get('cached_at', '')
            if not cached_at_str:
                print("Cache has no timestamp - needs refresh")
                return True
            
            # Parse the ISO format timestamp
            cached_at = datetime.fromisoformat(cached_at_str)
            today = datetime.now().date()
            cache_date = cached_at.date()
            
            if cache_date < today:
                print(f"Cache is from {cache_date}, today is {today} - needs refresh")
                return True
            else:
                print(f"Cache is from today ({cache_date}) - no refresh needed")
                return False
                
        except Exception as e:
            print(f"Error checking cache staleness: {e} - assuming stale")
            return True
    
    async def refresh_cache(self, days_back: int = 30):
        """
        Refresh the cache by fetching new data from the live API.
        
        Args:
            days_back: Number of days to fetch (default 30)
        """
        print(f"\n{'='*70}")
        print(f"Refreshing cache with the last {days_back} days of data...")
        print(f"{'='*70}")
        
        try:
            # Import here to avoid circular dependency
            from exciting_games_understat import ExcitingGameFinder
            
            # Fetch fresh data using the live API
            finder = ExcitingGameFinder(days_back=days_back, debug=True)
            exciting_games = await finder.find_exciting_games()
            
            # Save to cache file
            cache_data = {
                'cached_at': datetime.now().isoformat(),
                'days_back': days_back,
                'games': exciting_games
            }
            
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            print(f"✅ Cache refreshed successfully with {len(exciting_games)} matches")
            print(f"{'='*70}\n")
            
        except Exception as e:
            print(f"❌ Error refreshing cache: {e}")
            print("Will attempt to use existing cache data if available")
            print(f"{'='*70}\n")
            raise
    
    async def find_exciting_games(self) -> List[Dict[str, Any]]:
        """
        Find exciting games from cached data.
        Auto-refreshes cache if it's not from today.
        
        Returns:
            List of match analyses, sorted by excitement score
        """
        # Check if cache needs refresh
        if self.is_cache_stale():
            print("Cache is stale, attempting to refresh...")
            try:
                await self.refresh_cache(days_back=30)  # Default to 30 days for cache
            except Exception as e:
                print(f"Failed to refresh cache, will try to use existing data: {e}")
        
        print(f"Loading cached match data...")
        
        # Check if cache exists
        if not self.cache_file.exists():
            print("ERROR: match_cache.json not found!")
            print("Run cache_data.py locally first to generate the cache.")
            return []
        
        # Load cached data
        with open(self.cache_file, 'r') as f:
            cache = json.load(f)
        
        all_games = cache.get('games', [])
        cached_at = cache.get('cached_at', 'unknown')
        
        print(f"Cache created at: {cached_at}")
        print(f"Total games in cache: {len(all_games)}")
        
        # Filter by requested time window
        filtered_games = []
        for game in all_games:
            try:
                game_date = datetime.strptime(game['date'], '%Y-%m-%d %H:%M:%S')
                if game_date >= self.cutoff_date:
                    filtered_games.append(game)
            except (ValueError, KeyError):
                continue
        
        print(f"Games matching {self.days_back} day window: {len(filtered_games)}")
        
        # Sort by excitement score
        filtered_games.sort(key=lambda x: x.get('excitement_score', 0), reverse=True)
        
        return filtered_games
