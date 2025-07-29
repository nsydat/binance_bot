# strategies/macd_signal.py
import pandas as pd
import ta
import numpy as np

def strategy_macd_signal(df, df_higher=None):
    """
    Chiến lược MACD với histogram divergence và trend confirmation
    """
    # Chuẩn bị dữ liệu
    for col in ['close', 'high', 'low', 'volume']:
        df[col] = pd.to_numeric(df[col])
    
    # MACD
    macd = ta.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_histogram'] = macd.macd_diff()
    
    # EMA trend filter
    df['ema20'] = ta.trend.EMAIndicator(df['close'], window=20).ema_indicator()
    df['ema50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
    
    # RSI filter
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    
    # Volume confirmation
    df['volume_sma'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma']
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]
    
    # Higher timeframe confirmation
    higher_tf_trend = 'NEUTRAL'
    if df_higher is not None and len(df_higher) > 50:
        df_higher['ema20'] = ta.trend.EMAIndicator(pd.to_numeric(df_higher['close']), window=20).ema_indicator()
        df_higher['ema50'] = ta.trend.EMAIndicator(pd.to_numeric(df_higher['close']), window=50).ema_indicator()
        higher_current = df_higher.iloc[-1]
        if higher_current['ema20'] > higher_current['ema50']:
            higher_tf_trend = 'BULLISH'
        elif higher_current['ema20'] < higher_current['ema50']:
            higher_tf_trend = 'BEARISH'
    
    # MACD Bullish Signal
    macd_bullish_cross = (current['macd'] > current['macd_signal'] and 
                         prev['macd'] <= prev['macd_signal'])
    
    histogram_increasing = (current['macd_histogram'] > prev['macd_histogram'] and
                           prev['macd_histogram'] > prev2['macd_histogram'])
    
    buy_conditions = [
        macd_bullish_cross,                    # MACD cross up
        current['macd'] < 0,                   # MACD dưới 0 (oversold)
        histogram_increasing,                   # Histogram tăng
        current['close'] > current['ema20'],   # Trend filter
        current['rsi'] > 35 and current['rsi'] < 65,  # RSI filter
        current['volume_ratio'] > 1.0,        # Volume confirmation
        higher_tf_trend in ['BULLISH', 'NEUTRAL']  # Higher TF confirmation
    ]
    
    # MACD Bearish Signal
    macd_bearish_cross = (current['macd'] < current['macd_signal'] and 
                         prev['macd'] >= prev['macd_signal'])
    
    histogram_decreasing = (current['macd_histogram'] < prev['macd_histogram'] and
                           prev['macd_histogram'] < prev2['macd_histogram'])
    
    sell_conditions = [
        macd_bearish_cross,                    # MACD cross down
        current['macd'] > 0,                   # MACD trên 0 (overbought)
        histogram_decreasing,                   # Histogram giảm
        current['close'] < current['ema20'],   # Trend filter
        current['rsi'] > 35 and current['rsi'] < 65,  # RSI filter
        current['volume_ratio'] > 1.0,        # Volume confirmation
        higher_tf_trend in ['BEARISH', 'NEUTRAL']  # Higher TF confirmation
    ]
    
    def calculate_confidence(conditions, macd_strength):
        base_score = sum(conditions) / len(conditions)
        
        # MACD strength bonus
        macd_bonus = min(abs(macd_strength) * 0.1, 0.2)
        
        # Volume bonus
        volume_bonus = min((current['volume_ratio'] - 1) * 0.1, 0.15)
        
        return min(base_score + macd_bonus + volume_bonus, 1.0)
    
    # BUY Signal
    if sum(buy_conditions) >= 5:
        entry = current['close']
        atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], 14).average_true_range().iloc[-1]
        
        sl = entry - (2.0 * atr)
        tp = entry + (2.5 * (entry - sl))
        
        macd_strength = abs(current['macd'] - current['macd_signal'])
        confidence = calculate_confidence(buy_conditions, macd_strength)
        
        return 'BUY', entry, sl, tp, 0.001, confidence
    
    # SELL Signal
    elif sum(sell_conditions) >= 5:
        entry = current['close']
        atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], 14).average_true_range().iloc[-1]
        
        sl = entry + (2.0 * atr)
        tp = entry - (2.5 * (sl - entry))
        
        macd_strength = abs(current['macd'] - current['macd_signal'])
        confidence = calculate_confidence(sell_conditions, macd_strength)
        
        return 'SELL', entry, sl, tp, 0.001, confidence
    
    return None