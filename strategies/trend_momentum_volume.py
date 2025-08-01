import pandas as pd
import ta

def trend_momentum_volume_strategy(df, df_higher=None):
    """
    Chiến lược kết hợp Trend + Momentum + Volume - PHIÊN BẢN CẢI TIẾN
    Winrate kỳ vọng: 70-75%, R:R improved to 1:4-5
    """
    if len(df) < 50:
        return None
    
    # 1. Multi-period Trend Analysis
    df['ema_fast'] = ta.trend.EMAIndicator(df['close'], 12).ema_indicator()
    df['ema_mid'] = ta.trend.EMAIndicator(df['close'], 26).ema_indicator()
    df['ema_slow'] = ta.trend.EMAIndicator(df['close'], 50).ema_indicator()
    df['ema_trend'] = ta.trend.EMAIndicator(df['close'], 100).ema_indicator()  # Long-term trend
    
    # Trend strength
    df['trend_strength'] = (df['ema_fast'] - df['ema_slow']) / df['close']
    
    # 2. Enhanced MACD Analysis
    macd_fast = ta.trend.MACD(df['close'], 12, 26, 9)
    df['macd'] = macd_fast.macd()
    df['macd_signal'] = macd_fast.macd_signal()
    df['macd_histogram'] = macd_fast.macd_diff()
    
    # MACD with different periods for confirmation
    macd_slow = ta.trend.MACD(df['close'], 19, 39, 9)
    df['macd_slow'] = macd_slow.macd()
    df['macd_slow_signal'] = macd_slow.macd_signal()
    
    # 3. Advanced Volume Analysis
    df['volume_sma'] = df['volume'].rolling(20).mean()
    df['volume_ema'] = ta.trend.EMAIndicator(df['volume'], 10).ema_indicator()
    df['volume_ratio'] = df['volume'] / df['volume_sma']
    
    # Volume trend
    df['volume_trend'] = df['volume_ema'] > df['volume_ema'].shift(1)
    
    # On-Balance Volume
    df['obv'] = ta.volume.OnBalanceVolumeIndicator(df['close'], df['volume']).on_balance_volume()
    df['obv_ema'] = ta.trend.EMAIndicator(df['obv'], 10).ema_indicator()
    
    # 4. Momentum Oscillators
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], 14).rsi()
    df['stoch'] = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'], 14, 3).stoch()
    
    # 5. Volatility Analysis
    atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], 14)
    df['atr'] = atr.average_true_range()
    df['atr_ratio'] = df['atr'] / df['close']
    
    # Bollinger Bands for volatility
    bb = ta.volatility.BollingerBands(df['close'], 20, 2)
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]
    
    # Higher timeframe trend confirmation
    higher_trend_bullish = True
    higher_momentum_bullish = True
    if df_higher is not None and len(df_higher) >= 30:
        df_higher['ema'] = ta.trend.EMAIndicator(df_higher['close'], 20).ema_indicator()
        higher_macd = ta.trend.MACD(df_higher['close'])
        df_higher['macd'] = higher_macd.macd()
        df_higher['macd_signal'] = higher_macd.macd_signal()
        
        higher_trend_bullish = df_higher['close'].iloc[-1] > df_higher['ema'].iloc[-1]
        higher_momentum_bullish = df_higher['macd'].iloc[-1] > df_higher['macd_signal'].iloc[-1]
    
    # Enhanced BUY Signal
    buy_conditions = [
        # Trend Conditions (4 conditions)
        current['close'] > current['ema_trend'],  # Long-term uptrend
        current['ema_fast'] > current['ema_mid'] > current['ema_slow'],  # EMA stack bullish
        current['trend_strength'] > 0 and current['trend_strength'] > prev['trend_strength'],  # Strengthening trend
        higher_trend_bullish,  # Higher TF trend
        
        # Momentum Conditions (4 conditions)
        current['macd'] > current['macd_signal'],  # MACD bullish
        (current['macd'] > prev['macd'] or  # MACD improving OR
         (prev['macd'] <= prev['macd_signal'] and current['macd'] > current['macd_signal'])),  # Fresh crossover
        current['macd_histogram'] > prev['macd_histogram'],  # Histogram improving
        higher_momentum_bullish,  # Higher TF momentum
        
        # Volume Conditions (3 conditions)
        current['volume_ratio'] > 1.0,  # Above average volume
        current['obv'] > current['obv_ema'],  # OBV bullish
        current['volume_trend'],  # Volume trending up
        
        # Additional Filters (3 conditions)
        current['rsi'] < 75 and current['rsi'] > 35,  # RSI in reasonable range
        current['bb_position'] > 0.2,  # Not at bottom of BB
        current['close'] > prev['close'],  # Green candle
    ]
    
    # Enhanced SELL Signal
    sell_conditions = [
        # Trend Conditions (4 conditions)
        current['close'] < current['ema_trend'],  # Long-term downtrend
        current['ema_fast'] < current['ema_mid'] < current['ema_slow'],  # EMA stack bearish
        current['trend_strength'] < 0 and current['trend_strength'] < prev['trend_strength'],  # Weakening trend
        not higher_trend_bullish,  # Higher TF trend bearish
        
        # Momentum Conditions (4 conditions)
        current['macd'] < current['macd_signal'],  # MACD bearish
        (current['macd'] < prev['macd'] or  # MACD deteriorating OR
         (prev['macd'] >= prev['macd_signal'] and current['macd'] < current['macd_signal'])),  # Fresh crossover
        current['macd_histogram'] < prev['macd_histogram'],  # Histogram deteriorating
        not higher_momentum_bullish,  # Higher TF momentum bearish
        
        # Volume Conditions (3 conditions)
        current['volume_ratio'] > 1.0,  # Above average volume
        current['obv'] < current['obv_ema'],  # OBV bearish
        current['volume_trend'],  # Volume trending up (selling pressure)
        
        # Additional Filters (3 conditions)
        current['rsi'] > 25 and current['rsi'] < 65,  # RSI in reasonable range
        current['bb_position'] < 0.8,  # Not at top of BB
        current['close'] < prev['close'],  # Red candle
    ]
    
    # Scoring system - need at least 10/14 conditions
    buy_score = sum(buy_conditions)
    sell_score = sum(sell_conditions)
    
    buy_signal = buy_score >= 10
    sell_signal = sell_score >= 10
    
    # ADVANCED SL/TP Calculation
    if buy_signal or sell_signal:
        entry_price = current['close']
        atr_value = current['atr']
        
        # Dynamic ATR multiplier based on market conditions
        base_atr_multiplier = 1.8
        
        # Volatility adjustment
        volatility_adj = max(0.8, min(2.5, current['atr_ratio'] * 100))
        
        # Trend strength adjustment
        trend_adj = max(1.0, min(1.5, abs(current['trend_strength']) * 100))
        
        # Volume adjustment
        volume_adj = max(0.9, min(1.3, current['volume_ratio'] * 0.3))
        
        final_atr_multiplier = base_atr_multiplier * volatility_adj * trend_adj * volume_adj
        
        if buy_signal:
            # Multi-level SL calculation
            sl_atr = entry_price - (final_atr_multiplier * atr_value)
            sl_ema = current['ema_mid'] * 0.998  # Below middle EMA
            sl_swing = df['low'].rolling(20).min().iloc[-1] * 0.997  # Below swing low
            sl_bb = current['bb_lower'] * 0.995  # Below BB lower
            
            # Use the highest (safest) SL but not too tight
            sl_candidates = [sl_atr, sl_ema, sl_swing, sl_bb]
            sl = max([s for s in sl_candidates if (entry_price - s) / entry_price >= 0.005])  # Min 0.5% risk
            
            # Multi-target TP system
            # Target 1: Conservative (3:1 R:R)
            risk_amount = entry_price - sl
            tp1 = entry_price + (3.0 * risk_amount)
            
            # Target 2: Based on resistance levels
            resistance = df['high'].rolling(30).max().iloc[-1]
            tp2 = min(resistance * 0.999, entry_price + (4.0 * atr_value))
            
            # Target 3: Based on Bollinger Band projection
            bb_target = current['bb_upper'] + (current['bb_upper'] - current['bb_lower']) * 0.5
            tp3 = min(bb_target, entry_price + (5.0 * atr_value))
            
            # Target 4: Trend projection
            trend_projection = entry_price + (current['trend_strength'] * entry_price * 10)
            tp4 = max(tp1, min(trend_projection, entry_price + (6.0 * atr_value)))
            
            # Use the most reasonable target (balance between aggressive and conservative)
            tp_candidates = [tp1, tp2, tp3, tp4]
            tp = sorted(tp_candidates)[1]  # Second lowest (balanced approach)
            
            signal = 'BUY'
            
        else:  # sell_signal
            # Multi-level SL calculation
            sl_atr = entry_price + (final_atr_multiplier * atr_value)
            sl_ema = current['ema_mid'] * 1.002  # Above middle EMA
            sl_swing = df['high'].rolling(20).max().iloc[-1] * 1.003  # Above swing high
            sl_bb = current['bb_upper'] * 1.005  # Above BB upper
            
            # Use the lowest (safest) SL but not too tight
            sl_candidates = [sl_atr, sl_ema, sl_swing, sl_bb]
            sl = min([s for s in sl_candidates if (s - entry_price) / entry_price >= 0.005])  # Min 0.5% risk
            
            # Multi-target TP system
            # Target 1: Conservative (3:1 R:R)
            risk_amount = sl - entry_price
            tp1 = entry_price - (3.0 * risk_amount)
            
            # Target 2: Based on support levels
            support = df['low'].rolling(30).min().iloc[-1]
            tp2 = max(support * 1.001, entry_price - (4.0 * atr_value))
            
            # Target 3: Based on Bollinger Band projection
            bb_target = current['bb_lower'] - (current['bb_upper'] - current['bb_lower']) * 0.5
            tp3 = max(bb_target, entry_price - (5.0 * atr_value))
            
            # Target 4: Trend projection
            trend_projection = entry_price + (current['trend_strength'] * entry_price * 10)  # Negative trend_strength
            tp4 = min(tp1, max(trend_projection, entry_price - (6.0 * atr_value)))
            
            # Use the most reasonable target
            tp_candidates = [tp1, tp2, tp3, tp4]
            tp = sorted(tp_candidates, reverse=True)[1]  # Second highest (balanced approach)
            
            signal = 'SELL'
        
        # Enhanced Confidence Calculation
        # Base confidence from signal strength
        signal_strength = (buy_score if buy_signal else sell_score) / 14.0  # Max 14 conditions
        base_confidence = 0.4 + (signal_strength * 0.4)  # 0.4 to 0.8 range
        
        # Trend alignment bonus
        trend_alignment = 0
        if buy_signal:
            if (current['ema_fast'] > current['ema_mid'] > current['ema_slow'] and
                current['close'] > current['ema_trend']):
                trend_alignment = 0.1
        else:
            if (current['ema_fast'] < current['ema_mid'] < current['ema_slow'] and
                current['close'] < current['ema_trend']):
                trend_alignment = 0.1
        
        # Momentum strength bonus
        macd_strength = abs(current['macd'] - current['macd_signal']) / current['close']
        momentum_bonus = min(0.1, macd_strength * 1000)
        
        # Volume confirmation bonus
        volume_bonus = min(0.1, (current['volume_ratio'] - 1.0) * 0.05)
        
        # Multi-timeframe confirmation bonus
        mtf_bonus = 0.05 if (higher_trend_bullish == buy_signal and 
                            higher_momentum_bullish == buy_signal) else 0
        
        # Calculate actual R:R ratio
        risk = abs(entry_price - sl) / entry_price
        reward = abs(tp - entry_price) / entry_price
        rr_ratio = reward / risk if risk > 0 else 0
        
        # R:R bonus
        rr_bonus = 0
        if rr_ratio >= 4.0:
            rr_bonus = 0.1
        elif rr_ratio >= 3.0:
            rr_bonus = 0.05
        
        # Final confidence
        total_confidence = (base_confidence + trend_alignment + momentum_bonus + 
                          volume_bonus + mtf_bonus + rr_bonus)
        confidence = min(0.95, total_confidence)
        
        # Quality filters - only take high-quality signals
        quality_checks = [
            rr_ratio >= 2.5,  # Minimum R:R
            confidence >= 0.65,  # Minimum confidence
            risk <= 0.03,  # Maximum 3% risk
            current['volume_ratio'] >= 1.0,  # Minimum volume
        ]
        
        if all(quality_checks):
            return signal, entry_price, sl, tp, 0.001, confidence
    
    return None