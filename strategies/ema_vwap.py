# strategies/ema_vwap.py
import pandas as pd
import ta

def strategy_ema_vwap(df):
    df['close'] = pd.to_numeric(df['close'])
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])
    df['volume'] = pd.to_numeric(df['volume'])

    # EMA 20
    df['ema20'] = ta.trend.EMAIndicator(df['close'], window=20).ema_indicator()

    # VWAP
    df['vwap'] = ta.volume.VolumeWeightedAveragePrice(
        df['high'], df['low'], df['close'], df['volume']
    ).volume_weighted_average_price()

    current = df.iloc[-1]
    prev = df.iloc[-2]

    # Tín hiệu BUY
    if current['close'] > current['ema20'] and current['vwap'] < current['close'] and prev['close'] <= prev['vwap']:
        entry = current['close']
        sl = df['low'].rolling(10).min().iloc[-1] * 0.99
        tp = entry + 2 * (entry - sl)
        qty = 0.001  # Sẽ tính theo % sau
        return 'BUY', entry, sl, tp, qty

    # Tín hiệu SELL
    elif current['close'] < current['ema20'] and current['vwap'] > current['close'] and prev['close'] >= prev['vwap']:
        entry = current['close']
        sl = df['high'].rolling(10).max().iloc[-1] * 1.01
        tp = entry - 2 * (sl - entry)
        qty = 0.001
        return 'SELL', entry, sl, tp, qty

    return None