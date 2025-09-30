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


def _convert_team_abbrev_to_full(abbrev):
    """Convert team abbreviation to full name for matching with sportsbooks"""
    mapping = {
        'ARI': 'Arizona Cardinals', 'ATL': 'Atlanta Falcons', 'BAL': 'Baltimore Ravens',
        'BUF': 'Buffalo Bills', 'CAR': 'Carolina Panthers', 'CHI': 'Chicago Bears',
        'CIN': 'Cincinnati Bengals', 'CLE': 'Cleveland Browns', 'DAL': 'Dallas Cowboys',
        'DEN': 'Denver Broncos', 'DET': 'Detroit Lions', 'GB': 'Green Bay Packers',
        'HOU': 'Houston Texans', 'IND': 'Indianapolis Colts', 'JAC': 'Jacksonville Jaguars',
        'KC': 'Kansas City Chiefs', 'LV': 'Las Vegas Raiders', 'LAC': 'Los Angeles Chargers',
        'LAR': 'Los Angeles Rams', 'LA': 'Los Angeles Rams',  # Handle both LAR and LA
        'MIA': 'Miami Dolphins', 'MIN': 'Minnesota Vikings',
        'NE': 'New England Patriots', 'NO': 'New Orleans Saints', 'NYG': 'New York Giants',
        'NYJ': 'New York Jets', 'PHI': 'Philadelphia Eagles', 'PIT': 'Pittsburgh Steelers',
        'SF': 'San Francisco 49ers', 'SEA': 'Seattle Seahawks', 'TB': 'Tampa Bay Buccaneers',
        'TEN': 'Tennessee Titans', 'WAS': 'Washington Commanders'
    }
    return mapping.get(abbrev, abbrev)


def get_nfl_all_markets():
    """Get all active NFL markets - moneylines, spreads, and totals"""
    print("🏈 NFL ALL MARKETS ANALYSIS")
    print("=" * 50)
    
    try:
        # Load environment variables
        load_dotenv()
        api_key_id = os.getenv('KALSHI_API_KEY_ID')
        private_key = os.getenv('KALSHI_PY_PRIVATE_KEY_PEM')
        
        if not api_key_id or not private_key:
            print("❌ Missing API credentials in .env file")
            return {}
            
        client = create_client(base_url="https://api.elections.kalshi.com/trade-api/v2")
        
        all_markets = {}
        
        # Get different market types
        series_map = {
            'KXNFLGAME': 'moneyline',
            'KXNFLSPREAD': 'spread', 
            'KXNFLTOTAL': 'total'
        }
        
        for series_ticker, market_type in series_map.items():
            print(f"🔍 Fetching NFL {market_type} markets ({series_ticker})...")
            response = get_markets.sync(client=client, series_ticker=series_ticker, limit=1000)
            
            if not response or not response.markets:
                print(f"❌ No {market_type} markets found")
                continue
                
            # Filter for active markets only
            active_markets = [m for m in response.markets if m.status == 'active']
            print(f"✅ Found {len(active_markets)} active NFL {market_type} markets")
            
            all_markets[market_type] = active_markets
            print()
        
        return all_markets
        
    except Exception as e:
        print(f"❌ Error fetching NFL markets: {e}")
        return {}


def get_nfl_moneyline_markets():
    """Get all active NFL moneyline markets with liquidity data (backward compatibility)"""
    print("🏈 NFL MONEYLINE MARKETS ANALYSIS")
    print("=" * 50)
    
    try:
        all_markets = get_nfl_all_markets()
        if 'moneyline' not in all_markets:
            return []
        
        active_markets = all_markets['moneyline']
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


def analyze_thursday_game_lines():
    """Analyze available lines for Thursday's game"""
    print("🏈 THURSDAY GAME LINE ANALYSIS")
    print("=" * 40)
    
    all_markets = get_nfl_all_markets()
    
    if not all_markets:
        print("❌ No markets found")
        return
    
    # Look for Thursday games (typically have "THU" or specific date pattern)
    thursday_games = {}
    
    for market_type, markets in all_markets.items():
        print(f"\n📊 {market_type.upper()} MARKETS:")
        
        for market in markets[:10]:  # Show first 10 of each type
            title = market.title
            ticker = market.ticker
            yes_bid = getattr(market, 'yes_bid', 0)
            yes_ask = getattr(market, 'yes_ask', 0)
            volume = getattr(market, 'volume_24h', 0)
            
            # Extract line value for spreads/totals
            line_value = None
            if market_type in ['spread', 'total']:
                import re
                line_match = re.search(r'(\d+\.?\d*)\s*points?', title)
                if line_match:
                    line_value = float(line_match.group(1))
            
            # Try to identify Thursday games
            is_thursday = 'THU' in ticker or '26SEP' in ticker or '25SEP26' in ticker
            
            print(f"  {'🔥' if is_thursday else '  '} {title}")
            print(f"     Ticker: {ticker}")
            print(f"     Price: {yes_bid}¢/{yes_ask}¢ | Vol: ${volume:,}")
            if line_value:
                print(f"     Line: {line_value}")
            print()
            
            if is_thursday:
                game_key = ticker.split('-')[1] if '-' in ticker else ticker
                if game_key not in thursday_games:
                    thursday_games[game_key] = {}
                if market_type not in thursday_games[game_key]:
                    thursday_games[game_key][market_type] = []
                
                thursday_games[game_key][market_type].append({
                    'title': title,
                    'ticker': ticker,
                    'line_value': line_value,
                    'yes_bid': yes_bid,
                    'yes_ask': yes_ask,
                    'volume': volume
                })
    
    # Summary of Thursday games
    if thursday_games:
        print(f"\n🔥 THURSDAY GAMES SUMMARY:")
        print("=" * 30)
        for game_key, markets in thursday_games.items():
            print(f"\n📅 Game: {game_key}")
            for market_type, lines in markets.items():
                print(f"  {market_type.upper()}: {len(lines)} lines available")
                if market_type in ['spread', 'total']:
                    line_values = [l['line_value'] for l in lines if l['line_value']]
                    if line_values:
                        print(f"    Lines: {sorted(set(line_values))}")
    else:
        print("❌ No Thursday games identified")
    
    return thursday_games


def collect_all_kalshi_markets_to_excel():
    """Collect all Kalshi markets and save to Excel for data processor"""
    print("🎯 COLLECTING ALL KALSHI MARKETS TO EXCEL")
    print("=" * 50)
    
    all_markets = get_nfl_all_markets()
    
    if not all_markets:
        print("❌ No Kalshi markets found")
        return False
    
    all_rows = []
    collection_time = datetime.now().isoformat()
    
    for market_type, markets in all_markets.items():
        print(f"\n📊 Processing {len(markets)} {market_type.upper()} markets...")
        
        for market in markets:
            # Extract game info from ticker
            ticker_parts = market.ticker.split('-')
            if len(ticker_parts) >= 2:
                game_part = ticker_parts[1]
                
                # Extract teams from game_part (e.g., "25SEP28GBDAL" -> GB, DAL)
                # Pattern: [date]AWAYTEAMHOMETEAM where teams are 2-3 chars each
                if len(game_part) >= 9:  # Minimum: 7 date + 2 chars per team
                    # Find where teams start (after date pattern like "25SEP28")
                    import re
                    date_match = re.match(r'\d{2}[A-Z]{3}\d{2}', game_part)
                    if date_match:
                        date_end = date_match.end()
                        teams_part = game_part[date_end:]  # e.g., "GBDAL", "CINDEN"
                        
                        # Split teams - check against known 3-letter teams
                        if len(teams_part) == 5:  # Like "BALKC" or "GBDAL" or "LARXX"
                            # 3-letter team abbreviations in Kalshi (including LAR for Rams)
                            three_letter_teams = {'BAL', 'CAR', 'CIN', 'CLE', 'DEN', 'DET', 'HOU', 'IND', 'JAC', 'MIA', 'MIN', 'NYG', 'NYJ', 'PHI', 'PIT', 'SEA', 'TEN', 'WAS', 'ARI', 'ATL', 'BUF', 'CHI', 'DAL', 'LAC', 'LAR'}
                            
                            if teams_part[:3] in three_letter_teams:
                                away_team = teams_part[:3]   # "BAL" or "LAR"
                                home_team = teams_part[3:]   # "KC" or "XX"
                            else:
                                away_team = teams_part[:2]   # "GB" 
                                home_team = teams_part[2:]   # "DAL"
                        elif len(teams_part) == 6:  # Like "CINDEN" 
                            away_team = teams_part[:3]   # "CIN"
                            home_team = teams_part[3:]   # "DEN"
                        elif len(teams_part) == 4:  # Like "NYJMIA" -> NYJ, MIA
                            away_team = teams_part[:2]   # "NY" (incomplete)
                            home_team = teams_part[2:]   # "J" (incomplete)
                            # This case needs special handling
                            away_team, home_team = "UNK", "UNK"
                        else:
                            away_team, home_team = "UNK", "UNK"
                    else:
                        away_team, home_team = "UNK", "UNK"
                else:
                    away_team, home_team = "UNK", "UNK"
            else:
                game_part = "UNK"
                away_team, home_team = "UNK", "UNK"
            
            # Extract line value and team for spreads
            line_value = None
            team = None
            
            if market_type == 'spread' and market.title:
                import re
                # Extract team and line from title like "Denver wins by over 7.5 points?"
                team_match = re.search(r'(\w+(?:\s+\w+)*)\s+wins by over', market.title)
                line_match = re.search(r'(\d+\.?\d*)\s*points', market.title)
                
                if team_match:
                    team = team_match.group(1)
                if line_match:
                    line_value = float(line_match.group(1))
            
            elif market_type == 'total':
                # For totals, extract from ticker ending
                if 'TOTAL-' in market.ticker:
                    try:
                        line_value = float(market.ticker.split('TOTAL-')[-1])
                    except:
                        line_value = None
                team = 'total'
            
            elif market_type == 'moneyline':
                # Extract team from ticker (last part)
                if len(ticker_parts) >= 3:
                    team = ticker_parts[2]
                else:
                    team = "UNK"
            
            # Convert team abbreviations to full names for matching
            away_team_full = _convert_team_abbrev_to_full(away_team)
            home_team_full = _convert_team_abbrev_to_full(home_team)
            
            # Calculate probability from yes price
            yes_price = getattr(market, 'yes_bid', 50)
            if yes_price == 0:
                yes_price = 50  # Default if no bid
            kalshi_probability = yes_price / 100.0
            
            # Add the "Yes" side entry
            all_rows.append({
                'collection_time': collection_time,
                'series_ticker': ticker_parts[0] if ticker_parts else '',
                'ticker': market.ticker,
                'title': market.title,
                'bet_type': market_type,
                'game_id': game_part,
                'away_team': away_team_full,
                'home_team': home_team_full,
                'team': team,
                'side': 'Yes' if market_type in ['spread', 'total'] else 'ML',
                'line_value': line_value,
                'kalshi_probability': kalshi_probability,
                'yes_bid': getattr(market, 'yes_bid', 0),
                'yes_ask': getattr(market, 'yes_ask', 0),
                'volume_24h': getattr(market, 'volume_24h', 0),
                'open_interest': getattr(market, 'open_interest', 0),
                'sport': 'nfl',
                'source': 'kalshi'
            })
            
            # For spreads and totals, add the "No" side (moneylines already have both teams)
            if market_type in ['spread', 'total']:
                # Calculate No side prices
                yes_bid = getattr(market, 'yes_bid', 50)
                yes_ask = getattr(market, 'yes_ask', 50)
                no_bid = 100 - yes_ask
                no_ask = 100 - yes_bid
                no_probability = 1.0 - kalshi_probability
                
                # Determine opposing team/side
                if market_type == 'spread':
                    # If Denver wins by over X, then Cincinnati wins by under X
                    opposing_team = home_team_full if team == away_team_full else away_team_full
                    no_title = market.title.replace(team, opposing_team).replace('over', 'under')
                else:  # total
                    opposing_team = 'total'
                    no_title = market.title.replace('over', 'under')
                
                all_rows.append({
                    'collection_time': collection_time,
                    'series_ticker': ticker_parts[0] if ticker_parts else '',
                    'ticker': market.ticker + '-NO',
                    'title': no_title,
                    'bet_type': market_type,
                    'game_id': game_part,
                    'away_team': away_team_full,
                    'home_team': home_team_full,
                    'team': opposing_team,
                    'side': 'No',
                    'line_value': line_value,
                    'kalshi_probability': no_probability,
                    'yes_bid': no_bid,
                    'yes_ask': no_ask,
                    'volume_24h': getattr(market, 'volume_24h', 0),
                    'open_interest': getattr(market, 'open_interest', 0),
                    'sport': 'nfl',
                    'source': 'kalshi'
                })
    
    if all_rows:
        import pandas as pd
        df = pd.DataFrame(all_rows)
        df.to_excel('kalshi_all_markets.xlsx', index=False)
        
        print(f"\n✅ Saved {len(all_rows)} Kalshi entries to kalshi_all_markets.xlsx")
        print(f"📊 Breakdown:")
        for bet_type in df['bet_type'].unique():
            count = len(df[df['bet_type'] == bet_type])
            print(f"   {bet_type.upper()}: {count} entries")
        
        return True
    else:
        print("❌ No data to save")
        return False


if __name__ == "__main__":
    # Collect all Kalshi markets and save to Excel
    collect_all_kalshi_markets_to_excel()
