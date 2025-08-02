"""
Market data fetching module for the crypto trading bot.
Handles API calls to fetch real-time market data from Binance.

Citations:
- Binance API documentation: https://binance-docs.github.io/apidocs/spot/en/
- Python requests library: https://docs.python-requests.org/en/latest/
- REST API best practices: https://restfulapi.net/rest-api-design-tutorial-with-example/
- Error handling patterns: https://realpython.com/python-exceptions/
"""

import requests
from datetime import datetime
from config import BINANCE_BASE_URL, SYMBOL

def fetch_binance_data():
    """
    Fetches current market data from Binance API using two separate endpoints.
    Combines price and volume data to create a complete market snapshot.
    """
    try:    
        # fetch current price using ticker endpoint - most reliable for real-time pricing
        ticker_url = f"{BINANCE_BASE_URL}/ticker/price"
        params = {"symbol": SYMBOL}  # specify trading pair (e.g., BTCUSDT)
        
        response = requests.get(ticker_url, params=params, timeout=10)  # 10 second timeout prevents hanging
        response.raise_for_status()  # raises exception for HTTP error codes
        
        data = response.json()
        current_price = float(data['price'])  # convert string price to float
        
        # fetch volume from 24hr ticker stats - provides trading activity context
        stats_url = f"{BINANCE_BASE_URL}/ticker/24hr"
        stats_response = requests.get(stats_url, params=params, timeout=10)
        stats_response.raise_for_status()
        stats_data = stats_response.json()
        volume = float(stats_data['volume'])  # 24-hour trading volume
        
        # return structured data with ISO timestamp for consistency
        return {
            'datetime': datetime.now().isoformat(),  # standardized timestamp format
            'price': current_price,
            'volume': volume
        }
        
    except requests.exceptions.RequestException as e:
        # handle network-related errors (connection issues, timeouts, HTTP errors)
        print(f"Error fetching Binance data: {e}")
        return None
    except Exception as e:
        # catch any other unexpected errors (JSON parsing, type conversion, etc.)
        print(f"Unexpected error in fetch_binance_data: {e}")
        return None