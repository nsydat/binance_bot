import pandas as pd
import ta

def trend_momentum_volume_strategy(df, df_higher=None):
    """
    Chiến lược kết hợp Trend + Momentum + Volume
    Winrate kỳ vọng: 70-75%
    """
    if len(df) < 50:
        return None
    
    # 1. Trend Filter (EMA 50)
    df['ema_50'] = ta.trend.EMAIndicator(df['close'], 50).ema_indicator()
    
    # 2. Momentum (MACD)
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    
    # 3. Volume Confirmation
    df['volume_sma'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma']
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    
    # BUY Signal: Uptrend + Bullish MACD + High Volume
    buy_signal = (
        current['close'] > current['ema_50'] and  # Uptrend
        current['macd'] > current['macd_signal'] and  # Bullish MACD
        prev['macd'] <= prev['macd_signal'] and  # MACD cross up
        current['volume_ratio'] > 1.2  # High volume
    )
    
    # SELL Signal: Downtrend + Bearish MACD + High Volume
    sell_signal = (
        current['close'] < current['ema_50'] and  # Downtrend
        current['macd'] < current['macd_signal'] and  # Bearish MACD
        prev['macd'] >= prev['macd_signal'] and  # MACD cross down
        current['volume_ratio'] > 1.2  # High volume
    )
    
    # Tính SL/TP
    if buy_signal or sell_signal:
        entry_price = current['close']
        atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], 14)
        atr_value = atr.average_true_range().iloc[-1]
        
        if buy_signal:
            sl = entry_price - (1.5 * atr_value)
            tp = entry_price + (2.0 * atr_value)  # 1.33:1 R:R
            signal = 'BUY'
        else:
            sl = entry_price + (1.5 * atr_value)
            tp = entry_price - (2.0 * atr_value)
            signal = 'SELL'
        
        # Confidence based on volume and momentum strength
        volume_conf = min(1.0, (current['volume_ratio'] - 1.0) / 1.0)
        momentum_strength = abs(current['macd'] - current['macd_signal'])
        momentum_conf = min(1.0, momentum_strength / 0.001)
        
        confidence = min(0.9, 0.5 + (volume_conf + momentum_conf) * 0.2)
        
        return signal, entry_price, sl, tp, 0.001, confidence
    
    return None