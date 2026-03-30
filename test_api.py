#!/usr/bin/env python3
"""Quick test script to debug API-Football connection"""
import asyncio
import aiohttp
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

async def test_api():
    api_key = os.getenv('API_FOOTBALL_KEY')
    print(f"API Key: {api_key[:10]}...")
    
    base_url = "https://v3.football.api-sports.io"
    headers = {'x-apisports-key': api_key}
    
    # Free tier only supports 2022-2024 seasons
    season = 2024
    
    print(f"Current date: {datetime.now()}")
    print(f"Season: {season} (free tier limitation)")
    
    # Try end of 2023-2024 EPL season (typically ends in May)
    from_date = "2024-04-01"
    to_date = "2024-05-20"
    
    print(f"Date range: {from_date} to {to_date}")
    
    async with aiohttp.ClientSession(headers=headers) as session:
        # Test 1: Get ALL fixtures for EPL 2024 (no date filter)
        url = f"{base_url}/fixtures?league=39&season=2024"
        print(f"\nTest URL (all fixtures): {url}")
        
        async with session.get(url) as response:
            print(f"Status: {response.status}")
            data = await response.json()
            
            print(f"\nResponse keys: {list(data.keys())}")
            print(f"Errors: {data.get('errors')}")
            
            fixtures = data.get('response', [])
            print(f"Fixtures found: {len(fixtures)}")
            
            if fixtures:
                print(f"\nFirst fixture sample:")
                fixture = fixtures[0]
                print(f"  ID: {fixture['fixture']['id']}")
                print(f"  Date: {fixture['fixture']['date']}")
                print(f"  Teams: {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}")
                print(f"  Score: {fixture['goals']['home']}-{fixture['goals']['away']}")
                
                # Test 2: Get statistics for first fixture
                fixture_id = fixture['fixture']['id']
                stats_url = f"{base_url}/fixtures/statistics?fixture={fixture_id}"
                print(f"\nFetching stats: {stats_url}")
                
                async with session.get(stats_url) as stats_response:
                    print(f"Stats status: {stats_response.status}")
                    stats_data = await stats_response.json()
                    
                    stats = stats_data.get('response', [])
                    print(f"Teams with stats: {len(stats)}")
                    
                    if stats:
                        print("\nStatistics structure:")
                        for team_stats in stats:
                            team_name = team_stats['team']['name']
                            print(f"\n  {team_name}:")
                            for stat in team_stats['statistics']:
                                stat_type = stat['type']
                                stat_value = stat['value']
                                if 'goal' in stat_type.lower() or 'xg' in stat_type.lower() or 'expected' in stat_type.lower():
                                    print(f"    {stat_type}: {stat_value}")

if __name__ == "__main__":
    asyncio.run(test_api())
