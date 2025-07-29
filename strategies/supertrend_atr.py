# strategies/supertrend_atr.py
import pandas as pd
import ta

def strategy_supertrend_atr(df, period=10, multiplier=3):
    df['close'] = pd.to_numeric(df['close'])
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])

    # Tính ATR
    atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], period).average_true_range()
    hl2 = (df['high'] + df['low']) / 2

    upperband = hl2 + multiplier * atr
    lowerband = hl2 - multiplier * atr

    in_uptrend = [True] * len(df)
    for i in range(1, len(df)):
        if df['close'].iloc[i] > upperband.iloc[i-1]:
            in_uptrend[i] = True
        elif df['close'].iloc[i] < lowerband.iloc[i-1]:
            in_uptrend[i] = False
        else:
            in_uptrend[i] = in_uptrend[i-1]

    if in_uptrend[-1] and not in_uptrend[-2]:
        entry = df['close'].iloc[-1]
        sl = lowerband.iloc[-1] * 0.99
        tp = entry + 2 * (entry - sl)
        return 'BUY', entry, sl, tp, 0.001
    elif not in_uptrend[-1] and in_uptrend[-2]:
        entry = df['close'].iloc[-1]
        sl = upperband.iloc[-1] * 1.01
        tp = entry - 2 * (sl - entry)
        return 'SELL', entry, sl, tp, 0.001

    return None