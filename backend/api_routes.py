"""
API routes module for the crypto trading bot.
Defines all Flask endpoints for monitoring and control with enhanced parameter information.
"""

import os
import csv
from flask import Flask, jsonify
from config import trading_state, ORDER_CSV_PATH, get_indicator_periods
from file_manager import get_historical_data, load_trading_thresholds, get_current_position_from_orders, get_row_count
from trading_engine import check_trading_signals_with_thresholds

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    return app

def register_routes(app):
    """Register all API routes with the Flask app"""
    
    @app.route('/')
    def hello_world():
        return jsonify({
            "message": "Crypto Trading Bot API",
            "version": "2.0 - Enhanced with Unified Indicator Window",
            "endpoints": {
                "/status": "Get current trading status and market data",
                "/signals": "Get recent trading signals",
                "/trades": "Get recent trades",
                "/parameters": "Get current parameter configuration",
                "/end": "Terminate trading algorithm"
            }
        })

    @app.route('/end')
    def signal_end():
        trading_state.ending = True
        return jsonify({"message": "Trading algorithm terminated", "status": "stopped"})

    @app.route('/status')
    def get_status():
        """Get current trading status and latest market data with enhanced information"""
        try:
            historical_data = get_historical_data()
            thresholds = load_trading_thresholds()
            current_position, last_trade_price = get_current_position_from_orders()
            periods = get_indicator_periods(thresholds['indicator_window'])
            
            if historical_data:
                latest = historical_data[-1]
                
                # Calculate unrealized PnL if position exists
                unrealized_pnl = None
                if current_position and last_trade_price:
                    if current_position == 'LONG':
                        unrealized_pnl = ((latest['price'] - last_trade_price) / last_trade_price) * 100
                    elif current_position == 'SHORT':
                        unrealized_pnl = ((last_trade_price - latest['price']) / last_trade_price) * 100
                
                return jsonify({
                    "status": "running" if not trading_state.ending else "stopped",
                    "latest_data": {
                        "price": latest['price'],
                        "datetime": latest['datetime'],
                        "rsi": latest['rsi'],
                        "macd": latest['macd'],
                        "signal_line": latest['signal_line']
                    },
                    "indicators": {
                        "available": latest['rsi'] is not None,
                        "periods": periods,
                        "min_required": max(periods['rsi_window'], periods['macd_slow'], periods['signal_window'])
                    },
                    "position": {
                        "current_position": current_position,
                        "last_trade_price": last_trade_price,
                        "unrealized_pnl_percent": unrealized_pnl
                    },
                    "data_stats": {
                        "total_records": get_row_count(),
                        "cached_records": len(historical_data)
                    },
                    "configuration": {
                        "indicator_window": thresholds['indicator_window'],
                        "loop_interval": thresholds['loop_interval'],
                        "active": thresholds['active']
                    }
                })
            else:
                return jsonify({
                    "status": "running" if not trading_state.ending else "stopped", 
                    "message": "No data yet",
                    "configuration": {
                        "indicator_window": thresholds['indicator_window'],
                        "loop_interval": thresholds['loop_interval'],
                        "active": thresholds['active']
                    }
                })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error reading data: {str(e)}"
            }), 500

    @app.route('/signals')
    def get_recent_signals():
        """Get recent trading signals with enhanced analysis"""
        try:
            historical_data = get_historical_data()
            thresholds = load_trading_thresholds()
            recent_signals = []
            
            # Get last 10 records for signal analysis
            for data in historical_data[-10:]:
                signal, should_execute = check_trading_signals_with_thresholds(data, thresholds)
                
                # Enhanced signal information
                signal_info = {
                    "datetime": data['datetime'],
                    "price": data['price'],
                    "signal": signal,
                    "should_execute": should_execute,
                    "indicators": {
                        "rsi": data['rsi'],
                        "macd": data['macd'],
                        "signal_line": data['signal_line']
                    }
                }
                
                # Add RSI and MACD analysis
                if data['rsi'] is not None:
                    if data['rsi'] <= thresholds['rsi_buy_threshold']:
                        signal_info['rsi_condition'] = "oversold"
                    elif data['rsi'] >= thresholds['rsi_sell_threshold']:
                        signal_info['rsi_condition'] = "overbought"
                    else:
                        signal_info['rsi_condition'] = "neutral"
                
                if data['macd'] is not None and data['signal_line'] is not None:
                    signal_info['macd_position'] = "above_signal" if data['macd'] > data['signal_line'] else "below_signal"
                    signal_info['macd_divergence'] = abs(data['macd'] - data['signal_line'])
                
                recent_signals.append(signal_info)
            
            return jsonify({
                "recent_signals": recent_signals,
                "analysis_period": len(recent_signals),
                "thresholds_used": {
                    "rsi_buy": thresholds['rsi_buy_threshold'],
                    "rsi_sell": thresholds['rsi_sell_threshold'],
                    "macd_buy": thresholds['macd_buy_threshold'],
                    "macd_sell": thresholds['macd_sell_threshold']
                }
            })
        except Exception as e:
            return jsonify({"error": f"Error getting signals: {str(e)}"}), 500

    @app.route('/trades')
    def get_recent_trades():
        """Get recent trades from order.csv with enhanced information"""
        try:
            if not os.path.exists(ORDER_CSV_PATH):
                return jsonify({"trades": [], "summary": {"total_trades": 0}})
            
            trades = []
            with open(ORDER_CSV_PATH, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                all_trades = list(reader)
            
            recent_trades = all_trades[-20:]  # Last 20 trades
            
            # Enhanced trade information
            for trade in recent_trades:
                enhanced_trade = {
                    "datetime": trade['datetime'],
                    "side": trade['side'],
                    "price": float(trade['price']),
                    "quantity": float(trade['quantity']),
                    "trade_size": float(trade['trade_size']),
                    "position_value": float(trade['price']) * float(trade['quantity'])
                }
                trades.append(enhanced_trade)
            
            # Calculate summary statistics
            total_trades = len(all_trades)
            buy_trades = sum(1 for t in all_trades if t['side'] == 'BUY')
            sell_trades = sum(1 for t in all_trades if t['side'] == 'SELL')
            
            summary = {
                "total_trades": total_trades,
                "buy_trades": buy_trades,
                "sell_trades": sell_trades,
                "showing_recent": len(recent_trades)
            }
            
            return jsonify({
                "trades": trades,
                "summary": summary
            })
        except Exception as e:
            return jsonify({"error": f"Error reading trades: {str(e)}"}), 500

    @app.route('/parameters')
    def get_parameters():
        """Get current parameter configuration with validation info"""
        try:
            thresholds = load_trading_thresholds()
            periods = get_indicator_periods(thresholds['indicator_window'])
            
            return jsonify({
                "current_parameters": thresholds,
                "derived_periods": periods,
                "parameter_info": {
                    "indicator_window": "Controls all indicator periods (main tuning parameter)",
                    "rsi_window": f"Calculated as {periods['rsi_window']} from indicator_window",
                    "macd_fast": f"Calculated as {periods['macd_fast']} from indicator_window", 
                    "macd_slow": f"Same as indicator_window ({periods['macd_slow']})",
                    "signal_window": f"Calculated as {periods['signal_window']} from indicator_window"
                },
                "recommendations": {
                    "indicator_window": "20-30 for balanced sensitivity",
                    "rsi_thresholds": "Buy: 25-35, Sell: 65-80",
                    "stop_loss": "1-5% depending on volatility",
                    "stop_profit": "1.5-5% depending on strategy"
                }
            })
        except Exception as e:
            return jsonify({"error": f"Error getting parameters: {str(e)}"}), 500