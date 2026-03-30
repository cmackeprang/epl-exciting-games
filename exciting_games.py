#!/usr/bin/env python3
"""
EPL Exciting Game Finder - Identifies exciting Premier League matches worth watching
based on xG and goal statistics from Understat, without spoiling the final scores.
"""

import asyncio
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import json
import ssl
import certifi

import aiohttp
from understat import Understat


class ExcitingGameFinder:
    """Analyzes EPL matches to identify exciting games using xG-based diagnostics."""
    
    def __init__(self, days_back: int, debug: bool = False):
        """
        Initialize the finder.
        
        Args:
            days_back: Number of days to look back for matches
            debug: If True, shows xG and goals in output for validation
        """
        self.days_back = days_back
        self.debug = debug
        self.cutoff_date = datetime.now() - timedelta(days=days_back)
        
    async def fetch_recent_epl_matches(self) -> List[Dict[str, Any]]:
        """
        Fetch EPL matches from the specified time window.
        
        Returns:
            List of match dictionaries with relevant data
        """
        print(f"Fetching EPL matches from the last {self.days_back} days...")
        print(f"Current date: {datetime.now()}")
        print(f"Cutoff date: {self.cutoff_date}")
        
        # Create session with proper headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Create timeout and SSL context for better reliability
        timeout = aiohttp.ClientTimeout(total=60, connect=10)
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        async with aiohttp.ClientSession(headers=headers, timeout=timeout, connector=connector) as session:
            understat = Understat(session)
            
            # Get current season (2025/2026 season)
            current_year = datetime.now().year
            # EPL seasons typically start in August, so if we're before August, use previous year
            if datetime.now().month < 8:
                season = current_year - 1
            else:
                season = current_year
            
            print(f"Fetching data for season: {season}")
            
            try:
                # Fetch EPL league data for the current season
                print(f"Making API request to Understat for EPL {season}...")
                league_results = await understat.get_league_results(
                    league_name="EPL",
                    season=season
                )
                
                # Check if we got valid data
                if league_results is None:
                    print("ERROR: Received None from Understat API")
                    print("This suggests the API request failed or was blocked")
                    return []
                
                if not isinstance(league_results, list):
                    print(f"ERROR: Expected list from API, got {type(league_results)}")
                    print(f"Data received: {league_results}")
                    return []
                
                print(f"Total matches fetched from Understat: {len(league_results)}")
                
                # Filter matches within our time window
                recent_matches = []
                for match in league_results:
                    # Parse match datetime
                    match_datetime_str = match.get('datetime')
                    if match_datetime_str:
                        try:
                            match_datetime = datetime.strptime(
                                match_datetime_str, 
                                '%Y-%m-%d %H:%M:%S'
                            )
                            
                            # Check if match is within our window and has finished
                            if (match_datetime >= self.cutoff_date and 
                                match_datetime <= datetime.now() and
                                match.get('isResult', False)):
                                recent_matches.append(match)
                        except ValueError:
                            # Skip matches with invalid datetime format
                            continue
                
                print(f"Found {len(recent_matches)} completed matches in the time window.")
                if len(recent_matches) > 0:
                    print(f"First match date: {recent_matches[0].get('datetime')}")
                    print(f"Last match date: {recent_matches[-1].get('datetime')}")
                return recent_matches
                
            except Exception as e:
                print(f"Error fetching match data: {e}")
                print(f"Error type: {type(e).__name__}")
                import traceback
                traceback.print_exc()
                print("This may be due to network issues or Understat API changes.")
                return []
    
    def check_competitive_threat(self, home_xg: float, away_xg: float) -> bool:
        """
        Check if both teams created significant threats (both xG > 1.5).
        
        Args:
            home_xg: Home team expected goals
            away_xg: Away team expected goals
            
        Returns:
            True if both teams exceeded 1.5 xG
        """
        return home_xg > 1.5 and away_xg > 1.5
    
    def check_goal_overperformance(
        self, 
        home_goals: int, 
        away_goals: int,
        home_xg: float, 
        away_xg: float
    ) -> bool:
        """
        Check if combined goals exceeded combined xG by at least 2.3.
        
        Args:
            home_goals: Home team actual goals
            away_goals: Away team actual goals
            home_xg: Home team expected goals
            away_xg: Away team expected goals
            
        Returns:
            True if (goals - xG) >= 2.3
        """
        total_goals = home_goals + away_goals
        total_xg = home_xg + away_xg
        return (total_goals - total_xg) >= 2.3
    
    def check_significant_deviation(
        self,
        home_goals: int,
        away_goals: int,
        home_xg: float,
        away_xg: float
    ) -> bool:
        """
        Check if either team's goals deviated from xG by at least 2.0.
        
        Args:
            home_goals: Home team actual goals
            away_goals: Away team actual goals
            home_xg: Home team expected goals
            away_xg: Away team expected goals
            
        Returns:
            True if either team's |goals - xG| >= 2.0
        """
        home_deviation = abs(home_goals - home_xg)
        away_deviation = abs(away_goals - away_xg)
        return home_deviation >= 2.0 or away_deviation >= 2.0
    
    async def analyze_match(self, match: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a single match for excitement factors.
        
        Args:
            match: Match data from Understat
            
        Returns:
            Dictionary with excitement analysis results
        """
        # Extract basic match info
        match_id = match.get('id')
        home_team = match.get('h', {}).get('title', 'Unknown')
        away_team = match.get('a', {}).get('title', 'Unknown')
        home_goals = int(match.get('goals', {}).get('h', 0))
        away_goals = int(match.get('goals', {}).get('a', 0))
        home_xg = float(match.get('xG', {}).get('h', 0.0))
        away_xg = float(match.get('xG', {}).get('a', 0.0))
        match_date = match.get('datetime', '')
        
        # Run diagnostic checks
        is_competitive = self.check_competitive_threat(home_xg, away_xg)
        is_overperforming = self.check_goal_overperformance(
            home_goals, away_goals, home_xg, away_xg
        )
        has_deviation = self.check_significant_deviation(
            home_goals, away_goals, home_xg, away_xg
        )
        
        # Collect reasons this match is exciting
        reasons = []
        if is_competitive:
            reasons.append("High-quality chances for both sides")
        if is_overperforming:
            reasons.append("Unpredictable finishing - goals exceed expectations")
        if has_deviation:
            reasons.append("Significant deviation from expected outcomes")
        
        # Calculate composite excitement score
        excitement_score = 0
        if is_competitive:
            excitement_score += 2  # High weight
        if is_overperforming:
            excitement_score += 2  # High weight
        if has_deviation:
            excitement_score += 2  # High weight
        
        # Match is exciting if ANY criterion is met
        is_exciting = len(reasons) > 0
        
        return {
            'match_id': match_id,
            'date': match_date,
            'home_team': home_team,
            'away_team': away_team,
            'home_goals': home_goals,
            'away_goals': away_goals,
            'home_xg': home_xg,
            'away_xg': away_xg,
            'excitement_score': excitement_score,
            'is_exciting': is_exciting,
            'reasons': reasons,
        }
    
    async def find_exciting_games(self) -> List[Dict[str, Any]]:
        """
        Main method to find and rank exciting games.
        
        Returns:
            List of match analyses, sorted by excitement score
        """
        # Fetch recent matches
        matches = await self.fetch_recent_epl_matches()
        
        if not matches:
            print("No matches found in the specified time window.")
            return []
        
        # Analyze each match
        print(f"\nAnalyzing {len(matches)} matches for excitement factors...")
        analyses = []
        for match in matches:
            analysis = await self.analyze_match(match)
            analyses.append(analysis)
        
        # Filter to exciting games only and sort by score
        exciting_games = [a for a in analyses if a['is_exciting']]
        exciting_games.sort(key=lambda x: x['excitement_score'], reverse=True)
        
        return exciting_games
    
    def display_results(self, exciting_games: List[Dict[str, Any]]):
        """
        Display the results in a user-friendly format.
        
        Args:
            exciting_games: List of analyzed exciting matches
        """
        if not exciting_games:
            print("\n" + "="*70)
            print("No particularly exciting matches found in this time window.")
            print("Try increasing the number of days or waiting for more games.")
            print("="*70)
            return
        
        print("\n" + "="*70)
        print(f"🏆 EXCITING EPL MATCHES - Top {len(exciting_games)} Game(s) Worth Watching")
        print("="*70)
        
        for i, game in enumerate(exciting_games, 1):
            # Format date
            try:
                match_date = datetime.strptime(game['date'], '%Y-%m-%d %H:%M:%S')
                date_str = match_date.strftime('%A, %B %d, %Y')
            except:
                date_str = game['date']
            
            print(f"\n{i}. {game['home_team']} vs {game['away_team']}")
            print(f"   Date: {date_str}")
            
            # Debug mode: show excitement score, reasons, and actual stats
            if self.debug:
                print(f"   [DEBUG] Excitement Score: {game['excitement_score']:.2f}")
                
                if game['reasons']:
                    print(f"   Why it's exciting:")
                    for reason in game['reasons']:
                        print(f"      • {reason}")
                
                print(f"   [DEBUG] Score: {game['home_goals']}-{game['away_goals']}")
                print(f"   [DEBUG] xG: {game['home_xg']:.2f} - {game['away_xg']:.2f}")
        
        print("\n" + "="*70)


def get_user_input() -> Tuple[int, bool]:
    """
    Get user input for the time window and debug mode.
    
    Returns:
        Tuple of (days_back, debug_mode)
    """
    print("="*70)
    print("EPL Exciting Game Finder")
    print("="*70)
    print("\nThis program analyzes recent Premier League matches to identify")
    print("exciting games worth watching, without spoiling the results.")
    print()
    
    # Get number of days
    while True:
        try:
            days_input = input("How many days back should I check for matches? (1-90): ").strip()
            days = int(days_input)
            if 1 <= days <= 90:
                break
            else:
                print("Please enter a number between 1 and 90.")
        except ValueError:
            print("Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            exit(0)
    
    # Check for debug mode via command line
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--debug', action='store_true', help='Show xG and goals for validation')
    args, _ = parser.parse_known_args()
    
    return days, args.debug


async def main():
    """Main entry point for the program."""
    # Get user input
    days_back, debug_mode = get_user_input()
    
    # Create finder and run analysis
    finder = ExcitingGameFinder(days_back=days_back, debug=debug_mode)
    exciting_games = await finder.find_exciting_games()
    
    # Display results
    finder.display_results(exciting_games)
    
    print("\nNote: Scores and final results are hidden to preserve the excitement!")
    print("Watch the replays to see how these thrilling matches unfolded.\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nProgram interrupted by user. Exiting...")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        print("Please check your internet connection and try again.")
