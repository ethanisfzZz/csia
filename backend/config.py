"""
Configuration module for the crypto trading bot.
Handles all configuration constants and environment settings.
"""

import os

# API Configuration
BINANCE_BASE_URL = "https://api.binance.com/api/v3"
SYMBOL = "BTCUSDT"  # This can later be changed to any trading pair

# File Paths
CSV_FILE_PATH = "./dataframe/market_data.csv"
THRESHOLD_CSV_PATH = "./dataframe/threshold.csv"
ORDER_CSV_PATH = "./dataframe/order.csv"

# Trading State Configuration
CACHE_SIZE = 100  # Keep last 100 records in memory

# Parameter Validation Ranges
PARAMETER_RANGES = {
    'trade_size': {'min': 0.001, 'max': 1.0, 'recommended': (0.01, 0.1)},
    'stop_loss': {'min': 0.005, 'max': 0.1, 'recommended': (0.01, 0.05)},
    'stop_profit': {'min': 0.005, 'max': 0.15, 'recommended': (0.015, 0.05)},
    'rsi_buy_threshold': {'min': 10, 'max': 40, 'recommended': (25, 35)},
    'rsi_sell_threshold': {'min': 60, 'max': 90, 'recommended': (65, 80)},
    'macd_buy_threshold': {'min': -0.01, 'max': 0.01, 'recommended': (-0.001, 0.001)},
    'macd_sell_threshold': {'min': -0.01, 'max': 0.01, 'recommended': (-0.001, 0.001)},
    'position_size_usdt': {'min': 10.0, 'max': 10000.0, 'recommended': (50.0, 500.0)},
    'loop_interval': {'min': 30, 'max': 300, 'recommended': (60, 120)},
    'indicator_window': {'min': 10, 'max': 50, 'recommended': (20, 30)}
}

# Default Trading Thresholds - Optimized values
DEFAULT_THRESHOLDS = {
    'trade_size': 0.01,
    'stop_loss': 0.02,
    'stop_profit': 0.025,
    'rsi_buy_threshold': 30,
    'rsi_sell_threshold': 70,
    'macd_buy_threshold': 0.0,
    'macd_sell_threshold': 0.0,
    'position_size_usdt': 100.0,
    'active': True,
    'loop_interval': 60,
    'indicator_window': 26
}

# Technical Indicator Configuration - Now all derived from indicator_window
def get_indicator_periods(indicator_window):
    """Calculate all indicator periods based on the main indicator_window"""
    return {
        'rsi_window': max(10, int(indicator_window * 0.54)),  # ~14 when indicator_window=26
        'macd_fast': max(8, int(indicator_window * 0.46)),    # ~12 when indicator_window=26
        'macd_slow': indicator_window,                        # 26 (main period)
        'signal_window': max(6, int(indicator_window * 0.35)) # ~9 when indicator_window=26
    }

def validate_parameter(param_name, value):
    """Validate a parameter value and return warnings if out of recommended range"""
    if param_name not in PARAMETER_RANGES:
        return []
    
    ranges = PARAMETER_RANGES[param_name]
    warnings = []
    
    # Check hard limits
    if value < ranges['min']:
        warnings.append(f"⚠️  {param_name}={value} is below minimum ({ranges['min']})")
    elif value > ranges['max']:
        warnings.append(f"⚠️  {param_name}={value} is above maximum ({ranges['max']})")
    
    # Check recommended range
    rec_min, rec_max = ranges['recommended']
    if ranges['min'] <= value <= ranges['max']:  # Only check if within hard limits
        if value < rec_min:
            warnings.append(f"💡 {param_name}={value} is below recommended range ({rec_min}-{rec_max})")
        elif value > rec_max:
            warnings.append(f"💡 {param_name}={value} is above recommended range ({rec_min}-{rec_max})")
    
    return warnings

def validate_all_parameters(thresholds):
    """Validate all threshold parameters and return combined warnings"""
    all_warnings = []
    
    for param_name, value in thresholds.items():
        if param_name != 'active':  # Skip boolean parameter
            warnings = validate_parameter(param_name, value)
            all_warnings.extend(warnings)
    
    # Additional logic validation
    if thresholds['rsi_buy_threshold'] >= thresholds['rsi_sell_threshold']:
        all_warnings.append("⚠️  RSI buy threshold should be less than sell threshold")
    
    if thresholds['stop_loss'] >= thresholds['stop_profit']:
        all_warnings.append("💡 Stop loss is higher than stop profit - consider adjusting")
    
    return all_warnings

class TradingState:
    """Global trading state management"""
    def __init__(self):
        self.ending = False
        self.historical_data = []  # Keep historical completed candles
        self.cache_size = CACHE_SIZE

# Global trading state instance
trading_state = TradingState()