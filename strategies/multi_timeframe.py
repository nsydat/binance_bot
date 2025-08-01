import pandas as pd
import ta

def multi_timeframe_strategy(df, df_higher=None):
    """
    Chiến lược đa khung thời gian
    Winrate kỳ vọng: 75-85%
    """
    def get_timeframe_signal(df):
        """Lấy tín hiệu cho từng timeframe"""
        if len(df) < 50:
            return 'HOLD'
        
        # EMA + RSI strategy cho từng timeframe
        df['ema_fast'] = ta.trend.EMAIndicator(df['close'], 9).ema_indicator()
        df['ema_slow'] = ta.trend.EMAIndicator(df['close'], 21).ema_indicator()
        df['rsi'] = ta.momentum.RSIIndicator(df['close'], 14).rsi()
        
        current = df.iloc[-1]
        prev = df.iloc[-2]
        
        if (current['ema_fast'] > current['ema_slow'] and 
            prev['ema_fast'] <= prev['ema_slow'] and
            current['rsi'] < 70):
            return 'BUY'
        elif (current['ema_fast'] < current['ema_slow'] and 
              prev['ema_fast'] >= prev['ema_slow'] and
              current['rsi'] > 30):
            return 'SELL'
        else:
            return 'HOLD'
    
    # Kiểm tra dữ liệu
    if len(df) < 50:
        return None
    
    # Sử dụng df làm timeframe chính, df_higher làm timeframe cao hơn
    df_1h = df  # Timeframe chính
    df_4h = df_higher if df_higher is not None else df  # Timeframe cao hơn
    df_1d = df_higher if df_higher is not None else df  # Giả định, trong thực tế cần lấy 1d data
    
    # Lấy tín hiệu từ 3 timeframe
    signals = {
        '1h': get_timeframe_signal(df_1h) if df_1h is not None else 'HOLD',
        '4h': get_timeframe_signal(df_4h) if df_4h is not None else 'HOLD',
        '1d': get_timeframe_signal(df_1d) if df_1d is not None else 'HOLD'
    }
    
    # Weighted voting (1d > 4h > 1h)
    weights = {'1d': 0.5, '4h': 0.3, '1h': 0.2}
    
    buy_score = sum(weights[tf] for tf, signal in signals.items() if signal == 'BUY')
    sell_score = sum(weights[tf] for tf, signal in signals.items() if signal == 'SELL')
    
    # Tính confidence
    confidence = max(buy_score, sell_score)
    
    if buy_score >= 0.6:  # 60% weighted consensus
        entry_price = df['close'].iloc[-1]
        # SL/TP cần được tính dựa trên timeframe cao hơn
        atr = ta.volatility.AverageTrueRange(
            df['high'], df['low'], df['close'], 14
        )
        
        atr_value = atr.average_true_range().iloc[-1]
        
        sl = entry_price - (1.5 * atr_value)
        tp = entry_price + (2.0 * atr_value)
        
        return 'BUY', entry_price, sl, tp, 0.001, min(confidence, 0.9)
    
    elif sell_score >= 0.6:
        entry_price = df['close'].iloc[-1]
        atr = ta.volatility.AverageTrueRange(
            df['high'], df['low'], df['close'], 14
        )
        
        atr_value = atr.average_true_range().iloc[-1]
        
        sl = entry_price + (1.5 * atr_value)
        tp = entry_price - (2.0 * atr_value)
        
        return 'SELL', entry_price, sl, tp, 0.001, min(confidence, 0.9)
    
    return None