"""
Data processing module for the crypto trading bot.
Handles market data processing, indicator calculation, and data saving.

Citations:
- Technical analysis indicator calculation: https://www.investopedia.com/terms/t/technicalindicator.asp
- Time series data processing: https://pandas.pydata.org/docs/user_guide/timeseries.html
- Data pipeline patterns: https://realpython.com/python-data-structures/
"""

from file_manager import get_historical_data, append_to_csv
from technical_indicators import calculate_technical_indicators

def create_market_data_with_indicators(raw_data, indicator_window):
    """
    Create complete market data entry with pre-calculated indicators.
    This approach ensures indicators are calculated consistently using historical context.
    """
    if raw_data is None:
        return None
    
    # get historical data needed for indicator calculation
    historical_data = get_historical_data()
    
    # create temporary dataset that includes current data point for calculation
    # this ensures indicators are calculated with the most recent price included
    temp_historical_data = historical_data.copy()
    current_data_point = {
        'datetime': raw_data['datetime'],
        'price': raw_data['price'],
        'volume': raw_data['volume'],
        'rsi': None,  # will be calculated using historical context
        'macd': None,  # will be calculated using historical context
        'signal_line': None  # will be calculated using historical context
    }
    temp_historical_data.append(current_data_point)
    
    # calculate indicators using historical data + current point for accuracy
    rsi, macd, signal_line = calculate_technical_indicators(temp_historical_data, indicator_window)
    
    # create complete market data entry with all indicators populated
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
    """
    Save complete market data (including pre-calculated indicators) to CSV.
    Handles both file persistence and logging for monitoring.
    """
    if market_data is None:
        return False
    
    try:
        # persist data to CSV file for historical analysis
        append_to_csv(market_data)
        
        # create human-readable indicators info for logging
        indicators_info = ""
        if market_data['rsi'] is not None:
            indicators_info += f" | RSI: {market_data['rsi']:.2f}"  # 2 decimal places for readability
        if market_data['macd'] is not None:
            indicators_info += f" | MACD: {market_data['macd']:.6f}"  # 6 decimal places for precision
        if market_data['signal_line'] is not None:
            indicators_info += f" | Signal: {market_data['signal_line']:.6f}"  # 6 decimal places for precision
        
        # log successful save with price, volume, and indicator values
        print(f"Market data saved: Price={market_data['price']}, Volume={market_data['volume']}{indicators_info}")
        return True
        
    except Exception as e:
        print(f"Error saving market data: {e}")
        return False