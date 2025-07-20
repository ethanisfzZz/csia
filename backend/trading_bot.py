"""
Main trading bot module.
Contains the core trading loop and background processing logic with enhanced parameter validation.
"""

import time
import threading
from config import trading_state, get_indicator_periods
from file_manager import (
    load_historical_data, load_trading_thresholds, 
    ensure_threshold_csv_exists, ensure_order_csv_exists,
    get_current_position_from_orders, get_historical_data,
    create_parameter_summary
)
from market_data_fetcher import fetch_binance_data
from data_processor import create_market_data_with_indicators, save_market_data
from trading_engine import check_trading_signals_with_thresholds, execute_trade

def main_loop():
    """
    MAIN TRADING LOOP with unified indicator window and enhanced parameter validation
    """
    print("🚀 Starting Enhanced Crypto Trading Bot...")
    print("✨ Features: Unified indicator window, parameter validation, improved MACD logic")
    
    # Show initial configuration
    thresholds = create_parameter_summary()
    
    # Show derived indicator periods
    periods = get_indicator_periods(thresholds['indicator_window'])
    print("📈 DERIVED INDICATOR PERIODS:")
    print(f"   RSI Window: {periods['rsi_window']}")
    print(f"   MACD Fast: {periods['macd_fast']}")
    print(f"   MACD Slow: {periods['macd_slow']}")
    print(f"   Signal Window: {periods['signal_window']}")
    print("="*60 + "\n")
    
    loop_count = 0
    
    while not trading_state.ending:
        try:
            loop_count += 1
            
            # Load current thresholds (allows dynamic updates)
            thresholds = load_trading_thresholds()
            loop_interval = thresholds['loop_interval']
            indicator_window = thresholds['indicator_window']
            
            # Step 1: Fetch current raw market data
            raw_data = fetch_binance_data()
            
            if raw_data:
                # Step 2: Create complete market data with pre-calculated indicators
                market_data = create_market_data_with_indicators(raw_data, indicator_window)
                
                # Step 3: Save to CSV
                if save_market_data(market_data):
                    
                    # Step 4: Check for trading signals using enhanced logic
                    signal, should_execute = check_trading_signals_with_thresholds(market_data, thresholds)
                    
                    # Step 5: Execute trade if signal is strong enough
                    if should_execute:
                        execute_trade(signal, market_data, thresholds)
                    elif signal not in ["NO_SIGNAL", "HOLD"]:
                        print(f"🔍 Signal detected but not executed: {signal}")
                    
                    # Enhanced status information
                    display_status_info(market_data, signal, thresholds, loop_count)
                    
                else:
                    print("❌ Failed to save market data")
            else:
                print("⚠️  Failed to fetch market data, retrying next cycle")
            
            # Wait before next iteration using configurable interval
            time.sleep(loop_interval)
            
        except KeyboardInterrupt:
            print("\n🛑 Keyboard interrupt received, stopping trading bot...")
            trading_state.ending = True
            break
        except Exception as e:
            print(f"💥 Error in main loop: {e}")
            print("🔄 Continuing to next iteration...")
            time.sleep(5)
    
    print("🏁 Trading loop ended")

def display_status_info(market_data, signal, thresholds, loop_count):
    """Display enhanced status information with indicators and position details"""
    historical_count = len(trading_state.historical_data)
    periods = get_indicator_periods(thresholds['indicator_window'])
    min_required = max(periods['rsi_window'], periods['macd_slow'], periods['signal_window'])
    
    # Get current position
    current_position, last_trade_price = get_current_position_from_orders()
    
    # Create status line
    status_parts = []
    
    # Loop counter (useful for debugging)
    status_parts.append(f"Loop #{loop_count}")
    
    # Data collection status
    if market_data['rsi'] is None or market_data['macd'] is None:
        status_parts.append(f"Collecting data ({historical_count}/{min_required})")
    else:
        status_parts.append("Indicators ready")
    
    # Position information
    if current_position:
        position_info = f"Position: {current_position}"
        if last_trade_price:
            current_pnl = calculate_unrealized_pnl(current_position, last_trade_price, market_data['price'])
            position_info += f" @ ${last_trade_price:.2f} (PnL: {current_pnl:+.2f}%)"
        status_parts.append(position_info)
    else:
        status_parts.append("Position: None")
    
    # Signal information
    status_parts.append(f"Signal: {signal}")
    
    # Price information
    status_parts.append(f"Price: ${market_data['price']:,.2f}")
    
    # Print comprehensive status
    print(" | ".join(status_parts))
    
    # Show indicators if available (every 5th loop to avoid spam)
    if loop_count % 5 == 0 and market_data['rsi'] is not None:
        print(f"   📊 RSI: {market_data['rsi']:.1f}, MACD: {market_data['macd']:.6f}, Signal: {market_data['signal_line']:.6f}")

def calculate_unrealized_pnl(position_type, entry_price, current_price):
    """Calculate unrealized PnL percentage"""
    if position_type == 'LONG':
        return ((current_price - entry_price) / entry_price) * 100
    elif position_type == 'SHORT':
        return ((entry_price - current_price) / entry_price) * 100
    return 0.0

def start_background_trading():
    """Start the trading loop in a separate thread with enhanced initialization"""
    print("🔧 Initializing trading bot components...")
    
    # Load historical data on startup
    print("📚 Loading historical data...")
    load_historical_data()
    
    # Ensure all CSV files exist
    print("📁 Ensuring CSV files exist...")
    ensure_threshold_csv_exists()
    ensure_order_csv_exists()
    
    # Validate configuration
    print("🔍 Validating configuration...")
    thresholds = load_trading_thresholds()
    
    # Check if we have enough historical data
    historical_count = len(trading_state.historical_data)
    periods = get_indicator_periods(thresholds['indicator_window'])
    min_required = max(periods['rsi_window'], periods['macd_slow'], periods['signal_window'])
    
    if historical_count < min_required:
        print(f"⚠️  Warning: Only {historical_count} historical records available.")
        print(f"   Need {min_required} records for full indicator calculation.")
        print("   Bot will collect data until indicators are ready.")
    else:
        print(f"✅ {historical_count} historical records loaded - indicators ready!")
    
    # Start the trading thread
    print("🚀 Starting background trading thread...")
    trading_thread = threading.Thread(target=main_loop, daemon=True)
    trading_thread.start()
    print("✅ Background trading thread started successfully!")
    print("🌐 Flask web server will start next...")
    print("📡 API endpoints available at: /status, /signals, /trades, /end")
    print("🛑 Press Ctrl+C to stop the application\n")