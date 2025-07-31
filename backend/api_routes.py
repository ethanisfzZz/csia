"""
API routes module for the crypto trading bot with authentication.
"""

import os
import csv
import signal
import threading
from flask import Flask, jsonify, request
from flask_cors import CORS
from config import trading_state, ORDER_CSV_PATH, THRESHOLD_CSV_PATH, get_indicator_periods
from file_manager import get_historical_data, load_trading_thresholds, get_current_position_from_orders, get_row_count
from trading_engine import check_trading_signals_with_thresholds

def create_app():
    """Create and configure Flask application with CORS support"""
    app = Flask(__name__)
    CORS(app, origins=["*"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    return app

def shutdown_server():
    """Gracefully shutdown the Flask server"""
    def shutdown():
        trading_state.ending = True
        print("\n🛑 Shutdown initiated from web interface...")
        threading.Timer(2.0, lambda: os.kill(os.getpid(), signal.SIGTERM)).start()
    
    threading.Timer(0.5, shutdown).start()

def register_routes(app):
    """Register all API routes with the Flask app"""
    
    from auth import register_auth_routes, require_auth
    
    # Register auth routes
    register_auth_routes(app)
    
    @app.route('/')
    def hello_world():
        return jsonify({
            "message": "Crypto Trading Bot API with Authentication",
            "version": "2.1",
            "login": "POST /login with username and password",
            "debug": "GET /debug-csv to inspect user file"
        })

    @app.route('/end', methods=['POST'])
    @require_auth
    def signal_end():
        try:
            shutdown_server()
            return jsonify({
                "message": "Trading bot shutdown initiated", 
                "status": "stopping"
            })
        except Exception as e:
            return jsonify({"error": f"Shutdown failed: {str(e)}"}), 500

    @app.route('/save-config', methods=['POST'])
    @require_auth
    def save_configuration():
        try:
            data = request.get_json()
            if not data:
                return jsonify({"error": "No configuration data provided"}), 400
            
            required_fields = [
                'trade_size', 'stop_loss', 'stop_profit', 'rsi_buy_threshold',
                'rsi_sell_threshold', 'macd_buy_threshold', 'macd_sell_threshold',
                'position_size_usdt', 'active', 'loop_interval', 'indicator_window'
            ]
            
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing required field: {field}"}), 400
            
            dataframe_dir = os.path.dirname(THRESHOLD_CSV_PATH)
            os.makedirs(dataframe_dir, exist_ok=True)
            
            with open(THRESHOLD_CSV_PATH, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([
                    'trade_size', 'stop_loss', 'stop_profit', 'rsi_buy_threshold',
                    'rsi_sell_threshold', 'macd_buy_threshold', 'macd_sell_threshold',
                    'position_size_usdt', 'active', 'loop_interval', 'indicator_window'
                ])
                
                writer.writerow([
                    data['trade_size'], data['stop_loss'], data['stop_profit'],
                    data['rsi_buy_threshold'], data['rsi_sell_threshold'],
                    data['macd_buy_threshold'], data['macd_sell_threshold'],
                    data['position_size_usdt'], data['active'],
                    data['loop_interval'], data['indicator_window']
                ])
            
            print(f"✅ Configuration saved")
            return jsonify({"message": "Configuration saved successfully"})
            
        except Exception as e:
            print(f"❌ Error saving configuration: {e}")
            return jsonify({"error": f"Failed to save configuration: {str(e)}"}), 500

    @app.route('/status')
    @require_auth
    def get_status():
        try:
            historical_data = get_historical_data()
            thresholds = load_trading_thresholds()
            current_position, last_trade_price = get_current_position_from_orders()
            periods = get_indicator_periods(thresholds['indicator_window'])
            
            if historical_data:
                latest = historical_data[-1]
                
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
            return jsonify({"status": "error", "message": f"Error reading data: {str(e)}"}), 500

    @app.route('/trades')
    @require_auth
    def get_recent_trades():
        try:
            if not os.path.exists(ORDER_CSV_PATH):
                return jsonify({"trades": [], "summary": {"total_trades": 0}})
            
            trades = []
            with open(ORDER_CSV_PATH, 'r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                all_trades = list(reader)
            
            recent_trades = all_trades[-20:]
            
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
            
            total_trades = len(all_trades)
            buy_trades = sum(1 for t in all_trades if t['side'] == 'BUY')
            sell_trades = sum(1 for t in all_trades if t['side'] == 'SELL')
            
            summary = {
                "total_trades": total_trades,
                "buy_trades": buy_trades,
                "sell_trades": sell_trades,
                "showing_recent": len(recent_trades)
            }
            
            return jsonify({"trades": trades, "summary": summary})
        except Exception as e:
            return jsonify({"error": f"Error reading trades: {str(e)}"}), 500

    @app.route('/parameters')
    @require_auth
    def get_parameters():
        try:
            thresholds = load_trading_thresholds()
            periods = get_indicator_periods(thresholds['indicator_window'])
            
            return jsonify({
                "current_parameters": thresholds,
                "derived_periods": periods
            })
        except Exception as e:
            return jsonify({"error": f"Error getting parameters: {str(e)}"}), 500
    
    @app.route('/market-data')
    @require_auth
    def get_market_data():
        try:
            historical_data = get_historical_data()
            recent_data = historical_data[-100:] if len(historical_data) > 100 else historical_data
            
            return jsonify({
                "data": recent_data,
                "count": len(recent_data),
                "total_available": len(historical_data)
            })
        except Exception as e:
            return jsonify({"error": f"Error getting market data: {str(e)}"}), 500