#!/usr/bin/env python3
"""
NFL Markets Analysis - Kalshi API
Analyzes NFL moneyline markets for EV betting opportunities
"""

import kalshi_py
from kalshi_py.api.market import get_markets
from kalshi_py import create_client
from datetime import datetime
import os
from dotenv import load_dotenv


def get_nfl_moneyline_markets():
    """Get all active NFL moneyline markets with liquidity data"""
    print("🏈 NFL MONEYLINE MARKETS ANALYSIS")
    print("=" * 50)
    
    try:
        # Load environment variables
        load_dotenv()
        api_key_id = os.getenv('KALSHI_API_KEY_ID')
        private_key = os.getenv('KALSHI_PY_PRIVATE_KEY_PEM')
        
        if not api_key_id or not private_key:
            print("❌ Missing API credentials in .env file")
            return []
            
        client = create_client(base_url="https://api.elections.kalshi.com/trade-api/v2")
        
        # Get NFL moneyline markets
        print("🔍 Fetching NFL moneyline markets (KXNFLGAME)...")
        response = get_markets.sync(client=client, series_ticker='KXNFLGAME', limit=1000)
        
        if not response or not response.markets:
            print("❌ No NFL markets found")
            return []
            
        # Filter for active markets only
        active_markets = [m for m in response.markets if m.status == 'active']
        print(f"✅ Found {len(active_markets)} active NFL moneyline markets")
        print()
        
        # Analyze each market
        liquid_markets = []
        for i, market in enumerate(active_markets, 1):
            volume_24h = getattr(market, 'volume_24h', 0)
            open_interest = getattr(market, 'open_interest', 0)
            yes_bid = getattr(market, 'yes_bid', 0)
            yes_ask = getattr(market, 'yes_ask', 0)
            liquidity = getattr(market, 'liquidity', 0)
            
            # Check if market has meaningful activity
            is_liquid = volume_24h > 0 or open_interest > 0
            
            print(f"{i:2d}. {market.title}")
            print(f"    Ticker: {market.ticker}")
            print(f"    Price: Bid {yes_bid}¢ / Ask {yes_ask}¢ (Spread: {yes_ask - yes_bid}¢)")
            print(f"    Volume 24h: {volume_24h:,} | Open Interest: {open_interest:,}")
            print(f"    Liquidity: ${liquidity:,} | Status: {'🔥 LIQUID' if is_liquid else '💀 NO VOLUME'}")
            print()
            
            if is_liquid:
                liquid_markets.append({
                    'title': market.title,
                    'ticker': market.ticker,
                    'yes_bid': yes_bid,
                    'yes_ask': yes_ask,
                    'spread': yes_ask - yes_bid,
                    'volume_24h': volume_24h,
                    'open_interest': open_interest,
                    'liquidity': liquidity
                })
        
        print(f"📊 SUMMARY:")
        print(f"🔥 Liquid markets: {len(liquid_markets)}")
        print(f"💀 Illiquid markets: {len(active_markets) - len(liquid_markets)}")
        print()
        
        return liquid_markets
        
    except Exception as e:
        print(f"❌ Error fetching NFL markets: {e}")
        return []


def extract_games_from_markets(markets):
    """Extract unique games from market data"""
    games = {}
    
    for market in markets:
        # Extract game info from ticker
        # Example: KXNFLGAME-25SEP15LACLV-LAC -> game_id = 25SEP15LACLV
        ticker_parts = market['ticker'].split('-')
        if len(ticker_parts) >= 3:
            game_id = ticker_parts[1]  # 25SEP15LACLV
            team = ticker_parts[2]     # LAC or LV
            
            if game_id not in games:
                games[game_id] = {}
            
            games[game_id][team] = {
                'title': market['title'],
                'ticker': market['ticker'],
                'yes_ask': market['yes_ask'],
                'yes_bid': market['yes_bid'],
                'spread': market['spread'],
                'volume_24h': market['volume_24h'],
                'liquidity': market['liquidity']
            }
    
    return games


if __name__ == "__main__":
    # Get all liquid NFL moneyline markets
    markets = get_nfl_moneyline_markets()
    
    if markets:
        # Extract unique games
        games = extract_games_from_markets(markets)
        
        print(f"🎯 UNIQUE GAMES FOUND: {len(games)}")
        print("=" * 40)
        
        for game_id, teams in games.items():
            print(f"📅 Game: {game_id}")
            for team, data in teams.items():
                print(f"  {team}: {data['yes_ask']}¢ (Vol: {data['volume_24h']:,})")
            print()
        
        print("✅ Ready for sportsbook odds comparison!")
    else:
        print("❌ No liquid markets found")
