#!/usr/bin/env python3
"""
Cached version of ExcitingGameFinder that works with pre-fetched data from API-Football
Supports both EPL and Champions League with separate cache files.
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path


class CachedExcitingGameFinder:
    """Uses cached match data instead of live API calls."""
    
    # Cache file mapping by league
    CACHE_FILES = {
        'EPL': 'match_cache_epl.json',
        'UCL': 'match_cache_ucl.json',
    }
    
    def __init__(self, days_back: int, leagues: List[str] = None, debug: bool = False):
        """
        Initialize the finder with cache support.
        
        Args:
            days_back: Number of days to look back for matches
            leagues: List of leagues to search (e.g., ['EPL', 'UCL']). Defaults to ['EPL']
            debug: If True, shows xG and goals in output
        """
        self.days_back = days_back
        self.leagues = [l.upper() for l in (leagues if leagues else ['EPL'])]
        self.debug = debug
        self.cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Validate leagues
        for league in self.leagues:
            if league not in self.CACHE_FILES:
                raise ValueError(f"Unsupported league: {league}. Must be 'EPL' or 'UCL'")
    
    def is_cache_stale(self, league: str) -> bool:
        """
        Check if the cache for a specific league is from earlier than today.
        
        Args:
            league: League code ('EPL' or 'UCL')
            
        Returns:
            True if cache doesn't exist or is not from today, False otherwise
        """
        cache_filename = self.CACHE_FILES.get(league)
        cache_file = Path(__file__).parent / cache_filename
        
        if not cache_file.exists():
            print(f"Cache file {cache_filename} does not exist - needs refresh")
            return True
        
        try:
            with open(cache_file, 'r') as f:
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
    
    async def refresh_cache(self, league: str, days_back: int = 30):
        """
        Refresh the cache by fetching new data from the live API for a specific league.
        
        Args:
            league: League code ('EPL' or 'UCL')
            days_back: Number of days to fetch (default 30)
        """
        cache_filename = self.CACHE_FILES.get(league)
        cache_file = Path(__file__).parent / cache_filename
        
        print(f"\n{'='*70}")
        print(f"Refreshing {league} cache with the last {days_back} days of data...")
        print(f"{'='*70}")
        
        try:
            # Import here to avoid circular dependency
            from exciting_games import ExcitingGameFinder
            
            # Fetch fresh data using the live API
            finder = ExcitingGameFinder(days_back=days_back, leagues=[league], debug=True)
            exciting_games = await finder.find_exciting_games()
            
            # Save to cache file
            cache_data = {
                'cached_at': datetime.now().isoformat(),
                'days_back': days_back,
                'league': league,
                'games': exciting_games
            }
            
            with open(cache_file, 'w') as f:
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
        Find exciting games from cached data across all selected leagues.
        Auto-refreshes cache if it's not from today.
        
        Returns:
            List of match analyses, sorted by excitement score
        """
        all_games = []
        
        # Process each league
        for league in self.leagues:
            cache_filename = self.CACHE_FILES.get(league)
            cache_file = Path(__file__).parent / cache_filename
            
            # Check if cache needs refresh
            if self.is_cache_stale(league):
                print(f"{league} cache is stale, attempting to refresh...")
                try:
                    await self.refresh_cache(league, days_back=30)  # Default to 30 days for cache
                except Exception as e:
                    print(f"Failed to refresh {league} cache, will try to use existing data: {e}")
            
            print(f"Loading cached match data for {league}...")
            
            # Check if cache exists
            if not cache_file.exists():
                print(f"ERROR: {cache_filename} not found!")
                print("Run cache_data.py locally first to generate the cache.")
                continue
            
            # Load cached data
            with open(cache_file, 'r') as f:
                cache = json.load(f)
            
            games = cache.get('games', [])
            cached_at = cache.get('cached_at', 'unknown')
            cached_league = cache.get('league', 'unknown')
            
            print(f"Cache created at: {cached_at}")
            print(f"Cache league: {cached_league}")
            print(f"Total games in cache: {len(games)}")
            
            # Filter by requested time window
            for game in games:
                try:
                    game_date = datetime.strptime(game['date'], '%Y-%m-%d %H:%M:%S')
                    if game_date >= self.cutoff_date:
                        all_games.append(game)
                except (ValueError, KeyError):
                    continue
        
        print(f"Games matching {self.days_back} day window across all leagues: {len(all_games)}")
        
        # Sort by excitement score
        all_games.sort(key=lambda x: x.get('excitement_score', 0), reverse=True)
        
        return all_games
