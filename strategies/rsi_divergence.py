# strategies/rsi_divergence.py
import pandas as pd
import ta

def strategy_rsi_divergence(df, df_higher=None):
    if len(df) < 50:
        return None
    df['close'] = pd.to_numeric(df['close'])
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])

    # Tính RSI
    rsi_indicator = ta.momentum.RSIIndicator(df['close'], window=14)
    df['rsi'] = rsi_indicator.rsi()

    # Tìm đỉnh/đáy gần nhất
    def find_peaks(series, window=5):
        return (series == series.rolling(window, center=True).max())

    def find_valleys(series, window=5):
        return (series == series.rolling(window, center=True).min())

    peaks_price = find_peaks(df['high'], 5)
    valleys_price = find_valleys(df['low'], 5)
    peaks_rsi = find_peaks(df['rsi'], 5)
    valleys_rsi = find_valleys(df['rsi'], 5)

    # Bullish Divergence: Giá tạo đáy thấp hơn, RSI tạo đáy cao hơn
    for i in range(3, len(df) - 1):
        if valleys_price.iloc[i] and valleys_rsi.iloc[i]:
            if df['low'].iloc[i] < df['low'].iloc[i-2] and df['rsi'].iloc[i] > df['rsi'].iloc[i-2]:
                entry = df['close'].iloc[-1]
                sl = df['low'].iloc[i] * 0.99
                tp = entry + 2 * (entry - sl)
                return 'BUY', entry, sl, tp, 0.001, 0.7 

    # Bearish Divergence: Giá tạo đỉnh cao hơn, RSI tạo đỉnh thấp hơn
    for i in range(3, len(df) - 1):
        if peaks_price.iloc[i] and peaks_rsi.iloc[i]:
            if df['high'].iloc[i] > df['high'].iloc[i-2] and df['rsi'].iloc[i] < df['rsi'].iloc[i-2]:
                entry = df['close'].iloc[-1]
                sl = df['high'].iloc[i] * 1.01
                tp = entry - 2 * (sl - entry)
                return 'SELL', entry, sl, tp, 0.001

    return None