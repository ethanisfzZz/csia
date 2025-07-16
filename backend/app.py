##################################
########## DEPENDANCIES ##########
##################################

from flask import Flask
import requests
import time
import ta
import pandas as pd
from datetime import datetime
import threading
import csv
import os
import sys

##################################
######### INITIALIZATION #########
##################################

app = Flask(__name__)

BINANCE_BASE_URL = "https://api.binance.com/api/v3"
SYMBOL = "BTCUSDT"  # This can later be changed to any trading pair
LOOP_INTERVAL = 60  # seconds between data fetches
CSV_FILE_PATH = "./dataframe/market_data.csv"
THRESHOLD_CSV_PATH = "./dataframe/threshold.csv"
ORDER_CSV_PATH = "./dataframe/order.csv"
INDICATOR_WINDOW = 26  # Minimum data points needed for MACD

class TradingState:
    def __init__(self):
        self.ending = False
        self.historical_data = []  # Keep historical completed candles
        self.cache_size = 100  # Keep last 100 records in memory
        self.current_position = None  # Track current position: 'BUY' or 'SELL' or None
        self.last_trade_price = None  # Track last trade price for stop loss/take profit

trading_state = TradingState()

##################################
######### FILE I/O HELPERS #######
##################################

def ensure_csv_exists():
    """Ensure the CSV file exists with proper headers"""
    # Create dataframe directory if it doesn't exist
    dataframe_dir = os.path.dirname(CSV_FILE_PATH)
    os.makedirs(dataframe_dir, exist_ok=True)
    
    if not os.path.exists(CSV_FILE_PATH):
        print(f"Creating new market_data.csv file at {CSV_FILE_PATH}")
        with open(CSV_FILE_PATH, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['datetime', 'price', 'volume', 'rsi', 'macd', 'signal_line'])
    else:
        print(f"Using existing market_data.csv file at {CSV_FILE_PATH}")

def ensure_threshold_csv_exists():
    """Ensure the threshold CSV file exists with default values"""
    # Create dataframe directory if it doesn't exist
    dataframe_dir = os.path.dirname(THRESHOLD_CSV_PATH)
    os.makedirs(dataframe_dir, exist_ok=True)
    
    if not os.path.exists(THRESHOLD_CSV_PATH):
        print(f"Creating new threshold.csv file at {THRESHOLD_CSV_PATH}")
        with open(THRESHOLD_CSV_PATH, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['trade_size', 'stop_loss', 'stop_profit', 'rsi_buy_threshold', 
                           'rsi_sell_threshold', 'macd_buy_threshold', 'macd_sell_threshold', 
                           'position_size_usdt', 'active'])
            # Add realistic default thresholds
            writer.writerow([0.01, 0.02, 0.025, 30, 70, 0.0, 0.0, 100.0, 1])
    else:
        print(f"Using existing threshold.csv file at {THRESHOLD_CSV_PATH}")

def ensure_order_csv_exists():
    """Ensure the order CSV file exists with proper headers"""
    # Create dataframe directory if it doesn't exist
    dataframe_dir = os.path.dirname(ORDER_CSV_PATH)
    os.makedirs(dataframe_dir, exist_ok=True)
    
    if not os.path.exists(ORDER_CSV_PATH):
        print(f"Creating new order.csv file at {ORDER_CSV_PATH}")
        with open(ORDER_CSV_PATH, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['datetime', 'side', 'price', 'quantity', 'trade_size'])
    else:
        print(f"Using existing order.csv file at {ORDER_CSV_PATH}")

def load_trading_thresholds():
    """Load trading thresholds from CSV file"""
    ensure_threshold_csv_exists()
    
    try:
        with open(THRESHOLD_CSV_PATH, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            thresholds = list(reader)
            
            if thresholds and len(thresholds) > 0:
                # Get the first (and typically only) threshold configuration
                threshold = thresholds[0]
                return {
                    'trade_size': float(threshold['trade_size']),
                    'stop_loss': float(threshold['stop_loss']),
                    'stop_profit': float(threshold['stop_profit']),
                    'rsi_buy_threshold': float(threshold['rsi_buy_threshold']),
                    'rsi_sell_threshold': float(threshold['rsi_sell_threshold']),
                    'macd_buy_threshold': float(threshold['macd_buy_threshold']),
                    'macd_sell_threshold': float(threshold['macd_sell_threshold']),
                    'position_size_usdt': float(threshold['position_size_usdt']),
                    'active': bool(int(float(threshold['active'])))
                }
            else:
                print("No thresholds found in CSV, using defaults")
                return get_default_thresholds()
                
    except Exception as e:
        print(f"Error loading thresholds: {e}")
        return get_default_thresholds()

def get_default_thresholds():
    """Return default trading thresholds"""
    return {
        'trade_size': 0.01,
        'stop_loss': 0.02,
        'stop_profit': 0.025,
        'rsi_buy_threshold': 30,
        'rsi_sell_threshold': 70,
        'macd_buy_threshold': 0.0,
        'macd_sell_threshold': 0.0,
        'position_size_usdt': 100.0,
        'active': True
    }

def append_order_to_csv(order_data):
    """Append a trade order to the order CSV file"""
    ensure_order_csv_exists()
    
    try:
        with open(ORDER_CSV_PATH, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, lineterminator='\n')  # Explicitly set line terminator
            writer.writerow([
                order_data['datetime'],
                order_data['side'],
                order_data['price'],
                order_data['quantity'],
                order_data['trade_size']
            ])
            file.flush()  # Force write to disk immediately
        
        print(f"Order logged: {order_data['side']} {order_data['quantity']:.6f} at {order_data['price']}")
        
    except Exception as e:
        print(f"Error appending order to CSV: {e}")

def parse_csv_row(row):
    """Parse a CSV row and convert numeric fields"""
    try:
        return {
            'datetime': row['datetime'],
            'price': float(row['price']),
            'volume': float(row['volume']),
            'rsi': float(row['rsi']) if row['rsi'] and row['rsi'] != '' else None,
            'macd': float(row['macd']) if row['macd'] and row['macd'] != '' else None,
            'signal_line': float(row['signal_line']) if row['signal_line'] and row['signal_line'] != '' else None
        }
    except (ValueError, TypeError):
        return row

def append_to_csv(market_data):
    """Append a single row of market data to CSV file"""
    ensure_csv_exists()
    
    try:
        # Use 'a' mode to append, ensuring we write to a new line
        with open(CSV_FILE_PATH, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, lineterminator='\n')  # Explicitly set line terminator
            writer.writerow([
                market_data['datetime'],
                market_data['price'],
                market_data['volume'],
                market_data['rsi'] if market_data['rsi'] is not None else '',
                market_data['macd'] if market_data['macd'] is not None else '',
                market_data['signal_line'] if market_data['signal_line'] is not None else ''
            ])
            file.flush()  # Force write to disk immediately
        
        # Update historical data cache
        update_historical_cache(market_data)
        
    except Exception as e:
        print(f"Error appending to CSV: {e}")
        raise

def update_historical_cache(market_data):
    """Update the historical data cache with new completed candle"""
    parsed_data = parse_csv_row(market_data)
    trading_state.historical_data.append(parsed_data)
    
    # Keep only the last cache_size records
    if len(trading_state.historical_data) > trading_state.cache_size:
        trading_state.historical_data = trading_state.historical_data[-trading_state.cache_size:]

def load_historical_data():
    """Load historical data from CSV file into cache on startup"""
    ensure_csv_exists()
    
    try:
        with open(CSV_FILE_PATH, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            data = [parse_csv_row(row) for row in reader]
            
            # Keep only the last cache_size records
            trading_state.historical_data = data[-trading_state.cache_size:] if len(data) > trading_state.cache_size else data
            print(f"Loaded {len(trading_state.historical_data)} historical records into cache")
            
    except Exception as e:
        print(f"Error loading historical data: {e}")
        trading_state.historical_data = []

def get_historical_data():
    """Get historical completed candles for indicator calculation"""
    return trading_state.historical_data

def get_row_count():
    """Get the number of data rows efficiently"""
    if trading_state.historical_data:
        ensure_csv_exists()
        try:
            with open(CSV_FILE_PATH, 'r', newline='', encoding='utf-8') as file:
                return sum(1 for _ in file) - 1  # Subtract 1 for header
        except Exception:
            return len(trading_state.historical_data)
    return 0

##################################
######### FETCHING DATA ##########
##################################

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

##################################
####### TRADING ALGORITHM ########
##################################

def calculate_technical_indicators():
    """
    Calculate MACD and RSI indicators using COMPLETED historical candles only.
    This mimics real exchange behavior where indicators are calculated on closed candles.
    """
    historical_data = get_historical_data()
    
    if len(historical_data) < INDICATOR_WINDOW:
        return None, None, None
    
    try:
        # Extract prices from COMPLETED candles only
        prices = [candle['price'] for candle in historical_data]
        prices_series = pd.Series(prices)
        
        # Calculate RSI (14-period default)
        rsi_indicator = ta.momentum.RSIIndicator(close=prices_series, window=14)
        rsi_values = rsi_indicator.rsi()
        
        # Calculate MACD
        macd_indicator = ta.trend.MACD(close=prices_series)
        macd_values = macd_indicator.macd()
        signal_values = macd_indicator.macd_signal()
        
        # Get the latest COMPLETED values (not including current incomplete candle)
        latest_rsi = rsi_values.iloc[-1] if not rsi_values.empty else None
        latest_macd = macd_values.iloc[-1] if not macd_values.empty else None
        latest_signal = signal_values.iloc[-1] if not signal_values.empty else None
        
        if all(val is not None for val in [latest_rsi, latest_macd, latest_signal]):
            print(f"Technical indicators (from completed candles) - RSI: {latest_rsi:.2f}, MACD: {latest_macd:.6f}, Signal: {latest_signal:.6f}")
            return latest_rsi, latest_macd, latest_signal
        
        return None, None, None
        
    except Exception as e:
        print(f"Error calculating technical indicators: {e}")
        return None, None, None

def create_market_data_with_indicators(raw_data):
    """
    Create complete market data entry with pre-calculated indicators.
    This simulates real trading where indicators are calculated BEFORE 
    the current candle, not after.
    """
    if raw_data is None:
        return None
    
    # Calculate indicators using PREVIOUS completed candles
    rsi, macd, signal_line = calculate_technical_indicators()
    
    # Create complete market data entry
    market_data = {
        'datetime': raw_data['datetime'],
        'price': raw_data['price'],
        'volume': raw_data['volume'],
        'rsi': rsi,  # Based on previous completed candles
        'macd': macd,  # Based on previous completed candles  
        'signal_line': signal_line  # Based on previous completed candles
    }
    
    return market_data

def save_market_data(market_data):
    """Save complete market data (including pre-calculated indicators) to CSV"""
    if market_data is None:
        return False
    
    try:
        append_to_csv(market_data)
        indicators_info = ""
        if market_data['rsi'] is not None:
            indicators_info = f" | RSI: {market_data['rsi']:.2f}, MACD: {market_data['macd']:.6f}, Signal: {market_data['signal_line']:.6f}"
        
        print(f"Market data saved: Price={market_data['price']}, Volume={market_data['volume']}{indicators_info}")
        return True
        
    except Exception as e:
        print(f"Error saving market data: {e}")
        return False

def check_trading_signals_with_thresholds(market_data, thresholds):
    """
    Check for trading signals based on thresholds from CSV.
    Includes stop loss and take profit logic.
    """
    if market_data is None or market_data['rsi'] is None or not thresholds['active']:
        return "NO_SIGNAL", False
    
    rsi = market_data['rsi']
    macd = market_data['macd']
    signal_line = market_data['signal_line']
    current_price = market_data['price']
    
    # Check stop loss and take profit if we have a position
    if trading_state.current_position and trading_state.last_trade_price:
        if trading_state.current_position == 'BUY':
            # Check stop loss (price fell too much)
            if current_price <= trading_state.last_trade_price * (1 - thresholds['stop_loss']):
                return "SELL_STOP_LOSS", True
            # Check take profit (price rose enough)
            if current_price >= trading_state.last_trade_price * (1 + thresholds['stop_profit']):
                return "SELL_TAKE_PROFIT", True
        
        elif trading_state.current_position == 'SELL':
            # Check stop loss (price rose too much)
            if current_price >= trading_state.last_trade_price * (1 + thresholds['stop_loss']):
                return "BUY_STOP_LOSS", True
            # Check take profit (price fell enough)
            if current_price <= trading_state.last_trade_price * (1 - thresholds['stop_profit']):
                return "BUY_TAKE_PROFIT", True
    
    # Check for new position signals only if we don't have a position
    if trading_state.current_position is None:
        # Buy signal: RSI oversold AND MACD above signal line
        if (rsi <= thresholds['rsi_buy_threshold'] and 
            macd > signal_line and 
            macd > thresholds['macd_buy_threshold']):
            return "BUY_SIGNAL", True
        
        # Sell signal: RSI overbought AND MACD below signal line
        if (rsi >= thresholds['rsi_sell_threshold'] and 
            macd < signal_line and 
            macd < thresholds['macd_sell_threshold']):
            return "SELL_SIGNAL", True
    
    return "HOLD", False

def execute_trade(signal, market_data, thresholds):
    """
    Execute a trade based on the signal and log it to order.csv
    """
    if not signal.endswith('_SIGNAL') and not signal.endswith('_LOSS') and not signal.endswith('_PROFIT'):
        return
    
    current_price = market_data['price']
    trade_size = thresholds['trade_size']  # This is the fraction/percentage of position
    
    # Determine side based on signal
    if signal.startswith('BUY'):
        side = 'BUY'
    else:
        side = 'SELL'
    
    quantity = trade_size
    
    # Create order data matching your CSV structure
    order_data = {
        'datetime': market_data['datetime'],
        'side': side,
        'price': current_price,
        'quantity': quantity,
        'trade_size': trade_size
    }
    
    # Log the trade
    append_order_to_csv(order_data)
    
    # Update trading state for stop loss/take profit tracking
    if signal == 'BUY_SIGNAL':
        trading_state.current_position = 'BUY'
        trading_state.last_trade_price = current_price
    elif signal == 'SELL_SIGNAL':
        trading_state.current_position = 'SELL'
        trading_state.last_trade_price = current_price
    elif signal in ['SELL_STOP_LOSS', 'SELL_TAKE_PROFIT', 'BUY_STOP_LOSS', 'BUY_TAKE_PROFIT']:
        # Closing position
        trading_state.current_position = None
        trading_state.last_trade_price = None
    
    print(f"🚨 TRADE EXECUTED: {signal} - {side} {quantity} at {current_price}")

def main_loop():
    """
    MAIN TRADING LOOP with threshold-based trading execution
    """
    print("Starting Crypto Trading Bot with Threshold-Based Trading...")
    print("Indicators calculated using completed historical candles only")
    print("Running on Windows environment")
    
    while not trading_state.ending:
        try:
            # Load current thresholds (allows dynamic updates)
            thresholds = load_trading_thresholds()
            
            # Step 1: Fetch current raw market data
            raw_data = fetch_binance_data()
            
            if raw_data:
                # Step 2: Create complete market data with pre-calculated indicators
                market_data = create_market_data_with_indicators(raw_data)
                
                # Step 3: Save to CSV (no retroactive updates)
                if save_market_data(market_data):
                    
                    # Step 4: Check for trading signals using thresholds
                    signal, should_execute = check_trading_signals_with_thresholds(market_data, thresholds)
                    
                    # Step 5: Execute trade if signal is strong enough
                    if should_execute:
                        execute_trade(signal, market_data, thresholds)
                    elif signal != "NO_SIGNAL" and signal != "HOLD":
                        print(f"Signal detected but not executed: {signal}")
                    
                    # Status information
                    if market_data['rsi'] is None:
                        print(f"Collecting data... ({len(trading_state.historical_data)}/{INDICATOR_WINDOW} candles needed for indicators)")
                    else:
                        position_info = f"Position: {trading_state.current_position or 'None'}"
                        if trading_state.last_trade_price:
                            position_info += f" @ {trading_state.last_trade_price:.2f}"
                        print(f"Status: {position_info} | Signal: {signal}")
                    
                else:
                    print("Failed to save market data")
            else:
                print("Failed to fetch market data, retrying next cycle")
            
            # Wait before next iteration (simulating candle completion)
            time.sleep(LOOP_INTERVAL)
            
        except Exception as e:
            print(f"Error in main loop: {e}")
            print("Continuing to next iteration...")
            time.sleep(5)
    
    print("Trading loop ended")

def start_background_trading():
    """Start the trading loop in a separate thread"""
    # Load historical data on startup
    load_historical_data()
    
    # Ensure all CSV files exist
    ensure_threshold_csv_exists()
    ensure_order_csv_exists()
    
    trading_thread = threading.Thread(target=main_loop, daemon=True)
    trading_thread.start()
    print("Background trading thread started with threshold-based execution")

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
        historical_data = get_historical_data()
        thresholds = load_trading_thresholds()
        
        if historical_data:
            latest = historical_data[-1]
            return {
                "status": "running" if not trading_state.ending else "stopped",
                "latest_price": latest['price'],
                "latest_datetime": latest['datetime'],
                "latest_rsi": latest['rsi'],
                "latest_macd": latest['macd'],
                "latest_signal_line": latest['signal_line'],
                "total_records": get_row_count(),
                "indicators_available": latest['rsi'] is not None,
                "current_position": trading_state.current_position,
                "last_trade_price": trading_state.last_trade_price,
                "thresholds": thresholds
            }
        else:
            return {
                "status": "running" if not trading_state.ending else "stopped", 
                "message": "No data yet",
                "thresholds": thresholds
            }
    except Exception as e:
        return {
            "status": "running" if not trading_state.ending else "stopped", 
            "message": f"Error reading data: {str(e)}"
        }

@app.route('/signals')
def get_recent_signals():
    """Get recent trading signals"""
    try:
        historical_data = get_historical_data()
        thresholds = load_trading_thresholds()
        recent_signals = []
        
        for data in historical_data[-10:]:  # Last 10 records
            if data['rsi'] is not None:
                signal, should_execute = check_trading_signals_with_thresholds(data, thresholds)
                recent_signals.append({
                    "datetime": data['datetime'],
                    "price": data['price'],
                    "signal": signal,
                    "should_execute": should_execute,
                    "rsi": data['rsi'],
                    "macd": data['macd']
                })
        
        return {"recent_signals": recent_signals}
    except Exception as e:
        return {"error": f"Error getting signals: {str(e)}"}

@app.route('/trades')
def get_recent_trades():
    """Get recent trades from order.csv"""
    try:
        if not os.path.exists(ORDER_CSV_PATH):
            return {"trades": []}
        
        trades = []
        with open(ORDER_CSV_PATH, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            trades = list(reader)
        
        return {"trades": trades[-20:]}  # Last 20 trades
    except Exception as e:
        return {"error": f"Error reading trades: {str(e)}"}

if __name__ == '__main__':
    print("Starting Windows-Compatible Crypto Trading Bot...")
    print("Press Ctrl+C to stop the application")
    
    # Start background trading loop BEFORE starting Flask
    start_background_trading()
    
    # Start Flask API (this runs the web server)
    app.run(debug=True, use_reloader=False)  # use_reloader=False prevents double threading