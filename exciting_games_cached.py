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
        self.cache_file = Path(__file__).parent / "match_cache.json"
    
    async def find_exciting_games(self) -> List[Dict[str, Any]]:
        """
        Find exciting games from cached data.
        
        Returns:
            List of match analyses, sorted by excitement score
        """
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
