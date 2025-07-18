"""
File management module for the crypto trading bot.
Handles all CSV file operations and data persistence with parameter validation.
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
    """Ensure the CSV file exists with proper headers"""
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
    """Ensure the threshold CSV file exists with optimized default values"""
    dataframe_dir = os.path.dirname(THRESHOLD_CSV_PATH)
    os.makedirs(dataframe_dir, exist_ok=True)
    
    if not os.path.exists(THRESHOLD_CSV_PATH):
        print(f"Creating new threshold.csv file at {THRESHOLD_CSV_PATH}")
        with open(THRESHOLD_CSV_PATH, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['trade_size', 'stop_loss', 'stop_profit', 'rsi_buy_threshold', 
                           'rsi_sell_threshold', 'macd_buy_threshold', 'macd_sell_threshold', 
                           'position_size_usdt', 'active', 'loop_interval', 'indicator_window'])
            
            # Write the actual optimized default values
            writer.writerow([
                0.01,    # trade_size
                0.02,    # stop_loss (2%)
                0.025,   # stop_profit (2.5%)
                30,      # rsi_buy_threshold (oversold)
                70,      # rsi_sell_threshold (overbought)
                0.0,     # macd_buy_threshold (neutral)
                0.0,     # macd_sell_threshold (neutral)
                100.0,   # position_size_usdt ($100)
                1,       # active = True
                60,      # loop_interval (60 seconds)
                26       # indicator_window (26 periods - standard)
            ])
        print("✅ Created threshold.csv with optimized default values:")
        print(f"   Trade Size: 0.01 | Stop Loss: 2% | Stop Profit: 2.5%")
        print(f"   RSI: 30/70 | MACD: 0.0/0.0 | Position: $100 | Window: 26")
    else:
        print(f"Using existing threshold.csv file at {THRESHOLD_CSV_PATH}")

def ensure_order_csv_exists():
    """Ensure the order CSV file exists with proper headers"""
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
    """Load trading thresholds from CSV file with validation and warnings"""
    ensure_threshold_csv_exists()
    
    try:
        with open(THRESHOLD_CSV_PATH, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            thresholds = list(reader)
            
            if thresholds and len(thresholds) > 0:
                threshold = thresholds[0]
                
                # Parse configuration with error handling
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
                        'active': bool(int(float(threshold['active'])))
                    }
                    
                    # Add new parameters with defaults if they don't exist
                    config['loop_interval'] = int(float(threshold.get('loop_interval', 60)))
                    config['indicator_window'] = int(float(threshold.get('indicator_window', 26)))
                    
                except (ValueError, KeyError) as e:
                    print(f"⚠️  Error parsing threshold parameter: {e}")
                    print("Using default values for invalid parameters")
                    config = DEFAULT_THRESHOLDS.copy()
                
                # Validate parameters and show warnings
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
    """Get current position by reading the order.csv file"""
    try:
        if not os.path.exists(ORDER_CSV_PATH):
            return None, None
        
        with open(ORDER_CSV_PATH, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            orders = list(reader)
        
        if not orders:
            return None, None
        
        # Get the most recent order
        last_order = orders[-1]
        
        # Count BUY and SELL orders to determine current position
        buy_count = sum(1 for order in orders if order['side'] == 'BUY')
        sell_count = sum(1 for order in orders if order['side'] == 'SELL')
        
        if buy_count > sell_count:
            return 'LONG', float(last_order['price'])
        elif sell_count > buy_count:
            return 'SHORT', float(last_order['price'])
        else:
            return None, None
            
    except Exception as e:
        print(f"Error reading current position from orders: {e}")
        return None, None

def append_order_to_csv(order_data):
    """Append a trade order to the order CSV file"""
    ensure_order_csv_exists()
    
    try:
        with open(ORDER_CSV_PATH, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, lineterminator='\n')
            writer.writerow([
                order_data['datetime'],
                order_data['side'],
                order_data['price'],
                order_data['quantity'],
                order_data['trade_size']
            ])
            file.flush()
        
        print(f"Order logged: {order_data['side']} {order_data['quantity']:.6f} at {order_data['price']}")
        
    except Exception as e:
        print(f"Error appending order to CSV: {e}")

def parse_csv_row(row):
    """Parse a CSV row and convert numeric fields"""
    try:
        def safe_float(value):
            if value and value != '' and value != 'nan':
                try:
                    return float(value)
                except (ValueError, TypeError):
                    return None
            return None
        
        return {
            'datetime': row['datetime'],
            'price': float(row['price']),
            'volume': float(row['volume']),
            'rsi': safe_float(row['rsi']),
            'macd': safe_float(row['macd']),
            'signal_line': safe_float(row['signal_line'])
        }
    except (ValueError, TypeError) as e:
        print(f"Error parsing CSV row: {e}")
        return row

def format_indicator_value(value):
    """Format indicator value for CSV output"""
    if value is None or pd.isna(value):
        return ''
    try:
        if np.isnan(value):
            return ''
    except (TypeError, ValueError):
        pass
    return str(value)

def append_to_csv(market_data):
    """Append a single row of market data to CSV file"""
    ensure_csv_exists()
    
    try:
        with open(CSV_FILE_PATH, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, lineterminator='\n')
            writer.writerow([
                market_data['datetime'],
                market_data['price'],
                market_data['volume'],
                format_indicator_value(market_data['rsi']),
                format_indicator_value(market_data['macd']),
                format_indicator_value(market_data['signal_line'])
            ])
            file.flush()
        
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
    if os.path.exists(CSV_FILE_PATH):
        try:
            with open(CSV_FILE_PATH, 'r', newline='', encoding='utf-8') as file:
                return sum(1 for _ in file) - 1  # Subtract 1 for header
        except Exception:
            return len(trading_state.historical_data)
    return 0

def create_parameter_summary():
    """Create a summary of current parameter configuration for logging"""
    thresholds = load_trading_thresholds()
    
    print("\n" + "="*60)
    print("📊 CURRENT TRADING CONFIGURATION")
    print("="*60)
    print(f"Indicator Window: {thresholds['indicator_window']} periods")
    print(f"Loop Interval: {thresholds['loop_interval']} seconds")
    print(f"Trade Size: {thresholds['trade_size']}")
    print(f"Stop Loss: {thresholds['stop_loss']*100:.1f}%")
    print(f"Stop Profit: {thresholds['stop_profit']*100:.1f}%")
    print(f"RSI Thresholds: {thresholds['rsi_buy_threshold']}/{thresholds['rsi_sell_threshold']}")
    print(f"MACD Thresholds: {thresholds['macd_buy_threshold']}/{thresholds['macd_sell_threshold']}")
    print(f"Position Size: ${thresholds['position_size_usdt']}")
    print(f"Active: {thresholds['active']}")
    print("="*60 + "\n")
    
    return thresholds