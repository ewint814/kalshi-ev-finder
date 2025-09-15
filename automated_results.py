#!/usr/bin/env python3
"""
Automated Results Collector
Automatically gets game results from ESPN or other sources
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import json
import time

class AutomatedResults:
    """Automatically collect game results"""
    
    def __init__(self):
        self.results_file = "game_results.json"
    
    def get_nfl_results(self, week=None, year=2025):
        """Get NFL results from ESPN API"""
        print(f"🏈 GETTING NFL RESULTS")
        
        # ESPN NFL API endpoint
        if week is None:
            # Get current week
            week = self._get_current_nfl_week()
        
        url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
        params = {
            'dates': self._get_week_dates(week, year),
            'limit': 100
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            
            for event in data.get('events', []):
                game_result = self._process_nfl_game(event)
                if game_result:
                    results.append(game_result)
            
            print(f"✅ Found {len(results)} NFL game results")
            return results
            
        except requests.RequestException as e:
            print(f"❌ ESPN API Error: {e}")
            return []
    
    def get_mlb_results(self, date=None):
        """Get MLB results from ESPN API"""
        print(f"⚾ GETTING MLB RESULTS")
        
        if date is None:
            date = datetime.now().strftime('%Y%m%d')
        
        url = f"https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"
        params = {
            'dates': date,
            'limit': 100
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            
            for event in data.get('events', []):
                game_result = self._process_mlb_game(event)
                if game_result:
                    results.append(game_result)
            
            print(f"✅ Found {len(results)} MLB game results")
            return results
            
        except requests.RequestException as e:
            print(f"❌ ESPN API Error: {e}")
            return []
    
    def _process_nfl_game(self, event):
        """Process a single NFL game from ESPN"""
        try:
            # Check if game is completed
            status = event.get('status', {}).get('type', {}).get('name', '')
            if status != 'STATUS_FINAL':
                return None
            
            competitions = event.get('competitions', [])
            if not competitions:
                return None
            
            competition = competitions[0]
            competitors = competition.get('competitors', [])
            
            if len(competitors) != 2:
                return None
            
            # Extract team info and scores
            away_team = None
            home_team = None
            away_score = None
            home_score = None
            
            for competitor in competitors:
                team_name = competitor.get('team', {}).get('displayName', '')
                score = int(competitor.get('score', 0))
                home_away = competitor.get('homeAway', '')
                
                if home_away == 'home':
                    home_team = team_name
                    home_score = score
                elif home_away == 'away':
                    away_team = team_name
                    away_score = score
            
            if not all([away_team, home_team, away_score is not None, home_score is not None]):
                return None
            
            # Determine winner
            if away_score > home_score:
                winning_team = away_team
            elif home_score > away_score:
                winning_team = home_team
            else:
                winning_team = 'TIE'
            
            return {
                'sport': 'nfl',
                'away_team': away_team,
                'home_team': home_team,
                'away_score': away_score,
                'home_score': home_score,
                'total_score': away_score + home_score,
                'winning_team': winning_team,
                'game_date': event.get('date'),
                'espn_id': event.get('id'),
                'status': status
            }
            
        except Exception as e:
            print(f"⚠️  Error processing NFL game: {e}")
            return None
    
    def _process_mlb_game(self, event):
        """Process a single MLB game from ESPN"""
        try:
            # Check if game is completed
            status = event.get('status', {}).get('type', {}).get('name', '')
            if status != 'STATUS_FINAL':
                return None
            
            competitions = event.get('competitions', [])
            if not competitions:
                return None
            
            competition = competitions[0]
            competitors = competition.get('competitors', [])
            
            if len(competitors) != 2:
                return None
            
            # Extract team info and scores
            away_team = None
            home_team = None
            away_score = None
            home_score = None
            
            for competitor in competitors:
                team_name = competitor.get('team', {}).get('displayName', '')
                score = int(competitor.get('score', 0))
                home_away = competitor.get('homeAway', '')
                
                if home_away == 'home':
                    home_team = team_name
                    home_score = score
                elif home_away == 'away':
                    away_team = team_name
                    away_score = score
            
            if not all([away_team, home_team, away_score is not None, home_score is not None]):
                return None
            
            # Determine winner
            if away_score > home_score:
                winning_team = away_team
            elif home_score > away_score:
                winning_team = home_team
            else:
                winning_team = 'TIE'
            
            return {
                'sport': 'mlb',
                'away_team': away_team,
                'home_team': home_team,
                'away_score': away_score,
                'home_score': home_score,
                'total_score': away_score + home_score,
                'winning_team': winning_team,
                'game_date': event.get('date'),
                'espn_id': event.get('id'),
                'status': status
            }
            
        except Exception as e:
            print(f"⚠️  Error processing MLB game: {e}")
            return None
    
    def _get_current_nfl_week(self):
        """Estimate current NFL week based on date"""
        # NFL season typically starts first week of September
        # This is a rough estimate - could be made more accurate
        now = datetime.now()
        
        if now.month >= 9:  # September or later
            week = ((now - datetime(now.year, 9, 1)).days // 7) + 1
            return min(week, 18)  # Max 18 weeks in regular season
        elif now.month <= 2:  # January/February (playoffs)
            return 18 + ((now - datetime(now.year, 1, 1)).days // 7)
        else:
            return 1  # Off-season, default to week 1
    
    def _get_week_dates(self, week, year):
        """Get date range for NFL week"""
        # This is simplified - could be more accurate with actual NFL schedule
        season_start = datetime(year, 9, 7)  # Approximate season start
        week_start = season_start + timedelta(weeks=week-1)
        week_end = week_start + timedelta(days=6)
        
        return f"{week_start.strftime('%Y%m%d')}-{week_end.strftime('%Y%m%d')}"
    
    def update_odds_with_results(self, sportsbook_file="sportsbook_odds.xlsx", kalshi_file="kalshi_odds.xlsx"):
        """Update odds files with automated results"""
        print("🤖 UPDATING ODDS WITH AUTOMATED RESULTS")
        print("=" * 50)
        
        # Get results
        nfl_results = self.get_nfl_results()
        mlb_results = self.get_mlb_results()
        
        all_results = nfl_results + mlb_results
        
        if not all_results:
            print("📭 No completed games found")
            return
        
        # Update sportsbook odds
        self._update_sportsbook_odds(sportsbook_file, all_results)
        
        # Update Kalshi odds (if file exists)
        try:
            self._update_kalshi_odds(kalshi_file, all_results)
        except FileNotFoundError:
            print("⚠️  No Kalshi odds file found")
        
        print(f"✅ Updated odds with {len(all_results)} game results")
    
    def _update_sportsbook_odds(self, file_path, results):
        """Update sportsbook odds file with results"""
        try:
            df = pd.read_excel(file_path)
            updates_made = 0
            
            for result in results:
                # Find matching games by team names
                matching_games = df[
                    (df['away_team'].str.contains(result['away_team'].split()[-1], case=False, na=False)) &
                    (df['home_team'].str.contains(result['home_team'].split()[-1], case=False, na=False)) &
                    (df['sport'] == result['sport'])
                ]
                
                for idx, row in matching_games.iterrows():
                    if pd.isna(row['result']):  # Only update if not already set
                        
                        if row['bet_type'] == 'moneyline':
                            # Moneyline result
                            if row['team'] == result['winning_team'] or result['winning_team'] in row['team']:
                                df.at[idx, 'result'] = 1
                            else:
                                df.at[idx, 'result'] = 0
                            updates_made += 1
                        
                        elif row['bet_type'] == 'spread':
                            # Spread result
                            spread_line = row['spread_line']
                            if pd.notna(spread_line):
                                if 'away_team' in row['team'] or result['away_team'] in row['team']:
                                    # Away team spread
                                    if result['away_score'] + spread_line > result['home_score']:
                                        df.at[idx, 'result'] = 1
                                    else:
                                        df.at[idx, 'result'] = 0
                                else:
                                    # Home team spread
                                    if result['home_score'] + spread_line > result['away_score']:
                                        df.at[idx, 'result'] = 1
                                    else:
                                        df.at[idx, 'result'] = 0
                                updates_made += 1
                        
                        elif row['bet_type'] == 'total':
                            # Total result
                            total_line = row['total_line']
                            if pd.notna(total_line):
                                if 'Over' in row['team']:
                                    if result['total_score'] > total_line:
                                        df.at[idx, 'result'] = 1
                                    else:
                                        df.at[idx, 'result'] = 0
                                else:  # Under
                                    if result['total_score'] < total_line:
                                        df.at[idx, 'result'] = 1
                                    else:
                                        df.at[idx, 'result'] = 0
                                updates_made += 1
            
            # Save updated file
            df.to_excel(file_path, index=False)
            print(f"📊 Updated {updates_made} sportsbook entries")
            
        except Exception as e:
            print(f"❌ Error updating sportsbook odds: {e}")
    
    def _update_kalshi_odds(self, file_path, results):
        """Update Kalshi odds file with results"""
        try:
            df = pd.read_excel(file_path)
            updates_made = 0
            
            for result in results:
                # Find matching games
                matching_games = df[
                    (df['away_team'].str.contains(result['away_team'].split()[-1], case=False, na=False)) &
                    (df['home_team'].str.contains(result['home_team'].split()[-1], case=False, na=False)) &
                    (df['sport'] == result['sport'])
                ]
                
                for idx, row in matching_games.iterrows():
                    if pd.isna(row['result']):
                        # Kalshi moneyline result
                        if row['team'] == result['winning_team'] or result['winning_team'] in row['team']:
                            df.at[idx, 'result'] = 1
                        else:
                            df.at[idx, 'result'] = 0
                        updates_made += 1
            
            # Save updated file
            df.to_excel(file_path, index=False)
            print(f"🎯 Updated {updates_made} Kalshi entries")
            
        except Exception as e:
            print(f"❌ Error updating Kalshi odds: {e}")

def main():
    """Test automated results"""
    collector = AutomatedResults()
    
    print("🤖 AUTOMATED RESULTS COLLECTOR")
    print("=" * 35)
    print("Automatically gets game results from ESPN")
    print()
    
    print("💡 Usage:")
    print("collector.get_nfl_results()        # Get NFL results")
    print("collector.get_mlb_results()        # Get MLB results") 
    print("collector.update_odds_with_results() # Update all odds files")
    
    return collector

if __name__ == "__main__":
    collector = main()
