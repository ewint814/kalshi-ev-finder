#!/usr/bin/env python3
"""
Manual NFL Odds
Manually entered realistic moneyline odds for testing EV calculator
"""

def get_manual_nfl_odds():
    """Get manually entered NFL moneyline odds for current week"""
    print("📝 MANUAL NFL ODDS")
    print("=" * 20)
    
    # REAL NFL moneyline odds from VegasInsider Week 2 2025
    manual_odds = {
        # From https://www.vegasinsider.com/nfl/nfl-odds-week-2-2025/
        'GB': -190,   'WAS': +160,     # Packers vs Commanders
        'MIA': -130,  'NE': +110,      # Dolphins vs Patriots  
        'CIN': -185,  'JAC': +155,     # Bengals vs Jaguars
        'BAL': -900,  'CLE': +550,     # Ravens vs Browns
        'DAL': -250,  'NYG': +210,     # Cowboys vs Giants
        'LA': -275,   'TEN': +225,     # Rams vs Titans
        'BUF': -320,  'NYJ': +260,     # Bills vs Jets
        'DET': -225,  'CHI': +190,     # Lions vs Bears
        'ARI': -290,  'CAR': +240,     # Cardinals vs Panthers
        'DEN': -135,  'IND': +115,     # Colts vs Broncos
        'SF': -275,   'NO': +225,     # 49ers vs Seahawks
        'PIT': -145,  'SEA': +125,      # Steelers vs Chiefs
        'MIN': -210,  'ATL': +175,     # Vikings vs Falcons
        'PHI': -120,  'KC': +100,     # Saints (standalone for now)
        'HOU': -145,  'TB': +125,      # Texans vs Buccaneers
        'LAC': -190,  'LV': +160,      # Chargers vs Raiders
    }
    
    print(f"📊 Manual odds for {len(manual_odds)} teams:")
    for team, odds in sorted(manual_odds.items()):
        from espn_odds import american_to_probability
        prob = american_to_probability(odds)
        print(f"  {team}: {odds:+4d} ({prob:.1%})")
    
    return manual_odds


if __name__ == "__main__":
    odds = get_manual_nfl_odds()
    print(f"\n✅ Ready to use {len(odds)} manual odds for EV testing")
