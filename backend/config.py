"""
Configuration module for the crypto trading bot.
Handles all configuration constants and environment settings.

Citations:
- MACD technical analysis periods: https://www.investopedia.com/terms/m/macd.asp
- RSI calculation periods: https://www.investopedia.com/terms/r/rsi.asp
- Risk management principles: https://www.investopedia.com/articles/trading/09/risk-management.asp
- Parameter validation patterns: https://realpython.com/python-data-validation/
"""

import os

# API Configuration
BINANCE_BASE_URL = "https://api.binance.com/api/v3"
SYMBOL = "BTCUSDT"  # trading pair - can be changed to any supported symbol

# File Paths - centralized path management
CSV_FILE_PATH = "./dataframe/market_data.csv"
THRESHOLD_CSV_PATH = "./dataframe/threshold.csv"
ORDER_CSV_PATH = "./dataframe/order.csv"

# Trading State Configuration
CACHE_SIZE = 100  # keep last 100 records in memory for performance

# Parameter Validation Ranges - ensures safe trading parameters
# each parameter has min/max limits and recommended ranges for optimal performance
PARAMETER_RANGES = {
    'trade_size': {'min': 0.001, 'max': 1.0, 'recommended': (0.01, 0.1)},
    'stop_loss': {'min': 0.005, 'max': 0.1, 'recommended': (0.01, 0.05)},  # 0.5% to 10% max loss
    'stop_profit': {'min': 0.005, 'max': 0.15, 'recommended': (0.015, 0.05)},  # 0.5% to 15% max profit
    'rsi_buy_threshold': {'min': 10, 'max': 40, 'recommended': (25, 35)},  # oversold territory
    'rsi_sell_threshold': {'min': 60, 'max': 90, 'recommended': (65, 80)},  # overbought territory
    'macd_buy_threshold': {'min': -0.01, 'max': 0.01, 'recommended': (-0.001, 0.001)},
    'macd_sell_threshold': {'min': -0.01, 'max': 0.01, 'recommended': (-0.001, 0.001)},
    'position_size_usdt': {'min': 10.0, 'max': 10000.0, 'recommended': (50.0, 500.0)},  # USD position limits
    'loop_interval': {'min': 30, 'max': 300, 'recommended': (60, 120)},  # seconds between trading decisions
    'indicator_window': {'min': 10, 'max': 50, 'recommended': (20, 30)}  # periods for technical indicators
}

# Default Trading Thresholds - optimized values based on backtesting and common practices
DEFAULT_THRESHOLDS = {
    'trade_size': 0.01,  # 1% of portfolio per trade
    'stop_loss': 0.02,  # 2% stop loss - conservative risk management
    'stop_profit': 0.025,  # 2.5% take profit - slightly higher than stop loss
    'rsi_buy_threshold': 30,  # classic oversold level
    'rsi_sell_threshold': 70,  # classic overbought level
    'macd_buy_threshold': 0.0,  # neutral MACD level
    'macd_sell_threshold': 0.0,  # neutral MACD level
    'position_size_usdt': 100.0,  # $100 per position
    'active': True,  # trading enabled by default
    'loop_interval': 60,  # check every minute
    'indicator_window': 26  # standard MACD slow period
}

# Technical Indicator Configuration - all periods derived from main indicator_window
# this unified approach ensures consistent indicator calculation across the system
def get_indicator_periods(indicator_window):
    """
    Calculate all indicator periods based on the main indicator_window.
    Uses standard technical analysis ratios to derive optimal periods.
    """
    return {
        'rsi_window': max(10, int(indicator_window * 0.54)),  # ~14 when indicator_window=26 (standard RSI)
        'macd_fast': max(8, int(indicator_window * 0.46)),    # ~12 when indicator_window=26 (standard MACD fast)
        'macd_slow': indicator_window,                        # 26 (main period - standard MACD slow)
        'signal_window': max(6, int(indicator_window * 0.35)) # ~9 when indicator_window=26 (standard signal line)
    }

def validate_parameter(param_name, value):
    """
    Validate a parameter value and return warnings if out of recommended range.
    Helps users understand if their settings might be risky or suboptimal.
    """
    if param_name not in PARAMETER_RANGES:
        return []
    
    ranges = PARAMETER_RANGES[param_name]
    warnings = []
    
    # check hard limits first - these could break the system
    if value < ranges['min']:
        warnings.append(f"⚠️  {param_name}={value} is below minimum ({ranges['min']})")
    elif value > ranges['max']:
        warnings.append(f"⚠️  {param_name}={value} is above maximum ({ranges['max']})")
    
    # check recommended range - these are optimization suggestions
    rec_min, rec_max = ranges['recommended']
    if ranges['min'] <= value <= ranges['max']:  # only check if within hard limits
        if value < rec_min:
            warnings.append(f"💡 {param_name}={value} is below recommended range ({rec_min}-{rec_max})")
        elif value > rec_max:
            warnings.append(f"💡 {param_name}={value} is above recommended range ({rec_min}-{rec_max})")
    
    return warnings

def validate_all_parameters(thresholds):
    """
    Validate all threshold parameters and return combined warnings.
    Includes both individual parameter validation and logical consistency checks.
    """
    all_warnings = []
    
    # validate each parameter individually
    for param_name, value in thresholds.items():
        if param_name != 'active':  # skip boolean parameter
            warnings = validate_parameter(param_name, value)
            all_warnings.extend(warnings)
    
    # additional logic validation - check parameter relationships
    if thresholds['rsi_buy_threshold'] >= thresholds['rsi_sell_threshold']:
        all_warnings.append("⚠️  RSI buy threshold should be less than sell threshold")
    
    if thresholds['stop_loss'] >= thresholds['stop_profit']:
        all_warnings.append("💡 Stop loss is higher than stop profit - consider adjusting")
    
    return all_warnings

class TradingState:
    """
    Global trading state management - handles system-wide state and data caching.
    Provides centralized access to trading status and historical data.
    """
    def __init__(self):
        self.ending = False  # signal for graceful shutdown
        self.historical_data = []  # keep historical completed candles in memory
        self.cache_size = CACHE_SIZE  # limit memory usage

# global trading state instance - singleton pattern for system-wide access
trading_state = TradingState()