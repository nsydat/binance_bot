# strategies/ema_vwap.py - Phiên bản cải tiến
import pandas as pd
import ta
import numpy as np

def strategy_ema_vwap(df, df_higher=None):
    """
    Chiến lược EMA + VWAP cải tiến với multi-timeframe và adaptive parameters
    """
    # Đảm bảo dữ liệu số
    for col in ['close', 'high', 'low', 'volume']:
        df[col] = pd.to_numeric(df[col])
    
    # Tính các chỉ báo cơ bản
    df['ema9'] = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator()
    df['ema21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
    df['ema50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
    
    # VWAP với nhiều period
    df['vwap'] = ta.volume.VolumeWeightedAveragePrice(
        df['high'], df['low'], df['close'], df['volume']
    ).volume_weighted_average_price()
    
    # RSI để tránh vùng quá mua/quá bán
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    
    # Volume analysis
    df['volume_sma'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma']
    
    # Bollinger Bands để xác định volatility
    bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['close']
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]
    
    # Xác nhận xu hướng từ timeframe cao hơn (nếu có)
    higher_tf_bullish = True
    higher_tf_bearish = True
    
    if df_higher is not None and len(df_higher) > 20:
        df_higher['ema21'] = ta.trend.EMAIndicator(pd.to_numeric(df_higher['close']), window=21).ema_indicator()
        higher_current = df_higher.iloc[-1]
        higher_tf_bullish = pd.to_numeric(higher_current['close']) > higher_current['ema21']
        higher_tf_bearish = pd.to_numeric(higher_current['close']) < higher_current['ema21']
    
    # Điều kiện cơ bản cho BUY
    buy_conditions = [
        current['close'] > current['ema9'],  # Giá trên EMA ngắn hạn
        current['ema9'] > current['ema21'],  # EMA ngắn trên EMA dài
        current['close'] > current['vwap'],  # Giá trên VWAP
        current['vwap'] > prev['vwap'],     # VWAP tăng
        current['rsi'] > 30 and current['rsi'] < 70,  # RSI không ở vùng cực
        current['volume_ratio'] > 1.1,      # Volume tăng
        higher_tf_bullish,                  # Xác nhận từ TF cao hơn
        current['close'] > current['bb_lower'] * 1.01  # Không quá gần Bollinger Lower
    ]
    
    # Điều kiện cơ bản cho SELL
    sell_conditions = [
        current['close'] < current['ema9'],  # Giá dưới EMA ngắn hạn
        current['ema9'] < current['ema21'],  # EMA ngắn dưới EMA dài
        current['close'] < current['vwap'],  # Giá dưới VWAP
        current['vwap'] < prev['vwap'],     # VWAP giảm
        current['rsi'] > 30 and current['rsi'] < 70,  # RSI không ở vùng cực
        current['volume_ratio'] > 1.1,      # Volume tăng
        higher_tf_bearish,                  # Xác nhận từ TF cao hơn
        current['close'] < current['bb_upper'] * 0.99  # Không quá gần Bollinger Upper
    ]
    
    # Tính toán độ tin cậy
    def calculate_confidence(conditions, additional_factors):
        base_confidence = sum(conditions) / len(conditions)
        
        # Điều chỉnh dựa trên các yếu tố bổ sung
        momentum_bonus = 0
        if abs(current['close'] - prev['close']) / prev['close'] > 0.005:  # Momentum mạnh
            momentum_bonus += 0.1
        
        volume_bonus = min((current['volume_ratio'] - 1) * 0.1, 0.2)  # Bonus từ volume
        
        volatility_bonus = 0
        if current['bb_width'] > df['bb_width'].rolling(10).mean().iloc[-1]:  # Volatility cao
            volatility_bonus += 0.05
        
        return min(base_confidence + momentum_bonus + volume_bonus + volatility_bonus, 1.0)
    
    # Kiểm tra tín hiệu BUY
    if sum(buy_conditions) >= 6:  # Ít nhất 6/8 điều kiện
        entry = current['close']
        
        # Dynamic SL/TP dựa trên ATR
        atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], 14).average_true_range().iloc[-1]
        
        # Stop Loss: Dưới EMA21 hoặc 2*ATR, chọn gần hơn
        sl_ema = current['ema21'] * 0.995
        sl_atr = entry - (2 * atr)
        sl = max(sl_ema, sl_atr)  # Chọn SL gần hơn để giảm rủi ro
        
        # Take Profit: 2.5 lần rủi ro hoặc gần BB Upper
        risk = entry - sl
        tp_ratio = entry + (2.5 * risk)
        tp_bb = current['bb_upper'] * 0.99
        tp = min(tp_ratio, tp_bb)  # Chọn TP thực tế hơn
        
        confidence = calculate_confidence(buy_conditions, {
            'momentum': abs(current['close'] - prev['close']) / prev['close'],
            'volume': current['volume_ratio'],
            'trend_strength': (current['ema9'] - current['ema21']) / current['ema21']
        })
        
        return 'BUY', entry, sl, tp, 0.001, confidence
    
    # Kiểm tra tín hiệu SELL
    elif sum(sell_conditions) >= 6:  # Ít nhất 6/8 điều kiện
        entry = current['close']
        
        # Dynamic SL/TP dựa trên ATR
        atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], 14).average_true_range().iloc[-1]
        
        # Stop Loss: Trên EMA21 hoặc 2*ATR, chọn gần hơn
        sl_ema = current['ema21'] * 1.005
        sl_atr = entry + (2 * atr)
        sl = min(sl_ema, sl_atr)  # Chọn SL gần hơn để giảm rủi ro
        
        # Take Profit: 2.5 lần rủi ro hoặc gần BB Lower
        risk = sl - entry
        tp_ratio = entry - (2.5 * risk)
        tp_bb = current['bb_lower'] * 1.01
        tp = max(tp_ratio, tp_bb)  # Chọn TP thực tế hơn
        
        confidence = calculate_confidence(sell_conditions, {
            'momentum': abs(current['close'] - prev['close']) / prev['close'],
            'volume': current['volume_ratio'],
            'trend_strength': (current['ema21'] - current['ema9']) / current['ema9']
        })
        
        return 'SELL', entry, sl, tp, 0.001, confidence
    
    return None