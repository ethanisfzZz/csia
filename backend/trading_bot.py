"""
Main trading bot module.
Contains the core trading loop and background processing logic with enhanced parameter validation.

Citations:
- Python threading for background tasks: https://docs.python.org/3/library/threading.html
- Trading loop patterns: https://www.investopedia.com/articles/active-trading/101014/basics-algorithmic-trading-concepts-and-examples.asp
- Real-time data processing: https://realpython.com/python-concurrency/
- Graceful shutdown patterns: https://docs.python.org/3/library/signal.html
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
    MAIN TRADING LOOP with unified indicator window and enhanced parameter validation.
    This is the heart of the trading bot - runs continuously until shutdown signal.
    """
    print("🚀 Starting Enhanced Crypto Trading Bot...")
    print("✨ Features: Unified indicator window, parameter validation, improved MACD logic")
    
    # display initial configuration for user awareness
    thresholds = create_parameter_summary()
    
    # show derived indicator periods so users understand the technical setup
    periods = get_indicator_periods(thresholds['indicator_window'])
    print("📈 DERIVED INDICATOR PERIODS:")
    print(f"   RSI Window: {periods['rsi_window']}")
    print(f"   MACD Fast: {periods['macd_fast']}")
    print(f"   MACD Slow: {periods['macd_slow']}")
    print(f"   Signal Window: {periods['signal_window']}")
    print("="*60 + "\n")
    
    loop_count = 0  # track loop iterations for debugging and status display
    
    # main trading loop - continues until shutdown signal
    while not trading_state.ending:
        try:
            loop_count += 1
            
            # reload thresholds each loop to allow dynamic config updates without restart
            thresholds = load_trading_thresholds()
            loop_interval = thresholds['loop_interval']
            indicator_window = thresholds['indicator_window']
            
            # STEP 1: fetch current raw market data from Binance API
            raw_data = fetch_binance_data()
            
            if raw_data:
                # STEP 2: enhance raw data with pre-calculated technical indicators
                market_data = create_market_data_with_indicators(raw_data, indicator_window)
                
                # STEP 3: persist enhanced data to CSV for historical analysis
                if save_market_data(market_data):
                    
                    # STEP 4: analyze market conditions and check for trading signals
                    signal, should_execute = check_trading_signals_with_thresholds(market_data, thresholds)
                    
                    # STEP 5: execute trade if signal meets execution criteria
                    if should_execute:
                        execute_trade(signal, market_data, thresholds)
                    elif signal not in ["NO_SIGNAL", "HOLD"]:
                        print(f"🔍 Signal detected but not executed: {signal}")
                    
                    # display comprehensive status information
                    display_status_info(market_data, signal, thresholds, loop_count)
                    
                else:
                    print("❌ Failed to save market data")
            else:
                print("⚠️  Failed to fetch market data, retrying next cycle")
            
            # wait before next iteration using configurable interval
            time.sleep(loop_interval)
            
        except KeyboardInterrupt:
            print("\n🛑 Keyboard interrupt received, stopping trading bot...")
            trading_state.ending = True  # signal clean shutdown
            break
        except Exception as e:
            print(f"💥 Error in main loop: {e}")
            print("🔄 Continuing to next iteration...")
            time.sleep(5)  # brief pause before retry to avoid rapid error loops
    
    print("🏁 Trading loop ended")

def display_status_info(market_data, signal, thresholds, loop_count):
    """
    Display enhanced status information with indicators and position details.
    Provides comprehensive view of current trading state and market conditions.
    """
    historical_count = len(trading_state.historical_data)
    periods = get_indicator_periods(thresholds['indicator_window'])
    min_required = max(periods['rsi_window'], periods['macd_slow'], periods['signal_window'])
    
    # get current trading position and P&L information
    current_position, last_trade_price = get_current_position_from_orders()
    
    # build status line with key information
    status_parts = []
    
    # loop counter helps with debugging and shows bot activity
    status_parts.append(f"Loop #{loop_count}")
    
    # data collection status - important during initial startup
    if market_data['rsi'] is None or market_data['macd'] is None:
        status_parts.append(f"Collecting data ({historical_count}/{min_required})")
    else:
        status_parts.append("Indicators ready")
    
    # current position information with unrealized P&L
    if current_position:
        position_info = f"Position: {current_position}"
        if last_trade_price:
            current_pnl = calculate_unrealized_pnl(current_position, last_trade_price, market_data['price'])
            position_info += f" @ ${last_trade_price:.2f} (PnL: {current_pnl:+.2f}%)"
        status_parts.append(position_info)
    else:
        status_parts.append("Position: None")
    
    # current signal status
    status_parts.append(f"Signal: {signal}")
    
    # current market price
    status_parts.append(f"Price: ${market_data['price']:,.2f}")
    
    # print comprehensive status on single line
    print(" | ".join(status_parts))
    
    # show detailed indicators periodically to avoid spam but provide insight
    if loop_count % 5 == 0 and market_data['rsi'] is not None:
        print(f"   📊 RSI: {market_data['rsi']:.1f}, MACD: {market_data['macd']:.6f}, Signal: {market_data['signal_line']:.6f}")

def calculate_unrealized_pnl(position_type, entry_price, current_price):
    """
    Calculate unrealized P&L percentage based on position type.
    Shows how much profit/loss would be realized if position closed now.
    """
    if position_type == 'LONG':
        # long position profits when price goes up
        return ((current_price - entry_price) / entry_price) * 100
    elif position_type == 'SHORT':
        # short position profits when price goes down
        return ((entry_price - current_price) / entry_price) * 100
    return 0.0

def start_background_trading():
    """
    Start the trading loop in a separate thread with enhanced initialization.
    This allows the web interface to run simultaneously with the trading engine.
    """
    print("🔧 Initializing trading bot components...")
    
    # preload historical data on startup for immediate indicator calculation
    print("📚 Loading historical data...")
    load_historical_data()
    
    # ensure all required CSV files exist with proper structure
    print("📁 Ensuring CSV files exist...")
    ensure_threshold_csv_exists()
    ensure_order_csv_exists()
    
    # validate and display current configuration
    print("🔍 Validating configuration...")
    thresholds = load_trading_thresholds()
    
    # check if we have enough historical data for indicators
    historical_count = len(trading_state.historical_data)
    periods = get_indicator_periods(thresholds['indicator_window'])
    min_required = max(periods['rsi_window'], periods['macd_slow'], periods['signal_window'])
    
    if historical_count < min_required:
        print(f"⚠️  Warning: Only {historical_count} historical records available.")
        print(f"   Need {min_required} records for full indicator calculation.")
        print("   Bot will collect data until indicators are ready.")
    else:
        print(f"✅ {historical_count} historical records loaded - indicators ready!")
    
    # start the trading thread as daemon so it stops when main program exits
    print("🚀 Starting background trading thread...")
    trading_thread = threading.Thread(target=main_loop, daemon=True)
    trading_thread.start()
    print("✅ Background trading thread started successfully!")
    print("🌐 Flask web server will start next...")
    print("📡 API endpoints available at: /status, /signals, /trades, /end")
    print("🛑 Press Ctrl+C to stop the application\n")