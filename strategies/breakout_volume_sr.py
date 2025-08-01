import pandas as pd
import ta
import numpy as np

def breakout_volume_sr_strategy(df, df_higher=None):
    """
    Chiến lược kết hợp Breakout + Volume + Support/Resistance - PHIÊN BẢN CẢI TIẾN
    Winrate kỳ vọng: 65-70%, R:R improved to 1:4-6
    """
    if len(df) < 50:
        return None
    
    # 1. Advanced Support/Resistance Detection
    def find_pivots(df, window=10):
        """Find pivot highs and lows"""
        df['pivot_high'] = df['high'].rolling(window*2+1, center=True).max() == df['high']
        df['pivot_low'] = df['low'].rolling(window*2+1, center=True).min() == df['low']
        return df
    
    df = find_pivots(df, 8)
    
    # Get recent pivot levels
    recent_pivots = 20
    pivot_highs = df[df['pivot_high']]['high'].tail(recent_pivots).values
    pivot_lows = df[df['pivot_low']]['low'].tail(recent_pivots).values
    
    # Dynamic S/R levels based on price clustering
    current_price = df['close'].iloc[-1]
    
    # Find resistance levels (within 0.5% to 3% above current price)
    resistance_levels = []
    for high in pivot_highs:
        if current_price < high <= current_price * 1.03:
            resistance_levels.append(high)
    
    # Find support levels (within 0.5% to 3% below current price)
    support_levels = []
    for low in pivot_lows:
        if current_price * 0.97 <= low < current_price:
            support_levels.append(low)
    
    # Get strongest levels (most recent and clustered)
    resistance = max(resistance_levels) if resistance_levels else df['high'].rolling(20).max().iloc[-1]
    support = min(support_levels) if support_levels else df['low'].rolling(20).min().iloc[-1]
    
    # 2. Enhanced Volume Analysis
    df['volume_sma_short'] = df['volume'].rolling(10).mean()
    df['volume_sma_long'] = df['volume'].rolling(30).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma_long']
    df['volume_trend'] = df['volume_sma_short'] / df['volume_sma_long']
    
    # Volume-weighted average price for more context
    df['vwap'] = (df['close'] * df['volume']).rolling(20).sum() / df['volume'].rolling(20).sum()
    
    # On-Balance Volume for institutional flow
    df['obv'] = ta.volume.OnBalanceVolumeIndicator(df['close'], df['volume']).on_balance_volume()
    df['obv_ema'] = ta.trend.EMAIndicator(df['obv'], 10).ema_indicator()
    
    # Accumulation/Distribution Line
    df['ad_line'] = ta.volume.AccDistIndexIndicator(df['high'], df['low'], df['close'], df['volume']).acc_dist_index()
    
    # 3. Breakout Confirmation Indicators
    df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], 14).average_true_range()
    df['bb_upper'] = ta.volatility.BollingerBands(df['close'], 20, 2).bollinger_hband()
    df['bb_lower'] = ta.volatility.BollingerBands(df['close'], 20, 2).bollinger_lband()
    df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['close']
    
    # RSI for momentum confirmation
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], 14).rsi()
    
    # MACD for trend momentum
    macd = ta.trend.MACD(df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]
    
    # 4. Multi-timeframe trend filter
    higher_trend_bullish = True
    if df_higher is not None and len(df_higher) >= 20:
        df_higher['ema'] = ta.trend.EMAIndicator(df_higher['close'], 20).ema_indicator()
        higher_trend_bullish = df_higher['close'].iloc[-1] > df_higher['ema'].iloc[-1]
    
    # 5. Enhanced Breakout Detection
    
    # Calculate breakout strength
    resistance_distance = (resistance - current['close']) / current['close']
    support_distance = (current['close'] - support) / current['close']
    
    # BUY Signal: Resistance Breakout
    buy_breakout_conditions = [
        # Core breakout
        current['close'] > resistance,  # Above resistance
        prev['close'] <= resistance * 1.001,  # Previous candle was below/at resistance
        
        # Breakout strength
        (current['close'] - resistance) / current['close'] >= 0.002,  # At least 0.2% breakout
        current['close'] > prev['high'],  # New high
        
        # Volume confirmation
        current['volume_ratio'] >= 1.3,  # 30% above average volume
        current['volume'] > prev['volume'],  # Increasing volume
        current['volume_trend'] > 1.05,  # Volume trend improving
        
        # Institutional flow
        current['obv'] > current['obv_ema'],  # OBV bullish
        current['ad_line'] > prev['ad_line'],  # Accumulation
        
        # Price action
        current['close'] > current['vwap'],  # Above VWAP
        current['close'] > current['open'],  # Green candle
        
        # Momentum confirmation
        current['rsi'] > 50 and current['rsi'] < 80,  # Bullish but not overbought
        current['macd'] > current['macd_signal'],  # MACD bullish
        
        # Multi-timeframe
        higher_trend_bullish,  # Higher TF bullish
        
        # Volatility
        current['bb_width'] > df['bb_width'].rolling(20).mean().iloc[-1],  # Expanding volatility
    ]
    
    # SELL Signal: Support Breakdown
    sell_breakout_conditions = [
        # Core breakout
        current['close'] < support,  # Below support
        prev['close'] >= support * 0.999,  # Previous candle was above/at support
        
        # Breakout strength
        (support - current['close']) / current['close'] >= 0.002,  # At least 0.2% breakdown
        current['close'] < prev['low'],  # New low
        
        # Volume confirmation
        current['volume_ratio'] >= 1.3,  # 30% above average volume
        current['volume'] > prev['volume'],  # Increasing volume
        current['volume_trend'] > 1.05,  # Volume trend confirming
        
        # Institutional flow
        current['obv'] < current['obv_ema'],  # OBV bearish
        current['ad_line'] < prev['ad_line'],  # Distribution
        
        # Price action
        current['close'] < current['vwap'],  # Below VWAP
        current['close'] < current['open'],  # Red candle
        
        # Momentum confirmation
        current['rsi'] < 50 and current['rsi'] > 20,  # Bearish but not oversold
        current['macd'] < current['macd_signal'],  # MACD bearish
        
        # Multi-timeframe
        not higher_trend_bullish,  # Higher TF bearish
        
        # Volatility
        current['bb_width'] > df['bb_width'].rolling(20).mean().iloc[-1],  # Expanding volatility
    ]
    
    # Scoring system - need at least 10/14 conditions
    buy_score = sum(buy_breakout_conditions)
    sell_score = sum(sell_breakout_conditions)
    
    buy_signal = buy_score >= 10
    sell_signal = sell_score >= 10
    
    # 6. ADVANCED SL/TP System
    if buy_signal or sell_signal:
        entry_price = current['close']
        atr_value = current['atr']
        
        # Dynamic ATR multiplier based on volatility and volume
        base_multiplier = 1.5
        vol_multiplier = max(1.0, min(2.0, current['volume_ratio'] * 0.5))
        bb_multiplier = max(1.0, min(1.8, current['bb_width'] * 50))
        
        final_multiplier = base_multiplier * vol_multiplier * bb_multiplier
        
        if buy_signal:
            # Multi-level SL for breakouts
            # SL 1: Just below breakout level
            sl_breakout = resistance * 0.998  # 0.2% below resistance
            
            # SL 2: ATR-based
            sl_atr = entry_price - (final_multiplier * atr_value)
            
            # SL 3: Previous swing low
            sl_swing = df['low'].rolling(15).min().iloc[-1] * 0.997
            
            # SL 4: VWAP support
            sl_vwap = current['vwap'] * 0.998
            
            # Use the highest (safest) but reasonable SL
            sl_candidates = [sl_breakout, sl_atr, sl_swing, sl_vwap]
            sl = max([s for s in sl_candidates if (entry_price - s) / entry_price <= 0.025])  # Max 2.5% risk
            
            # Multi-target TP system
            # TP 1: Next resistance level or measured move
            next_resistance = max([r for r in resistance_levels if r > entry_price] + [entry_price * 1.05])
            measured_move = entry_price + (resistance - support)  # Classic breakout target
            tp1 = min(next_resistance, measured_move)
            
            # TP 2: ATR-based (4:1 R:R minimum)
            risk = entry_price - sl
            tp2 = entry_price + (4.0 * risk)
            
            # TP 3: Bollinger Band projection
            bb_range = current['bb_upper'] - current['bb_lower']
            tp3 = current['bb_upper'] + (bb_range * 0.5)
            
            # TP 4: Volume-weighted target
            volume_strength = min(2.0, current['volume_ratio'])
            tp4 = entry_price + (volume_strength * 2.0 * atr_value)
            
            # Choose balanced target
            tp_candidates = [tp1, tp2, tp3, tp4]
            tp = sorted(tp_candidates)[1]  # Second lowest (balanced)
            
            signal = 'BUY'
            
        else:  # sell_signal
            # Multi-level SL for breakdowns
            # SL 1: Just above breakdown level
            sl_breakout = support * 1.002  # 0.2% above support
            
            # SL 2: ATR-based
            sl_atr = entry_price + (final_multiplier * atr_value)
            
            # SL 3: Previous swing high
            sl_swing = df['high'].rolling(15).max().iloc[-1] * 1.003
            
            # SL 4: VWAP resistance
            sl_vwap = current['vwap'] * 1.002
            
            # Use the lowest (safest) but reasonable SL
            sl_candidates = [sl_breakout, sl_atr, sl_swing, sl_vwap]
            sl = min([s for s in sl_candidates if (s - entry_price) / entry_price <= 0.025])  # Max 2.5% risk
            
            # Multi-target TP system
            # TP 1: Next support level or measured move
            next_support = min([s for s in support_levels if s < entry_price] + [entry_price * 0.95])
            measured_move = entry_price - (resistance - support)  # Classic breakdown target
            tp1 = max(next_support, measured_move)
            
            # TP 2: ATR-based (4:1 R:R minimum)
            risk = sl - entry_price
            tp2 = entry_price - (4.0 * risk)
            
            # TP 3: Bollinger Band projection
            bb_range = current['bb_upper'] - current['bb_lower']
            tp3 = current['bb_lower'] - (bb_range * 0.5)
            
            # TP 4: Volume-weighted target
            volume_strength = min(2.0, current['volume_ratio'])
            tp4 = entry_price - (volume_strength * 2.0 * atr_value)
            
            # Choose balanced target
            tp_candidates = [tp1, tp2, tp3, tp4]
            tp = sorted(tp_candidates, reverse=True)[1]  # Second highest (balanced)
            
            signal = 'SELL'
        
        # 7. Enhanced Confidence Scoring
        signal_strength = (buy_score if buy_signal else sell_score) / 14.0
        base_confidence = 0.45 + (signal_strength * 0.35)  # 0.45 to 0.8
        
        # Breakout strength bonus
        breakout_strength = abs(current['close'] - (resistance if buy_signal else support)) / current['close']
        breakout_bonus = min(0.1, breakout_strength * 20)
        
        # Volume confirmation bonus
        volume_bonus = min(0.1, (current['volume_ratio'] - 1.3) * 0.1)
        
        # Multi-timeframe bonus
        mtf_bonus = 0.05 if (higher_trend_bullish == buy_signal) else 0
        
        # Calculate R:R ratio
        risk = abs(entry_price - sl) / entry_price
        reward = abs(tp - entry_price) / entry_price
        rr_ratio = reward / risk if risk > 0 else 0
        
        # R:R bonus
        rr_bonus = 0
        if rr_ratio >= 5.0:
            rr_bonus = 0.1
        elif rr_ratio >= 4.0:
            rr_bonus = 0.08
        elif rr_ratio >= 3.0:
            rr_bonus = 0.05
        
        # Final confidence
        total_confidence = (base_confidence + breakout_bonus + volume_bonus + 
                          mtf_bonus + rr_bonus)
        confidence = min(0.95, total_confidence)
        
        # Quality filters for breakout trades
        quality_checks = [
            rr_ratio >= 3.0,  # Minimum 3:1 R:R for breakouts
            confidence >= 0.7,  # Higher confidence threshold for breakouts
            risk <= 0.025,  # Maximum 2.5% risk
            current['volume_ratio'] >= 1.3,  # Strong volume required
            breakout_strength >= 0.002,  # Meaningful breakout
        ]
        
        if all(quality_checks):
            return signal, entry_price, sl, tp, 0.001, confidence
    
    return None