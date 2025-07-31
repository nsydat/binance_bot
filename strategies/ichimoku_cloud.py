# strategies/ichimoku_cloud.py
import pandas as pd
import ta
import numpy as np

def strategy_ichimoku_cloud(df, df_higher=None):
    """
    Ichimoku Cloud Strategy với cloud breakout và multi-timeframe confirmation
    
    Components:
    - Tenkan-sen (Conversion Line): (9-period high + 9-period low) / 2
    - Kijun-sen (Base Line): (26-period high + 26-period low) / 2  
    - Senkou Span A (Leading Span A): (Tenkan-sen + Kijun-sen) / 2, shifted +26
    - Senkou Span B (Leading Span B): (52-period high + 52-period low) / 2, shifted +26
    - Chikou Span (Lagging Span): Current close shifted -26
    
    Entry Conditions:
    BUY: Price above cloud + Tenkan > Kijun + Chikou above price 26 periods ago + volume
    SELL: Price below cloud + Tenkan < Kijun + Chikou below price 26 periods ago + volume
    """
    
    if len(df) < 78:  # Cần ít nhất 78 periods cho Ichimoku
        return None
    
    # Đảm bảo dữ liệu số
    for col in ['close', 'high', 'low', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Tính các thành phần Ichimoku
    # Tenkan-sen (Conversion Line) - 9 periods
    high_9 = df['high'].rolling(window=9).max()
    low_9 = df['low'].rolling(window=9).min()
    df['tenkan_sen'] = (high_9 + low_9) / 2
    
    # Kijun-sen (Base Line) - 26 periods  
    high_26 = df['high'].rolling(window=26).max()
    low_26 = df['low'].rolling(window=26).min()
    df['kijun_sen'] = (high_26 + low_26) / 2
    
    # Senkou Span A (Leading Span A) - shifted +26
    senkou_span_a = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(26)
    df['senkou_span_a'] = senkou_span_a
    
    # Senkou Span B (Leading Span B) - 52 periods, shifted +26
    high_52 = df['high'].rolling(window=52).max()
    low_52 = df['low'].rolling(window=52).min()
    senkou_span_b = ((high_52 + low_52) / 2).shift(26)
    df['senkou_span_b'] = senkou_span_b
    
    # Chikou Span (Lagging Span) - shifted -26
    df['chikou_span'] = df['close'].shift(-26)
    
    # Cloud boundaries (current position)
    df['cloud_top'] = df[['senkou_span_a', 'senkou_span_b']].max(axis=1)
    df['cloud_bottom'] = df[['senkou_span_a', 'senkou_span_b']].min(axis=1)
    
    # Additional indicators for confirmation
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df['volume_sma'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma']
    
    # ATR for dynamic SL/TP
    df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], 14).average_true_range()
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Kiểm tra vị trí giá so với cloud
    price_above_cloud = current['close'] > current['cloud_top']
    price_below_cloud = current['close'] < current['cloud_bottom']
    price_in_cloud = not price_above_cloud and not price_below_cloud
    
    # Cloud color (bullish vs bearish)
    cloud_bullish = current['senkou_span_a'] > current['senkou_span_b']
    cloud_bearish = current['senkou_span_a'] < current['senkou_span_b']
    
    # Tenkan/Kijun relationship
    tenkan_above_kijun = current['tenkan_sen'] > current['kijun_sen']
    tenkan_below_kijun = current['tenkan_sen'] < current['kijun_sen']
    
    # Tenkan/Kijun cross
    tk_bullish_cross = (current['tenkan_sen'] > current['kijun_sen'] and 
                       prev['tenkan_sen'] <= prev['kijun_sen'])
    tk_bearish_cross = (current['tenkan_sen'] < current['kijun_sen'] and 
                       prev['tenkan_sen'] >= prev['kijun_sen'])
    
    # Chikou Span confirmation (26 periods ago)
    if len(df) > 26:
        chikou_current = current['chikou_span']
        price_26_ago = df['close'].iloc[-27] if len(df) > 27 else df['close'].iloc[0]
        chikou_bullish = chikou_current > price_26_ago
        chikou_bearish = chikou_current < price_26_ago
    else:
        chikou_bullish = True
        chikou_bearish = True
    
    # Cloud breakout detection
    cloud_breakout_bullish = (price_above_cloud and 
                             prev['close'] <= prev['cloud_top'])
    cloud_breakout_bearish = (price_below_cloud and 
                             prev['close'] >= prev['cloud_bottom'])
    
    # Future cloud analysis (next 26 periods projection)
    future_cloud_bullish = True
    future_cloud_bearish = True
    if len(df) >= 52:
        # Tính future cloud color
        future_tenkan = (df['high'].tail(9).max() + df['low'].tail(9).min()) / 2
        future_kijun = (df['high'].tail(26).max() + df['low'].tail(26).min()) / 2
        future_senkou_a = (future_tenkan + future_kijun) / 2
        future_senkou_b = (df['high'].tail(52).max() + df['low'].tail(52).min()) / 2
        
        future_cloud_bullish = future_senkou_a > future_senkou_b
        future_cloud_bearish = future_senkou_a < future_senkou_b
    
    # Higher timeframe confirmation
    higher_tf_bullish = True
    higher_tf_bearish = True
    
    if df_higher is not None and len(df_higher) > 78:
        # Tính Ichimoku cho timeframe cao hơn
        df_higher_num = df_higher.copy()
        for col in ['close', 'high', 'low']:
            df_higher_num[col] = pd.to_numeric(df_higher_num[col], errors='coerce')
        
        h_high_26 = df_higher_num['high'].rolling(26).max()
        h_low_26 = df_higher_num['low'].rolling(26).min()
        h_kijun = (h_high_26 + h_low_26) / 2
        
        h_high_9 = df_higher_num['high'].rolling(9).max()
        h_low_9 = df_higher_num['low'].rolling(9).min()
        h_tenkan = (h_high_9 + h_low_9) / 2
        
        h_senkou_a = ((h_tenkan + h_kijun) / 2).shift(26)
        h_high_52 = df_higher_num['high'].rolling(52).max()
        h_low_52 = df_higher_num['low'].rolling(52).min()
        h_senkou_b = ((h_high_52 + h_low_52) / 2).shift(26)
        
        h_current = df_higher_num.iloc[-1]
        h_cloud_top = max(h_senkou_a.iloc[-1] if not pd.isna(h_senkou_a.iloc[-1]) else 0,
                         h_senkou_b.iloc[-1] if not pd.isna(h_senkou_b.iloc[-1]) else 0)
        h_cloud_bottom = min(h_senkou_a.iloc[-1] if not pd.isna(h_senkou_a.iloc[-1]) else float('inf'),
                            h_senkou_b.iloc[-1] if not pd.isna(h_senkou_b.iloc[-1]) else float('inf'))
        
        higher_tf_bullish = h_current['close'] > h_cloud_top and h_tenkan.iloc[-1] > h_kijun.iloc[-1]
        higher_tf_bearish = h_current['close'] < h_cloud_bottom and h_tenkan.iloc[-1] < h_kijun.iloc[-1]
    
    # BUY Conditions
    buy_conditions = [
        price_above_cloud,                    # Giá trên cloud
        cloud_bullish,                       # Cloud màu xanh (bullish)
        tenkan_above_kijun,                  # Tenkan trên Kijun
        chikou_bullish,                      # Chikou span bullish
        current['rsi'] > 30 and current['rsi'] < 70,  # RSI filter
        current['volume_ratio'] > 1.0,       # Volume confirmation
        future_cloud_bullish,                # Future cloud bullish
        higher_tf_bullish                    # Higher TF confirmation
    ]
    
    # SELL Conditions  
    sell_conditions = [
        price_below_cloud,                   # Giá dưới cloud
        cloud_bearish,                       # Cloud màu đỏ (bearish)
        tenkan_below_kijun,                  # Tenkan dưới Kijun
        chikou_bearish,                      # Chikou span bearish
        current['rsi'] > 30 and current['rsi'] < 70,  # RSI filter
        current['volume_ratio'] > 1.0,       # Volume confirmation
        future_cloud_bearish,                # Future cloud bearish
        higher_tf_bearish                    # Higher TF confirmation
    ]
    
    # Bonus conditions for higher confidence
    def calculate_confidence(base_conditions, bonus_factors):
        base_score = sum(base_conditions) / len(base_conditions)
        
        bonus = 0
        # Cloud breakout bonus
        if bonus_factors.get('breakout', False):
            bonus += 0.15
        
        # TK cross bonus
        if bonus_factors.get('tk_cross', False):
            bonus += 0.1
        
        # Strong volume bonus
        if current['volume_ratio'] > 1.5:
            bonus += 0.1
        
        # Price momentum bonus
        price_momentum = abs(current['close'] - prev['close']) / prev['close']
        if price_momentum > 0.01:  # 1% move
            bonus += 0.05
        
        return min(base_score + bonus, 1.0)
    
    # BUY Signal
    if sum(buy_conditions) >= 6:  # Ít nhất 6/8 điều kiện
        entry = current['close']
        
        # Dynamic SL based on cloud and ATR
        cloud_support = current['cloud_top']
        atr_sl = entry - (2.0 * current['atr'])
        sl = min(cloud_support * 0.995, atr_sl)  # Chọn SL gần hơn
        
        # TP based on Kijun-sen projection hoặc R:R ratio
        kijun_target = current['kijun_sen'] + (current['kijun_sen'] - current['cloud_bottom'])
        risk = entry - sl
        ratio_target = entry + (2.5 * risk)
        tp = max(kijun_target, ratio_target)  # Chọn target xa hơn
        
        confidence = calculate_confidence(buy_conditions, {
            'breakout': cloud_breakout_bullish,
            'tk_cross': tk_bullish_cross,
            'momentum': abs(current['close'] - prev['close']) / prev['close']
        })
        
        return 'BUY', entry, sl, tp, 0.001, confidence
    
    # SELL Signal
    elif sum(sell_conditions) >= 6:  # Ít nhất 6/8 điều kiện
        entry = current['close']
        
        # Dynamic SL based on cloud and ATR
        cloud_resistance = current['cloud_bottom']
        atr_sl = entry + (2.0 * current['atr'])
        sl = max(cloud_resistance * 1.005, atr_sl)  # Chọn SL gần hơn
        
        # TP based on Kijun-sen projection hoặc R:R ratio
        kijun_target = current['kijun_sen'] - (current['cloud_top'] - current['kijun_sen'])
        risk = sl - entry
        ratio_target = entry - (2.5 * risk)
        tp = min(kijun_target, ratio_target)  # Chọn target xa hơn
        
        confidence = calculate_confidence(sell_conditions, {
            'breakout': cloud_breakout_bearish,
            'tk_cross': tk_bearish_cross,
            'momentum': abs(current['close'] - prev['close']) / prev['close']
        })
        
        return 'SELL', entry, sl, tp, 0.001, confidence
    
    return None


def strategy_ichimoku_simple(df, df_higher=None):
    """
    Simplified Ichimoku strategy focusing on key signals only
    Better for beginners or when computational resources are limited
    """
    if len(df) < 52:
        return None
    
    # Convert to numeric
    for col in ['close', 'high', 'low', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Basic Ichimoku components
    high_26 = df['high'].rolling(26).max()
    low_26 = df['low'].rolling(26).min()
    df['kijun_sen'] = (high_26 + low_26) / 2
    
    high_9 = df['high'].rolling(9).max()
    low_9 = df['low'].rolling(9).min()
    df['tenkan_sen'] = (high_9 + low_9) / 2
    
    # Cloud calculation
    senkou_a = ((df['tenkan_sen'] + df['kijun_sen']) / 2).shift(26)
    high_52 = df['high'].rolling(52).max()
    low_52 = df['low'].rolling(52).min()
    senkou_b = ((high_52 + low_52) / 2).shift(26)
    
    df['cloud_top'] = pd.concat([senkou_a, senkou_b], axis=1).max(axis=1)
    df['cloud_bottom'] = pd.concat([senkou_a, senkou_b], axis=1).min(axis=1)
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Simple signals
    # BUY: Price above cloud + Tenkan crosses above Kijun
    if (current['close'] > current['cloud_top'] and 
        current['tenkan_sen'] > current['kijun_sen'] and
        prev['tenkan_sen'] <= prev['kijun_sen']):
        
        entry = current['close']
        sl = current['cloud_top'] * 0.995
        tp = entry + 2 * (entry - sl)
        return 'BUY', entry, sl, tp, 0.001, 0.75
    
    # SELL: Price below cloud + Tenkan crosses below Kijun  
    elif (current['close'] < current['cloud_bottom'] and
          current['tenkan_sen'] < current['kijun_sen'] and
          prev['tenkan_sen'] >= prev['kijun_sen']):
        
        entry = current['close']
        sl = current['cloud_bottom'] * 1.005
        tp = entry - 2 * (sl - entry)
        return 'SELL', entry, sl, tp, 0.001, 0.75
    
    return None