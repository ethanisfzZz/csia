"""
Trading engine module for the crypto trading bot.
Handles trading signals, position management, and trade execution with improved MACD logic.

Citations:
- MACD trading strategy: https://www.investopedia.com/terms/m/macd.asp
- RSI technical analysis: https://www.investopedia.com/terms/r/rsi.asp
- Stop loss/take profit concepts: https://www.investopedia.com/terms/s/stop-lossorder.asp
"""

from file_manager import get_current_position_from_orders, append_order_to_csv, get_historical_data
from technical_indicators import (
    check_macd_crossover, get_macd_trend_strength, analyze_rsi_condition
)

def check_trading_signals_with_thresholds(market_data, thresholds):
    """
    Enhanced trading signal detection with intuitive MACD logic and RSI confirmation.
    
    Trading Logic:
    1. Check stop loss/take proof first (if position exists) - risk management priority
    2. For new positions: Require both RSI and MACD confirmation to reduce false signals
    3. MACD crossovers are primary signals, RSI provides confirmation
    4. Thresholds act as additional filters
    """
    # basic validation - ensure we have data and trading is enabled
    if (market_data is None or not thresholds['active']):
        return "NO_SIGNAL", False
    
    current_price = market_data['price']
    
    # get our current trading position from order history
    current_position, last_trade_price = get_current_position_from_orders()
    
    # STEP 1: prioritize risk management - check exits before entries
    if current_position and last_trade_price:
        stop_loss_signal, should_execute_stop = check_stop_loss_take_profit(
            current_position, current_price, last_trade_price, thresholds
        )
        if should_execute_stop:
            return stop_loss_signal, True
    
    # STEP 2: only look for new positions if we're not already in one
    if current_position is None:
        signal, should_execute = check_new_position_signals(market_data, thresholds)
        return signal, should_execute
    
    return "HOLD", False

def check_stop_loss_take_profit(current_position, current_price, last_trade_price, thresholds):
    """
    Check stop loss and take profit conditions for existing positions.
    Uses percentage-based thresholds for consistent risk management.
    """
    if current_position == 'LONG':
        # stop loss: price fell below our threshold
        if current_price <= last_trade_price * (1 - thresholds['stop_loss']):
            loss_pct = ((last_trade_price - current_price) / last_trade_price) * 100
            print(f"💥 Stop Loss Triggered! LONG position down {loss_pct:.2f}%")
            return "SELL_STOP_LOSS", True
        
        # take profit: price rose above our target
        if current_price >= last_trade_price * (1 + thresholds['stop_profit']):
            profit_pct = ((current_price - last_trade_price) / last_trade_price) * 100
            print(f"💰 Take Profit Triggered! LONG position up {profit_pct:.2f}%")
            return "SELL_TAKE_PROFIT", True
    
    elif current_position == 'SHORT':
        # stop loss: price rose above our threshold (bad for short)
        if current_price >= last_trade_price * (1 + thresholds['stop_loss']):
            loss_pct = ((current_price - last_trade_price) / last_trade_price) * 100
            print(f"💥 Stop Loss Triggered! SHORT position down {loss_pct:.2f}%")
            return "BUY_STOP_LOSS", True
        
        # take profit: price fell below our target (good for short)
        if current_price <= last_trade_price * (1 - thresholds['stop_profit']):
            profit_pct = ((last_trade_price - current_price) / last_trade_price) * 100
            print(f"💰 Take Profit Triggered! SHORT position up {profit_pct:.2f}%")
            return "BUY_TAKE_PROFIT", True
    
    return "HOLD", False

def check_new_position_signals(market_data, thresholds):
    """
    Check for new position entry signals using enhanced MACD and RSI logic.
    Combines multiple indicators to reduce false signals and improve accuracy.
    """
    rsi = market_data['rsi']
    macd = market_data['macd']
    signal_line = market_data['signal_line']
    
    # ensure we have all required indicators before making decisions
    if None in [rsi, macd, signal_line]:
        return "NO_SIGNAL", False
    
    historical_data = get_historical_data()
    
    # get MACD crossover info - key for trend detection
    bullish_cross, bearish_cross, crossover_strength = check_macd_crossover(
        historical_data, macd, signal_line
    )
    
    # analyze current market conditions
    macd_trend = get_macd_trend_strength(macd, signal_line)
    rsi_condition = analyze_rsi_condition(rsi, thresholds['rsi_buy_threshold'], thresholds['rsi_sell_threshold'])
    
    # check buy conditions with detailed reasoning
    buy_signal, buy_reason = check_buy_conditions(
        rsi, macd, signal_line, bullish_cross, crossover_strength, 
        macd_trend, rsi_condition, thresholds
    )
    
    if buy_signal:
        print(f"📈 BUY Signal: {buy_reason}")
        return "BUY_SIGNAL", True
    
    # check sell conditions with detailed reasoning
    sell_signal, sell_reason = check_sell_conditions(
        rsi, macd, signal_line, bearish_cross, crossover_strength,
        macd_trend, rsi_condition, thresholds
    )
    
    if sell_signal:
        print(f"📉 SELL Signal: {sell_reason}")
        return "SELL_SIGNAL", True
    
    # log current conditions for debugging - helps with strategy optimization
    print(f"Market Analysis - RSI: {rsi:.1f} ({rsi_condition}), MACD: {macd_trend}, "
          f"Crossover: {crossover_strength or 'none'}")
    
    return "HOLD", False

def check_buy_conditions(rsi, macd, signal_line, bullish_cross, crossover_strength, 
                        macd_trend, rsi_condition, thresholds):
    """
    Check all conditions for a BUY signal with detailed reasoning.
    Uses multi-factor confirmation to improve signal quality.
    """
    # primary condition: MACD bullish crossover - trend change indicator
    if bullish_cross:
        # strong crossover + oversold RSI = high confidence signal
        if (crossover_strength == "strong" and 
            rsi_condition in ["oversold", "extremely_oversold"] and
            macd > thresholds['macd_buy_threshold']):
            return True, f"Strong bullish MACD crossover + RSI oversold ({rsi:.1f})"
        
        # weak crossover but very oversold = still worth taking
        if (rsi_condition == "extremely_oversold" and 
            macd > thresholds['macd_buy_threshold']):
            return True, f"MACD bullish crossover + Extremely oversold RSI ({rsi:.1f})"
    
    # secondary condition: strong trend + oversold condition
    if (macd_trend == "strong_bullish" and 
        rsi_condition in ["oversold", "extremely_oversold"] and
        macd > thresholds['macd_buy_threshold']):
        return True, f"Strong bullish MACD trend + RSI oversold ({rsi:.1f})"
    
    return False, ""

def check_sell_conditions(rsi, macd, signal_line, bearish_cross, crossover_strength,
                         macd_trend, rsi_condition, thresholds):
    """
    Check all conditions for a SELL signal with detailed reasoning.
    Mirror logic of buy conditions but for bearish scenarios.
    """
    # primary condition: MACD bearish crossover - trend reversal indicator
    if bearish_cross:
        # strong crossover + overbought RSI = high confidence sell signal
        if (crossover_strength == "strong" and 
            rsi_condition in ["overbought", "extremely_overbought"] and
            macd < thresholds['macd_sell_threshold']):
            return True, f"Strong bearish MACD crossover + RSI overbought ({rsi:.1f})"
        
        # weak crossover but very overbought = still worth selling
        if (rsi_condition == "extremely_overbought" and 
            macd < thresholds['macd_sell_threshold']):
            return True, f"MACD bearish crossover + Extremely overbought RSI ({rsi:.1f})"
    
    # secondary condition: strong bearish trend + overbought
    if (macd_trend == "strong_bearish" and 
        rsi_condition in ["overbought", "extremely_overbought"] and
        macd < thresholds['macd_sell_threshold']):
        return True, f"Strong bearish MACD trend + RSI overbought ({rsi:.1f})"
    
    return False, ""

def execute_trade(signal, market_data, thresholds):
    """
    Execute a trade based on the signal and log it to order.csv.
    Handles the actual trade execution and record keeping.
    """
    # only execute actual trading signals
    if not any(signal.endswith(suffix) for suffix in ['_SIGNAL', '_LOSS', '_PROFIT']):
        return
    
    current_price = market_data['price']
    trade_size = thresholds['trade_size']
    
    # determine if we're buying or selling based on signal type
    if signal.startswith('BUY'):
        side = 'BUY'
    else:
        side = 'SELL'
    
    quantity = trade_size
    
    # create structured order data for CSV logging
    order_data = {
        'datetime': market_data['datetime'],
        'side': side,
        'price': current_price,
        'quantity': quantity,
        'trade_size': trade_size
    }
    
    # log the trade to CSV for record keeping
    append_order_to_csv(order_data)
    
    # enhanced logging with trade type classification
    trade_type = signal.replace('_SIGNAL', '').replace('_LOSS', ' STOP').replace('_PROFIT', ' PROFIT')
    print(f"🚨 TRADE EXECUTED: {trade_type} - {side} {quantity} at ${current_price:,.2f}")
    
    # calculate and display position value for portfolio tracking
    position_value = quantity * current_price
    print(f"💵 Position Value: ${position_value:,.2f}")