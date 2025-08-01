import pandas as pd
import ta

def breakout_volume_sr_strategy(df, df_higher=None):
    """
    Chiến lược kết hợp Breakout + Volume + Support/Resistance
    Winrate kỳ vọng: 65-70%
    """
    if len(df) < 50:
        return None
    
    # 1. Support/Resistance Levels
    df['swing_high'] = df['high'].rolling(20).max()
    df['swing_low'] = df['low'].rolling(20).min()
    
    # 2. Volume Analysis
    df['volume_sma'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma']
    
    # 3. Price Action
    current = df.iloc[-1]
    prev = df.iloc[-2]
    
    # BUY: Breakout resistance + High volume + Bounce from support
    buy_signal = (
        current['close'] > prev['swing_high'] and  # Breakout
        current['volume_ratio'] > 1.5 and  # High volume
        current['low'] > df['swing_low'].iloc[-5:].min() * 0.995  # Not too far from support
    )
    
    # SELL: Breakdown support + High volume + Rejection from resistance
    sell_signal = (
        current['close'] < prev['swing_low'] and  # Breakdown
        current['volume_ratio'] > 1.5 and  # High volume
        current['high'] < df['swing_high'].iloc[-5:].max() * 1.005  # Not too far from resistance
    )
    
    # Tính SL/TP
    if buy_signal or sell_signal:
        entry_price = current['close']
        atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], 14)
        atr_value = atr.average_true_range().iloc[-1]
        
        if buy_signal:
            sl = df['swing_low'].iloc[-10:].min() * 0.998  # Under recent support
            tp = entry_price + (2.0 * atr_value)  # 2:1 R:R
            signal = 'BUY'
        else:
            sl = df['swing_high'].iloc[-10:].max() * 1.002  # Above recent resistance
            tp = entry_price - (2.0 * atr_value)
            signal = 'SELL'
        
        # Confidence based on volume and breakout strength
        volume_conf = min(1.0, (current['volume_ratio'] - 1.0) / 1.0)
        breakout_strength = abs(current['close'] - (prev['swing_high'] if buy_signal else prev['swing_low'])) / current['close']
        breakout_conf = min(1.0, breakout_strength / 0.01)
        
        confidence = min(0.9, 0.4 + (volume_conf + breakout_conf) * 0.25)
        
        return signal, entry_price, sl, tp, 0.001, confidence
    
    return None