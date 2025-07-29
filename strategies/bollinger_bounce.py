# strategies/bollinger_bounce.py
import pandas as pd
import ta
import numpy as np

def strategy_bollinger_bounce(df, df_higher=None):
    """
    Chiến lược Bollinger Bands bounce với mean reversion
    - BUY: Giá chạm Lower Band + quá bán (RSI) + xác nhận từ khung lớn hơn
    - SELL: Giá chạm Upper Band + quá mua (RSI) + xác nhận từ khung lớn hơn
    - Dùng độ dốc của band để phát hiện "squeeze"
    """
    # Tính Bollinger Bands
    bb = ta.volatility.BollingerBands(close=df['close'], window=20, window_dev=2)
    df['bb_high'] = bb.bollinger_hband()
    df['bb_low'] = bb.bollinger_lband()
    df['bb_mid'] = bb.bollinger_mavg()
    df['bb_width'] = bb.bollinger_wband()  # Độ rộng band - phát hiện Squeeze
    df['bb_percent'] = bb.bollinger_pband()  # % giá so với band (0-1)

    # Tính RSI
    rsi_indicator = ta.momentum.RSIIndicator(close=df['close'], window=14)
    df['rsi'] = rsi_indicator.rsi()

    current = df.iloc[-1]
    prev = df.iloc[-2]

    # Xác nhận xu hướng từ khung thời gian lớn hơn (nếu có)
    trend_confirmation = True
    if df_higher is not None and len(df_higher) > 20:
        higher_bb = ta.volatility.BollingerBands(df_higher['close'], window=20, window_dev=2)
        higher_rsi = ta.momentum.RSIIndicator(df_higher['close'], window=14).rsi()
        higher_current = df_higher.iloc[-1]
        
        # Chỉ vào lệnh nếu khung lớn hơn đang ở vùng quá bán/quá mua
        if current['close'] < current['bb_low']:
            trend_confirmation = higher_current['close'] > higher_bb.bollinger_lband().iloc[-1] and higher_rsi.iloc[-1] < 40
        elif current['close'] > current['bb_high']:
            trend_confirmation = higher_current['close'] < higher_bb.bollinger_hband().iloc[-1] and higher_rsi.iloc[-1] > 60

    # Phát hiện "Squeeze" - band co hẹp → sắp có biến động
    bb_width_ma = df['bb_width'].rolling(20).mean()
    is_squeeze = current['bb_width'] < bb_width_ma.iloc[-1] * 0.8  # Band đang hẹp hơn 20%

    # Điều kiện BUY: Giá chạm Lower Band + RSI quá bán + bật lên
    if (current['close'] <= current['bb_low'] * 1.005 and  # chạm hoặc xuyên nhẹ
        prev['close'] > prev['bb_low'] and                # trước đó chưa chạm
        current['rsi'] < 30 and                           # quá bán
        current['close'] > current['bb_mid'] * 0.99 and   # đang bật lên khỏi đáy
        trend_confirmation):

        entry = current['close']
        sl = current['bb_low'] * 0.99  # dưới đáy band
        tp = entry + 2 * (entry - sl)
        qty = 0.001
        # Tăng độ tin cậy nếu có squeeze
        confidence = 0.7 + (0.15 if is_squeeze else 0.0) + (0.1 if current['volume'] > df['volume'].mean() else 0)
        return 'BUY', entry, sl, tp, qty, min(confidence, 1.0)

    # Điều kiện SELL: Giá chạm Upper Band + RSI quá mua + rớt xuống
    elif (current['close'] >= current['bb_high'] * 0.995 and
          prev['close'] < prev['bb_high'] and
          current['rsi'] > 70 and
          current['close'] < current['bb_mid'] * 1.01 and
          trend_confirmation):

        entry = current['close']
        sl = current['bb_high'] * 1.01  # trên đỉnh band
        tp = entry - 2 * (sl - entry)
        qty = 0.001
        confidence = 0.7 + (0.15 if is_squeeze else 0.0) + (0.1 if current['volume'] > df['volume'].mean() else 0)
        return 'SELL', entry, sl, tp, qty, min(confidence, 1.0)

    return None