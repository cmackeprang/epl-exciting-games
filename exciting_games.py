#!/usr/bin/env python3
"""
Exciting Game Finder - Identifies exciting football matches worth watching
based on xG and goal statistics from API-Football (RapidAPI), without spoiling the final scores.
Supports EPL and Champions League.
"""

import asyncio
import argparse
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import json

import aiohttp
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ExcitingGameFinder:
    """Analyzes football matches to identify exciting games using xG-based diagnostics."""
    
    # League IDs for API-Football
    LEAGUE_IDS = {
        'EPL': 39,
        'UCL': 2,  # UEFA Champions League
    }
    
    LEAGUE_NAMES = {
        39: 'Premier League',
        2: 'Champions League',
    }
    
    def __init__(self, days_back: int, leagues: List[str] = None, debug: bool = False):
        """
        Initialize the finder.
        
        Args:
            days_back: Number of days to look back for matches
            leagues: List of leagues to search (e.g., ['EPL', 'UCL']). Defaults to ['EPL']
            debug: If True, shows xG and goals in output for validation
        """
        self.days_back = days_back
        self.leagues = leagues if leagues else ['EPL']
        
        # Validate leagues
        for league in self.leagues:
            if league.upper() not in self.LEAGUE_IDS:
                raise ValueError(f"Unsupported league: {league}. Must be 'EPL' or 'UCL'")
        
        self.leagues = [l.upper() for l in self.leagues]
        self.debug = debug
        self.cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Get API key from environment
        self.api_key = os.getenv('API_FOOTBALL_KEY')
        if not self.api_key:
            raise ValueError(
                "API_FOOTBALL_KEY not found in environment variables. "
                "Please set it in .env file or environment."
            )
        
    async def fetch_recent_matches(self, league: str) -> List[Dict[str, Any]]:
        """
        Fetch matches from the specified time window using API-Football.
        
        Args:
            league: League code ('EPL' or 'UCL')
            
        Returns:
            List of match dictionaries with relevant data
        """
        league_id = self.LEAGUE_IDS.get(league)
        league_name = self.LEAGUE_NAMES.get(league_id, league)
        
        print(f"Fetching {league_name} matches from the last {self.days_back} days...")
        print(f"Current date: {datetime.now()}")
        print(f"Cutoff date: {self.cutoff_date}")
        
        # API-Football free tier only has access to seasons 2022-2024
        # Use 2024 season data (2024-2025 season: Aug 2024 - May 2025)
        # Since we're in 2026, we fetch all 2024 season matches and filter to most recent
        season = 2024
        print(f"Using season: {season} (free tier limitation: 2022-2024 only)")
        print(f"Note: Season 2024 = 2024-2025 season (Aug 2024 - May 2025)")
        print(f"Will fetch all season matches and return most recent {self.days_back} days worth")
        
        # API-Football Direct endpoint and headers
        base_url = "https://v3.football.api-sports.io"
        headers = {
            'x-apisports-key': self.api_key
        }
        
        timeout = aiohttp.ClientTimeout(total=60, connect=10)
        
        try:
            async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
                # Fetch ALL fixtures for the league and season (no date filter)
                fixtures_url = (
                    f"{base_url}/fixtures"
                    f"?league={league_id}"
                    f"&season={season}"
                    f"&status=FT"  # Only finished matches
                )
                
                print(f"Making API request to API-Football...")
                print(f"URL: {fixtures_url}")
                
                async with session.get(fixtures_url) as response:
                    if response.status != 200:
                        print(f"ERROR: API returned status {response.status}")
                        response_text = await response.text()
                        print(f"Response: {response_text[:500]}")
                        return []
                    
                    data = await response.json()
                    
                    if 'errors' in data and data['errors']:
                        print(f"ERROR: API returned errors: {data['errors']}")
                        return []
                    
                    fixtures = data.get('response', [])
                    print(f"Total fixtures fetched: {len(fixtures)}")
                    
                    if not fixtures:
                        print(f"No fixtures found for {league_name} season {season}")
                        return []
                    
                    # Sort by date descending to get most recent first
                    fixtures.sort(key=lambda x: x['fixture']['date'], reverse=True)
                    
                    # Limit number of fixtures to process (to save API calls)
                    max_fixtures = min(len(fixtures), 50)  # Process up to 50 most recent matches
                    recent_fixtures = fixtures[:max_fixtures]
                    
                    print(f"Processing {len(recent_fixtures)} most recent fixtures")
                    
                    # Now fetch statistics for each fixture to get xG data
                    matches_with_stats = []
                    for fixture in recent_fixtures:
                        fixture_id = fixture['fixture']['id']
                        
                        # Fetch statistics for this fixture
                        stats_url = f"{base_url}/fixtures/statistics?fixture={fixture_id}"
                        
                        async with session.get(stats_url) as stats_response:
                            if stats_response.status == 200:
                                stats_data = await stats_response.json()
                                fixture['statistics'] = stats_data.get('response', [])
                                matches_with_stats.append(fixture)
                            else:
                                print(f"Warning: Could not fetch statistics for fixture {fixture_id}")
                    
                    print(f"Found {len(matches_with_stats)} matches with statistics")
                    return matches_with_stats
                    
        except Exception as e:
            print(f"Error fetching match data: {e}")
            print(f"Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return []
    
    def extract_xg_from_stats(self, statistics: List[Dict[str, Any]]) -> Tuple[float, float]:
        """
        Extract xG data from API-Football statistics.
        
        Args:
            statistics: List of team statistics from API-Football
            
        Returns:
            Tuple of (home_xg, away_xg)
        """
        home_xg = 0.0
        away_xg = 0.0
        
        for team_stats in statistics:
            # Find the xG statistic
            for stat in team_stats.get('statistics', []):
                if stat.get('type') == 'expected_goals':
                    xg_value = stat.get('value')
                    if xg_value is not None:
                        try:
                            xg = float(xg_value)
                            # Check if this is home or away team
                            if team_stats.get('team', {}).get('id') == team_stats.get('team', {}).get('id'):
                                # Determine home/away by looking at fixture data
                                # This will be set in analyze_match where we have full context
                                pass
                        except (ValueError, TypeError):
                            pass
        
        return home_xg, away_xg
    
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
    
    async def analyze_match(self, match: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze a single match for excitement factors.
        
        Args:
            match: Match data from API-Football
            
        Returns:
            Dictionary with excitement analysis results, or None if xG data unavailable
        """
        # Extract basic match info from API-Football structure
        fixture_id = match['fixture']['id']
        home_team = match['teams']['home']['name']
        away_team = match['teams']['away']['name']
        home_goals = match['goals']['home'] or 0
        away_goals = match['goals']['away'] or 0
        match_date = match['fixture']['date']  # ISO format
        league_id = match['league']['id']
        
        # Parse and format date
        try:
            match_datetime = datetime.fromisoformat(match_date.replace('Z', '+00:00'))
            formatted_date = match_datetime.strftime('%Y-%m-%d %H:%M:%S')
        except:
            formatted_date = match_date
        
        # Extract xG data from statistics
        home_xg = 0.0
        away_xg = 0.0
        
        home_team_id = match['teams']['home']['id']
        
        statistics = match.get('statistics', [])
        
        for team_stats in statistics:
            team_id = team_stats.get('team', {}).get('id')
            team_name = team_stats.get('team', {}).get('name')
            is_home = (team_id == home_team_id)
            
            # Find xG in statistics
            for stat in team_stats.get('statistics', []):
                stat_type = stat.get('type')
                stat_value = stat.get('value')
                
                if stat_type == 'expected_goals':
                    if stat_value is not None:
                        try:
                            xg = float(stat_value)
                            if is_home:
                                home_xg = xg
                            else:
                                away_xg = xg
                        except (ValueError, TypeError):
                            pass
        
        # Skip if we don't have xG data
        if home_xg == 0.0 and away_xg == 0.0:
            return None
        
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
            'match_id': str(fixture_id),
            'date': formatted_date,
            'home_team': home_team,
            'away_team': away_team,
            'home_goals': home_goals,
            'away_goals': away_goals,
            'home_xg': home_xg,
            'away_xg': away_xg,
            'excitement_score': excitement_score,
            'is_exciting': is_exciting,
            'reasons': reasons,
            'league': self.LEAGUE_NAMES.get(league_id, 'Unknown'),
        }
    
    async def find_exciting_games(self) -> List[Dict[str, Any]]:
        """
        Main method to find and rank exciting games across all selected leagues.
        
        Returns:
            List of match analyses, sorted by excitement score
        """
        all_matches = []
        
        # Fetch matches from all selected leagues
        for league in self.leagues:
            matches = await self.fetch_recent_matches(league)
            all_matches.extend(matches)
        
        if not all_matches:
            print("No matches found in the specified time window.")
            return []
        
        # Analyze each match
        print(f"\nAnalyzing {len(all_matches)} matches for excitement factors...")
        analyses = []
        for match in all_matches:
            analysis = await self.analyze_match(match)
            if analysis:  # Only include if xG data was available
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
        leagues_str = ', '.join([self.LEAGUE_NAMES.get(self.LEAGUE_IDS.get(l), l) for l in self.leagues])
        
        if not exciting_games:
            print("\n" + "="*70)
            print(f"No particularly exciting matches found in this time window.")
            print(f"Searched: {leagues_str}")
            print("Try increasing the number of days or waiting for more games.")
            print("="*70)
            return
        
        print("\n" + "="*70)
        print(f"🏆 EXCITING MATCHES ({leagues_str}) - Top {len(exciting_games)} Game(s) Worth Watching")
        print("="*70)
        
        for i, game in enumerate(exciting_games, 1):
            # Format date
            try:
                match_date = datetime.strptime(game['date'], '%Y-%m-%d %H:%M:%S')
                date_str = match_date.strftime('%A, %B %d, %Y')
            except:
                date_str = game['date']
            
            print(f"\n{i}. {game['home_team']} vs {game['away_team']}")
            print(f"   League: {game.get('league', 'Unknown')}")
            print(f"   Date: {date_str}")
            
            # Spoiler mode: show excitement score, reasons, and actual stats
            if self.debug:
                print(f"   [DEBUG] Excitement Score: {game['excitement_score']:.2f}")
                
                if game['reasons']:
                    print(f"   Why it's exciting:")
                    for reason in game['reasons']:
                        print(f"      • {reason}")
                
                print(f"   [DEBUG] Score: {game['home_goals']}-{game['away_goals']}")
                print(f"   [DEBUG] xG: {game['home_xg']:.2f} - {game['away_xg']:.2f}")
        
        print("\n" + "="*70)


def get_user_input() -> Tuple[int, List[str], bool]:
    """
    Get user input for the time window, leagues, and spoiler mode.
    
    Returns:
        Tuple of (days_back, leagues, debug_mode)
    """
    print("="*70)
    print("Exciting Game Finder (API-Football)")
    print("="*70)
    print("\nThis program analyzes recent football matches to identify")
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
    
    # Get league selection
    selected_leagues = []
    while True:
        try:
            print("\nSelect leagues (you can select multiple):")
            print("1. Premier League (EPL)")
            print("2. Champions League (UCL)")
            print("3. Both leagues")
            league_choice = input("Enter choice (1, 2, or 3): ").strip()
            
            if league_choice == '1':
                selected_leagues = ['EPL']
                break
            elif league_choice == '2':
                selected_leagues = ['UCL']
                break
            elif league_choice == '3':
                selected_leagues = ['EPL', 'UCL']
                break
            else:
                print("Please enter 1, 2, or 3.")
        except KeyboardInterrupt:
            print("\n\nExiting...")
            exit(0)
    
    # Check for spoiler mode via command line
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--debug', action='store_true', help='Show xG and goals for validation')
    args, _ = parser.parse_known_args()
    
    return days, selected_leagues, args.debug


async def main():
    """Main execution function."""
    days_back, leagues, debug = get_user_input()
    
    try:
        finder = ExcitingGameFinder(days_back=days_back, leagues=leagues, debug=debug)
        exciting_games = await finder.find_exciting_games()
        finder.display_results(exciting_games)
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nMake sure you have:")
        print("1. Created a .env file with your API_FOOTBALL_KEY")
        print("2. Signed up at https://www.api-football.com/")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
