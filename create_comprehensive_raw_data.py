#!/usr/bin/env python3
"""
Create comprehensive raw data file with all Kalshi, all Sportsbook data, 
and matched pairs with row references
"""

import pandas as pd

def create_comprehensive_raw_data():
    print('🔍 CREATING COMPREHENSIVE RAW DATA WITH MATCHES')
    print('=' * 55)

    # Load both datasets
    sb_df = pd.read_excel('sportsbook_odds.xlsx')
    kalshi_df = pd.read_excel('kalshi_all_markets.xlsx')

    print(f'📊 Sportsbook: {len(sb_df)} entries')
    print(f'🎯 Kalshi: {len(kalshi_df)} entries')

    # Add row numbers for reference
    sb_df_with_rows = sb_df.copy()
    sb_df_with_rows.insert(0, 'Row_ID', range(1, len(sb_df) + 1))

    kalshi_df_with_rows = kalshi_df.copy()
    kalshi_df_with_rows.insert(0, 'Row_ID', range(1, len(kalshi_df) + 1))

    # Create matches with row references
    matches = []
    match_count = 0

    for kalshi_idx, kalshi_row in kalshi_df_with_rows.iterrows():
        bet_type = kalshi_row.get('bet_type', '')
        
        if bet_type == 'moneyline':
            # Match by team names only (ignore game_id since formats are different)
            kalshi_team = kalshi_row['team']
            
            # Handle abbreviation vs full name matching
            # If Kalshi team is abbreviation (2-3 chars), match with away/home teams
            if len(kalshi_team) <= 3:
                # Convert abbreviation to full team name for matching
                abbrev_to_keyword = {
                    'CIN': 'Cincinnati', 'DEN': 'Denver', 'NYJ': 'New York', 'MIA': 'Miami',
                    'GB': 'Green Bay', 'DAL': 'Dallas', 'KC': 'Kansas City', 'LAR': 'Los Angeles',
                    'BUF': 'Buffalo', 'BAL': 'Baltimore', 'PIT': 'Pittsburgh', 'CLE': 'Cleveland',
                    'NE': 'New England', 'TB': 'Tampa Bay', 'ATL': 'Atlanta', 'CAR': 'Carolina',
                    'NO': 'New Orleans', 'MIN': 'Minnesota', 'DET': 'Detroit', 'CHI': 'Chicago',
                    'LAC': 'Los Angeles', 'LV': 'Las Vegas', 'ARI': 'Arizona', 'SF': 'San Francisco',
                    'SEA': 'Seattle', 'HOU': 'Houston', 'IND': 'Indianapolis', 'JAX': 'Jacksonville',
                    'TEN': 'Tennessee', 'WAS': 'Washington', 'NYG': 'New York', 'PHI': 'Philadelphia'
                }
                
                keyword = abbrev_to_keyword.get(kalshi_team, kalshi_team)
                target_team = kalshi_row['away_team'] if keyword in kalshi_row['away_team'] else kalshi_row['home_team']
                
                # Match only the specific team side
                sb_matches = sb_df_with_rows[
                    (sb_df_with_rows['bet_type'] == 'moneyline') &
                    (sb_df_with_rows['away_team'] == kalshi_row['away_team']) &
                    (sb_df_with_rows['home_team'] == kalshi_row['home_team']) &
                    (sb_df_with_rows['team'] == target_team)
                ]
            else:
                # Use flexible matching for full names
                kalshi_team_words = kalshi_team.split()
                sb_matches = sb_df_with_rows[
                    (sb_df_with_rows['bet_type'] == 'moneyline') &
                    (sb_df_with_rows['away_team'] == kalshi_row['away_team']) &
                    (sb_df_with_rows['home_team'] == kalshi_row['home_team']) &
                    (sb_df_with_rows['team'].str.contains('|'.join(kalshi_team_words), case=False, na=False))
                ]
            
        elif bet_type == 'spread':
            # Convert Kalshi line based on whether it's whole number or half point
            kalshi_line = kalshi_row.get('line_value')
            if kalshi_line is not None:
                # If whole number, subtract 0.5 to avoid push (Kalshi 7 = SB 6.5)
                # If half point, use directly (Kalshi 7.5 = SB 7.5)
                if kalshi_line % 1 == 0:  # Whole number
                    converted_line = kalshi_line - 0.5
                else:  # Half point
                    converted_line = kalshi_line
                
                if kalshi_row.get('side') == 'Yes':
                    # Kalshi "Denver over X" = Sportsbook "Denver -X"
                    sportsbook_line = -converted_line
                else:  # No side
                    # Kalshi "Cincinnati under X" = Sportsbook "Cincinnati +X" 
                    sportsbook_line = converted_line
                    
                sb_matches = sb_df_with_rows[
                    (sb_df_with_rows['bet_type'] == 'spread') &
                    (sb_df_with_rows['away_team'] == kalshi_row['away_team']) &
                    (sb_df_with_rows['home_team'] == kalshi_row['home_team']) &
                    (sb_df_with_rows['spread_line'] == sportsbook_line)
                ]
            else:
                sb_matches = pd.DataFrame()
                
        elif bet_type == 'total':
            # Convert Kalshi total: ticker X = sportsbook X-0.5
            kalshi_total = kalshi_row.get('line_value')
            if kalshi_total is not None:
                sportsbook_total = kalshi_total - 0.5
                
                sb_matches = sb_df_with_rows[
                    (sb_df_with_rows['bet_type'] == 'total') &
                    (sb_df_with_rows['away_team'] == kalshi_row['away_team']) &
                    (sb_df_with_rows['home_team'] == kalshi_row['home_team']) &
                    (sb_df_with_rows['total_line'] == sportsbook_total)
                ]
            else:
                sb_matches = pd.DataFrame()
        else:
            sb_matches = pd.DataFrame()
        
        # Add matches - THIS IS WHERE WE GET ALL BOOKMAKER MATCHES
        for _, sb_row in sb_matches.iterrows():
            match_count += 1
            away_team = kalshi_row['away_team']
            home_team = kalshi_row['home_team']
            team_side = kalshi_row['team']
            side = kalshi_row.get('side', 'ML')
            
            matches.append({
                'Match_ID': match_count,
                'Kalshi_Row': kalshi_row['Row_ID'],
                'Sportsbook_Row': sb_row['Row_ID'],
                'Game': f'{away_team} @ {home_team}',
                'Bet_Type': bet_type,
                'Line_Value': kalshi_row.get('line_value'),
                'Kalshi_Team_Side': f'{team_side} ({side})',
                'Sportsbook_Team': sb_row['team'],
                'Bookmaker': sb_row['bookmaker'],  # This captures each bookmaker separately
                'Kalshi_Probability': kalshi_row['kalshi_probability'],
                'Sportsbook_Probability': sb_row.get('implied_prob_vig_adj', 0),
                'Probability_Diff': kalshi_row['kalshi_probability'] - sb_row.get('implied_prob_vig_adj', 0),
                'Sportsbook_American_Odds': sb_row.get('american_odds', 0),
                'Kalshi_Bid_Ask': f"{kalshi_row.get('yes_bid', 0)}¢/{kalshi_row.get('yes_ask', 0)}¢"
            })

    matches_df = pd.DataFrame(matches)
    print(f'🔗 Found {len(matches_df)} total matches')

    # Create non-matches analysis
    matched_kalshi_rows = set(matches_df['Kalshi_Row'].tolist()) if not matches_df.empty else set()
    non_matched_kalshi = kalshi_df_with_rows[~kalshi_df_with_rows['Row_ID'].isin(matched_kalshi_rows)].copy()
    
    print(f'❌ Non-matched Kalshi entries: {len(non_matched_kalshi)}')
    
    # Add analysis columns for non-matches
    non_matched_kalshi['Potential_Issue'] = non_matched_kalshi.apply(lambda row: 
        'No line_value' if pd.isna(row.get('line_value')) else
        'Team name mismatch?' if row['bet_type'] != 'moneyline' else
        'Game not in sportsbooks?', axis=1)

    # Save to Excel with multiple sheets
    with pd.ExcelWriter('final_ml_team_fix.xlsx', engine='openpyxl') as writer:
        
        # Sheet 1: All Kalshi data with row IDs
        kalshi_df_with_rows.to_excel(writer, sheet_name='Kalshi All Data', index=False)
        
        # Sheet 2: All Sportsbook data with row IDs  
        sb_df_with_rows.to_excel(writer, sheet_name='Sportsbook All Data', index=False)
        
        # Sheet 3: Matches with row references
        matches_df.to_excel(writer, sheet_name='Matched Pairs', index=False)
        
        # Sheet 4: Non-matched Kalshi entries for analysis
        non_matched_kalshi.to_excel(writer, sheet_name='Non-Matched Kalshi', index=False)
        
        # Sheet 5: Summary
        summary_data = {
            'Metric': ['Kalshi Entries', 'Sportsbook Entries', 'Total Matches', 'Unique Games Matched', 'Match Rate'],
            'Value': [
                len(kalshi_df),
                len(sb_df), 
                len(matches_df),
                matches_df['Game'].nunique() if not matches_df.empty else 0,
                f'{len(matches_df)/len(kalshi_df)*100:.1f}%' if len(kalshi_df) > 0 else '0%'
            ]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)

    print('✅ Created final_ml_team_fix.xlsx with:')
    print('   📊 Sheet 1: Kalshi All Data (with Row_IDs)')
    print('   📊 Sheet 2: Sportsbook All Data (with Row_IDs)')
    print('   🔗 Sheet 3: Matched Pairs (with row references)')
    print('   ❌ Sheet 4: Non-Matched Kalshi (for debugging)')
    print('   📈 Sheet 5: Summary statistics')

if __name__ == "__main__":
    create_comprehensive_raw_data()
