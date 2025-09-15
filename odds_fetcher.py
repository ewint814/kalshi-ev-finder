#!/usr/bin/env python3
"""
The Odds API Integration for NFL Moneyline Odds
Fetches real-time NFL odds from multiple sportsbooks
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class OddsFetcher:
    """Fetch NFL moneyline odds from The Odds API"""
    
    def __init__(self):
        self.api_key = os.getenv('ODDS_API_KEY')
        self.base_url = "https://api.the-odds-api.com/v4"
        self.sport = "americanfootball_nfl"
        self.markets = "h2h"  # head-to-head (moneyline)
        self.regions = "us"   # US sportsbooks
        self.odds_format = "american"
        
        if not self.api_key:
            print("⚠️  WARNING: ODDS_API_KEY not found in .env file")
            print("   Get your free API key from: https://the-odds-api.com/")
    
    def get_nfl_odds(self) -> Optional[Dict]:
        """
        Fetch current NFL moneyline odds from The Odds API
        Filter for current week's games only
        
        Returns:
            Dict with odds data or None if error
        """
        if not self.api_key:
            print("❌ No API key configured")
            return None
            
        url = f"{self.base_url}/sports/{self.sport}/odds"
        
        # Get current week's games (Sept 11-15, 2025)
        params = {
            'api_key': self.api_key,
            'regions': self.regions,
            'markets': self.markets,
            'oddsFormat': self.odds_format,
            'dateFormat': 'iso',
            'commence_time_from': '2025-09-11T00:00:00Z',  # Thursday Sep 11
            'commence_time_to': '2025-09-16T06:00:00Z'     # Tuesday Sep 16 (after MNF)
        }
        
        try:
            print(f"🔍 Fetching NFL odds from The Odds API...")
            response = requests.get(url, params=params, timeout=10)
            
            # Check remaining requests
            remaining = response.headers.get('x-requests-remaining')
            used = response.headers.get('x-requests-used')
            
            print(f"📊 API Usage: {used} used, {remaining} remaining")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Retrieved odds for {len(data)} NFL games")
                
                # Show first few games to verify correct week
                print(f"\n🔍 Games from API (first 5):")
                for i, game in enumerate(data[:5]):
                    home = game.get('home_team', 'Unknown')
                    away = game.get('away_team', 'Unknown')
                    print(f"  {i+1}. {away} @ {home}")
                
                return data
            else:
                print(f"❌ API Error {response.status_code}: {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return None
    
    def parse_odds_to_teams(self, odds_data: List[Dict]) -> Dict[str, int]:
        """
        Convert The Odds API format to our team code format
        
        Args:
            odds_data: Raw data from The Odds API
            
        Returns:
            Dict mapping team codes to American odds
        """
        team_odds = {}
        
        if not odds_data:
            return team_odds
            
        print(f"\n📝 PARSING ODDS FROM THE ODDS API")
        print("=" * 40)
        
        from datetime import datetime
        
        for game in odds_data:
            home_team = game.get('home_team', '')
            away_team = game.get('away_team', '')
            commence_time = game.get('commence_time', '')
            
            # Filter by commence_time - only current week (Sept 11-16, 2025)
            if commence_time:
                try:
                    game_date = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
                    # Current NFL week: Sept 11-16, 2025
                    week_start = datetime.fromisoformat('2025-09-11T00:00:00+00:00')
                    week_end = datetime.fromisoformat('2025-09-17T00:00:00+00:00')
                    
                    if not (week_start <= game_date < week_end):
                        print(f"  ⚠️  Skipped: {away_team} @ {home_team} (wrong week: {game_date.strftime('%Y-%m-%d')})")
                        continue
                except Exception as e:
                    print(f"  ⚠️  Skipped: {away_team} @ {home_team} (date parsing error)")
                    continue
            
            # Convert team names to our codes
            home_code = self._team_name_to_code(home_team)
            away_code = self._team_name_to_code(away_team)
            
            # Skip if either team mapping failed
            if not home_code or not away_code:
                print(f"  ⚠️  Skipped: {away_team} @ {home_team} (team mapping failed)")
                continue
                
            # Skip if we already have odds for these teams (avoid duplicates)
            if home_code in team_odds or away_code in team_odds:
                print(f"  ⚠️  Skipped: {away_team} @ {home_team} (teams already processed)")
                continue
            
            # Collect odds from ALL bookmakers for averaging
            bookmakers = game.get('bookmakers', [])
            if not bookmakers:
                continue
                
            home_odds_list = []
            away_odds_list = []
            
            # Collect all odds for this game
            for bookmaker in bookmakers:
                markets = bookmaker.get('markets', [])
                for market in markets:
                    if market.get('key') == 'h2h':  # moneyline
                        outcomes = market.get('outcomes', [])
                        
                        for outcome in outcomes:
                            team_name = outcome.get('name', '')
                            odds = outcome.get('price', 0)
                            
                            if team_name == home_team and home_code:
                                home_odds_list.append(odds)
                            elif team_name == away_team and away_code:
                                away_odds_list.append(odds)
            
            # Calculate average odds
            if home_odds_list and home_code:
                avg_home_odds = self._calculate_average_odds(home_odds_list)
                team_odds[home_code] = avg_home_odds
                
            if away_odds_list and away_code:
                avg_away_odds = self._calculate_average_odds(away_odds_list)
                team_odds[away_code] = avg_away_odds
            
            if home_code and away_code:
                home_odds = team_odds.get(home_code, 'N/A')
                away_odds = team_odds.get(away_code, 'N/A')
                print(f"  {away_code} @ {home_code}: {away_odds:+d} / {home_odds:+d}")
        
        print(f"\n📊 Parsed odds for {len(team_odds)} teams")
        return team_odds
    
    def _team_name_to_code(self, team_name: str) -> Optional[str]:
        """
        Convert full team name to our 2-3 letter code
        This is a simplified mapping - could be enhanced
        """
        name_to_code = {
            # AFC East
            'Buffalo Bills': 'BUF',
            'Miami Dolphins': 'MIA', 
            'New England Patriots': 'NE',
            'New York Jets': 'NYJ',
            
            # AFC North  
            'Baltimore Ravens': 'BAL',
            'Cincinnati Bengals': 'CIN',
            'Cleveland Browns': 'CLE',
            'Pittsburgh Steelers': 'PIT',
            
            # AFC South
            'Houston Texans': 'HOU',
            'Indianapolis Colts': 'IND',
            'Jacksonville Jaguars': 'JAC',
            'Tennessee Titans': 'TEN',
            
            # AFC West
            'Denver Broncos': 'DEN',
            'Kansas City Chiefs': 'KC',
            'Las Vegas Raiders': 'LV',
            'Los Angeles Chargers': 'LAC',
            
            # NFC East
            'Dallas Cowboys': 'DAL',
            'New York Giants': 'NYG',
            'Philadelphia Eagles': 'PHI',
            'Washington Commanders': 'WAS',
            
            # NFC North
            'Chicago Bears': 'CHI',
            'Detroit Lions': 'DET',
            'Green Bay Packers': 'GB',
            'Minnesota Vikings': 'MIN',
            
            # NFC South
            'Atlanta Falcons': 'ATL',
            'Carolina Panthers': 'CAR',
            'New Orleans Saints': 'NO',
            'Tampa Bay Buccaneers': 'TB',
            
            # NFC West
            'Arizona Cardinals': 'ARI',
            'Los Angeles Rams': 'LA',
            'San Francisco 49ers': 'SF',
            'Seattle Seahawks': 'SEA'
        }
        
        return name_to_code.get(team_name)
    
    def _calculate_average_odds(self, odds_list: List[int]) -> int:
        """
        Calculate average American odds (more complex than simple mean)
        Converts to probabilities, averages, then back to odds
        """
        if not odds_list:
            return 0
            
        # Convert American odds to probabilities
        probabilities = []
        for odds in odds_list:
            if odds > 0:
                prob = 100 / (odds + 100)
            else:
                prob = abs(odds) / (abs(odds) + 100)
            probabilities.append(prob)
        
        # Average the probabilities
        avg_prob = sum(probabilities) / len(probabilities)
        
        # Convert back to American odds
        if avg_prob >= 0.5:
            avg_odds = int(-avg_prob / (1 - avg_prob) * 100)
        else:
            avg_odds = int((1 - avg_prob) / avg_prob * 100)
            
        return avg_odds
    
    def save_odds_to_file(self, team_odds: Dict[str, int], filename: str = None) -> str:
        """Save odds to a timestamped JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"nfl_odds_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'source': 'The Odds API',
                'odds': team_odds
            }, f, indent=2)
        
        print(f"💾 Saved odds to: {filename}")
        return filename


def main():
    """Test the odds fetcher"""
    print("🏈 NFL ODDS FETCHER - THE ODDS API")
    print("=" * 40)
    
    fetcher = OddsFetcher()
    
    # Fetch odds
    raw_odds = fetcher.get_nfl_odds()
    
    if raw_odds:
        # Parse to our format
        team_odds = fetcher.parse_odds_to_teams(raw_odds)
        
        if team_odds:
            # Save to file
            fetcher.save_odds_to_file(team_odds)
            
            print(f"\n✅ SUCCESS: Retrieved odds for {len(team_odds)} teams")
        else:
            print("❌ No odds could be parsed")
    else:
        print("❌ Failed to fetch odds")


if __name__ == "__main__":
    main()
