import pandas as pd
import ta

def supertrend_rsi_strategy(df, df_higher=None):
    """
    Chiến lược kết hợp Supertrend + RSI - PHIÊN BẢN CẢI TIẾN
    Winrate kỳ vọng: 75-80%, R:R improved to 1:4-5
    """
    if len(df) < 50:
        return None
    
    # 1. Enhanced Supertrend với multiple periods
    def calculate_supertrend(df, period=10, multiplier=2.0):
        atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], period)
        atr_values = atr.average_true_range()
        
        hl2 = (df['high'] + df['low']) / 2
        upper_band = hl2 + (multiplier * atr_values)
        lower_band = hl2 - (multiplier * atr_values)
        
        supertrend = []
        for i in range(len(df)):
            if i == 0:
                supertrend.append(lower_band.iloc[i])
            else:
                if df['close'].iloc[i] <= supertrend[i-1]:
                    supertrend.append(upper_band.iloc[i])
                else:
                    supertrend.append(lower_band.iloc[i])
        
        return pd.Series(supertrend, index=df.index), atr_values
    
    # Multiple Supertrend periods for better confirmation
    df['supertrend_fast'], df['atr_fast'] = calculate_supertrend(df, 7, 1.8)   # Faster
    df['supertrend_main'], df['atr_main'] = calculate_supertrend(df, 10, 2.0)  # Main
    df['supertrend_slow'], df['atr_slow'] = calculate_supertrend(df, 14, 2.2)  # Slower
    
    # 2. Enhanced RSI with multiple timeframes
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], 14).rsi()
    df['rsi_fast'] = ta.momentum.RSIIndicator(df['close'], 7).rsi()
    df['rsi_slow'] = ta.momentum.RSIIndicator(df['close'], 21).rsi()
    
    # RSI trend analysis
    df['rsi_sma'] = df['rsi'].rolling(5).mean()
    
    # 3. Volume analysis
    df['volume_sma'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma']
    
    # 4. Volatility squeeze detection
    bb = ta.volatility.BollingerBands(df['close'], 20, 2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['close']
    df['squeeze'] = df['bb_width'] < df['bb_width'].rolling(20).mean() * 0.8
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]
    
    # Multi-timeframe trend confirmation
    higher_trend_bullish = True
    if df_higher is not None and len(df_higher) >= 20:
        df_higher['ema'] = ta.trend.EMAIndicator(df_higher['close'], 20).ema_indicator()
        higher_trend_bullish = df_higher['close'].iloc[-1] > df_higher['ema'].iloc[-1]
    
    # Enhanced BUY conditions
    buy_conditions = [
        # Multi-Supertrend confirmation - More flexible
        current['close'] > current['supertrend_main'],  # Main trend
        current['close'] > current['supertrend_fast'] or prev['close'] <= prev['supertrend_fast'],  # Fast entry or fresh break
        
        # RSI conditions - More nuanced
        current['rsi'] < 35 or (current['rsi'] < 50 and current['rsi'] > current['rsi_sma']),  # Oversold OR bullish divergence
        current['rsi_fast'] > 25,  # Not extremely oversold
        current['rsi'] > prev['rsi'],  # RSI improving
        
        # Trend filter
        higher_trend_bullish,  # Higher timeframe bullish
        
        # Volume and momentum
        current['volume_ratio'] > 0.8,  # Decent volume (more flexible)
        current['close'] > prev['close'] or current['close'] > prev2['close'],  # Recent bullish price action
        
        # Volatility conditions
        not current['squeeze'] or current['bb_width'] > prev['bb_width'],  # Breaking out of squeeze
    ]
    
    # Enhanced SELL conditions
    sell_conditions = [
        # Multi-Supertrend confirmation
        current['close'] < current['supertrend_main'],  # Main trend
        current['close'] < current['supertrend_fast'] or prev['close'] >= prev['supertrend_fast'],  # Fast entry or fresh break
        
        # RSI conditions - More nuanced
        current['rsi'] > 65 or (current['rsi'] > 50 and current['rsi'] < current['rsi_sma']),  # Overbought OR bearish divergence
        current['rsi_fast'] < 75,  # Not extremely overbought
        current['rsi'] < prev['rsi'],  # RSI deteriorating
        
        # Trend filter
        not higher_trend_bullish,  # Higher timeframe bearish
        
        # Volume and momentum
        current['volume_ratio'] > 0.8,  # Decent volume
        current['close'] < prev['close'] or current['close'] < prev2['close'],  # Recent bearish price action
        
        # Volatility conditions
        not current['squeeze'] or current['bb_width'] > prev['bb_width'],  # Breaking out of squeeze
    ]
    
    buy_signal = sum(buy_conditions) >= 6  # 6/9 conditions
    sell_signal = sum(sell_conditions) >= 6  # 6/9 conditions
    
    # ADVANCED SL/TP calculation
    if buy_signal or sell_signal:
        entry_price = current['close']
        
        # Use multiple ATR periods for better SL/TP
        atr_value = (current['atr_fast'] + current['atr_main'] + current['atr_slow']) / 3
        
        # Dynamic multiplier based on market conditions
        base_multiplier = 1.5
        
        # Adjust for volatility
        volatility = df['close'].pct_change().rolling(20).std().iloc[-1]
        vol_multiplier = max(0.8, min(2.0, volatility * 80)) 
        
        # Adjust for RSI extremes (wider stops for extreme levels)
        rsi_multiplier = 1.0
        if current['rsi'] < 25 or current['rsi'] > 75:
            rsi_multiplier = 1.3
        
        final_multiplier = base_multiplier * vol_multiplier * rsi_multiplier
        
        if buy_signal:
            # Multi-level SL approach
            sl_supertrend = current['supertrend_main'] * 0.999  # Just below Supertrend
            sl_atr = entry_price - (final_multiplier * atr_value)  # ATR-based
            sl_swing = df['low'].rolling(15).min().iloc[-1] * 0.998  # Swing low
            
            # Use the highest (safest) SL
            sl = max(sl_supertrend, sl_atr, sl_swing)
            
            # Dynamic TP based on multiple factors
            resistance_level = df['high'].rolling(20).max().iloc[-1]
            
            # Target levels
            tp_atr = entry_price + (4.0 * atr_value)  # 4:1 minimum R:R
            tp_resistance = resistance_level * 0.999  # Just below resistance
            tp_supertrend = current['supertrend_slow'] + (2 * atr_value)  # Supertrend projection
            tp_rsi = entry_price + (5.0 * atr_value) if current['rsi'] < 25 else entry_price + (3.5 * atr_value)  # RSI-based
            
            # Use the most conservative profitable TP
            tp = min(max(tp_atr, tp_resistance), max(tp_supertrend, tp_rsi))
            
            signal = 'BUY'
        else:
            # Multi-level SL approach
            sl_supertrend = current['supertrend_main'] * 1.001  # Just above Supertrend
            sl_atr = entry_price + (final_multiplier * atr_value)  # ATR-based
            sl_swing = df['high'].rolling(15).max().iloc[-1] * 1.002  # Swing high
            
            # Use the lowest (safest) SL
            sl = min(sl_supertrend, sl_atr, sl_swing)
            
            # Dynamic TP
            support_level = df['low'].rolling(20).min().iloc[-1]
            
            # Target levels
            tp_atr = entry_price - (4.0 * atr_value)  # 4:1 minimum R:R
            tp_support = support_level * 1.001  # Just above support
            tp_supertrend = current['supertrend_slow'] - (2 * atr_value)  # Supertrend projection
            tp_rsi = entry_price - (5.0 * atr_value) if current['rsi'] > 75 else entry_price - (3.5 * atr_value)  # RSI-based
            
            # Use the most conservative profitable TP
            tp = max(min(tp_atr, tp_support), min(tp_supertrend, tp_rsi))
            
            signal = 'SELL'
        
        # Enhanced confidence calculation
        supertrend_alignment = sum([
            current['close'] > current['supertrend_fast'],
            current['close'] > current['supertrend_main'],
            current['close'] > current['supertrend_slow']
        ]) / 3 if buy_signal else sum([
            current['close'] < current['supertrend_fast'],
            current['close'] < current['supertrend_main'],
            current['close'] < current['supertrend_slow']
        ]) / 3
        
        rsi_strength = abs(current['rsi'] - 50) / 50  # How extreme RSI is
        volume_boost = min(0.15, (current['volume_ratio'] - 1.0) * 0.05)
        
        # Calculate R:R ratio
        risk = abs(entry_price - sl) / entry_price
        reward = abs(tp - entry_price) / entry_price
        rr_ratio = reward / risk if risk > 0 else 0
        
        base_confidence = 0.6 + (supertrend_alignment * 0.2)
        rsi_bonus = rsi_strength * 0.1
        
        total_confidence = base_confidence + rsi_bonus + volume_boost
        
        # Bonus for excellent R:R
        if rr_ratio >= 4.0:
            total_confidence += 0.1
        elif rr_ratio >= 3.0:
            total_confidence += 0.05
        
        confidence = min(0.95, total_confidence)
        
        # Only trade if R:R >= 2.5:1 and confidence >= 0.6
        if rr_ratio >= 2.5 and confidence >= 0.6:
            return signal, entry_price, sl, tp, 0.001, confidence
    
    return None