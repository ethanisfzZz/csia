"""
Technical indicators module for the crypto trading bot.
Handles calculation of RSI, MACD, and other technical indicators using unified indicator_window.
"""

import pandas as pd
import numpy as np
import ta
from config import get_indicator_periods

def calculate_technical_indicators(historical_data, indicator_window=26):
    """
    Calculate MACD and RSI indicators using unified indicator_window approach.
    All periods are derived from the main indicator_window parameter.
    """
    # Get all periods based on indicator_window
    periods = get_indicator_periods(indicator_window)
    rsi_window = periods['rsi_window']
    macd_fast = periods['macd_fast']
    macd_slow = periods['macd_slow']
    signal_window = periods['signal_window']
    
    # Minimum data required is the largest period needed
    min_required = max(rsi_window, macd_slow, signal_window)
    
    if len(historical_data) < min_required:
        print(f"Not enough data for indicators: {len(historical_data)}/{min_required} required")
        print(f"Periods - RSI:{rsi_window}, MACD:{macd_fast}/{macd_slow}, Signal:{signal_window}")
        return None, None, None
    
    try:
        # Extract prices from historical data
        prices = []
        for candle in historical_data:
            if candle['price'] is not None:
                prices.append(candle['price'])
        
        if len(prices) < min_required:
            print(f"Not enough valid prices for indicators: {len(prices)}/{min_required} required")
            return None, None, None
            
        prices_series = pd.Series(prices)
        
        # Calculate RSI using derived window
        latest_rsi = None
        try:
            if len(prices_series) >= rsi_window:
                rsi_indicator = ta.momentum.RSIIndicator(close=prices_series, window=rsi_window)
                rsi_values = rsi_indicator.rsi()
                latest_rsi = rsi_values.iloc[-1] if len(rsi_values) > 0 and not pd.isna(rsi_values.iloc[-1]) else None
        except Exception as e:
            print(f"Error calculating RSI: {e}")
        
        # Calculate MACD with derived periods
        latest_macd = None
        latest_signal = None
        try:
            if len(prices_series) >= macd_slow:
                macd_indicator = ta.trend.MACD(
                    close=prices_series, 
                    window_slow=macd_slow,
                    window_fast=macd_fast,
                    window_sign=signal_window
                )
                macd_values = macd_indicator.macd()
                signal_values = macd_indicator.macd_signal()
                
                if len(macd_values) > 0 and not pd.isna(macd_values.iloc[-1]):
                    latest_macd = macd_values.iloc[-1]
                if len(signal_values) > 0 and not pd.isna(signal_values.iloc[-1]):
                    latest_signal = signal_values.iloc[-1]
        except Exception as e:
            print(f"Error calculating MACD: {e}")
        
        # Validate results
        def is_valid_number(value):
            return value is not None and not pd.isna(value) and np.isfinite(value)
        
        final_rsi = latest_rsi if is_valid_number(latest_rsi) else None
        final_macd = latest_macd if is_valid_number(latest_macd) else None
        final_signal = latest_signal if is_valid_number(latest_signal) else None
        
        # Enhanced debug output
        rsi_str = f"{final_rsi:.2f}" if final_rsi is not None else "N/A"
        macd_str = f"{final_macd:.6f}" if final_macd is not None else "N/A"
        signal_str = f"{final_signal:.6f}" if final_signal is not None else "N/A"
        
        print(f"Indicators (Window:{indicator_window}) - RSI({rsi_window}): {rsi_str}, "
              f"MACD({macd_fast}/{macd_slow}): {macd_str}, Signal({signal_window}): {signal_str}")
        
        return final_rsi, final_macd, final_signal
        
    except Exception as e:
        print(f"Error calculating technical indicators: {e}")
        return None, None, None

def check_macd_crossover(historical_data, current_macd, current_signal):
    """
    Check for MACD crossover by comparing current and previous periods.
    Returns more detailed crossover information.
    """
    if len(historical_data) < 2 or current_macd is None or current_signal is None:
        return False, False, None
    
    # Get previous MACD and signal values
    prev_data = historical_data[-2]
    if prev_data['macd'] is None or prev_data['signal_line'] is None:
        return False, False, None
    
    prev_macd = prev_data['macd']
    prev_signal = prev_data['signal_line']
    
    # Calculate MACD momentum (current - previous)
    macd_momentum = current_macd - prev_macd
    
    # Bullish crossover: MACD crosses above signal line
    bullish_cross = (prev_macd <= prev_signal) and (current_macd > current_signal)
    
    # Bearish crossover: MACD crosses below signal line
    bearish_cross = (prev_macd >= prev_signal) and (current_macd < current_signal)
    
    # Additional confirmation: check if crossover has momentum
    crossover_strength = None
    if bullish_cross:
        crossover_strength = "strong" if macd_momentum > 0 else "weak"
    elif bearish_cross:
        crossover_strength = "strong" if macd_momentum < 0 else "weak"
    
    return bullish_cross, bearish_cross, crossover_strength

def get_macd_trend_strength(current_macd, current_signal):
    """
    Determine MACD trend strength based on line separation and position.
    """
    if current_macd is None or current_signal is None:
        return "unknown"
    
    separation = abs(current_macd - current_signal)
    
    if current_macd > current_signal:
        if separation > 0.001:  # Significant separation
            return "strong_bullish"
        else:
            return "weak_bullish"
    else:
        if separation > 0.001:  # Significant separation
            return "strong_bearish"
        else:
            return "weak_bearish"

def analyze_rsi_condition(rsi_value, buy_threshold, sell_threshold):
    """
    Analyze RSI condition with more nuanced interpretation.
    """
    if rsi_value is None:
        return "unknown"
    
    if rsi_value <= buy_threshold:
        if rsi_value <= buy_threshold - 5:
            return "extremely_oversold"
        else:
            return "oversold"
    elif rsi_value >= sell_threshold:
        if rsi_value >= sell_threshold + 5:
            return "extremely_overbought"
        else:
            return "overbought"
    elif 40 <= rsi_value <= 60:
        return "neutral"
    elif rsi_value < 40:
        return "approaching_oversold"
    else:
        return "approaching_overbought"