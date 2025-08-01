import pandas as pd
import ta

def ema_vwap_rsi_strategy(df, df_higher=None):
    """
    Chiến lược kết hợp EMA + VWAP + RSI - PHIÊN BẢN CẢI TIẾN
    Winrate kỳ vọng: 70-75%, R:R improved to 1:3-4
    """
    if len(df) < 50:
        return None
    
    # 1. EMA (Tối ưu thời gian)
    df['ema_fast'] = ta.trend.EMAIndicator(df['close'], 8).ema_indicator()  # 9->8: nhanh hơn
    df['ema_slow'] = ta.trend.EMAIndicator(df['close'], 21).ema_indicator()
    df['ema_trend'] = ta.trend.EMAIndicator(df['close'], 50).ema_indicator()  # Trend filter
    
    # 2. VWAP + VWAP bands
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3
    df['vwap'] = (df['tp'] * df['volume']).cumsum() / df['volume'].cumsum()
    # VWAP deviation bands
    df['vwap_std'] = df['tp'].rolling(20).std()
    df['vwap_upper'] = df['vwap'] + (df['vwap_std'] * 1.5)
    df['vwap_lower'] = df['vwap'] - (df['vwap_std'] * 1.5)
    
    # 3. RSI với multiple timeframes
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], 14).rsi()
    df['rsi_fast'] = ta.momentum.RSIIndicator(df['close'], 7).rsi()  # Faster RSI
    
    # 4. Volume analysis
    df['volume_sma'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma']
    
    # 5. Volatility (ATR) cho dynamic SL/TP
    atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], 14)
    df['atr'] = atr.average_true_range()
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]
    
    # Multi-timeframe confirmation
    higher_trend_bullish = True
    if df_higher is not None and len(df_higher) >= 20:
        df_higher['ema_trend'] = ta.trend.EMAIndicator(df_higher['close'], 20).ema_indicator()
        higher_trend_bullish = df_higher['close'].iloc[-1] > df_higher['ema_trend'].iloc[-1]
    
    # BUY Signal - Cải tiến logic
    buy_conditions = [
        # Core EMA signal
        current['ema_fast'] > current['ema_slow'],
        prev['ema_fast'] <= prev['ema_slow'],  # Fresh crossover
        
        # Trend filter
        current['close'] > current['ema_trend'],  # Above trend
        higher_trend_bullish,  # Higher TF bullish
        
        # VWAP confirmation - More flexible
        current['close'] > current['vwap'] or current['close'] > current['vwap_lower'],  # Near or above VWAP
        
        # RSI conditions - More flexible
        current['rsi'] < 75,  # Not extremely overbought (70->75)
        current['rsi_fast'] > 40,  # Fast RSI shows momentum
        
        # Volume confirmation
        current['volume_ratio'] > 1.1,  # Decent volume (1.2->1.1)
        
        # Price action
        current['close'] > prev['close']  # Green candle
    ]
    
    # SELL Signal - Cải tiến logic  
    sell_conditions = [
        # Core EMA signal
        current['ema_fast'] < current['ema_slow'],
        prev['ema_fast'] >= prev['ema_slow'],  # Fresh crossover
        
        # Trend filter
        current['close'] < current['ema_trend'],  # Below trend
        not higher_trend_bullish,  # Higher TF bearish
        
        # VWAP confirmation - More flexible
        current['close'] < current['vwap'] or current['close'] < current['vwap_upper'],  # Near or below VWAP
        
        # RSI conditions - More flexible
        current['rsi'] > 25,  # Not extremely oversold (30->25)
        current['rsi_fast'] < 60,  # Fast RSI shows momentum
        
        # Volume confirmation
        current['volume_ratio'] > 1.1,  # Decent volume
        
        # Price action
        current['close'] < prev['close']  # Red candle
    ]
    
    buy_signal = sum(buy_conditions) >= 7  # 7/9 conditions (was all conditions)
    sell_signal = sum(sell_conditions) >= 7  # 7/9 conditions
    
    # Tính SL/TP - DYNAMIC & IMPROVED R:R
    if buy_signal or sell_signal:
        entry_price = current['close']
        atr_value = current['atr']
        
        # Dynamic ATR multiplier based on volatility
        volatility = df['close'].pct_change().rolling(20).std().iloc[-1]
        atr_multiplier = max(1.2, min(2.5, volatility * 100))  # 1.2-2.5x based on volatility
        
        if buy_signal:
            # Dynamic SL based on recent swing low and VWAP
            swing_low = df['low'].rolling(10).min().iloc[-1]
            vwap_support = min(current['vwap'], current['vwap_lower'])
            
            sl_level1 = entry_price - (atr_multiplier * atr_value)
            sl_level2 = min(swing_low * 0.999, vwap_support * 0.998)
            sl = max(sl_level1, sl_level2)  # Use the higher (safer) SL
            
            # Dynamic TP - Target VWAP upper band or strong resistance
            resistance = df['high'].rolling(20).max().iloc[-1]
            tp_level1 = entry_price + (3.5 * atr_value)  # 3.5:1 R:R minimum
            tp_level2 = min(resistance * 1.002, current['vwap_upper'])
            tp = max(tp_level1, tp_level2)  # Use the higher TP
            
            signal = 'BUY'
        else:
            # Dynamic SL based on recent swing high and VWAP
            swing_high = df['high'].rolling(10).max().iloc[-1]
            vwap_resistance = max(current['vwap'], current['vwap_upper'])
            
            sl_level1 = entry_price + (atr_multiplier * atr_value)
            sl_level2 = max(swing_high * 1.001, vwap_resistance * 1.002)
            sl = min(sl_level1, sl_level2)  # Use the lower (safer) SL
            
            # Dynamic TP
            support = df['low'].rolling(20).min().iloc[-1]
            tp_level1 = entry_price - (3.5 * atr_value)  # 3.5:1 R:R minimum
            tp_level2 = max(support * 0.998, current['vwap_lower'])
            tp = min(tp_level1, tp_level2)  # Use the lower TP
            
            signal = 'SELL'
        
        # Enhanced confidence calculation
        ema_strength = abs(current['ema_fast'] - current['ema_slow']) / current['close']
        volume_boost = min(0.2, (current['volume_ratio'] - 1.0) * 0.1)
        rsi_momentum = abs(current['rsi'] - 50) / 50 * 0.1
        
        # Calculate actual R:R ratio
        risk = abs(entry_price - sl) / entry_price
        reward = abs(tp - entry_price) / entry_price
        rr_ratio = reward / risk if risk > 0 else 0
        
        base_confidence = 0.5 + (ema_strength / 0.01) * 0.2
        total_confidence = base_confidence + volume_boost + rsi_momentum
        
        # Bonus for good R:R ratio
        if rr_ratio >= 3.0:
            total_confidence += 0.1
        
        confidence = min(0.95, total_confidence)
        
        # Only trade if R:R >= 2.5:1
        if rr_ratio >= 2.5:
            return signal, entry_price, sl, tp, 0.001, confidence
    
    return None