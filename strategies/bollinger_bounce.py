# strategies/bollinger_bounce.py
import pandas as pd
import ta
import numpy as np

def strategy_bollinger_bounce(df, df_higher=None):
    """
    Chiến lược Bollinger Bands bounce với mean reversion - IMPROVED
    - Thêm nhiều bộ lọc để giảm tín hiệu sai
    - Quản lý rủi ro tốt hơn với dynamic SL/TP
    - Xác nhận xu hướng từ nhiều chỉ báo
    """
    if len(df) < 50:
        return None
        
    # Tính Bollinger Bands với nhiều period
    bb20 = ta.volatility.BollingerBands(close=df['close'], window=20, window_dev=2)
    bb50 = ta.volatility.BollingerBands(close=df['close'], window=50, window_dev=2)
    
    df['bb_high'] = bb20.bollinger_hband()
    df['bb_low'] = bb20.bollinger_lband()
    df['bb_mid'] = bb20.bollinger_mavg()
    df['bb_width'] = bb20.bollinger_wband()
    df['bb_percent'] = bb20.bollinger_pband()
    
    # BB dài hạn để xác định xu hướng tổng thể
    df['bb50_high'] = bb50.bollinger_hband()
    df['bb50_low'] = bb50.bollinger_lband()
    df['bb50_mid'] = bb50.bollinger_mavg()

    # Tính RSI và Stochastic để xác nhận
    df['rsi'] = ta.momentum.RSIIndicator(close=df['close'], window=14).rsi()
    stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
    df['stoch_k'] = stoch.stoch()
    df['stoch_d'] = stoch.stoch_signal()
    
    # EMA để xác định xu hướng
    df['ema20'] = ta.trend.EMAIndicator(df['close'], window=20).ema_indicator()
    df['ema50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
    
    # Volume analysis
    df['volume_sma'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma']
    
    # ATR cho dynamic SL/TP
    df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], 14).average_true_range()

    current = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]

    # Xác nhận xu hướng từ khung thời gian lớn hơn
    higher_tf_bullish = True
    higher_tf_bearish = True
    
    if df_higher is not None and len(df_higher) > 50:
        # Tính BB cho timeframe cao hơn
        higher_bb = ta.volatility.BollingerBands(df_higher['close'], window=20, window_dev=2)
        higher_ema20 = ta.trend.EMAIndicator(df_higher['close'], window=20).ema_indicator()
        higher_rsi = ta.momentum.RSIIndicator(df_higher['close'], window=14).rsi()
        
        higher_current = df_higher.iloc[-1]
        
        # Xu hướng từ TF cao hơn
        higher_tf_bullish = (higher_current['close'] > higher_ema20.iloc[-1] and 
                            higher_rsi.iloc[-1] < 70)
        higher_tf_bearish = (higher_current['close'] < higher_ema20.iloc[-1] and 
                            higher_rsi.iloc[-1] > 30)

    # Phát hiện "Squeeze" - band co hẹp
    bb_width_ma = df['bb_width'].rolling(20).mean()
    is_squeeze = current['bb_width'] < bb_width_ma.iloc[-1] * 0.7
    
    # Kiểm tra momentum tăng/giảm
    price_momentum = (current['close'] - prev2['close']) / prev2['close']
    
    # === ĐIỀU KIỆN BUY NÂNG CAP ===
    buy_conditions = [
        # 1. Giá bounce từ Lower Band
        current['close'] <= current['bb_low'] * 1.002,
        prev['close'] > prev['bb_low'],  # Trước đó chưa chạm
        current['close'] > prev['close'],  # Đang bounce lên
        
        # 2. RSI + Stochastic xác nhận oversold
        current['rsi'] < 35,
        current['stoch_k'] < 25,
        current['stoch_k'] > current['stoch_d'],  # Stoch đang cross up
        
        # 3. Xu hướng tổng thể không quá bearish
        current['close'] > current['bb50_low'],  # Trên BB dài hạn
        current['ema20'] > current['ema50'] * 0.995,  # EMA không quá bearish
        
        # 4. Volume và momentum
        current['volume_ratio'] > 1.1,  # Volume tăng
        price_momentum > -0.02,  # Không rơi quá mạnh
        
        # 5. Xác nhận từ TF cao hơn
        higher_tf_bullish
    ]
    
    if sum(buy_conditions) >= 9:  # Cần ít nhất 9/11 điều kiện
        entry = current['close']
        
        # Dynamic SL dựa trên ATR và BB
        sl_bb = current['bb_low'] * 0.995
        sl_atr = entry - (1.5 * current['atr'])
        sl = max(sl_bb, sl_atr)  # Chọn SL xa hơn để tránh noise
        
        # TP conservative hơn
        risk = entry - sl
        tp = entry + (1.8 * risk)  # R:R = 1.8:1 thay vì 2:1
        
        # Tính confidence
        confidence = 0.5 + (sum(buy_conditions) - 9) * 0.05
        if is_squeeze:
            confidence += 0.1
        if current['volume_ratio'] > 1.5:
            confidence += 0.1
            
        return 'BUY', entry, sl, tp, 0.001, min(confidence, 0.9)

    # === ĐIỀU KIỆN SELL NÂNG CAP ===
    sell_conditions = [
        # 1. Giá bounce từ Upper Band
        current['close'] >= current['bb_high'] * 0.998,
        prev['close'] < prev['bb_high'],  # Trước đó chưa chạm
        current['close'] < prev['close'],  # Đang bounce xuống
        
        # 2. RSI + Stochastic xác nhận overbought
        current['rsi'] > 65,
        current['stoch_k'] > 75,
        current['stoch_k'] < current['stoch_d'],  # Stoch đang cross down
        
        # 3. Xu hướng tổng thể không quá bullish
        current['close'] < current['bb50_high'],  # Dưới BB dài hạn
        current['ema20'] < current['ema50'] * 1.005,  # EMA không quá bullish
        
        # 4. Volume và momentum
        current['volume_ratio'] > 1.1,  # Volume tăng
        price_momentum < 0.02,  # Không tăng quá mạnh
        
        # 5. Xác nhận từ TF cao hơn
        higher_tf_bearish
    ]

    if sum(sell_conditions) >= 9:  # Cần ít nhất 9/11 điều kiện
        entry = current['close']
        
        # Dynamic SL dựa trên ATR và BB
        sl_bb = current['bb_high'] * 1.005
        sl_atr = entry + (1.5 * current['atr'])
        sl = min(sl_bb, sl_atr)  # Chọn SL xa hơn để tránh noise
        
        # TP conservative hơn
        risk = sl - entry
        tp = entry - (1.8 * risk)  # R:R = 1.8:1
        
        # Tính confidence
        confidence = 0.5 + (sum(sell_conditions) - 9) * 0.05
        if is_squeeze:
            confidence += 0.1
        if current['volume_ratio'] > 1.5:
            confidence += 0.1
            
        return 'SELL', entry, sl, tp, 0.001, min(confidence, 0.9)

    return None