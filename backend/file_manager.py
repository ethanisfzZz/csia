"""
File management module for the crypto trading bot.
Handles all CSV file operations and data persistence with parameter validation.

Citations:
- CSV file handling: https://docs.python.org/3/library/csv.html
- Pandas data manipulation: https://pandas.pydata.org/docs/
- NumPy NaN handling: https://numpy.org/doc/stable/reference/generated/numpy.isnan.html
- File system operations: https://docs.python.org/3/library/os.html
"""

import csv
import os
import pandas as pd
import numpy as np
from config import (
    CSV_FILE_PATH, THRESHOLD_CSV_PATH, ORDER_CSV_PATH, 
    DEFAULT_THRESHOLDS, trading_state, validate_all_parameters
)

def ensure_csv_exists():
    """Ensure the CSV file exists with proper headers for market data storage."""
    dataframe_dir = os.path.dirname(CSV_FILE_PATH)
    os.makedirs(dataframe_dir, exist_ok=True)  # create directory structure if needed
    
    if not os.path.exists(CSV_FILE_PATH):
        print(f"Creating new market_data.csv file at {CSV_FILE_PATH}")
        # create file with proper column headers for all data types
        with open(CSV_FILE_PATH, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['datetime', 'price', 'volume', 'rsi', 'macd', 'signal_line'])
    else:
        print(f"Using existing market_data.csv file at {CSV_FILE_PATH}")

def ensure_threshold_csv_exists():
    """Ensure the threshold CSV file exists with optimized default values for trading parameters."""
    dataframe_dir = os.path.dirname(THRESHOLD_CSV_PATH)
    os.makedirs(dataframe_dir, exist_ok=True)
    
    if not os.path.exists(THRESHOLD_CSV_PATH):
        print(f"Creating new threshold.csv file at {THRESHOLD_CSV_PATH}")
        with open(THRESHOLD_CSV_PATH, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # write comprehensive header row for all trading parameters
            writer.writerow(['trade_size', 'stop_loss', 'stop_profit', 'rsi_buy_threshold', 
                           'rsi_sell_threshold', 'macd_buy_threshold', 'macd_sell_threshold', 
                           'position_size_usdt', 'active', 'loop_interval', 'indicator_window'])
            
            # write optimized default values based on trading best practices
            writer.writerow([
                0.01,    # trade_size - 1% position sizing
                0.02,    # stop_loss - 2% maximum loss
                0.025,   # stop_profit - 2.5% target profit
                30,      # rsi_buy_threshold - classic oversold level
                70,      # rsi_sell_threshold - classic overbought level
                0.0,     # macd_buy_threshold - neutral crossover level
                0.0,     # macd_sell_threshold - neutral crossover level
                100.0,   # position_size_usdt - $100 per trade
                1,       # active = True (boolean as integer)
                60,      # loop_interval - check every minute
                26       # indicator_window - standard MACD period
            ])
        print("✅ Created threshold.csv with optimized default values:")
        print(f"   Trade Size: 0.01 | Stop Loss: 2% | Stop Profit: 2.5%")
        print(f"   RSI: 30/70 | MACD: 0.0/0.0 | Position: $100 | Window: 26")
    else:
        print(f"Using existing threshold.csv file at {THRESHOLD_CSV_PATH}")

def ensure_order_csv_exists():
    """Ensure the order CSV file exists with proper headers for trade tracking."""
    dataframe_dir = os.path.dirname(ORDER_CSV_PATH)
    os.makedirs(dataframe_dir, exist_ok=True)
    
    if not os.path.exists(ORDER_CSV_PATH):
        print(f"Creating new order.csv file at {ORDER_CSV_PATH}")
        with open(ORDER_CSV_PATH, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            # headers for comprehensive trade tracking
            writer.writerow(['datetime', 'side', 'price', 'quantity', 'trade_size'])
    else:
        print(f"Using existing order.csv file at {ORDER_CSV_PATH}")

def load_trading_thresholds():
    """
    Load trading thresholds from CSV file with validation and warnings.
    Includes comprehensive error handling and parameter validation.
    """
    ensure_threshold_csv_exists()
    
    try:
        with open(THRESHOLD_CSV_PATH, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            thresholds = list(reader)
            
            if thresholds and len(thresholds) > 0:
                threshold = thresholds[0]  # use first row of configuration
                
                # parse configuration with comprehensive error handling
                config = {}
                try:
                    config = {
                        'trade_size': float(threshold['trade_size']),
                        'stop_loss': float(threshold['stop_loss']),
                        'stop_profit': float(threshold['stop_profit']),
                        'rsi_buy_threshold': float(threshold['rsi_buy_threshold']),
                        'rsi_sell_threshold': float(threshold['rsi_sell_threshold']),
                        'macd_buy_threshold': float(threshold['macd_buy_threshold']),
                        'macd_sell_threshold': float(threshold['macd_sell_threshold']),
                        'position_size_usdt': float(threshold['position_size_usdt']),
                        'active': bool(int(float(threshold['active'])))  # convert 1/0 to boolean
                    }
                    
                    # add new parameters with defaults if they don't exist (backward compatibility)
                    config['loop_interval'] = int(float(threshold.get('loop_interval', 60)))
                    config['indicator_window'] = int(float(threshold.get('indicator_window', 26)))
                    
                except (ValueError, KeyError) as e:
                    print(f"⚠️  Error parsing threshold parameter: {e}")
                    print("Using default values for invalid parameters")
                    config = DEFAULT_THRESHOLDS.copy()
                
                # validate parameters and display warnings to help users optimize settings
                warnings = validate_all_parameters(config)
                if warnings:
                    print("\n" + "="*50)
                    print("🔍 PARAMETER VALIDATION WARNINGS:")
                    print("="*50)
                    for warning in warnings:
                        print(warning)
                    print("="*50 + "\n")
                
                return config
            else:
                print("No thresholds found in CSV, using defaults")
                return DEFAULT_THRESHOLDS
                
    except Exception as e:
        print(f"Error loading thresholds: {e}")
        return DEFAULT_THRESHOLDS

def get_current_position_from_orders():
    """
    Get current position by analyzing the order history.
    Calculates net position by counting buy vs sell orders.
    """
    try:
        if not os.path.exists(ORDER_CSV_PATH):
            return None, None
        
        with open(ORDER_CSV_PATH, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            orders = list(reader)
        
        if not orders:
            return None, None
        
        # get the most recent order for price reference
        last_order = orders[-1]
        
        # calculate net position by counting orders
        buy_count = sum(1 for order in orders if order['side'] == 'BUY')
        sell_count = sum(1 for order in orders if order['side'] == 'SELL')
        
        # determine current position based on order imbalance
        if buy_count > sell_count:
            return 'LONG', float(last_order['price'])
        elif sell_count > buy_count:
            return 'SHORT', float(last_order['price'])
        else:
            return None, None  # no net position
            
    except Exception as e:
        print(f"Error reading current position from orders: {e}")
        return None, None

def append_order_to_csv(order_data):
    """Append a trade order to the order CSV file for permanent record keeping."""
    ensure_order_csv_exists()
    
    try:
        with open(ORDER_CSV_PATH, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, lineterminator='\n')  # explicit line terminator for consistency
            writer.writerow([
                order_data['datetime'],
                order_data['side'],
                order_data['price'],
                order_data['quantity'],
                order_data['trade_size']
            ])
            file.flush()  # ensure data is written immediately
        
        print(f"Order logged: {order_data['side']} {order_data['quantity']:.6f} at {order_data['price']}")
        
    except Exception as e:
        print(f"Error appending order to CSV: {e}")

def parse_csv_row(row):
    """
    Parse a CSV row and convert numeric fields with robust error handling.
    Handles various data type issues that can occur with CSV files.
    """
    try:
        def safe_float(value):
            """safely convert string to float, handling empty/invalid values"""
            if value and value != '' and value != 'nan':
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return None
            return None
        
        return {
            'datetime': row['datetime'],
            'price': float(row['price']),  # price is always required
            'volume': float(row['volume']),  # volume is always required
            'rsi': safe_float(row['rsi']),  # indicators can be None during initial data collection
            'macd': safe_float(row['macd']),
            'signal_line': safe_float(row['signal_line'])
        }
    except (ValueError, TypeError) as e:
        print(f"Error parsing CSV row: {e}")
        return row  # return original row if parsing fails

def format_indicator_value(value):
    """Format indicator value for CSV output, handling None and NaN values properly."""
    if value is None or pd.isna(value):
        return ''  # empty string for missing values
    try:
        if np.isnan(value):  # handle numpy NaN values
            return ''
    except (TypeError, ValueError):
        pass  # value is not a numpy type
    return str(value)

def append_to_csv(market_data):
    """
    Append a single row of market data to CSV file with proper formatting.
    Updates both file storage and in-memory cache for performance.
    """
    ensure_csv_exists()
    
    try:
        with open(CSV_FILE_PATH, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, lineterminator='\n')
            writer.writerow([
                market_data['datetime'],
                market_data['price'],
                market_data['volume'],
                format_indicator_value(market_data['rsi']),  # handle None/NaN properly
                format_indicator_value(market_data['macd']),
                format_indicator_value(market_data['signal_line'])
            ])
            file.flush()  # ensure immediate write to disk
        
        # update in-memory cache for fast access
        update_historical_cache(market_data)
        
    except Exception as e:
        print(f"Error appending to CSV: {e}")
        raise

def update_historical_cache(market_data):
    """
    Update the historical data cache with new completed candle.
    Maintains fixed cache size for memory efficiency.
    """
    parsed_data = parse_csv_row(market_data)
    trading_state.historical_data.append(parsed_data)
    
    # keep only the last cache_size records to prevent memory bloat
    if len(trading_state.historical_data) > trading_state.cache_size:
        trading_state.historical_data = trading_state.historical_data[-trading_state.cache_size:]

def load_historical_data():
    """
    Load historical data from CSV file into cache on startup.
    Provides fast access to recent data for indicator calculations.
    """
    ensure_csv_exists()
    
    try:
        with open(CSV_FILE_PATH, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            data = [parse_csv_row(row) for row in reader]
            
            # keep only recent data to optimize memory usage
            trading_state.historical_data = data[-trading_state.cache_size:] if len(data) > trading_state.cache_size else data
            print(f"Loaded {len(trading_state.historical_data)} historical records into cache")
            
    except Exception as e:
        print(f"Error loading historical data: {e}")
        trading_state.historical_data = []

def get_historical_data():
    """Get historical completed candles for indicator calculation - provides cached access."""
    return trading_state.historical_data

def get_row_count():
    """Get the number of data rows efficiently without loading all data into memory."""
    if os.path.exists(CSV_FILE_PATH):
        try:
            with open(CSV_FILE_PATH, 'r', newline='', encoding='utf-8') as file:
                return sum(1 for _ in file) - 1  # subtract 1 for header row
        except Exception:
            return len(trading_state.historical_data)  # fallback to cached count
    return 0

def create_parameter_summary():
    """
    Create a comprehensive summary of current parameter configuration for logging.
    Helps users understand their current settings at startup.
    """
    thresholds = load_trading_thresholds()
    
    print("\n" + "="*60)
    print("📊 CURRENT TRADING CONFIGURATION")
    print("="*60)
    print(f"Indicator Window: {thresholds['indicator_window']} periods")
    print(f"Loop Interval: {thresholds['loop_interval']} seconds")
    print(f"Trade Size: {thresholds['trade_size']}")
    print(f"Stop Loss: {thresholds['stop_loss']*100:.1f}%")  # convert to percentage
    print(f"Stop Profit: {thresholds['stop_profit']*100:.1f}%")  # convert to percentage
    print(f"RSI Thresholds: {thresholds['rsi_buy_threshold']}/{thresholds['rsi_sell_threshold']}")
    print(f"MACD Thresholds: {thresholds['macd_buy_threshold']}/{thresholds['macd_sell_threshold']}")
    print(f"Position Size: ${thresholds['position_size_usdt']}")
    print(f"Active: {thresholds['active']}")
    print("="*60 + "\n")
    
    return thresholds