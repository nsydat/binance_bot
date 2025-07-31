# strategies/macd_signal.py - Phiên bản cải tiến
import pandas as pd
import ta
import numpy as np

def strategy_macd_signal(df, df_higher=None):
    """
    Chiến lược MACD cải tiến với:
    - MACD Histogram divergence detection
    - Multi-timeframe confirmation
    - Dynamic SL/TP với ATR
    - Volume và momentum filters
    - Signal strength scoring
    """
    if len(df) < 50:
        return None
        
    # Chuẩn bị dữ liệu
    for col in ['close', 'high', 'low', 'volume']:
        df[col] = pd.to_numeric(df[col])
    
    # MACD với multiple timeframes
    macd = ta.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['macd_histogram'] = macd.macd_diff()
    
    # Tính MACD momentum và slope
    df['macd_momentum'] = df['macd'].diff()
    df['histogram_momentum'] = df['macd_histogram'].diff()
    df['macd_slope'] = df['macd'].rolling(3).apply(lambda x: np.polyfit(range(3), x, 1)[0])
    
    # EMA trend filters với multiple periods
    df['ema9'] = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator()
    df['ema21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
    df['ema50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
    
    # RSI với dynamic levels
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df['rsi_sma'] = df['rsi'].rolling(10).mean()
    
    # Volume analysis
    df['volume_sma'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma']
    df['volume_trend'] = df['volume_sma'].diff() > 0
    
    # ATR cho dynamic SL/TP
    df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], 14).average_true_range()
    df['atr_ratio'] = df['atr'] / df['close']  # Normalized ATR
    
    # Bollinger Bands cho volatility context
    bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]
    prev3 = df.iloc[-4]
    
    # Higher timeframe analysis
    higher_tf_bias = 0  # -1: bearish, 0: neutral, 1: bullish
    higher_tf_strength = 0
    
    if df_higher is not None and len(df_higher) > 50:
        # Tính MACD cho higher timeframe
        higher_macd = ta.trend.MACD(pd.to_numeric(df_higher['close']))
        higher_df = df_higher.copy()
        higher_df['macd'] = higher_macd.macd()
        higher_df['macd_signal'] = higher_macd.macd_signal()
        higher_df['ema21'] = ta.trend.EMAIndicator(pd.to_numeric(df_higher['close']), window=21).ema_indicator()
        higher_df['ema50'] = ta.trend.EMAIndicator(pd.to_numeric(df_higher['close']), window=50).ema_indicator()
        
        higher_current = higher_df.iloc[-1]
        
        # Xác định bias từ higher timeframe
        if (higher_current['macd'] > higher_current['macd_signal'] and 
            higher_current['ema21'] > higher_current['ema50']):
            higher_tf_bias = 1
            higher_tf_strength = abs(higher_current['macd'] - higher_current['macd_signal'])
        elif (higher_current['macd'] < higher_current['macd_signal'] and 
              higher_current['ema21'] < higher_current['ema50']):
            higher_tf_bias = -1
            higher_tf_strength = abs(higher_current['macd'] - higher_current['macd_signal'])
    
    # MACD Signal Detection với cải tiến
    def detect_macd_cross():
        # Classic cross
        bullish_cross = (current['macd'] > current['macd_signal'] and 
                        prev['macd'] <= prev['macd_signal'])
        bearish_cross = (current['macd'] < current['macd_signal'] and 
                        prev['macd'] >= prev['macd_signal'])
        
        # Histogram confirmation
        histogram_bullish = (current['macd_histogram'] > 0 and 
                           current['histogram_momentum'] > 0)
        histogram_bearish = (current['macd_histogram'] < 0 and 
                           current['histogram_momentum'] < 0)
        
        return bullish_cross, bearish_cross, histogram_bullish, histogram_bearish
    
    bullish_cross, bearish_cross, histogram_bullish, histogram_bearish = detect_macd_cross()
    
    # Zero-line cross detection
    macd_above_zero = current['macd'] > 0
    macd_below_zero = current['macd'] < 0
    zero_line_cross_up = current['macd'] > 0 and prev['macd'] <= 0
    zero_line_cross_down = current['macd'] < 0 and prev['macd'] >= 0
    
    # Divergence detection (simplified)
    def check_divergence():
        # Kiểm tra divergence trong 10 nến gần nhất
        price_trend = (current['close'] - prev3['close']) / prev3['close']
        macd_trend = (current['macd'] - prev3['macd']) / abs(prev3['macd'] + 0.0001)
        
        bullish_div = price_trend < -0.01 and macd_trend > 0.05
        bearish_div = price_trend > 0.01 and macd_trend < -0.05
        
        return bullish_div, bearish_div
    
    bullish_divergence, bearish_divergence = check_divergence()
    
    # Enhanced Buy Conditions
    buy_conditions = [
        # MACD signals
        bullish_cross or zero_line_cross_up,                    # Primary signal
        current['macd_slope'] > 0,                              # MACD improving
        histogram_bullish or current['histogram_momentum'] > 0,  # Histogram support
        
        # Trend alignment
        current['close'] > current['ema9'],                     # Short-term trend
        current['ema9'] > current['ema21'] or current['close'] > current['ema21'], # Medium trend
        
        # RSI conditions
        current['rsi'] > 30 and current['rsi'] < 75,           # Not oversold/overbought
        current['rsi'] > current['rsi_sma'],                   # RSI improving
        
        # Volume confirmation
        current['volume_ratio'] > 0.8,                         # Decent volume
        
        # Market structure
        current['bb_position'] > 0.2,                          # Not at bottom of BB
        higher_tf_bias >= 0,                                   # Higher TF not bearish
        
        # Additional filters
        current['atr_ratio'] < 0.05 or current['volume_ratio'] > 1.2  # Low vol or high vol
    ]
    
    # Enhanced Sell Conditions
    sell_conditions = [
        # MACD signals
        bearish_cross or zero_line_cross_down,                  # Primary signal
        current['macd_slope'] < 0,                              # MACD deteriorating
        histogram_bearish or current['histogram_momentum'] < 0,  # Histogram support
        
        # Trend alignment
        current['close'] < current['ema9'],                     # Short-term trend
        current['ema9'] < current['ema21'] or current['close'] < current['ema21'], # Medium trend
        
        # RSI conditions
        current['rsi'] > 25 and current['rsi'] < 70,           # Not oversold/overbought
        current['rsi'] < current['rsi_sma'],                   # RSI deteriorating
        
        # Volume confirmation
        current['volume_ratio'] > 0.8,                         # Decent volume
        
        # Market structure
        current['bb_position'] < 0.8,                          # Not at top of BB
        higher_tf_bias <= 0,                                   # Higher TF not bullish
        
        # Additional filters
        current['atr_ratio'] < 0.05 or current['volume_ratio'] > 1.2  # Low vol or high vol
    ]
    
    # Signal Strength Calculation
    def calculate_signal_strength(conditions, signal_type):
        base_score = sum(conditions) / len(conditions)
        
        # MACD strength bonus
        macd_strength = abs(current['macd'] - current['macd_signal']) / (current['atr'] + 0.0001)
        macd_bonus = min(macd_strength * 0.1, 0.2)
        
        # Volume bonus
        volume_bonus = min((current['volume_ratio'] - 1) * 0.05, 0.15)
        
        # Higher timeframe bonus
        htf_bonus = 0
        if signal_type == 'BUY' and higher_tf_bias > 0:
            htf_bonus = min(higher_tf_strength * 0.1, 0.15)
        elif signal_type == 'SELL' and higher_tf_bias < 0:
            htf_bonus = min(higher_tf_strength * 0.1, 0.15)
        
        # Divergence bonus
        div_bonus = 0
        if (signal_type == 'BUY' and bullish_divergence) or (signal_type == 'SELL' and bearish_divergence):
            div_bonus = 0.1
        
        # Momentum bonus
        momentum_bonus = 0
        if signal_type == 'BUY' and current['macd_momentum'] > 0:
            momentum_bonus = 0.05
        elif signal_type == 'SELL' and current['macd_momentum'] < 0:
            momentum_bonus = 0.05
        
        total_score = base_score + macd_bonus + volume_bonus + htf_bonus + div_bonus + momentum_bonus
        return min(total_score, 1.0)
    
    # Dynamic Position Sizing based on confidence
    def get_position_size(confidence):
        base_size = 0.001
        if confidence > 0.8:
            return base_size * 1.5
        elif confidence > 0.7:
            return base_size * 1.2
        return base_size
    
    # BUY Signal Processing
    buy_score = sum(buy_conditions)
    if buy_score >= 7:  # Require at least 7/11 conditions
        entry = current['close']
        
        # Dynamic SL based on MACD and ATR
        atr_mult = 2.0 if current['atr_ratio'] > 0.03 else 2.5  # Tighter SL in high volatility
        sl_atr = entry - (atr_mult * current['atr'])
        sl_ema = current['ema21'] * 0.995
        sl_macd = entry - abs(current['macd_signal']) * 100  # MACD-based SL
        
        sl = max(sl_atr, sl_ema, sl_macd)  # Use the highest (closest) SL
        
        # Dynamic TP based on risk-reward and market structure
        risk = entry - sl
        rr_ratio = 2.5 if current['atr_ratio'] < 0.02 else 2.0  # Lower RR in high vol
        tp_rr = entry + (rr_ratio * risk)
        tp_bb = current['bb_upper'] * 0.995  # Take profit near BB upper
        
        tp = min(tp_rr, tp_bb)  # Use more conservative TP
        
        confidence = calculate_signal_strength(buy_conditions, 'BUY')
        qty = get_position_size(confidence)
        
        return 'BUY', entry, sl, tp, qty, confidence
    
    # SELL Signal Processing  
    sell_score = sum(sell_conditions)
    if sell_score >= 7:  # Require at least 7/11 conditions
        entry = current['close']
        
        # Dynamic SL based on MACD and ATR
        atr_mult = 2.0 if current['atr_ratio'] > 0.03 else 2.5
        sl_atr = entry + (atr_mult * current['atr'])
        sl_ema = current['ema21'] * 1.005
        sl_macd = entry + abs(current['macd_signal']) * 100
        
        sl = min(sl_atr, sl_ema, sl_macd)  # Use the lowest (closest) SL
        
        # Dynamic TP
        risk = sl - entry
        rr_ratio = 2.5 if current['atr_ratio'] < 0.02 else 2.0
        tp_rr = entry - (rr_ratio * risk)
        tp_bb = current['bb_lower'] * 1.005
        
        tp = max(tp_rr, tp_bb)  # Use more conservative TP
        
        confidence = calculate_signal_strength(sell_conditions, 'SELL')
        qty = get_position_size(confidence)
        
        return 'SELL', entry, sl, tp, qty, confidence
    
    return None