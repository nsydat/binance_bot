# strategies/supertrend_atr.py - Phiên bản cải tiến
import pandas as pd
import ta
import numpy as np

def strategy_supertrend_atr(df, period=10, multiplier=3, df_higher=None):
    """
    Chiến lược SuperTrend cải tiến với:
    - Multi-period SuperTrend analysis
    - Dynamic ATR multiplier
    - Volume và momentum confirmation
    - Trend strength measurement
    - False breakout filtering
    - Multi-timeframe alignment
    """
    if len(df) < 50:
        return None
        
    df = df.reset_index(drop=True)
    
    # Chuẩn bị dữ liệu
    for col in ['close', 'high', 'low', 'volume']:
        df[col] = pd.to_numeric(df[col])
    
    # Multiple SuperTrend periods cho confirmation
    def calculate_supertrend(df, period, multiplier):
        atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], period).average_true_range()
        hl2 = (df['high'] + df['low']) / 2
        
        upperband = hl2 + multiplier * atr
        lowerband = hl2 - multiplier * atr
        
        # Improved SuperTrend calculation với trend persistence
        supertrend = [0] * len(df)
        direction = [1] * len(df)  # 1: uptrend, -1: downtrend
        
        for i in range(1, len(df)):
            # Current bands
            curr_upper = upperband.iloc[i]
            curr_lower = lowerband.iloc[i]
            prev_upper = upperband.iloc[i-1] if i > 0 else curr_upper
            prev_lower = lowerband.iloc[i-1] if i > 0 else curr_lower
            
            # Adjust bands
            if curr_upper < prev_upper or df['close'].iloc[i-1] > prev_upper:
                curr_upper = prev_upper
            if curr_lower > prev_lower or df['close'].iloc[i-1] < prev_lower:
                curr_lower = prev_lower
            
            # Determine direction
            if df['close'].iloc[i] <= curr_lower:
                direction[i] = -1
                supertrend[i] = curr_upper
            elif df['close'].iloc[i] >= curr_upper:
                direction[i] = 1
                supertrend[i] = curr_lower
            else:
                direction[i] = direction[i-1]
                supertrend[i] = supertrend[i-1]
        
        return pd.Series(supertrend), pd.Series(direction), atr, upperband, lowerband
    
    # Calculate multiple SuperTrend periods
    st_short, dir_short, atr_short, upper_short, lower_short = calculate_supertrend(df, 7, 2.5)
    st_medium, dir_medium, atr_medium, upper_medium, lower_medium = calculate_supertrend(df, period, multiplier)
    st_long, dir_long, atr_long, upper_long, lower_long = calculate_supertrend(df, 21, 4.0)
    
    df['st_short'] = st_short
    df['st_medium'] = st_medium
    df['st_long'] = st_long
    df['dir_short'] = dir_short
    df['dir_medium'] = dir_medium  
    df['dir_long'] = dir_long
    df['atr'] = atr_medium
    
    # Trend alignment score
    df['trend_alignment'] = (df['dir_short'] + df['dir_medium'] + df['dir_long']) / 3
    
    # Additional technical indicators
    df['ema9'] = ta.trend.EMAIndicator(df['close'], window=9).ema_indicator()
    df['ema21'] = ta.trend.EMAIndicator(df['close'], window=21).ema_indicator()
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    
    # Volume analysis
    df['volume_sma'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma']
    df['volume_trend'] = df['volume_sma'].rolling(5).apply(lambda x: 1 if x.iloc[-1] > x.iloc[0] else -1)
    
    # Price momentum
    df['momentum'] = df['close'].pct_change(5)
    df['momentum_sma'] = df['momentum'].rolling(10).mean()
    
    # Volatility context
    df['atr_ratio'] = df['atr'] / df['close']
    df['volatility_percentile'] = df['atr_ratio'].rolling(50).rank(pct=True)
    
    # Bollinger Bands for additional context
    bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]
    
    # Higher timeframe analysis
    higher_tf_trend = 0  # -1: bearish, 0: neutral, 1: bullish
    higher_tf_strength = 0
    
    if df_higher is not None and len(df_higher) > 21:
        higher_st, higher_dir, _, _, _ = calculate_supertrend(df_higher.reset_index(drop=True), 14, 3)
        higher_current = df_higher.iloc[-1]
        higher_prev = df_higher.iloc[-2]
        
        if higher_dir.iloc[-1] == 1 and higher_dir.iloc[-2] != 1:
            higher_tf_trend = 1
            higher_tf_strength = abs(pd.to_numeric(higher_current['close']) - higher_st.iloc[-1]) / higher_st.iloc[-1]
        elif higher_dir.iloc[-1] == -1 and higher_dir.iloc[-2] != -1:
            higher_tf_trend = -1
            higher_tf_strength = abs(pd.to_numeric(higher_current['close']) - higher_st.iloc[-1]) / higher_st.iloc[-1]
        else:
            higher_tf_trend = higher_dir.iloc[-1]
    
    # Trend change detection với cải tiến
    def detect_trend_change():
        # Classic SuperTrend signal
        bullish_change = (current['dir_medium'] == 1 and prev['dir_medium'] != 1)
        bearish_change = (current['dir_medium'] == -1 and prev['dir_medium'] != -1)
        
        # Confirmation from multiple timeframes
        multi_tf_bullish = current['trend_alignment'] > 0.33  # At least 2/3 timeframes bullish
        multi_tf_bearish = current['trend_alignment'] < -0.33  # At least 2/3 timeframes bearish
        
        # Momentum confirmation
        momentum_bullish = current['momentum'] > 0 and current['momentum_sma'] > 0
        momentum_bearish = current['momentum'] < 0 and current['momentum_sma'] < 0
        
        return (bullish_change, bearish_change, multi_tf_bullish, multi_tf_bearish, 
                momentum_bullish, momentum_bearish)
    
    (bullish_change, bearish_change, multi_tf_bullish, multi_tf_bearish,
     momentum_bullish, momentum_bearish) = detect_trend_change()
    
    # False breakout filter
    def check_false_breakout():
        # Kiểm tra xem có phải là false breakout không
        price_distance_from_st = abs(current['close'] - current['st_medium']) / current['atr']
        
        # Nếu giá quá gần SuperTrend, có thể là false breakout
        too_close = price_distance_from_st < 0.5
        
        # Kiểm tra volume support
        volume_support = current['volume_ratio'] > 1.0
        
        # Kiểm tra momentum
        momentum_support = abs(current['momentum']) > 0.005
        
        return not too_close and volume_support and momentum_support
    
    valid_breakout = check_false_breakout()
    
    # Dynamic confidence calculation
    def calculate_confidence(signal_type, conditions):
        base_confidence = sum(conditions) / len(conditions)
        
        # Trend alignment bonus
        if signal_type == 'BUY':
            trend_bonus = max(0, current['trend_alignment']) * 0.2
        else:
            trend_bonus = max(0, -current['trend_alignment']) * 0.2
        
        # Volume bonus
        volume_bonus = min((current['volume_ratio'] - 1) * 0.1, 0.15)
        
        # Higher timeframe bonus
        htf_bonus = 0
        if ((signal_type == 'BUY' and higher_tf_trend >= 0) or 
            (signal_type == 'SELL' and higher_tf_trend <= 0)):
            htf_bonus = 0.1
        
        # Volatility bonus (thích ứng với volatility)
        vol_bonus = 0
        if current['volatility_percentile'] > 0.7:  # High volatility
            vol_bonus = 0.05
        elif current['volatility_percentile'] < 0.3:  # Low volatility
            vol_bonus = 0.1
        
        # Distance from SuperTrend bonus
        distance_bonus = min(abs(current['close'] - current['st_medium']) / current['atr'] * 0.05, 0.1)
        
        total_confidence = (base_confidence + trend_bonus + volume_bonus + 
                          htf_bonus + vol_bonus + distance_bonus)
        
        return min(total_confidence, 1.0)
    
    # Enhanced Buy Conditions
    buy_conditions = [
        bullish_change,                                    # Primary SuperTrend signal
        multi_tf_bullish or current['trend_alignment'] > 0, # Multi-timeframe support
        current['close'] > current['ema9'],                # Price above short EMA
        current['rsi'] > 35 and current['rsi'] < 75,      # RSI not extreme
        momentum_bullish,                                  # Momentum support
        current['volume_ratio'] > 0.8,                    # Volume support
        valid_breakout,                                    # Not a false breakout
        current['bb_position'] > 0.1,                     # Not at BB bottom
        higher_tf_trend >= -0.5,                          # Higher TF not strongly bearish
        current['close'] > prev['st_medium'],             # Confirmation close above ST
    ]
    
    # Enhanced Sell Conditions  
    sell_conditions = [
        bearish_change,                                    # Primary SuperTrend signal
        multi_tf_bearish or current['trend_alignment'] < 0, # Multi-timeframe support
        current['close'] < current['ema9'],                # Price below short EMA
        current['rsi'] > 25 and current['rsi'] < 65,      # RSI not extreme
        momentum_bearish,                                  # Momentum support
        current['volume_ratio'] > 0.8,                    # Volume support
        valid_breakout,                                    # Not a false breakout
        current['bb_position'] < 0.9,                     # Not at BB top
        higher_tf_trend <= 0.5,                           # Higher TF not strongly bullish
        current['close'] < prev['st_medium'],             # Confirmation close below ST
    ]
    
    # Dynamic position sizing
    def get_position_size(confidence, volatility_percentile):
        base_size = 0.001
        
        # Reduce size in high volatility
        if volatility_percentile > 0.8:
            vol_multiplier = 0.7
        elif volatility_percentile > 0.6:
            vol_multiplier = 0.85
        else:
            vol_multiplier = 1.0
        
        # Increase size with higher confidence
        if confidence > 0.8:
            conf_multiplier = 1.3
        elif confidence > 0.7:
            conf_multiplier = 1.1
        else:
            conf_multiplier = 1.0
        
        return base_size * vol_multiplier * conf_multiplier
    
    # BUY Signal Processing
    buy_score = sum(buy_conditions)
    if buy_score >= 7:  # Require at least 7/10 conditions
        entry = current['close']
        
        # Dynamic SL - use closest SuperTrend level
        sl_options = [
            current['st_short'] * 0.995,
            current['st_medium'] * 0.995,
            entry - (2.0 * current['atr'])
        ]
        sl = max(sl_options)  # Use highest (closest) SL
        
        # Dynamic TP based on trend strength and volatility
        risk = entry - sl
        
        # Adjust RR based on trend alignment and volatility
        if current['trend_alignment'] > 0.66:  # Strong trend
            rr_ratio = 3.0
        elif current['volatility_percentile'] > 0.7:  # High volatility
            rr_ratio = 2.0
        else:
            rr_ratio = 2.5
        
        tp_rr = entry + (rr_ratio * risk)
        tp_bb = current['bb_upper'] * 0.995
        tp = min(tp_rr, tp_bb)
        
        confidence = calculate_confidence('BUY', buy_conditions)
        qty = get_position_size(confidence, current['volatility_percentile'])
        
        return 'BUY', entry, sl, tp, qty, confidence
    
    # SELL Signal Processing
    sell_score = sum(sell_conditions)
    if sell_score >= 7:  # Require at least 7/10 conditions
        entry = current['close']
        
        # Dynamic SL - use closest SuperTrend level
        sl_options = [
            current['st_short'] * 1.005,
            current['st_medium'] * 1.005,
            entry + (2.0 * current['atr'])
        ]
        sl = min(sl_options)  # Use lowest (closest) SL
        
        # Dynamic TP
        risk = sl - entry
        
        if current['trend_alignment'] < -0.66:  # Strong downtrend
            rr_ratio = 3.0
        elif current['volatility_percentile'] > 0.7:  # High volatility
            rr_ratio = 2.0
        else:
            rr_ratio = 2.5
        
        tp_rr = entry - (rr_ratio * risk)
        tp_bb = current['bb_lower'] * 1.005
        tp = max(tp_rr, tp_bb)
        
        confidence = calculate_confidence('SELL', sell_conditions)
        qty = get_position_size(confidence, current['volatility_percentile'])
        
        return 'SELL', entry, sl, tp, qty, confidence
    
    return None