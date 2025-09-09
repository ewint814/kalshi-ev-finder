#!/usr/bin/env python3
"""
Kalshi EV Finder - Main Entry Point
Find positive expected value betting opportunities on NFL games
"""

from nfl_markets import get_nfl_moneyline_markets, extract_games_from_markets


def main():
    """Main application entry point"""
    print("🎯 KALSHI EV FINDER")
    print("=" * 30)
    print("Finding positive EV NFL betting opportunities...")
    print()
    
    # Step 1: Get liquid NFL moneyline markets from Kalshi
    print("📊 STEP 1: Fetching Kalshi NFL Markets")
    markets = get_nfl_moneyline_markets()
    
    if not markets:
        print("❌ No liquid markets found. Exiting.")
        return
    
    # Step 2: Extract unique games
    games = extract_games_from_markets(markets)
    print(f"🎮 Found {len(games)} unique NFL games with liquid betting markets")
    
    # Step 3: TODO - Get sportsbook odds for comparison
    print("\n🔍 STEP 2: Get Sportsbook Odds (TODO)")
    print("Next: Implement sportsbook odds fetching")
    
    # Step 4: TODO - Calculate EV opportunities  
    print("\n💰 STEP 3: Calculate EV Opportunities (TODO)")
    print("Next: Compare Kalshi prices vs sportsbook implied probabilities")
    
    print("\n✅ Current status: Kalshi market data collection complete!")


if __name__ == "__main__":
    main()
