"""
Market data fetching module for the crypto trading bot.
Handles API calls to fetch real-time market data from Binance.
"""

import requests
from datetime import datetime
from config import BINANCE_BASE_URL, SYMBOL

def fetch_binance_data():
    """Fetches current market data from Binance API"""
    try:    
        # Fetch Current Price
        ticker_url = f"{BINANCE_BASE_URL}/ticker/price"
        params = {"symbol": SYMBOL}
        
        response = requests.get(ticker_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        current_price = float(data['price'])
        
        # Fetch Volume (From 24hr Ticker Stats)
        stats_url = f"{BINANCE_BASE_URL}/ticker/24hr"
        stats_response = requests.get(stats_url, params=params, timeout=10)
        stats_response.raise_for_status()
        stats_data = stats_response.json()
        volume = float(stats_data['volume'])
        
        return {
            'datetime': datetime.now().isoformat(),
            'price': current_price,
            'volume': volume
        }
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Binance data: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error in fetch_binance_data: {e}")
        return None