# strategies/rsi_divergence.py - IMPROVED VERSION
import pandas as pd
import ta
import numpy as np

def strategy_rsi_divergence(df, df_higher=None):
    """
    Chiến lược RSI Divergence nâng cấp với multiple confirmations
    - Thêm nhiều loại divergence patterns
    - Volume và momentum confirmation
    - Multi-timeframe validation
    """
    if len(df) < 100:
        return None
        
    # Chuẩn bị dữ liệu
    for col in ['close', 'high', 'low', 'volume']:
        df[col] = pd.to_numeric(df[col])

    # Tính các oscillators
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df['rsi_smooth'] = df['rsi'].rolling(3).mean()  # RSI smooth để giảm noise
    
    # Stochastic RSI
    stoch_rsi = ta.momentum.StochRSIIndicator(df['close'])
    df['stoch_rsi_k'] = stoch_rsi.stochrsi_k()
    df['stoch_rsi_d'] = stoch_rsi.stochrsi_d()
    
    # MACD để xác nhận momentum
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_histogram'] = macd.macd_diff()
    
    # EMA để filter trend
    df['ema20'] = ta.trend.EMAIndicator(df['close'], window=20).ema_indicator()
    df['ema50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
    df['ema100'] = ta.trend.EMAIndicator(df['close'], window=100).ema_indicator()
    
    # Volume analysis
    df['volume_sma'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma']
    
    # ATR cho volatility
    df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], 14).average_true_range()
    
    # Bollinger Bands position
    bb = ta.volatility.BollingerBands(df['close'])
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    df['bb_position'] = (df['close'] - bb.bollinger_lband()) / (bb.bollinger_hband() - bb.bollinger_lband())

    # Advanced peak/valley detection với multiple windows
    def find_peaks_valleys_advanced(price_series, rsi_series, window=7, min_periods=20):
        """Tìm peaks/valleys với validation tốt hơn"""
        peaks_price = []
        valleys_price = []
        peaks_rsi = []
        valleys_rsi = []
        
        for i in range(window, len(price_series) - window):
            # Price peaks/valleys
            is_price_peak = all(price_series.iloc[i] >= price_series.iloc[i-j] for j in range(1, window+1)) and \
                           all(price_series.iloc[i] >= price_series.iloc[i+j] for j in range(1, window+1))
            is_price_valley = all(price_series.iloc[i] <= price_series.iloc[i-j] for j in range(1, window+1)) and \
                             all(price_series.iloc[i] <= price_series.iloc[i+j] for j in range(1, window+1))
            
            # RSI peaks/valleys
            is_rsi_peak = all(rsi_series.iloc[i] >= rsi_series.iloc[i-j] for j in range(1, window+1)) and \
                         all(rsi_series.iloc[i] >= rsi_series.iloc[i+j] for j in range(1, window+1))
            is_rsi_valley = all(rsi_series.iloc[i] <= rsi_series.iloc[i-j] for j in range(1, window+1)) and \
                           all(rsi_series.iloc[i] <= rsi_series.iloc[i+j] for j in range(1, window+1))
            
            if is_price_peak:
                peaks_price.append(i)
            if is_price_valley:
                valleys_price.append(i)
            if is_rsi_peak:
                peaks_rsi.append(i)
            if is_rsi_valley:
                valleys_rsi.append(i)
        
        return peaks_price, valleys_price, peaks_rsi, valleys_rsi

    # Tìm peaks và valleys
    peaks_price, valleys_price, peaks_rsi, valleys_rsi = find_peaks_valleys_advanced(
        df['high'], df['rsi_smooth'], window=5
    )
    
    current = df.iloc[-1]
    current_idx = len(df) - 1
    
    # Higher timeframe confirmation
    higher_tf_bullish = True
    higher_tf_bearish = True
    
    if df_higher is not None and len(df_higher) > 50:
        higher_rsi = ta.momentum.RSIIndicator(pd.to_numeric(df_higher['close']), window=14).rsi()
        higher_ema20 = ta.trend.EMAIndicator(pd.to_numeric(df_higher['close']), window=20).ema_indicator()
        higher_ema50 = ta.trend.EMAIndicator(pd.to_numeric(df_higher['close']), window=50).ema_indicator()
        
        higher_current = df_higher.iloc[-1]
        
        higher_tf_bullish = (higher_ema20.iloc[-1] > higher_ema50.iloc[-1] and 
                            higher_rsi.iloc[-1] < 70)
        higher_tf_bearish = (higher_ema20.iloc[-1] < higher_ema50.iloc[-1] and 
                            higher_rsi.iloc[-1] > 30)
    
    # Tìm Bullish Divergence (RSI tăng trong khi giá giảm)
    def check_bullish_divergence():
        if len(valleys_price) < 2 or len(valleys_rsi) < 2:
            return False, 0
            
        # Tìm 2 đáy gần nhất
        recent_valleys_price = [v for v in valleys_price if current_idx - v <= 50]  # Trong 50 candles
        recent_valleys_rsi = [v for v in valleys_rsi if current_idx - v <= 50]
        
        if len(recent_valleys_price) < 2 or len(recent_valleys_rsi) < 2:
            return False, 0
            
        # Lấy 2 đáy gần nhất
        valley1_price_idx = recent_valleys_price[-2]
        valley2_price_idx = recent_valleys_price[-1]
        valley1_rsi_idx = recent_valleys_rsi[-2]
        valley2_rsi_idx = recent_valleys_rsi[-1]
        
        # Kiểm tra divergence: giá thấp hơn, RSI cao hơn
        price_lower = df['low'].iloc[valley2_price_idx] < df['low'].iloc[valley1_price_idx]
        rsi_higher = df['rsi_smooth'].iloc[valley2_rsi_idx] > df['rsi_smooth'].iloc[valley1_rsi_idx]
        
        # Kiểm tra RSI trong vùng oversold
        rsi_oversold = df['rsi_smooth'].iloc[valley2_rsi_idx] < 40
        
        # Tính strength của divergence
        price_diff = (df['low'].iloc[valley1_price_idx] - df['low'].iloc[valley2_price_idx]) / df['low'].iloc[valley1_price_idx]
        rsi_diff = df['rsi_smooth'].iloc[valley2_rsi_idx] - df['rsi_smooth'].iloc[valley1_rsi_idx]
        
        strength = (price_diff * 100 + rsi_diff) / 2  # Combined strength score
        
        return (price_lower and rsi_higher and rsi_oversold), strength
    
    # Tìm Bearish Divergence (RSI giảm trong khi giá tăng)
    def check_bearish_divergence():
        if len(peaks_price) < 2 or len(peaks_rsi) < 2:
            return False, 0
            
        # Tìm 2 đỉnh gần nhất
        recent_peaks_price = [p for p in peaks_price if current_idx - p <= 50]
        recent_peaks_rsi = [p for p in peaks_rsi if current_idx - p <= 50]
        
        if len(recent_peaks_price) < 2 or len(recent_peaks_rsi) < 2:
            return False, 0
            
        # Lấy 2 đỉnh gần nhất
        peak1_price_idx = recent_peaks_price[-2]
        peak2_price_idx = recent_peaks_price[-1]
        peak1_rsi_idx = recent_peaks_rsi[-2]
        peak2_rsi_idx = recent_peaks_rsi[-1]
        
        # Kiểm tra divergence: giá cao hơn, RSI thấp hơn
        price_higher = df['high'].iloc[peak2_price_idx] > df['high'].iloc[peak1_price_idx]
        rsi_lower = df['rsi_smooth'].iloc[peak2_rsi_idx] < df['rsi_smooth'].iloc[peak1_rsi_idx]
        
        # Kiểm tra RSI trong vùng overbought
        rsi_overbought = df['rsi_smooth'].iloc[peak2_rsi_idx] > 60
        
        # Tính strength của divergence
        price_diff = (df['high'].iloc[peak2_price_idx] - df['high'].iloc[peak1_price_idx]) / df['high'].iloc[peak1_price_idx]
        rsi_diff = df['rsi_smooth'].iloc[peak1_rsi_idx] - df['rsi_smooth'].iloc[peak2_rsi_idx]
        
        strength = (price_diff * 100 + rsi_diff) / 2
        
        return (price_higher and rsi_lower and rsi_overbought), strength
    
    # Kiểm tra divergences
    bullish_div, bull_strength = check_bullish_divergence()
    bearish_div, bear_strength = check_bearish_divergence()
    
    # === BULLISH DIVERGENCE SIGNAL ===
    if bullish_div:
        buy_conditions = [
            bullish_div,                                    # Có bullish divergence
            current['rsi'] < 50,                           # RSI không quá cao
            current['stoch_rsi_k'] < 0.3,                  # Stoch RSI oversold
            current['close'] > current['ema20'],           # Giá bắt đầu phục hồi
            current['macd_histogram'] > df['macd_histogram'].iloc[-2],  # MACD histogram cải thiện
            current['volume_ratio'] > 1.0,                # Volume confirmation
            current['bb_position'] < 0.3,                 # Gần BB lower
            bull_strength > 2,                             # Divergence đủ mạnh
            higher_tf_bullish,                             # TF cao hơn support
            current['close'] > df['close'].iloc[-3],       # Giá đang recovery
            current['atr'] / current['close'] < 0.03       # Volatility không quá cao
        ]
        
        if sum(buy_conditions) >= 8:  # Cần 8/11 điều kiện
            entry = current['close']
            
            # SL dưới recent swing low hoặc BB lower
            recent_swing_low = min(df['low'].iloc[-20:])
            sl_swing = recent_swing_low * 0.995
            sl_bb = current['bb_lower'] * 0.99
            sl = max(sl_swing, sl_bb)
            
            # TP dựa trên R:R và resistance levels
            risk = entry - sl
            tp_rr = entry + (2.5 * risk)
            tp_bb = current['bb_upper'] * 0.98
            tp = min(tp_rr, tp_bb)
            
            # Confidence dựa trên strength và conditions
            confidence = 0.4 + (sum(buy_conditions) - 8) * 0.05 + (bull_strength / 10)
            confidence = min(confidence, 0.85)
            
            return 'BUY', entry, sl, tp, 0.001, confidence
    
    # === BEARISH DIVERGENCE SIGNAL ===
    if bearish_div:
        sell_conditions = [
            bearish_div,                                    # Có bearish divergence
            current['rsi'] > 50,                           # RSI không quá thấp
            current['stoch_rsi_k'] > 0.7,                  # Stoch RSI overbought
            current['close'] < current['ema20'],           # Giá bắt đầu suy yếu
            current['macd_histogram'] < df['macd_histogram'].iloc[-2],  # MACD histogram xấu đi
            current['volume_ratio'] > 1.0,                # Volume confirmation
            current['bb_position'] > 0.7,                 # Gần BB upper
            bear_strength > 2,                             # Divergence đủ mạnh
            higher_tf_bearish,                             # TF cao hơn support
            current['close'] < df['close'].iloc[-3],       # Giá đang decline
            current['atr'] / current['close'] < 0.03       # Volatility không quá cao
        ]
        
        if sum(sell_conditions) >= 8:  # Cần 8/11 điều kiện
            entry = current['close']
            
            # SL trên recent swing high hoặc BB upper
            recent_swing_high = max(df['high'].iloc[-20:])
            sl_swing = recent_swing_high * 1.005
            sl_bb = current['bb_upper'] * 1.01
            sl = min(sl_swing, sl_bb)
            
            # TP dựa trên R:R và support levels
            risk = sl - entry
            tp_rr = entry - (2.5 * risk)
            tp_bb = current['bb_lower'] * 1.02
            tp = max(tp_rr, tp_bb)
            
            # Confidence dựa trên strength và conditions
            confidence = 0.4 + (sum(sell_conditions) - 8) * 0.05 + (bear_strength / 10)
            confidence = min(confidence, 0.85)
            
            return 'SELL', entry, sl, tp, 0.001, confidence

    return None