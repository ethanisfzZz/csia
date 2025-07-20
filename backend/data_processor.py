"""
Data processing module for the crypto trading bot.
Handles market data processing, indicator calculation, and data saving.
"""

from file_manager import get_historical_data, append_to_csv
from technical_indicators import calculate_technical_indicators

def create_market_data_with_indicators(raw_data, indicator_window):
    """
    Create complete market data entry with pre-calculated indicators.
    """
    if raw_data is None:
        return None
    
    # Get historical data for indicator calculation
    historical_data = get_historical_data()
    
    # Create a temporary list that includes the current data point for calculation
    # This ensures we calculate indicators including the current price
    temp_historical_data = historical_data.copy()
    current_data_point = {
        'datetime': raw_data['datetime'],
        'price': raw_data['price'],
        'volume': raw_data['volume'],
        'rsi': None,  # Will be calculated
        'macd': None,  # Will be calculated
        'signal_line': None  # Will be calculated
    }
    temp_historical_data.append(current_data_point)
    
    # Calculate indicators using historical data + current point
    rsi, macd, signal_line = calculate_technical_indicators(temp_historical_data, indicator_window)
    
    # Create complete market data entry
    market_data = {
        'datetime': raw_data['datetime'],
        'price': raw_data['price'],
        'volume': raw_data['volume'],
        'rsi': rsi,
        'macd': macd,
        'signal_line': signal_line
    }
    
    return market_data

def save_market_data(market_data):
    """Save complete market data (including pre-calculated indicators) to CSV"""
    if market_data is None:
        return False
    
    try:
        append_to_csv(market_data)
        
        # Create indicators info for logging
        indicators_info = ""
        if market_data['rsi'] is not None:
            indicators_info += f" | RSI: {market_data['rsi']:.2f}"
        if market_data['macd'] is not None:
            indicators_info += f" | MACD: {market_data['macd']:.6f}"
        if market_data['signal_line'] is not None:
            indicators_info += f" | Signal: {market_data['signal_line']:.6f}"
        
        print(f"Market data saved: Price={market_data['price']}, Volume={market_data['volume']}{indicators_info}")
        return True
        
    except Exception as e:
        print(f"Error saving market data: {e}")
        return False