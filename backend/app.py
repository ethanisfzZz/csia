##### DEPENANCIES #####


from flask import Flask
import pandas as pd
import requests
import time
from datetime import datetime
import threading


##### INITIALIZATION #####


app = Flask(__name__)
ending = False

BINANCE_BASE_URL = "https://api.binance.com/api/v3"
SYMBOL = "BTCUSDT"  # can be changed to any trading pair 


##### FETCHING DATA #####


def fetch_binance_data(): # Fetches Data From Binance API 
    try:    
        # Fetch Current Price
        ticker_url = f"{BINANCE_BASE_URL}/ticker/price"
        params = {"symbol": SYMBOL}
        
        response = requests.get(ticker_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        current_price = float(data['price'])
        
        # Fetch Volume (From 24hr Ticker Stats)
        stats_url = f"{BINANCE_BASE_URL}/ticker/24hr"
        stats_response = requests.get(stats_url, params=params)
        stats_response.raise_for_status()
        stats_data = stats_response.json()
        volume = float(stats_data['volume'])
        
        return {
            'datetime': datetime.now().isoformat(),
            'price': current_price,
            'volume': volume,
            'rsi': None,  # calculated later
            'macd': None,  # calculated later
            'signal_line': None  # calculated later
        }
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Binance data: {e}")
        return None

def save_market_data(market_data): #Saves Live Market Data to MarketData.CSV
    if market_data is None:
        return
    
    try:
        # Try to read existing data
        try:
            df = pd.read_csv("./market_data.csv")
        except FileNotFoundError:
            # Create new DataFrame if file doesn't exist
            df = pd.DataFrame(columns=['datetime', 'price', 'volume', 'rsi', 'macd', 'signal_line'])
        
        # Add new data
        new_row = pd.DataFrame([market_data])
        df = pd.concat([df, new_row], ignore_index=True)
        
        # Save to CSV
        df.to_csv("./market_data.csv", index=False)
        print(f"Market data saved: Price={market_data['price']}, Volume={market_data['volume']}")
        
    except Exception as e:
        print(f"Error saving market data: {e}")


##### CRYPTO TRADING ALGORITHM #####


def main_loop():
    """MAIN TRADING LOOP - runs in background"""
    global ending
    
    print("Starting trading loop...")
    while not ending:
        try:
            # Fetch from Binance
            market_data = fetch_binance_data()
            
            if market_data:
                # Write to market_data.csv
                save_market_data(market_data)
                
                # Make decision - trading logic integrated later
                pass
            
            time.sleep(3600)  # Wait 1 hour
            
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(60)  # wait before retrying

def start_background_trading():
    """Start the trading loop in a separate thread"""
    trading_thread = threading.Thread(target=main_loop, daemon=True)
    trading_thread.start()
    print("Background trading thread started")


##### ENDPOINTS #####


@app.route('/')
def hello_world():
    return 'Hello World'

@app.route('/end')
def signal_end():
    global ending
    ending = True
    return "Trading algorithm terminated"

@app.route('/status')
def get_status():
    """Get current trading status and latest market data"""
    try:
        df = pd.read_csv("./market_data.csv")
        if len(df) > 0:
            latest = df.iloc[-1]
            return {
                "status": "running" if not ending else "stopped",
                "latest_price": latest['price'],
                "latest_datetime": latest['datetime'],
                "total_records": len(df)
            }
        else:
            return {"status": "running" if not ending else "stopped", "message": "No data yet"}
    except FileNotFoundError:
        return {"status": "running" if not ending else "stopped", "message": "No market data file found"}

if __name__ == '__main__':
    # Start background trading loop BEFORE starting Flask
    start_background_trading()
    
    # Start Flask API (this runs the web server)
    app.run(debug=True, use_reloader=False)  # use_reloader=False prevents double threading