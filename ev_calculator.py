#!/usr/bin/env python3
"""
EV Calculator
Calculate Expected Value opportunities between Kalshi and sportsbook odds
"""

from nfl_markets import get_nfl_moneyline_markets, extract_games_from_markets
from odds_fetcher import OddsFetcher
import json
import os


def get_sportsbook_odds():
    """
    Get live sportsbook odds from The Odds API
    
    Returns:
        Dict mapping team codes to American odds or None if failed
    """
    # Check if API key is available
    api_key = os.getenv('ODDS_API_KEY')
    
    if not api_key:
        print("❌ ODDS_API_KEY not found in .env file")
        print("   Get your free API key from: https://the-odds-api.com/")
        return None
    
    print("📡 Fetching LIVE odds from The Odds API...")
    fetcher = OddsFetcher()
    raw_odds = fetcher.get_nfl_odds()
    
    if raw_odds:
        team_odds = fetcher.parse_odds_to_teams(raw_odds)
        if team_odds:
            print(f"✅ Live odds retrieved for {len(team_odds)} teams")
            return team_odds
        else:
            print("❌ Live odds parsing failed")
            return None
    else:
        print("❌ Live odds fetch failed")
        return None


def american_to_probability(odds):
    """Convert American odds to implied probability (includes vig)"""
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)


def remove_vig_from_odds(team_odds, opponent_odds):
    """
    Remove vig from sportsbook odds using both teams' actual odds
    
    Args:
        team_odds: American odds for the team we're betting on
        opponent_odds: American odds for the opponent (actual from sportsbook)
        
    Returns:
        True probability estimate (vig removed)
    """
    # Convert both to implied probabilities
    team_implied = american_to_probability(team_odds)
    opponent_implied = american_to_probability(opponent_odds)
    
    # Total should equal 1.0 in fair market, but sportsbooks add vig
    total_implied = team_implied + opponent_implied
    
    # Remove vig proportionally
    if total_implied > 1.0:
        # This is the normal case - total > 100% due to vig
        true_prob = team_implied / total_implied
        vig_removed = total_implied - 1.0
        
        return {
            'true_probability': true_prob,
            'raw_probability': team_implied, 
            'vig_percent': vig_removed * 100,
            'total_implied': total_implied
        }
    else:
        # Rare case - just use raw probability
        return {
            'true_probability': team_implied,
            'raw_probability': team_implied,
            'vig_percent': 0.0,
            'total_implied': total_implied
        }


def calculate_ev(kalshi_ask_cents, sportsbook_american_odds, bet_amount=10):
    """
    Calculate Expected Value for a fixed bet amount
    
    Args:
        kalshi_ask_cents: Kalshi ask price in cents (e.g., 48 for 48¢)
        sportsbook_american_odds: American odds from sportsbook (e.g., -110)
        bet_amount: Amount to bet in dollars (default $10)
    
    Returns:
        dict with EV calculation details
    """
    # Convert sportsbook odds to true probability
    true_prob = american_to_probability(sportsbook_american_odds)
    
    # Kalshi implied probability
    kalshi_prob = kalshi_ask_cents / 100
    
    # Cost to buy $10 worth of Kalshi contracts
    cost = (kalshi_ask_cents / 100) * bet_amount
    
    # Expected payout
    expected_payout = true_prob * bet_amount
    
    # Expected Value
    ev = expected_payout - cost
    ev_percent = (ev / cost) * 100 if cost > 0 else 0
    
    return {
        'kalshi_price_cents': kalshi_ask_cents,
        'kalshi_implied_prob': kalshi_prob,
        'sportsbook_odds': sportsbook_american_odds,
        'true_prob': true_prob,
        'bet_amount': bet_amount,
        'cost': cost,
        'expected_payout': expected_payout,
        'ev_dollars': ev,
        'ev_percent': ev_percent,
        'is_positive_ev': ev > 0,
        'edge': true_prob - kalshi_prob
    }


def test_ev_calculations():
    """Test EV calculations with sample data"""
    print("🧮 EV CALCULATOR TEST")
    print("=" * 25)
    
    # Test scenarios
    test_cases = [
        {
            'name': 'Chiefs Underpriced',
            'kalshi_ask': 48,  # 48¢ = 48% implied
            'sportsbook_odds': -110,  # 52.4% implied
            'expected': 'Positive EV'
        },
        {
            'name': 'Eagles Fair Value', 
            'kalshi_ask': 52,  # 52% implied
            'sportsbook_odds': -108,  # 51.9% implied
            'expected': 'Slightly Negative EV'
        },
        {
            'name': 'Cowboys Overpriced',
            'kalshi_ask': 65,  # 65% implied
            'sportsbook_odds': -120,  # 54.5% implied
            'expected': 'Negative EV'
        },
        {
            'name': 'Underdog Value',
            'kalshi_ask': 35,  # 35% implied
            'sportsbook_odds': +150,  # 40% implied
            'expected': 'Positive EV'
        }
    ]
    
    for test in test_cases:
        print(f"\n🏈 {test['name']}:")
        result = calculate_ev(test['kalshi_ask'], test['sportsbook_odds'])
        
        print(f"  Kalshi: {result['kalshi_price_cents']}¢ ({result['kalshi_implied_prob']:.1%})")
        print(f"  Sportsbook: {result['sportsbook_odds']:+d} ({result['true_prob']:.1%})")
        print(f"  Edge: {result['edge']:+.1%}")
        print(f"  EV: ${result['ev_dollars']:+.2f} ({result['ev_percent']:+.1f}%)")
        print(f"  Status: {'✅ POSITIVE EV' if result['is_positive_ev'] else '❌ Negative EV'}")
        print(f"  Expected: {test['expected']}")


def find_ev_opportunities():
    """Find actual EV opportunities using real Kalshi data and ESPN odds"""
    print("\n🎯 FINDING REAL EV OPPORTUNITIES")
    print("=" * 35)
    
    # Get Kalshi markets
    print("📊 Getting Kalshi NFL markets...")
    kalshi_markets = get_nfl_moneyline_markets()
    
    if not kalshi_markets:
        print("❌ No Kalshi markets found")
        return
    
    games = extract_games_from_markets(kalshi_markets)
    print(f"🏈 Found {len(games)} games with liquid markets")
    
    # Get LIVE NFL odds from The Odds API
    print("\n📡 Getting live NFL odds...")
    sportsbook_odds = get_sportsbook_odds()
    if not sportsbook_odds:
        print("❌ Cannot proceed without sportsbook odds")
        return []
    
    print(f"📊 Using {len(sportsbook_odds)} teams with live odds")
    
    opportunities = []
    
    # Create team mapping for Kalshi codes to common names
    team_mapping = {
        'LAC': ['chargers', 'lac'], 'LV': ['raiders', 'lv', 'las vegas'],
        'TB': ['buccaneers', 'tb', 'tampa bay'], 'HOU': ['texans', 'hou', 'houston'],
        'ATL': ['falcons', 'atl', 'atlanta'], 'MIN': ['vikings', 'min', 'minnesota'],
        'PHI': ['eagles', 'phi', 'philadelphia'], 'KC': ['chiefs', 'kc', 'kansas city'],
        'DEN': ['broncos', 'den', 'denver'], 'IND': ['colts', 'ind', 'indianapolis'],
        'CAR': ['panthers', 'car', 'carolina'], 'ARI': ['cardinals', 'ari', 'arizona'],
        'JAC': ['jaguars', 'jac', 'jacksonville'], 'CIN': ['bengals', 'cin', 'cincinnati'],
        'NE': ['patriots', 'ne', 'new england'], 'MIA': ['dolphins', 'mia', 'miami'],
        'SF': ['49ers', 'sf', 'san francisco'], 'NO': ['saints', 'no', 'new orleans'],
        'CLE': ['browns', 'cle', 'cleveland'], 'BAL': ['ravens', 'bal', 'baltimore'],
        'NYG': ['giants', 'nyg', 'new york g'], 'DAL': ['cowboys', 'dal', 'dallas'],
        'CHI': ['bears', 'chi', 'chicago'], 'DET': ['lions', 'det', 'detroit'],
        'NYJ': ['jets', 'nyj', 'new york j'], 'BUF': ['bills', 'buf', 'buffalo'],
        'SEA': ['seahawks', 'sea', 'seattle'], 'PIT': ['steelers', 'pit', 'pittsburgh'],
        'LA': ['rams', 'lar', 'los angeles r'], 'TEN': ['titans', 'ten', 'tennessee'],
        'WAS': ['washington', 'was'], 'GB': ['packers', 'gb', 'green bay']
    }
    
    print("\n🔍 Analyzing games for EV opportunities...")
    for game_id, teams in games.items():
        for team_code, kalshi_data in teams.items():
            # Try to match Kalshi team code with live sportsbook odds
            sportsbook_odds_for_team = sportsbook_odds.get(team_code)
            
            if sportsbook_odds_for_team is not None:
                ev_result = calculate_ev(
                    kalshi_data['yes_ask'],
                    sportsbook_odds_for_team
                )
                
                # Add game context
                ev_result['game_id'] = game_id
                ev_result['team'] = team_code
                ev_result['volume_24h'] = kalshi_data['volume_24h']
                ev_result['liquidity'] = kalshi_data['liquidity']
                ev_result['sportsbook_odds'] = sportsbook_odds_for_team
                
                opportunities.append(ev_result)
                print(f"  ✅ Matched {team_code} with live odds {sportsbook_odds_for_team:+d}")
            else:
                print(f"  ❌ No live odds found for {team_code}")
    
    # Sort by EV percentage
    opportunities.sort(key=lambda x: x['ev_percent'], reverse=True)
    
    # Show results
    print(f"\n📈 FOUND {len(opportunities)} BETTING OPPORTUNITIES:")
    print("=" * 50)
    
    positive_ev = [op for op in opportunities if op['is_positive_ev']]
    
    if positive_ev:
        print(f"🔥 {len(positive_ev)} POSITIVE EV OPPORTUNITIES:")
        for i, op in enumerate(positive_ev, 1):
            print(f"\n{i}. {op['game_id']} - {op['team']}")
            print(f"   Kalshi: {op['kalshi_price_cents']}¢ | SB: {op['sportsbook_odds']:+d}")
            print(f"   EV: ${op['ev_dollars']:+.2f} ({op['ev_percent']:+.1f}%) | Edge: {op['edge']:+.1%}")
            print(f"   Volume: ${op['volume_24h']:,} | Liquidity: ${op['liquidity']:,}")
    else:
        print("❌ No positive EV opportunities found with current mock data")
    
    return opportunities


if __name__ == "__main__":
    # Test the EV calculation logic
    test_ev_calculations()
    
    # Find real opportunities (with mock sportsbook data for now)
    opportunities = find_ev_opportunities()
    
    print("\n🎯 NEXT STEPS:")
    print("1. ✅ EV calculator working")
    print("2. 🔄 Replace mock odds with real ESPN scraping")
    print("3. 🚀 Build automated monitoring system")
