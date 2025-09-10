#!/usr/bin/env python3
"""
Kalshi EV Finder - Main Entry Point
Find positive expected value betting opportunities on NFL games
"""

from ev_calculator import find_ev_opportunities
from paper_tracker import create_paper_trades
import sys


def main():
    """Main application entry point"""
    print("🎯 KALSHI EV FINDER")
    print("=" * 30)
    print("Finding positive EV NFL betting opportunities...")
    print()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "paper":
            # Generate paper trades
            print("📝 Generating paper trades...")
            min_ev = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
            bet_size = int(sys.argv[3]) if len(sys.argv) > 3 else 20
            create_paper_trades(min_ev_percent=min_ev, max_bet_amount=bet_size)
            
        elif command == "find":
            # Find EV opportunities
            print("🔍 Finding EV opportunities...")
            opportunities = find_ev_opportunities()
            if opportunities:
                positive_ev = [op for op in opportunities if op['is_positive_ev']]
                print(f"\n🎯 SUMMARY: Found {len(positive_ev)} positive EV opportunities")
            
        else:
            print("❌ Unknown command. Use 'paper' or 'find'")
    else:
        # Default: show EV opportunities
        print("🔍 Finding current EV opportunities...")
        opportunities = find_ev_opportunities()
        
        if opportunities:
            positive_ev = [op for op in opportunities if op['is_positive_ev']]
            print(f"\n🎯 SUMMARY:")
            print(f"✅ Found {len(positive_ev)} positive EV opportunities")
            print(f"💰 Best EV: {positive_ev[0]['team']} +{positive_ev[0]['ev_percent']:.1f}%")
            print(f"\n📝 To generate paper trades: python main.py paper")
            print(f"🔍 To see full analysis: python main.py find")


if __name__ == "__main__":
    main()
