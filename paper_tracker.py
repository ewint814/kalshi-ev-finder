#!/usr/bin/env python3
"""
Paper Trading Tracker
Automatically generate CSV entries for paper trading EV opportunities
"""

import csv
from datetime import datetime
import os
from ev_calculator import find_ev_opportunities


def create_paper_trades(min_ev_percent=1.0, max_bet_amount=20):
    """
    Generate paper trading entries from current EV opportunities
    
    Args:
        min_ev_percent: Minimum EV percentage to include (default 1%)
        max_bet_amount: Maximum bet amount for paper trading (default $20)
    """
    print("📝 PAPER TRADING TRACKER")
    print("=" * 30)
    
    # Get current EV opportunities
    print("🔍 Finding current EV opportunities...")
    opportunities = find_ev_opportunities()
    
    if not opportunities:
        print("❌ No opportunities found")
        return
    
    # Filter for positive EV above threshold
    good_opportunities = [
        op for op in opportunities 
        if op['is_positive_ev'] and op['ev_percent'] >= min_ev_percent
    ]
    
    print(f"✅ Found {len(good_opportunities)} opportunities above {min_ev_percent}% EV")
    
    # Create CSV filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"paper_trades_{timestamp}.csv"
    filepath = os.path.join(os.getcwd(), filename)
    
    # CSV headers
    headers = [
        'Date', 'Time', 'Game_ID', 'Team', 'Market_Type',
        'Kalshi_Price', 'Sportsbook_Odds', 'Implied_Prob', 
        'EV_Percent', 'EV_Dollars', 'Bet_Amount',
        'Max_Win', 'Max_Loss', 'Outcome', 'Profit_Loss', 'Notes'
    ]
    
    paper_trades = []
    
    for i, op in enumerate(good_opportunities):
        # Calculate bet sizing (simple fixed amount for now)
        bet_amount = min(max_bet_amount, max_bet_amount)
        
        # Calculate potential outcomes
        kalshi_cost = (op['kalshi_price_cents'] / 100) * bet_amount
        max_win = bet_amount - kalshi_cost
        max_loss = kalshi_cost
        
        trade_entry = {
            'Date': datetime.now().strftime("%Y-%m-%d"),
            'Time': datetime.now().strftime("%H:%M"),
            'Game_ID': op['game_id'],
            'Team': op['team'],
            'Market_Type': 'Moneyline',
            'Kalshi_Price': f"{op['kalshi_price_cents']}¢",
            'Sportsbook_Odds': f"{op['sportsbook_odds']:+d}",
            'Implied_Prob': f"{op['true_prob']:.1%}",
            'EV_Percent': f"{op['ev_percent']:+.1f}%",
            'EV_Dollars': f"${op['ev_dollars']:+.2f}",
            'Bet_Amount': f"${bet_amount}",
            'Max_Win': f"${max_win:.2f}",
            'Max_Loss': f"${max_loss:.2f}",
            'Outcome': '',  # To be filled after game
            'Profit_Loss': '',  # To be calculated after game
            'Notes': f"Vol: ${op['volume_24h']:,}"
        }
        
        paper_trades.append(trade_entry)
        
        print(f"{i+1:2d}. {op['team']} ({op['game_id']})")
        print(f"    EV: {op['ev_percent']:+.1f}% | Bet: ${bet_amount} | Win: ${max_win:.2f} | Lose: ${max_loss:.2f}")
    
    # Write to CSV
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            writer.writerows(paper_trades)
        
        print(f"\n✅ Paper trades saved to: {filename}")
        print(f"📊 {len(paper_trades)} trades ready for tracking")
        print(f"💰 Total paper capital allocated: ${len(paper_trades) * max_bet_amount}")
        
        return filepath
        
    except Exception as e:
        print(f"❌ Error saving CSV: {e}")
        return None


def update_paper_trade_results(csv_file, game_results):
    """
    Update paper trading CSV with actual game results
    
    Args:
        csv_file: Path to the paper trading CSV
        game_results: Dict of {game_id: {team: 'win'/'loss'}}
    """
    print(f"📊 Updating results in {csv_file}")
    
    try:
        # Read existing trades
        trades = []
        with open(csv_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            trades = list(reader)
        
        # Update with results
        updated_trades = []
        total_profit = 0
        
        for trade in trades:
            game_id = trade['Game_ID']
            team = trade['Team']
            
            if game_id in game_results and team in game_results[game_id]:
                outcome = game_results[game_id][team]
                trade['Outcome'] = outcome
                
                # Calculate P&L
                bet_amount = float(trade['Bet_Amount'].replace('$', ''))
                if outcome == 'win':
                    profit = float(trade['Max_Win'].replace('$', ''))
                    trade['Profit_Loss'] = f"${profit:+.2f}"
                else:
                    loss = -float(trade['Max_Loss'].replace('$', ''))
                    trade['Profit_Loss'] = f"${loss:+.2f}"
                
                total_profit += float(trade['Profit_Loss'].replace('$', ''))
            
            updated_trades.append(trade)
        
        # Write updated CSV
        with open(csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=updated_trades[0].keys())
            writer.writeheader()
            writer.writerows(updated_trades)
        
        print(f"✅ Updated {len([t for t in updated_trades if t['Outcome']])} trade results")
        print(f"💰 Current P&L: ${total_profit:+.2f}")
        
    except Exception as e:
        print(f"❌ Error updating results: {e}")


if __name__ == "__main__":
    # Generate paper trades for current opportunities
    csv_file = create_paper_trades(min_ev_percent=2.0, max_bet_amount=20)
    
    if csv_file:
        print(f"\n🎯 NEXT STEPS:")
        print(f"1. Wait for games to finish")
        print(f"2. Update results manually or with game data")
        print(f"3. Track performance over time")
        print(f"4. Validate if +EV predictions are accurate")
        
        # Example of how to update results (manual for now)
        print(f"\n📝 To update results later:")
        print(f"game_results = {{'25SEP14SFNO': {{'NO': 'win', 'SF': 'loss'}}}}")
        print(f"update_paper_trade_results('{os.path.basename(csv_file)}', game_results)")
