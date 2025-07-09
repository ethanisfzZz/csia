##################################
########## DEPENDANCIES ##########
##################################



from flask import Flask
import pandas as pd
import requests
import time
import ta
from datetime import datetime
import threading



##################################
######### INITIALIZATION #########
##################################



app = Flask(__name__)

BINANCE_BASE_URL = "https://api.binance.com/api/v3"
SYMBOL = "BTCUSDT"  #This can later be changed to any trading pair

class TradingState: #Using this class to avoid global variables
    def __init__(self):
        self.ending = False

trading_state = TradingState()



##################################
######### FETCHING DATA ##########
##################################




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
        df.to_csv("./dataframe/market_data.csv", index=False)
        print(f"Market data saved: Price={market_data['price']}, Volume={market_data['volume']}")
        
    except Exception as e:
        print(f"Error saving market data: {e}")



##################################
####### TRADING ALGORITHM ########
##################################



def calculate_technical_indicators(df):
    """Calculate MACD and RSI indicators"""
    if len(df) < 26:  # Need at least 26 periods for MACD
        return None, None, None
    
    # Convert price column to float and create Series
    prices = pd.Series(df['price'].astype(float))
    
    # Calculate RSI (14-period default)
    rsi = ta.momentum.RSIIndicator(close=prices, window=14).rsi()
    
    # Calculate MACD
    macd_indicator = ta.trend.MACD(close=prices)
    macd = macd_indicator.macd()
    signal_line = macd_indicator.macd_signal()
    
    # Get the latest values
    latest_rsi = rsi.iloc[-1] if not rsi.empty else None
    latest_macd = macd.iloc[-1] if not macd.empty else None
    latest_signal = signal_line.iloc[-1] if not signal_line.empty else None
    
    return latest_rsi, latest_macd, latest_signal

def main_loop():
    """MAIN TRADING LOOP - runs in background"""
    
    print("Starting trading loop...")
    try:
        # Fetch from Binance (ends after immediate fetch)
        market_data = fetch_binance_data()
        
        if market_data:
            # First save the basic market data
            save_market_data(market_data)
            
            # Calculate technical indicators using historical data
            try:
                df = pd.read_csv("./dataframe/market_data.csv")
                
                # Calculate MACD and RSI
                rsi, macd, signal_line = calculate_technical_indicators(df)
                
                if rsi is not None and macd is not None and signal_line is not None:
                    # Update the latest row with calculated indicators
                    df.loc[df.index[-1], 'rsi'] = rsi
                    df.loc[df.index[-1], 'macd'] = macd
                    df.loc[df.index[-1], 'signal_line'] = signal_line
                    
                    # Save updated data back to CSV
                    df.to_csv("./dataframe/market_data.csv", index=False)
                    print(f"Technical indicators calculated - RSI: {rsi:.2f}, MACD: {macd:.6f}, Signal: {signal_line:.6f}")
                else:
                    print("Not enough data to calculate technical indicators (need at least 26 data points)")
                    
            except Exception as e:
                print(f"Error calculating technical indicators: {e}")
            
            # Make decision - trading logic integrated later
            pass
        
        # Set ending to True after immediate fetch
        trading_state.ending = True
        print("Data fetched, trading loop completed")
        
    except Exception as e:
        print(f"Error in main loop: {e}")
        trading_state.ending = True

def start_background_trading():
    """Start the trading loop in a separate thread"""
    trading_thread = threading.Thread(target=main_loop, daemon=True)
    trading_thread.start()
    print("Background trading thread started")



##################################
########### ENDPOINTS ############
##################################



@app.route('/')
def hello_world():
    return 'Hello World'

@app.route('/end')
def signal_end():
    trading_state.ending = True
    return "Trading algorithm terminated"

@app.route('/status')
def get_status():
    """Get current trading status and latest market data"""
    try:
        df = pd.read_csv("./market_data.csv")
        if len(df) > 0:
            latest = df.iloc[-1]
            return {
                "status": "running" if not trading_state.ending else "stopped",
                "latest_price": latest['price'],
                "latest_datetime": latest['datetime'],
                "total_records": len(df)
            }
        else:
            return {"status": "running" if not trading_state.ending else "stopped", "message": "No data yet"}
    except FileNotFoundError:
        return {"status": "running" if not trading_state.ending else "stopped", "message": "No market data file found"}

if __name__ == '__main__':
    # Start background trading loop BEFORE starting Flask
    start_background_trading()
    
    # Start Flask API (this runs the web server)
    app.run(debug=True, use_reloader=False)  # use_reloader=False prevents double threading