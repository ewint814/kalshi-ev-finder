#!/usr/bin/env python3
"""
Data Processor
Combines Kalshi + Sportsbook odds and creates easy results entry
"""

import pandas as pd
from datetime import datetime
import re

class DataProcessor:
    """Process and combine odds data from multiple sources"""
    
    def __init__(self):
        self.sportsbook_file = "sportsbook_odds.xlsx"
        self.kalshi_file = "kalshi_odds.xlsx"
        self.combined_file = "combined_odds_analysis.xlsx"
    
    def combine_all_data(self):
        """Combine Kalshi and sportsbook data into analysis-ready format"""
        print("🔄 COMBINING ALL ODDS DATA")
        print("=" * 40)
        
        # Load data
        sportsbook_df = self._load_sportsbook_data()
        kalshi_df = self._load_kalshi_data()
        
        if sportsbook_df is None and kalshi_df is None:
            print("❌ No data found to combine")
            return
        
        # Create combined analysis
        self._create_combined_analysis(sportsbook_df, kalshi_df)
        
        print(f"✅ Combined analysis saved to: {self.combined_file}")
    
    def _load_sportsbook_data(self):
        """Load sportsbook odds data"""
        try:
            df = pd.read_excel(self.sportsbook_file)
            print(f"📊 Loaded {len(df)} sportsbook entries")
            return df
        except FileNotFoundError:
            print("⚠️  No sportsbook data found")
            return None
    
    def _load_kalshi_data(self):
        """Load Kalshi odds data"""
        try:
            df = pd.read_excel(self.kalshi_file)
            print(f"🎯 Loaded {len(df)} Kalshi entries")
            return df
        except FileNotFoundError:
            print("⚠️  No Kalshi data found")
            return None
    
    def _create_combined_analysis(self, sportsbook_df, kalshi_df):
        """Create combined analysis with multiple sheets"""
        
        with pd.ExcelWriter(self.combined_file, engine='openpyxl') as writer:
            
            # Sheet 1: Raw combined data
            if sportsbook_df is not None and kalshi_df is not None:
                self._create_raw_combined_sheet(sportsbook_df, kalshi_df, writer)
            
            # Sheet 2: Game results entry (simplified)
            self._create_results_entry_sheet(sportsbook_df, kalshi_df, writer)
            
            # Sheet 3: Matched odds comparison
            if sportsbook_df is not None and kalshi_df is not None:
                self._create_odds_comparison_sheet(sportsbook_df, kalshi_df, writer)
            
            # Sheet 4: Summary stats
            self._create_summary_sheet(sportsbook_df, kalshi_df, writer)
    
    def _create_raw_combined_sheet(self, sportsbook_df, kalshi_df, writer):
        """Create sheet with all raw data combined"""
        
        # Standardize columns for combination
        sportsbook_std = sportsbook_df.copy()
        sportsbook_std['source_type'] = 'sportsbook'
        sportsbook_std['probability'] = sportsbook_std['implied_prob_vig_adj']
        
        kalshi_std = kalshi_df.copy()
        kalshi_std['source_type'] = 'kalshi'
        kalshi_std['probability'] = kalshi_std['kalshi_probability']
        kalshi_std['bookmaker'] = 'kalshi'
        
        # Combine
        combined = pd.concat([sportsbook_std, kalshi_std], ignore_index=True, sort=False)
        combined = combined.sort_values(['game_time', 'game_id', 'bet_type'])
        
        combined.to_excel(writer, sheet_name='Raw Combined Data', index=False)
    
    def _create_results_entry_sheet(self, sportsbook_df, kalshi_df, writer):
        """Create simplified sheet for manual results entry"""
        
        # Get unique games from both sources
        games = set()
        
        if sportsbook_df is not None:
            for _, row in sportsbook_df.iterrows():
                games.add((
                    row['game_id'], 
                    row['away_team'], 
                    row['home_team'], 
                    row['game_time'],
                    row['sport']
                ))
        
        if kalshi_df is not None:
            for _, row in kalshi_df.iterrows():
                games.add((
                    row['game_id'],
                    row['away_team'], 
                    row['home_team'],
                    row['game_time'],
                    row['sport']
                ))
        
        # Create results entry format
        results_data = []
        for game_id, away, home, game_time, sport in games:
            
            # Get spread and total lines from sportsbook data (if available)
            spread_line = None
            total_line = None
            
            if sportsbook_df is not None:
                game_data = sportsbook_df[sportsbook_df['game_id'] == game_id]
                
                spread_data = game_data[game_data['bet_type'] == 'spread']
                if not spread_data.empty:
                    spread_line = spread_data.iloc[0]['spread_line']
                
                total_data = game_data[game_data['bet_type'] == 'total']
                if not total_data.empty:
                    total_line = total_data.iloc[0]['total_line']
            
            results_data.append({
                'game_id': game_id,
                'away_team': away,
                'home_team': home,
                'game_time': game_time,
                'sport': sport,
                'spread_line': spread_line,
                'total_line': total_line,
                
                # Results to fill manually
                'winning_team': '',  # Enter team name that won
                'away_score': '',    # Enter away team final score
                'home_score': '',    # Enter home team final score
                'total_score': '',   # Will calculate automatically
                
                # Auto-calculated results (don't edit these)
                'moneyline_result_away': '',  # 1 if away won, 0 if lost
                'moneyline_result_home': '',  # 1 if home won, 0 if lost
                'spread_result_away': '',     # 1 if away covered, 0 if not
                'spread_result_home': '',     # 1 if home covered, 0 if not
                'total_result_over': '',      # 1 if over hit, 0 if under
                'total_result_under': '',     # 1 if under hit, 0 if over
                
                'notes': ''  # Any additional notes
            })
        
        results_df = pd.DataFrame(results_data)
        results_df = results_df.sort_values('game_time')
        
        results_df.to_excel(writer, sheet_name='Game Results Entry', index=False)
        
        print(f"📝 Created results entry sheet with {len(results_df)} games")
    
    def _create_odds_comparison_sheet(self, sportsbook_df, kalshi_df, writer):
        """Create sheet comparing Kalshi vs sportsbook odds for same games"""
        
        comparison_data = []
        
        # Find matching games (by teams and approximate time)
        for _, kalshi_game in kalshi_df.iterrows():
            if kalshi_game['bet_type'] != 'moneyline':
                continue
                
            # Find corresponding sportsbook moneyline
            sportsbook_matches = sportsbook_df[
                (sportsbook_df['away_team'] == kalshi_game['away_team']) &
                (sportsbook_df['home_team'] == kalshi_game['home_team']) &
                (sportsbook_df['bet_type'] == 'moneyline') &
                (sportsbook_df['team'] == kalshi_game['team'])
            ]
            
            if not sportsbook_matches.empty:
                # Get consensus sportsbook probability (average across bookmakers)
                avg_sportsbook_prob = sportsbook_matches['implied_prob_vig_adj'].mean()
                
                comparison_data.append({
                    'game_id': kalshi_game['game_id'],
                    'away_team': kalshi_game['away_team'],
                    'home_team': kalshi_game['home_team'],
                    'game_time': kalshi_game['game_time'],
                    'team': kalshi_game['team'],
                    'kalshi_probability': kalshi_game['kalshi_probability'],
                    'sportsbook_avg_probability': avg_sportsbook_prob,
                    'probability_difference': kalshi_game['kalshi_probability'] - avg_sportsbook_prob,
                    'kalshi_higher': kalshi_game['kalshi_probability'] > avg_sportsbook_prob,
                    'num_sportsbooks': len(sportsbook_matches),
                    'result': None  # To be filled from results entry
                })
        
        if comparison_data:
            comparison_df = pd.DataFrame(comparison_data)
            comparison_df = comparison_df.sort_values('probability_difference', key=abs, ascending=False)
            comparison_df.to_excel(writer, sheet_name='Kalshi vs Sportsbooks', index=False)
            
            print(f"🔍 Created odds comparison with {len(comparison_df)} matched predictions")
    
    def _create_summary_sheet(self, sportsbook_df, kalshi_df, writer):
        """Create summary statistics sheet"""
        
        summary_data = []
        
        # Overall stats
        summary_data.append(['Metric', 'Value'])
        summary_data.append(['Analysis Date', datetime.now().strftime('%Y-%m-%d %H:%M')])
        summary_data.append(['', ''])
        
        if sportsbook_df is not None:
            summary_data.append(['SPORTSBOOK DATA', ''])
            summary_data.append(['Total Entries', len(sportsbook_df)])
            summary_data.append(['Unique Games', sportsbook_df['game_id'].nunique()])
            summary_data.append(['Sports', ', '.join(sportsbook_df['sport'].unique())])
            summary_data.append(['Bet Types', ', '.join(sportsbook_df['bet_type'].unique())])
            summary_data.append(['Bookmakers', ', '.join(sportsbook_df['bookmaker'].unique())])
            summary_data.append(['Avg Market Vig', f"{sportsbook_df['market_vig'].mean():.1%}"])
            summary_data.append(['', ''])
        
        if kalshi_df is not None:
            summary_data.append(['KALSHI DATA', ''])
            summary_data.append(['Total Entries', len(kalshi_df)])
            summary_data.append(['Unique Games', kalshi_df['game_id'].nunique()])
            summary_data.append(['Sports', ', '.join(kalshi_df['sport'].unique())])
            summary_data.append(['Avg Probability', f"{kalshi_df['kalshi_probability'].mean():.1%}"])
            summary_data.append(['', ''])
        
        # Data collection info
        summary_data.append(['DATA COLLECTION', ''])
        summary_data.append(['Next Steps', '1. Fill Game Results Entry sheet'])
        summary_data.append(['', '2. Run calibration analysis'])
        summary_data.append(['', '3. Identify best odds source'])
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False, header=False)
    
    def update_results_from_entry_sheet(self):
        """Update all data with results from the entry sheet"""
        print("🔄 UPDATING RESULTS FROM ENTRY SHEET")
        
        try:
            # Read the results entry sheet
            results_df = pd.read_excel(self.combined_file, sheet_name='Game Results Entry')
            
            # Process each completed game
            updates_made = 0
            for _, row in results_df.iterrows():
                if pd.notna(row['winning_team']) and pd.notna(row['away_score']) and pd.notna(row['home_score']):
                    
                    # Calculate results
                    away_score = int(row['away_score'])
                    home_score = int(row['home_score'])
                    total_score = away_score + home_score
                    winning_team = row['winning_team']
                    
                    # Update source data files
                    self._update_sportsbook_results(row, away_score, home_score, total_score, winning_team)
                    self._update_kalshi_results(row, winning_team)
                    
                    updates_made += 1
            
            if updates_made > 0:
                print(f"✅ Updated results for {updates_made} games")
                # Recreate combined analysis with updated results
                self.combine_all_data()
            else:
                print("📭 No new results to update")
                
        except Exception as e:
            print(f"❌ Error updating results: {e}")
    
    def _update_sportsbook_results(self, game_row, away_score, home_score, total_score, winning_team):
        """Update sportsbook data with game results"""
        try:
            df = pd.read_excel(self.sportsbook_file)
            game_data = df[df['game_id'] == game_row['game_id']]
            
            for idx, row in game_data.iterrows():
                if row['bet_type'] == 'moneyline':
                    # Moneyline result
                    if row['team'] == winning_team:
                        df.at[idx, 'result'] = 1
                    else:
                        df.at[idx, 'result'] = 0
                
                elif row['bet_type'] == 'spread':
                    # Spread result
                    spread_line = row['spread_line']
                    if row['team'] == game_row['away_team']:
                        # Away team spread
                        if away_score + spread_line > home_score:
                            df.at[idx, 'result'] = 1
                        else:
                            df.at[idx, 'result'] = 0
                    else:
                        # Home team spread
                        if home_score + spread_line > away_score:
                            df.at[idx, 'result'] = 1
                        else:
                            df.at[idx, 'result'] = 0
                
                elif row['bet_type'] == 'total':
                    # Total result
                    total_line = row['total_line']
                    if row['team'] == 'Over':
                        if total_score > total_line:
                            df.at[idx, 'result'] = 1
                        else:
                            df.at[idx, 'result'] = 0
                    else:  # Under
                        if total_score < total_line:
                            df.at[idx, 'result'] = 1
                        else:
                            df.at[idx, 'result'] = 0
            
            # Save updated sportsbook data
            df.to_excel(self.sportsbook_file, index=False)
            
        except Exception as e:
            print(f"⚠️  Error updating sportsbook results: {e}")
    
    def _update_kalshi_results(self, game_row, winning_team):
        """Update Kalshi data with game results"""
        try:
            df = pd.read_excel(self.kalshi_file)
            game_data = df[df['game_id'] == game_row['game_id']]
            
            for idx, row in game_data.iterrows():
                if row['team'] == winning_team:
                    df.at[idx, 'result'] = 1
                else:
                    df.at[idx, 'result'] = 0
            
            # Save updated Kalshi data
            df.to_excel(self.kalshi_file, index=False)
            
        except Exception as e:
            print(f"⚠️  Error updating Kalshi results: {e}")

def main():
    processor = DataProcessor()
    
    print("🔄 DATA PROCESSOR")
    print("=" * 20)
    print("Combines Kalshi + Sportsbook odds for analysis")
    print()
    
    print("💡 Usage:")
    print("processor.combine_all_data()              # Combine all odds data")
    print("processor.update_results_from_entry_sheet() # Update with game results")
    
    return processor

if __name__ == "__main__":
    processor = main()
