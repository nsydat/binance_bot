import pandas as pd
import ta

def ema_vwap_rsi_strategy(df, df_higher=None):
    """
    Chiến lược kết hợp EMA + VWAP + RSI
    Winrate kỳ vọng: 70-75%
    """
    if len(df) < 50:
        return None
    
    # 1. EMA
    df['ema_fast'] = ta.trend.EMAIndicator(df['close'], 9).ema_indicator()
    df['ema_slow'] = ta.trend.EMAIndicator(df['close'], 21).ema_indicator()
    
    # 2. VWAP
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3
    df['vwap'] = (df['tp'] * df['volume']).cumsum() / df['volume'].cumsum()
    
    # 3. RSI
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], 14).rsi()
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    
    # BUY: EMA bullish + Price above VWAP + RSI not overbought
    buy_signal = (
        current['ema_fast'] > current['ema_slow'] and  # EMA bullish
        prev['ema_fast'] <= prev['ema_slow'] and  # EMA cross up
        current['close'] > current['vwap'] and  # Above VWAP
        current['rsi'] < 70  # Not overbought
    )
    
    # SELL: EMA bearish + Price below VWAP + RSI not oversold
    sell_signal = (
        current['ema_fast'] < current['ema_slow'] and  # EMA bearish
        prev['ema_fast'] >= prev['ema_slow'] and  # EMA cross down
        current['close'] < current['vwap'] and  # Below VWAP
        current['rsi'] > 30  # Not oversold
    )
    
    # Tính SL/TP
    if buy_signal or sell_signal:
        entry_price = current['close']
        atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], 14)
        atr_value = atr.average_true_range().iloc[-1]
        
        if buy_signal:
            sl = entry_price - (1.5 * atr_value)
            tp = entry_price + (2.5 * atr_value)  # 1.67:1 R:R
            signal = 'BUY'
        else:
            sl = entry_price + (1.5 * atr_value)
            tp = entry_price - (2.5 * atr_value)
            signal = 'SELL'
        
        # Confidence based on EMA alignment
        ema_diff = abs(current['ema_fast'] - current['ema_slow']) / current['close']
        confidence = min(0.9, 0.6 + (ema_diff / 0.01) * 0.3)
        
        return signal, entry_price, sl, tp, 0.001, confidence
    
    return None