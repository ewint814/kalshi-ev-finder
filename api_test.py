#!/usr/bin/env python3
"""
Kalshi API Test Script
Tests connection to Kalshi's API using the official kalshi-py library
"""

import kalshi_py
from kalshi_py.api.market import get_markets
from kalshi_py import create_client
from datetime import datetime
import json
import inspect
import os
from dotenv import load_dotenv

def search_kxnflgame_markets():
    """Search specifically for KXNFLGAME series that user found on website"""
    print("🏈 KXNFLGAME Market Search:")
    print("=" * 40)
    
    try:
        # Load environment variables
        load_dotenv()
        api_key_id = os.getenv('KALSHI_API_KEY_ID')
        private_key = os.getenv('KALSHI_PY_PRIVATE_KEY_PEM')
        
        if not api_key_id or not private_key:
            print("❌ Missing API credentials")
            return
            
        client = create_client(base_url="https://api.elections.kalshi.com/trade-api/v2")
        
        # Search specifically for KXNFLGAME series
        print("🔍 Searching for KXNFLGAME series...")
        try:
            response = get_markets.sync(client=client, series_ticker='KXNFLGAME', limit=500)
            if response and response.markets:
                print(f"🎉 SUCCESS! Found {len(response.markets)} KXNFLGAME markets:")
                print("=" * 60)
                
                for i, market in enumerate(response.markets, 1):
                    print(f"{i:2d}. {market.title}")
                    print(f"    Ticker: {market.ticker}")
                    print(f"    Status: {market.status}")
                    if hasattr(market, 'last_price') and market.last_price:
                        print(f"    Price: {market.last_price} | Bid: {getattr(market, 'yes_bid', 0)} | Ask: {getattr(market, 'yes_ask', 0)}")
                    print(f"    Closes: {market.close_time}")
                    print()
                
                # Separate active vs finalized markets
                active_markets = [m for m in response.markets if m.status == 'active']
                finalized_markets = [m for m in response.markets if m.status == 'finalized']
                other_markets = [m for m in response.markets if m.status not in ['active', 'finalized']]
                
                print(f"\n📊 MARKET STATUS BREAKDOWN:")
                print(f"✅ Active markets: {len(active_markets)}")
                print(f"🏁 Finalized markets: {len(finalized_markets)}")
                print(f"📋 Other status: {len(other_markets)}")
                
                if active_markets:
                    print(f"\n🏈 ACTIVE NFL GAMES:")
                    for i, market in enumerate(active_markets, 1):
                        print(f"{i:2d}. {market.title}")
                        print(f"    Ticker: {market.ticker}")
                        print(f"    Price: {market.last_price} | Bid: {getattr(market, 'yes_bid', 0)} | Ask: {getattr(market, 'yes_ask', 0)}")
                        print(f"    Closes: {market.close_time}")
                        print()
                
                return response.markets
            else:
                print("❌ No KXNFLGAME markets found")
                
        except Exception as e:
            print(f"❌ Error searching KXNFLGAME: {e}")
            
        # Also try NFL spread, total, and touchdown markets
        nfl_series = ['KXNFL', 'KXNFLGAME', 'KXNFLSPREAD', 'KXNFLOVER', 'KXNFLUNDER', 
                     'KXNFLTOTAL', 'KXNFLTD', 'KXNFLFIRSTTD', 'KXNFLANYTD', 
                     'KXNFLPTS', 'KXNFLOU']
        print(f"\n🔍 Searching for NFL spreads, totals, and touchdown markets:")
        
        for variation in nfl_series:
            try:
                response = get_markets.sync(client=client, series_ticker=variation, limit=50)
                if response and response.markets:
                    print(f"✅ Found {len(response.markets)} markets for '{variation}':")
                    for market in response.markets[:3]:  # Show first 3
                        print(f"  - {market.title} | {market.ticker}")
                else:
                    print(f"  No markets for '{variation}'")
            except Exception as e:
                print(f"  Error with '{variation}': {e}")
                
    except Exception as e:
        print(f"❌ Error in KXNFLGAME search: {e}")

def search_all_nfl_market_types():
    """Search for all types of NFL markets: moneyline, spreads, totals, touchdowns"""
    print("🏈 Comprehensive NFL Market Type Search:")
    print("=" * 50)
    
    try:
        # Load environment variables
        load_dotenv()
        api_key_id = os.getenv('KALSHI_API_KEY_ID')
        private_key = os.getenv('KALSHI_PY_PRIVATE_KEY_PEM')
        
        if not api_key_id or not private_key:
            print("❌ Missing API credentials")
            return
            
        client = create_client(base_url="https://api.elections.kalshi.com/trade-api/v2")
        
        # Define all possible NFL market types
        nfl_market_types = {
            'KXNFLGAME': 'Moneyline (Winner)',
            'KXNFLSPREAD': 'Point Spreads', 
            'KXNFLOVER': 'Over Totals',
            'KXNFLUNDER': 'Under Totals',
            'KXNFLTOTAL': 'Total Points',
            'KXNFLOU': 'Over/Under',
            'KXNFLPTS': 'Points Markets',
            'KXNFLFIRSTTD': 'First Touchdown',
            'KXNFLANYTD': 'Anytime Touchdown',
            'KXNFLTD': 'Touchdown Markets',
            'KXNFLRUSH': 'Rushing Markets',
            'KXNFLPASS': 'Passing Markets',
            'KXNFLREC': 'Receiving Markets'
        }
        
        print("🔍 Searching for different NFL market types:")
        print()
        
        found_types = {}
        
        for series_ticker, description in nfl_market_types.items():
            try:
                # Get all markets with pagination
                all_markets = []
                cursor = None
                page = 1
                
                while True:
                    print(f"   Fetching {description} page {page}...")
                    if cursor:
                        response = get_markets.sync(client=client, series_ticker=series_ticker, cursor=cursor, limit=1000)
                    else:
                        response = get_markets.sync(client=client, series_ticker=series_ticker, limit=1000)
                    
                    if response and response.markets:
                        all_markets.extend(response.markets)
                        print(f"   Got {len(response.markets)} markets on page {page}")
                        
                        # Check for pagination - this might not work with current API
                        if len(response.markets) < 1000:  # Assume we got all if less than 1000
                            break
                        
                        page += 1
                        if page > 10:  # Safety limit
                            print(f"   Stopping at page {page} for safety")
                            break
                    else:
                        break
                
                if all_markets:
                    active_markets = [m for m in all_markets if m.status == 'active']
                    found_types[series_ticker] = {
                        'description': description,
                        'total': len(all_markets),
                        'active': len(active_markets),
                        'markets': all_markets
                    }
                    print(f"✅ {description} ({series_ticker}): {len(all_markets)} total, {len(active_markets)} active")
                    
                    # Show a few examples of active markets
                    if active_markets:
                        print(f"   Examples:")
                        # Show detailed analysis for KXNFLGAME (moneyline) markets
                        if series_ticker == 'KXNFLGAME':
                            print(f"   🏈 DETAILED MONEYLINE ANALYSIS:")
                            print(f"   📊 All {len(active_markets)} active moneyline markets:")
                            
                            for i, market in enumerate(active_markets):
                                # Extract key liquidity metrics
                                volume = getattr(market, 'volume', 0)
                                volume_24h = getattr(market, 'volume_24h', 0)
                                open_interest = getattr(market, 'open_interest', 0)
                                yes_bid = getattr(market, 'yes_bid', 0)
                                yes_ask = getattr(market, 'yes_ask', 0)
                                liquidity = getattr(market, 'liquidity', 0)
                                
                                # Show liquidity status
                                liquidity_status = "🔥 LIQUID" if volume_24h > 0 or open_interest > 0 else "💀 NO VOLUME"
                                
                                print(f"   {i+1:2d}. {market.title}")
                                print(f"       Ticker: {market.ticker}")
                                print(f"       Bid/Ask: {yes_bid}¢/{yes_ask}¢ | Spread: {yes_ask - yes_bid}¢")
                                print(f"       Volume: {volume} | 24h: {volume_24h} | OI: {open_interest} | {liquidity_status}")
                                print(f"       Liquidity: ${liquidity:,}")
                                print()
                            
                            # Summary of liquid vs illiquid
                            liquid_markets = [m for m in active_markets if getattr(m, 'volume_24h', 0) > 0 or getattr(m, 'open_interest', 0) > 0]
                            print(f"   📈 LIQUIDITY SUMMARY:")
                            print(f"   🔥 Liquid markets (with volume/OI): {len(liquid_markets)}")
                            print(f"   💀 Illiquid markets: {len(active_markets) - len(liquid_markets)}")
                            
                        elif series_ticker == 'KXNFLTOTAL':
                            print(f"   First 20 Total Points markets:")
                            for i, market in enumerate(active_markets[:20]):
                                print(f"   {i+1:2d}. {market.title} | {market.ticker}")
                            
                            # Show ALL total point options for LAC vs LV game
                            print(f"\n   🎯 ALL TOTAL POINT OPTIONS for LAC vs LV game:")
                            lac_lv_totals = []
                            for market in active_markets:
                                if 'LACLV' in market.ticker:
                                    # Extract the total number from ticker
                                    ticker_parts = market.ticker.split('-')
                                    if len(ticker_parts) >= 3:
                                        total_num = ticker_parts[2]
                                        try:
                                            lac_lv_totals.append((int(total_num), market.title, market.ticker))
                                        except ValueError:
                                            pass  # Skip if not a number
                            
                            # Sort by total number and remove duplicates
                            unique_totals = {}
                            for total, title, ticker in lac_lv_totals:
                                if total not in unique_totals:
                                    unique_totals[total] = (title, ticker)
                            
                            sorted_totals = sorted(unique_totals.items())
                            print(f"   📊 Found {len(sorted_totals)} UNIQUE totals for LAC vs LV:")
                            for i, (total, (title, ticker)) in enumerate(sorted_totals):
                                print(f"   {i+1:2d}. {total} points | {ticker}")
                            
                            print(f"   🤯 WOW! {len(sorted_totals)} different total point options for ONE GAME!")
                            
                            # Now let's check the ACTUAL market data for liquidity
                            print(f"\n   💰 CHECKING LIQUIDITY - Sample market data:")
                            if active_markets and len(active_markets) > 0:
                                sample_market = active_markets[0]
                                print(f"   📊 Sample market fields available:")
                                for attr in dir(sample_market):
                                    if not attr.startswith('_'):
                                        try:
                                            value = getattr(sample_market, attr)
                                            if not callable(value):
                                                print(f"      {attr}: {value}")
                                        except:
                                            print(f"      {attr}: <unable to access>")
                            
                            # Show the range
                            if sorted_totals:
                                min_total = sorted_totals[0][0]
                                max_total = sorted_totals[-1][0]
                                print(f"   📈 Range: {min_total} to {max_total} points ({max_total - min_total + 1} point spread)")
                        elif series_ticker == 'KXNFLSPREAD':
                            print(f"   First 20 Spread markets:")
                            for i, market in enumerate(active_markets[:20]):
                                print(f"   {i+1:2d}. {market.title} | {market.ticker}")
                            
                            # Count unique games in spread markets
                            unique_games = set()
                            for market in active_markets:
                                # Extract game identifier from ticker (before the last dash)
                                ticker_parts = market.ticker.split('-')
                                if len(ticker_parts) >= 2:
                                    game_id = '-'.join(ticker_parts[:2])  # KXNFLSPREAD-25SEP15LACLV
                                    unique_games.add(game_id)
                            print(f"   📊 Unique games with spreads: {len(unique_games)}")
                        else:
                            for market in active_markets[:2]:  # Show first 2
                                print(f"   - {market.title} | {market.ticker}")
                            if len(active_markets) > 2:
                                print(f"   ... and {len(active_markets) - 2} more")
                        print()
                else:
                    print(f"❌ No {description} markets found ({series_ticker})")
                    
            except Exception as e:
                print(f"❌ Error searching {description} ({series_ticker}): {e}")
        
        # Summary
        print("\n📊 NFL MARKET TYPES SUMMARY:")
        print("=" * 40)
        if found_types:
            total_markets = sum(data['total'] for data in found_types.values())
            total_active = sum(data['active'] for data in found_types.values())
            print(f"🎯 Found {len(found_types)} different market types")
            print(f"📈 Total NFL markets: {total_markets}")
            print(f"✅ Active NFL markets: {total_active}")
            print()
            
            for series, data in found_types.items():
                if data['active'] > 0:
                    print(f"• {data['description']}: {data['active']} active markets")
        else:
            print("❌ No NFL markets found across any series")
            
        return found_types
        
    except Exception as e:
        print(f"❌ Error in comprehensive NFL search: {e}")
        return {}

def search_nfl_markets():
    """Search specifically for active NFL markets using discovered patterns"""
    print("🏈 Focused NFL Market Search:")
    
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        # Verify environment variables are loaded
        api_key_id = os.getenv('KALSHI_API_KEY_ID')
        private_key = os.getenv('KALSHI_PY_PRIVATE_KEY_PEM')
        
        if not api_key_id or not private_key:
            print("❌ Missing API credentials in .env file")
            return
            
        print(f"✅ Loaded API Key ID: {api_key_id[:10]}...")
        
        # Create Kalshi client using the official method with production URL
        client = create_client(base_url="https://api.elections.kalshi.com/trade-api/v2")
        
        # Search for NFL markets using discovered ticker patterns
        nfl_patterns = ['KXNFL', 'NFL', 'FOOTBALL']
        
        print("\n🔍 Searching for active NFL markets by ticker patterns:")
        for pattern in nfl_patterns:
            try:
                response = get_markets.sync(client=client, tickers=pattern, limit=100)
                if response and response.markets:
                    print(f"📊 Found {len(response.markets)} markets for ticker pattern '{pattern}':")
                    for market in response.markets:
                        print(f"  - {market.title}")
                        print(f"    Ticker: {market.ticker} | Status: {market.status}")
                        if hasattr(market, 'last_price') and market.last_price:
                            print(f"    Price: {market.last_price} | Bid: {getattr(market, 'yes_bid', 0)} | Ask: {getattr(market, 'yes_ask', 0)}")
                        print(f"    Closes: {market.close_time}")
                        print()
                else:
                    print(f"  No markets found for ticker pattern '{pattern}'")
            except Exception as e:
                print(f"  Error searching ticker pattern '{pattern}': {e}")
        
        print("\n🔍 Searching all markets (no status filter) for NFL patterns:")
        try:
            response = get_markets.sync(client=client, limit=1000)
            if response and response.markets:
                nfl_active = []
                for market in response.markets:
                    title_lower = market.title.lower()
                    ticker_lower = market.ticker.lower()
                    
                    # Look for NFL patterns
                    if any(pattern in title_lower or pattern in ticker_lower 
                           for pattern in ['nfl', 'football', 'touchdown', 'chiefs', 'cowboys', 
                                         'patriots', 'steelers', 'packers', 'ravens', 'bills']):
                        nfl_active.append(market)
                
                if nfl_active:
                    print(f"🏈 Found {len(nfl_active)} NFL markets:")
                    for market in nfl_active:
                        print(f"  - {market.title}")
                        print(f"    Ticker: {market.ticker} | Status: {market.status}")
                        if hasattr(market, 'last_price') and market.last_price:
                            print(f"    Price: {market.last_price} | Bid: {getattr(market, 'yes_bid', 0)} | Ask: {getattr(market, 'yes_ask', 0)}")
                        print(f"    Closes: {market.close_time}")
                        print()
                else:
                    print("❌ No NFL markets found in current batch")
            else:
                print("❌ No active markets returned")
        except Exception as e:
            print(f"❌ Error searching markets: {e}")
        
        # Try searching by specific series tickers that might exist
        print("\n🔍 Trying specific NFL series ticker patterns:")
        nfl_series = ['KXNFLGAME', 'NFLGAME', 'NFLTD', 'NFLWIN', 'NFLSPREAD', 'NFLOVER', 'NFLUNDER']
        
        for series in nfl_series:
            try:
                response = get_markets.sync(client=client, series_ticker=series, limit=50)
                if response and response.markets:
                    print(f"📊 Found {len(response.markets)} markets for series '{series}':")
                    for market in response.markets[:3]:  # Show first 3
                        print(f"  - {market.title} | {market.ticker}")
                else:
                    print(f"  No markets found for series '{series}'")
            except Exception as e:
                print(f"  Error searching series '{series}': {e}")
                
    except Exception as e:
        print(f"❌ Error in NFL market search: {e}")

def website_vs_api_check():
    """Help compare what's on the website vs what we can access via API"""
    print("🌐 Website vs API Comparison Check:")
    print("=" * 60)
    
    print("📋 INSTRUCTIONS:")
    print("1. Go to kalshi.com and find the NFL markets you see")
    print("2. Copy some specific market titles or tickers you see")
    print("3. We'll search for those exact markets via API")
    print()
    
    try:
        # Load environment variables
        load_dotenv()
        api_key_id = os.getenv('KALSHI_API_KEY_ID')
        private_key = os.getenv('KALSHI_PY_PRIVATE_KEY_PEM')
        
        if not api_key_id or not private_key:
            print("❌ Missing API credentials")
            return
            
        client = create_client(base_url="https://api.elections.kalshi.com/trade-api/v2")
        
        # Search for specific market titles you might see on website
        website_examples = [
            "Chiefs", "Cowboys", "Bills", "Dolphins", "Patriots",
            "Week 2", "Sunday", "touchdown", "spread", "over", "under",
            "NFL", "football", "game", "win", "score"
        ]
        
        print("🔍 Searching for markets that might match website examples:")
        print("(These are common NFL terms you might see on the website)")
        print()
        
        all_markets = []
        
        # Get a large sample of markets
        for page in range(3):  # Get 3 pages
            try:
                if page == 0:
                    response = get_markets.sync(client=client, limit=1000)
                else:
                    # Try to get more markets with pagination
                    response = get_markets.sync(client=client, limit=1000)
                
                if response and response.markets:
                    all_markets.extend(response.markets)
                    print(f"  Loaded page {page + 1}: {len(response.markets)} markets")
                else:
                    break
            except Exception as e:
                print(f"  Error loading page {page + 1}: {e}")
                break
        
        print(f"\n📊 Total markets loaded: {len(all_markets)}")
        
        # Search for any markets that might be NFL-related
        potential_nfl = []
        for market in all_markets:
            title_lower = market.title.lower()
            ticker_lower = market.ticker.lower()
            
            for term in website_examples:
                if term.lower() in title_lower or term.lower() in ticker_lower:
                    potential_nfl.append((market, term))
                    break
        
        if potential_nfl:
            print(f"\n🏈 Found {len(potential_nfl)} potentially NFL-related markets:")
            for market, matched_term in potential_nfl:
                print(f"  - {market.title}")
                print(f"    Ticker: {market.ticker} | Status: {market.status}")
                print(f"    Matched term: '{matched_term}'")
                if hasattr(market, 'last_price') and market.last_price:
                    print(f"    Price: {market.last_price}")
                print(f"    Closes: {market.close_time}")
                print()
        else:
            print("\n❌ No NFL-related markets found in API")
            print("\n💡 NEXT STEPS:")
            print("1. Check what specific markets you see on kalshi.com")
            print("2. Note the exact titles and tickers")
            print("3. This might indicate:")
            print("   - Markets are only available through partner platforms")
            print("   - Geographic restrictions")
            print("   - API access limitations")
            print("   - Timing issues (markets appear closer to game time)")
        
        print(f"\n📈 SUMMARY:")
        print(f"- Total markets in API: {len(all_markets)}")
        print(f"- NFL-related found: {len(potential_nfl)}")
        print(f"- API endpoint: https://api.elections.kalshi.com/trade-api/v2")
        print(f"- Using production keys: Yes")
        
    except Exception as e:
        print(f"❌ Error in website vs API check: {e}")

def search_sports_markets():
    """Search specifically for NFL/MLB and other sports markets"""
    print("🏈⚾ Searching for NFL/MLB Sports Markets:")
    
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        # Verify environment variables are loaded
        api_key_id = os.getenv('KALSHI_API_KEY_ID')
        private_key = os.getenv('KALSHI_PY_PRIVATE_KEY_PEM')
        
        if not api_key_id or not private_key:
            print("❌ Missing API credentials in .env file")
            return
            
        print(f"✅ Loaded API Key ID: {api_key_id[:10]}...")
        
        # Create Kalshi client using the official method with production URL
        client = create_client(base_url="https://api.elections.kalshi.com/trade-api/v2")
        
        # Try different search strategies
        sports_keywords = ['NFL', 'MLB', 'FOOTBALL', 'BASEBALL', 'SPORT', 'GAME', 'MATCH']
        
        print("\n🔍 Strategy 1: Search for sports-related series tickers")
        for keyword in sports_keywords:
            try:
                response = get_markets.sync(client=client, series_ticker=keyword, limit=50)
                if response and response.markets:
                    print(f"📊 Found {len(response.markets)} markets for series_ticker='{keyword}':")
                    for market in response.markets:
                        print(f"  - {market.title} | {market.ticker}")
                else:
                    print(f"  No markets found for series_ticker='{keyword}'")
            except Exception as e:
                print(f"  Error searching series_ticker='{keyword}': {e}")
        
        print("\n🔍 Strategy 2: Search for sports-related event tickers")  
        for keyword in sports_keywords:
            try:
                response = get_markets.sync(client=client, event_ticker=keyword, limit=50)
                if response and response.markets:
                    print(f"📊 Found {len(response.markets)} markets for event_ticker='{keyword}':")
                    for market in response.markets:
                        print(f"  - {market.title} | {market.ticker}")
                else:
                    print(f"  No markets found for event_ticker='{keyword}'")
            except Exception as e:
                print(f"  Error searching event_ticker='{keyword}': {e}")
        
        print("\n🔍 Strategy 3: Look for sports patterns in all markets")
        response = get_markets.sync(client=client, limit=1000)  # API limit seems to be around 1000
        if response and response.markets:
            sports_markets = []
            for market in response.markets:
                title_lower = market.title.lower()
                ticker_lower = market.ticker.lower()
                
                # Look for sports keywords in title or ticker
                if any(keyword.lower() in title_lower or keyword.lower() in ticker_lower 
                       for keyword in ['nfl', 'mlb', 'football', 'baseball', 'sports', 'game', 
                                     'team', 'win', 'score', 'season', 'playoff', 'championship',
                                     'league', 'match', 'vs', 'chiefs', 'cowboys', 'patriots',
                                     'steelers', 'packers', 'ravens', 'bills', 'dolphins',
                                     'yankees', 'dodgers', 'astros', 'mets', 'red sox']):
                    sports_markets.append(market)
            
            if sports_markets:
                print(f"📊 Found {len(sports_markets)} potential sports markets:")
                for market in sports_markets:
                    print(f"  - {market.title}")
                    print(f"    Ticker: {market.ticker} | Status: {market.status}")
                    if hasattr(market, 'last_price') and market.last_price:
                        print(f"    Price: {market.last_price} | Bid: {getattr(market, 'yes_bid', 0)} | Ask: {getattr(market, 'yes_ask', 0)}")
                    print(f"    Closes: {market.close_time}")
                print()
            else:
                print("❌ No sports markets found using keyword search")
        
        print("\n🔍 Strategy 4: Try different market statuses")
        for status in ['active', 'initialized', 'settled', 'closed']:
            try:
                response = get_markets.sync(client=client, status=status, limit=500)
                if response and response.markets:
                    print(f"📊 Found {len(response.markets)} markets with status='{status}'")
                    # Look for NFL/MLB in these markets
                    nfl_mlb_markets = []
                    for market in response.markets:
                        title_lower = market.title.lower()
                        ticker_lower = market.ticker.lower()
                        if any(keyword in title_lower or keyword in ticker_lower 
                               for keyword in ['nfl', 'mlb', 'football', 'baseball', 'chiefs', 'cowboys', 'yankees', 'dodgers']):
                            nfl_mlb_markets.append(market)
                    
                    if nfl_mlb_markets:
                        print(f"  🏈⚾ Found {len(nfl_mlb_markets)} NFL/MLB markets in '{status}' status:")
                        for market in nfl_mlb_markets[:5]:  # Show first 5
                            print(f"    - {market.title} | {market.ticker}")
                else:
                    print(f"  No markets found for status='{status}'")
            except Exception as e:
                print(f"  Error searching status='{status}': {e}")
        
        print("\n🔍 Strategy 5: Check if there's pagination (cursor)")
        try:
            all_markets = []
            cursor = None
            page = 1
            
            while page <= 5:  # Limit to 5 pages to avoid infinite loop
                if cursor:
                    response = get_markets.sync(client=client, cursor=cursor, limit=1000)
                else:
                    response = get_markets.sync(client=client, limit=1000)
                
                if response and response.markets:
                    print(f"  Page {page}: Found {len(response.markets)} markets")
                    all_markets.extend(response.markets)
                    
                    # Check if there's a next cursor (this might not be available in the response)
                    if hasattr(response, 'cursor') and response.cursor:
                        cursor = response.cursor
                        page += 1
                    else:
                        break
                else:
                    break
            
            print(f"📊 Total markets across all pages: {len(all_markets)}")
            
            # Search for NFL/MLB in all pages
            nfl_mlb_all = []
            for market in all_markets:
                title_lower = market.title.lower()
                ticker_lower = market.ticker.lower()
                if any(keyword in title_lower or keyword in ticker_lower 
                       for keyword in ['nfl', 'mlb', 'football', 'baseball', 'chiefs', 'cowboys', 'yankees', 'dodgers']):
                    nfl_mlb_all.append(market)
            
            if nfl_mlb_all:
                print(f"🏈⚾ Found {len(nfl_mlb_all)} NFL/MLB markets across all pages:")
                for market in nfl_mlb_all:
                    print(f"  - {market.title} | {market.ticker}")
            else:
                print("❌ Still no NFL/MLB markets found across all pages")
                
        except Exception as e:
            print(f"❌ Error with pagination search: {e}")
                
    except Exception as e:
        print(f"❌ Error searching for sports markets: {e}")

def show_all_markets():
    """Just show all the markets available on Kalshi using the official API client"""
    print("📋 All Available Markets on Kalshi:")
    
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        # Verify environment variables are loaded
        api_key_id = os.getenv('KALSHI_API_KEY_ID')
        private_key = os.getenv('KALSHI_PY_PRIVATE_KEY_PEM')
        
        if not api_key_id or not private_key:
            print("❌ Missing API credentials in .env file")
            print("Make sure your .env file contains:")
            print("KALSHI_API_KEY_ID=your-key-id")
            print("KALSHI_PY_PRIVATE_KEY_PEM=your-private-key")
            return
            
        print(f"✅ Loaded API Key ID: {api_key_id[:10]}...")
        print(f"✅ Loaded Private Key: {len(private_key)} characters")
        
        # Create Kalshi client using the official method with production URL
        client = create_client(base_url="https://api.elections.kalshi.com/trade-api/v2")
        
        # Get markets using the official API method
        response = get_markets.sync(client=client, limit=1000)  # Increase limit to see more markets
        
        if response and response.markets:
            markets = response.markets
            print(f"✅ Found {len(markets)} total markets")
            print("=" * 80)
            
            for i, market in enumerate(markets, 1):
                print(f"{i:3d}. {market.title}")
                print(f"     Ticker: {market.ticker} | Status: {market.status}")
                
                # Show pricing if available
                if hasattr(market, 'last_price') and market.last_price:
                    print(f"     Price: {market.last_price} | Bid: {getattr(market, 'yes_bid', 0)} | Ask: {getattr(market, 'yes_ask', 0)}")
                
                print(f"     Closes: {market.close_time}")
                print()
        else:
            print("❌ No markets data received")
            
    except Exception as e:
        print(f"❌ Error connecting to Kalshi API: {e}")
        print("Note: This requires API authentication. You may need to set up API keys.")

def get_market_details(ticker):
    """Get detailed information about a specific market using the official API"""
    print(f"\n🔍 Getting details for market: {ticker}")
    
    try:
        client = kalshi_py.Client(base_url="https://api.elections.kalshi.com/trade-api/v2")
        market = client.get_market(ticker)
        
        if market:
            print(f"Title: {market.get('title', 'N/A')}")
            print(f"Status: {market.get('status', 'N/A')}")
            print(f"Close Time: {market.get('close_time', 'N/A')}")
            print(f"Yes Bid: {market.get('yes_bid', 'N/A')}")
            print(f"Yes Ask: {market.get('yes_ask', 'N/A')}")
            print(f"Last Price: {market.get('last_price', 'N/A')}")
            return market
        else:
            print(f"❌ Failed to get market details for {ticker}")
    except Exception as e:
        print(f"❌ Error getting market details: {e}")
    
    return None

def explore_kalshi_api():
    """Explore the kalshi-py library to understand available methods and get_markets parameters"""
    print("🔍 Exploring kalshi-py library...")
    
    # Check get_markets function signature and parameters
    print("\n📋 Exploring get_markets function:")
    print("=" * 50)
    try:
        from kalshi_py.api.market import get_markets
        sig = inspect.signature(get_markets.sync)
        print(f"get_markets.sync signature: {sig}")
        
        # Try to get parameter details
        for param_name, param in sig.parameters.items():
            print(f"  - {param_name}: {param.annotation} = {param.default}")
            
    except Exception as e:
        print(f"❌ Error exploring get_markets: {e}")
    
    # Check what's available in the kalshi_py module
    print("\n📦 Available in kalshi_py module:")
    print("=" * 50)
    for name in dir(kalshi_py):
        if not name.startswith('_'):
            obj = getattr(kalshi_py, name)
            print(f"- {name}: {type(obj)}")
    
    # Try to create a client and see what methods it has
    try:
        print("\n🔧 Trying to create a Client...")
        
        # Try different ways to create the client
        try:
            client = kalshi_py.Client(base_url="https://api.elections.kalshi.com/trade-api/v2")
            print("✅ Client created successfully with base_url")
        except Exception as e1:
            print(f"❌ Failed with base_url: {e1}")
            try:
                client = kalshi_py.Client()
                print("✅ Client created successfully without parameters")
            except Exception as e2:
                print(f"❌ Failed without parameters: {e2}")
                return
        
        print("\n📋 Available methods on Client:")
        print("=" * 50)
        for name in dir(client):
            if not name.startswith('_'):
                method = getattr(client, name)
                if callable(method):
                    # Try to get the method signature
                    try:
                        sig = inspect.signature(method)
                        print(f"- {name}{sig}")
                    except:
                        print(f"- {name}()")
                else:
                    print(f"- {name} (property): {type(method)}")
                    
    except Exception as e:
        print(f"❌ Error exploring client: {e}")

if __name__ == "__main__":
    print("🚀 Kalshi NFL Market Type Search")
    print("=" * 50)
    
    # Search for all NFL market types (spreads, totals, touchdowns) with correct limits
    search_all_nfl_market_types()
    
    print("\n✅ NFL market type search complete!")
