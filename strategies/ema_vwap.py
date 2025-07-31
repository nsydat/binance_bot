# strategies/ema_vwap.py - Phiên bản cải tiến NÂNG CAP
import pandas as pd
import ta
import numpy as np

def strategy_ema_vwap(df, df_higher=None):
    """
    Chiến lược EMA + VWAP cải tiến với filtering nghiêm ngặt hơn
    - Thêm trend strength filter
    - Confirmation từ nhiều timeframe
    - Risk management tốt hơn
    """
    if len(df) < 100:
        return None
        
    # Đảm bảo dữ liệu số
    for col in ['close', 'high', 'low', 'volume']:
        df[col] = pd.to_numeric(df[col])
    
    # Tính các EMA với nhiều period
    df['ema9'] = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator()
    df['ema21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
    df['ema50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
    df['ema100'] = ta.trend.EMAIndicator(df['close'], window=100).ema_indicator()
    
    # VWAP
    df['vwap'] = ta.volume.VolumeWeightedAveragePrice(
        df['high'], df['low'], df['close'], df['volume']
    ).volume_weighted_average_price()
    
    # VWAP bands để xác định support/resistance
    vwap_std = df['close'].rolling(20).std()
    df['vwap_upper'] = df['vwap'] + (1.5 * vwap_std)
    df['vwap_lower'] = df['vwap'] - (1.5 * vwap_std)
    
    # RSI và Stochastic để tránh vùng cực
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
    df['stoch_k'] = stoch.stoch()
    
    # MACD để xác nhận momentum
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_histogram'] = macd.macd_diff()
    
    # Volume analysis nâng cao
    df['volume_sma20'] = df['volume'].rolling(20).mean()
    df['volume_sma50'] = df['volume'].rolling(50).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma20']
    df['volume_trend'] = df['volume_sma20'] / df['volume_sma50']
    
    # ATR cho volatility
    df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], 14).average_true_range()
    df['atr_ratio'] = df['atr'] / df['close']
    
    # Bollinger Bands
    bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    df['bb_mid'] = bb.bollinger_mavg()
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]
    
    # Tính trend strength
    ema_alignment_bull = (current['ema9'] > current['ema21'] > current['ema50'] > current['ema100'])
    ema_alignment_bear = (current['ema9'] < current['ema21'] < current['ema50'] < current['ema100'])
    
    # VWAP trend
    vwap_bullish = current['vwap'] > prev['vwap'] > prev2['vwap']
    vwap_bearish = current['vwap'] < prev['vwap'] < prev2['vwap']
    
    # Higher timeframe confirmation
    higher_tf_bullish = True
    higher_tf_bearish = True
    
    if df_higher is not None and len(df_higher) > 50:
        # Tính EMA và VWAP cho TF cao hơn
        higher_ema21 = ta.trend.EMAIndicator(pd.to_numeric(df_higher['close']), window=21).ema_indicator()
        higher_ema50 = ta.trend.EMAIndicator(pd.to_numeric(df_higher['close']), window=50).ema_indicator()
        higher_vwap = ta.volume.VolumeWeightedAveragePrice(
            pd.to_numeric(df_higher['high']), 
            pd.to_numeric(df_higher['low']), 
            pd.to_numeric(df_higher['close']), 
            pd.to_numeric(df_higher['volume'])
        ).volume_weighted_average_price()
        
        higher_current = df_higher.iloc[-1]
        higher_prev = df_higher.iloc[-2]
        
        higher_tf_bullish = (pd.to_numeric(higher_current['close']) > higher_ema21.iloc[-1] > higher_ema50.iloc[-1] and
                            higher_vwap.iloc[-1] > higher_vwap.iloc[-2])
        higher_tf_bearish = (pd.to_numeric(higher_current['close']) < higher_ema21.iloc[-1] < higher_ema50.iloc[-1] and
                            higher_vwap.iloc[-1] < higher_vwap.iloc[-2])
    
    # === ĐIỀU KIỆN BUY NÂNG CAP ===
    buy_conditions = [
        # 1. EMA alignment và trend
        current['close'] > current['ema9'] > current['ema21'],
        current['ema21'] > current['ema50'],  # Trend medium-term
        ema_alignment_bull or (current['ema9'] > current['ema21'] > current['ema50']),  # Strong trend
        
        # 2. VWAP conditions
        current['close'] > current['vwap'],
        vwap_bullish,  # VWAP trending up
        current['close'] > current['vwap_lower'] * 1.01,  # Không quá gần VWAP lower
        
        # 3. Momentum confirmations
        current['macd'] > current['macd_signal'],
        current['macd_histogram'] > prev['macd_histogram'],  # MACD histogram tăng
        
        # 4. Oscillator filters
        current['rsi'] > 40 and current['rsi'] < 70,  # RSI trong vùng tốt
        current['stoch_k'] > 25 and current['stoch_k'] < 80,  # Stoch không cực
        
        # 5. Volume confirmations
        current['volume_ratio'] > 1.2,  # Volume cao hơn bình thường
        current['volume_trend'] > 0.95,  # Volume trend tích cực
        
        # 6. Price position
        current['close'] > current['bb_mid'],  # Trên BB middle
        current['close'] < current['bb_upper'] * 0.98,  # Không quá gần BB upper
        
        # 7. Volatility và risk
        current['atr_ratio'] < 0.03,  # Volatility không quá cao
        
        # 8. Higher timeframe
        higher_tf_bullish
    ]
    
    # === ĐIỀU KIỆN SELL NÂNG CAP ===
    sell_conditions = [
        # 1. EMA alignment và trend
        current['close'] < current['ema9'] < current['ema21'],
        current['ema21'] < current['ema50'],  # Trend medium-term
        ema_alignment_bear or (current['ema9'] < current['ema21'] < current['ema50']),  # Strong trend
        
        # 2. VWAP conditions
        current['close'] < current['vwap'],
        vwap_bearish,  # VWAP trending down
        current['close'] < current['vwap_upper'] * 0.99,  # Không quá gần VWAP upper
        
        # 3. Momentum confirmations
        current['macd'] < current['macd_signal'],
        current['macd_histogram'] < prev['macd_histogram'],  # MACD histogram giảm
        
        # 4. Oscillator filters
        current['rsi'] > 30 and current['rsi'] < 60,  # RSI trong vùng tốt
        current['stoch_k'] > 20 and current['stoch_k'] < 75,  # Stoch không cực
        
        # 5. Volume confirmations
        current['volume_ratio'] > 1.2,  # Volume cao hơn bình thường
        current['volume_trend'] > 0.95,  # Volume trend tích cực
        
        # 6. Price position
        current['close'] < current['bb_mid'],  # Dưới BB middle
        current['close'] > current['bb_lower'] * 1.02,  # Không quá gần BB lower
        
        # 7. Volatility và risk
        current['atr_ratio'] < 0.03,  # Volatility không quá cao
        
        # 8. Higher timeframe
        higher_tf_bearish
    ]
    
    # Tính confidence score
    def calculate_confidence(conditions, signal_type):
        base_score = sum(conditions) / len(conditions)
        
        # Bonus từ trend strength
        trend_bonus = 0
        if signal_type == 'BUY' and ema_alignment_bull:
            trend_bonus += 0.1
        elif signal_type == 'SELL' and ema_alignment_bear:
            trend_bonus += 0.1
            
        # Bonus từ volume
        volume_bonus = min((current['volume_ratio'] - 1.2) * 0.1, 0.15)
        
        # Bonus từ MACD strength
        macd_strength = abs(current['macd'] - current['macd_signal']) / current['close']
        macd_bonus = min(macd_strength * 1000, 0.1)
        
        return min(base_score + trend_bonus + volume_bonus + macd_bonus, 0.95)
    
    # Kiểm tra tín hiệu BUY (cần ít nhất 12/15 điều kiện)
    if sum(buy_conditions) >= 12:
        entry = current['close']
        
        # Dynamic SL/TP dựa trên ATR và EMA
        sl_ema = current['ema21'] * 0.995
        sl_atr = entry - (1.8 * current['atr'])  # Conservative hơn
        sl = max(sl_ema, sl_atr)
        
        # TP conservative với R:R tốt hơn
        risk = entry - sl
        tp_ratio = entry + (2.2 * risk)  # R:R = 2.2:1
        tp_bb = current['bb_upper'] * 0.98
        tp = min(tp_ratio, tp_bb)
        
        confidence = calculate_confidence(buy_conditions, 'BUY')
        
        return 'BUY', entry, sl, tp, 0.001, confidence
    
    # Kiểm tra tín hiệu SELL (cần ít nhất 12/15 điều kiện)
    elif sum(sell_conditions) >= 12:
        entry = current['close']
        
        # Dynamic SL/TP dựa trên ATR và EMA
        sl_ema = current['ema21'] * 1.005
        sl_atr = entry + (1.8 * current['atr'])  # Conservative hơn
        sl = min(sl_ema, sl_atr)
        
        # TP conservative với R:R tốt hơn
        risk = sl - entry
        tp_ratio = entry - (2.2 * risk)  # R:R = 2.2:1
        tp_bb = current['bb_lower'] * 1.02
        tp = max(tp_ratio, tp_bb)
        
        confidence = calculate_confidence(sell_conditions, 'SELL')
        
        return 'SELL', entry, sl, tp, 0.001, confidence
    
    return None