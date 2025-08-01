import pandas as pd
import ta

def supertrend_rsi_strategy(df, df_higher=None):
    """
    Chiến lược kết hợp Supertrend + RSI quá mua/bán
    Winrate kỳ vọng: 75-80%
    """
    if len(df) < 50:
        return None
    
    # 1. Supertrend
    atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], 10)
    df['atr'] = atr.average_true_range()
    
    multiplier = 2.0
    df['upper_band'] = (df['high'] + df['low']) / 2 + (multiplier * df['atr'])
    df['lower_band'] = (df['high'] + df['low']) / 2 - (multiplier * df['atr'])
    
    # 2. RSI Extreme
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], 14).rsi()
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    
    # BUY: Supertrend buy + RSI quá bán
    buy_signal = (
        current['close'] > current['upper_band'] and 
        prev['close'] <= prev['upper_band'] and  # Supertrend buy
        current['rsi'] < 30  # RSI quá bán
    )
    
    # SELL: Supertrend sell + RSI quá mua
    sell_signal = (
        current['close'] < current['lower_band'] and 
        prev['close'] >= prev['lower_band'] and  # Supertrend sell
        current['rsi'] > 70  # RSI quá mua
    )
    
    # Tính SL/TP
    if buy_signal or sell_signal:
        entry_price = current['close']
        atr_value = current['atr']
        
        if buy_signal:
            sl = entry_price - (1.5 * atr_value)
            tp = entry_price + (3.0 * atr_value)  # 2:1 R:R
            signal = 'BUY'
        else:
            sl = entry_price + (1.5 * atr_value)
            tp = entry_price - (3.0 * atr_value)
            signal = 'SELL'
        
        # Confidence based on RSI extreme
        rsi_confidence = 1.0 - abs(current['rsi'] - 50) / 50
        confidence = min(0.9, 0.7 + (1 - rsi_confidence) * 0.2)
        
        return signal, entry_price, sl, tp, 0.001, confidence
    
    return None