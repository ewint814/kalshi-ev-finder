#!/usr/bin/env python3
"""
Odds API Collector
Collects moneylines, spreads, and totals from sportsbooks
"""

import json
import pandas as pd
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class OddsAPICollector:
    """Collect odds from Odds API (paid service)"""
    
    def __init__(self, odds_api_key=None):
        self.api_key = odds_api_key or os.getenv('ODDS_API_KEY')
        self.data_file = "sportsbook_odds.xlsx"
    
    def collect_all_markets(self, sports=['americanfootball_nfl', 'baseball_mlb']):
        """Collect moneylines, spreads, and totals for specified sports"""
        if not self.api_key:
            print("❌ Need ODDS_API_KEY environment variable")
            return
        
        print(f"📊 COLLECTING ALL MARKETS - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 60)
        
        all_rows = []
        collection_time = datetime.now().isoformat()
        
        for sport in sports:
            sport_name = 'NFL' if 'nfl' in sport else 'MLB'
            print(f"\n{sport_name} - Collecting moneylines, spreads, totals...")
            
            try:
                # Single API call gets all markets
                url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
                params = {
                    'apiKey': self.api_key,
                    'regions': 'us',
                    'markets': 'h2h,spreads,totals',  # All three markets
                    'oddsFormat': 'american',
                    'dateFormat': 'iso'
                }
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                games = response.json()
                
                if not games:
                    print(f"📭 No {sport_name} games found")
                    continue
                
                # Process each game
                for game in games:
                    game_rows = self._process_game_all_markets(
                        game, sport_name.lower(), collection_time
                    )
                    all_rows.extend(game_rows)
                
                print(f"✅ {sport_name}: {len([r for r in all_rows if r['sport'] == sport_name.lower()])} entries")
                
            except requests.RequestException as e:
                print(f"❌ {sport_name} Error: {e}")
                continue
        
        if all_rows:
            self._save_odds_data(all_rows)
            print(f"\n📊 Total collected: {len(all_rows)} entries")
            print(f"💾 Saved to: {self.data_file}")
    
    def _process_game_all_markets(self, game, sport, collection_time):
        """Process all markets for a single game"""
        rows = []
        
        game_id = game['id']
        away_team = game['away_team']
        home_team = game['home_team']
        game_time = game['commence_time']
        
        # Calculate hours until game
        game_dt = datetime.fromisoformat(game_time.replace('Z', '+00:00')).replace(tzinfo=None)
        hours_until = (game_dt - datetime.now()).total_seconds() / 3600
        
        # Process each bookmaker
        for bookmaker in game['bookmakers']:
            bm_name = bookmaker['key']
            
            # Process each market type
            for market in bookmaker['markets']:
                market_type = market['key']
                
                if market_type == 'h2h':
                    # Moneyline processing
                    rows.extend(self._process_moneyline_market(
                        market, game_id, away_team, home_team, game_time, 
                        hours_until, bm_name, sport, collection_time
                    ))
                
                elif market_type == 'spreads':
                    # Spread processing  
                    rows.extend(self._process_spread_market(
                        market, game_id, away_team, home_team, game_time,
                        hours_until, bm_name, sport, collection_time
                    ))
                
                elif market_type == 'totals':
                    # Totals processing
                    rows.extend(self._process_totals_market(
                        market, game_id, away_team, home_team, game_time,
                        hours_until, bm_name, sport, collection_time
                    ))
        
        return rows
    
    def _process_moneyline_market(self, market, game_id, away_team, home_team, 
                                 game_time, hours_until, bm_name, sport, collection_time):
        """Process moneyline market with vig adjustment"""
        rows = []
        outcomes = market['outcomes']
        
        if len(outcomes) == 2:
            # Calculate vig adjustment
            probs = []
            for outcome in outcomes:
                american_odds = outcome['price']
                if american_odds > 0:
                    prob = 100 / (american_odds + 100)
                else:
                    prob = abs(american_odds) / (abs(american_odds) + 100)
                probs.append(prob)
            
            total_prob = sum(probs)
            vig = total_prob - 1.0
            
            # Create entries for both teams
            for i, outcome in enumerate(outcomes):
                team = outcome['name']
                american_odds = outcome['price']
                raw_prob = probs[i]
                adj_prob = raw_prob / total_prob
                
                rows.append({
                    'collection_time': collection_time,
                    'game_id': game_id,
                    'away_team': away_team,
                    'home_team': home_team,
                    'game_time': game_time,
                    'hours_until_game': round(hours_until, 1),
                    'sport': sport,
                    'bet_type': 'moneyline',
                    'bookmaker': bm_name,
                    'team': team,
                    'american_odds': american_odds,
                    'implied_prob_raw': round(raw_prob, 4),
                    'implied_prob_vig_adj': round(adj_prob, 4),
                    'market_vig': round(vig, 4),
                    'spread_line': None,
                    'total_line': None,
                    'result': None
                })
        
        return rows
    
    def _process_spread_market(self, market, game_id, away_team, home_team,
                              game_time, hours_until, bm_name, sport, collection_time):
        """Process spread market"""
        rows = []
        outcomes = market['outcomes']
        
        if len(outcomes) == 2:
            # Calculate vig adjustment (same logic as moneyline)
            probs = []
            for outcome in outcomes:
                american_odds = outcome['price']
                if american_odds > 0:
                    prob = 100 / (american_odds + 100)
                else:
                    prob = abs(american_odds) / (abs(american_odds) + 100)
                probs.append(prob)
            
            total_prob = sum(probs)
            vig = total_prob - 1.0
            
            for i, outcome in enumerate(outcomes):
                team = outcome['name']
                american_odds = outcome['price']
                spread_line = outcome.get('point', 0)  # The spread
                raw_prob = probs[i]
                adj_prob = raw_prob / total_prob
                
                rows.append({
                    'collection_time': collection_time,
                    'game_id': game_id,
                    'away_team': away_team,
                    'home_team': home_team,
                    'game_time': game_time,
                    'hours_until_game': round(hours_until, 1),
                    'sport': sport,
                    'bet_type': 'spread',
                    'bookmaker': bm_name,
                    'team': team,
                    'american_odds': american_odds,
                    'implied_prob_raw': round(raw_prob, 4),
                    'implied_prob_vig_adj': round(adj_prob, 4),
                    'market_vig': round(vig, 4),
                    'spread_line': spread_line,
                    'total_line': None,
                    'result': None
                })
        
        return rows
    
    def _process_totals_market(self, market, game_id, away_team, home_team,
                              game_time, hours_until, bm_name, sport, collection_time):
        """Process totals (over/under) market"""
        rows = []
        outcomes = market['outcomes']
        
        if len(outcomes) == 2:
            # Calculate vig adjustment
            probs = []
            for outcome in outcomes:
                american_odds = outcome['price']
                if american_odds > 0:
                    prob = 100 / (american_odds + 100)
                else:
                    prob = abs(american_odds) / (abs(american_odds) + 100)
                probs.append(prob)
            
            total_prob = sum(probs)
            vig = total_prob - 1.0
            
            for i, outcome in enumerate(outcomes):
                over_under = outcome['name']  # "Over" or "Under"
                american_odds = outcome['price']
                total_line = outcome.get('point', 0)  # The total number
                raw_prob = probs[i]
                adj_prob = raw_prob / total_prob
                
                rows.append({
                    'collection_time': collection_time,
                    'game_id': game_id,
                    'away_team': away_team,
                    'home_team': home_team,
                    'game_time': game_time,
                    'hours_until_game': round(hours_until, 1),
                    'sport': sport,
                    'bet_type': 'total',
                    'bookmaker': bm_name,
                    'team': over_under,  # "Over" or "Under"
                    'american_odds': american_odds,
                    'implied_prob_raw': round(raw_prob, 4),
                    'implied_prob_vig_adj': round(adj_prob, 4),
                    'market_vig': round(vig, 4),
                    'spread_line': None,
                    'total_line': total_line,
                    'result': None
                })
        
        return rows
    
    def _save_odds_data(self, rows):
        """Save odds data to Excel"""
        if not rows:
            return
        
        df = pd.DataFrame(rows)
        
        # Try to append to existing data
        try:
            existing_df = pd.read_excel(self.data_file)
            combined_df = pd.concat([existing_df, df], ignore_index=True)
        except FileNotFoundError:
            combined_df = df
        
        combined_df.to_excel(self.data_file, index=False)
    
    def show_summary(self):
        """Show summary of collected odds"""
        try:
            df = pd.read_excel(self.data_file)
            
            print("📊 SPORTSBOOK ODDS SUMMARY")
            print("=" * 40)
            print(f"Total entries: {len(df)}")
            print(f"Unique games: {df['game_id'].nunique()}")
            print(f"Sports: {', '.join(df['sport'].unique())}")
            print(f"Bet types: {', '.join(df['bet_type'].unique())}")
            print(f"Bookmakers: {', '.join(df['bookmaker'].unique())}")
            
            # By sport and bet type
            print("\nBy Sport & Bet Type:")
            for sport in df['sport'].unique():
                sport_data = df[df['sport'] == sport]
                for bet_type in sport_data['bet_type'].unique():
                    type_data = sport_data[sport_data['bet_type'] == bet_type]
                    games = type_data['game_id'].nunique()
                    entries = len(type_data)
                    print(f"  {sport.upper()} {bet_type}: {games} games, {entries} entries")
            
        except FileNotFoundError:
            print("📭 No sportsbook odds collected yet")

def main():
    collector = OddsAPICollector()
    
    print("📊 SPORTSBOOK ODDS COLLECTOR")
    print("=" * 35)
    print("Collects moneylines, spreads, and totals from sportsbooks")
    print()
    
    collector.show_summary()
    
    print("\n💡 Usage:")
    print("collector.collect_all_markets()  # Collect all markets for NFL & MLB")
    
    return collector

if __name__ == "__main__":
    collector = main()
