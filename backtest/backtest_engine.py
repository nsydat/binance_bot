# backtest/backtest_engine.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from utils.data_fetcher import get_klines_df
from strategies.ema_vwap import strategy_ema_vwap
from strategies.rsi_divergence import strategy_rsi_divergence
from strategies.supertrend_atr import strategy_supertrend_atr
from strategies.macd_signal import strategy_macd_signal
from strategies.bollinger_bounce import strategy_bollinger_bounce

# Danh sách chiến lược
STRATEGIES = {
    "EMA_VWAP": strategy_ema_vwap,
    "RSI_DIVERGENCE": strategy_rsi_divergence,
    "SUPERTREND_ATR": strategy_supertrend_atr,
    "MACD_SIGNAL": strategy_macd_signal,
    "BOLLINGER_BOUNCE": strategy_bollinger_bounce
}

def run_backtest(symbol="DOGEUSDT", interval="5m", days=90, initial_balance=1000):
    """
    Chạy backtest trên dữ liệu quá khứ
    """
    print(f"📊 Đang chạy backtest cho {symbol} ({interval}) trong {days} ngày qua...")

    # Lấy dữ liệu
    df = get_klines_df(symbol, interval, limit=10000)
    if df is None or len(df) < 100:
        print("❌ Không đủ dữ liệu")
        return None

    # Lọc theo thời gian
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df[df['timestamp'] >= start_time].copy()
    df = df.reset_index(drop=True)

    results = []
    balance = initial_balance

    # Chạy từng cây nến
    for i in range(50, len(df)):
        current_df = df.iloc[:i].copy().reset_index(drop=True)
        current_price = current_df['close'].iloc[-1]
        signal_found = False

        for strat_name in STRATEGIES:
            result = STRATEGIES[strat_name](current_df)
            if result and not signal_found:
                side, entry, sl, tp, qty, confidence = result
                # Giả định vào lệnh
                if side == 'BUY':
                    if tp >= current_price:
                        outcome = 'win'
                        profit_pct = (tp - entry) / entry * 100
                    else:
                        outcome = 'loss'
                        profit_pct = (sl - entry) / entry * 100
                else:
                    if tp <= current_price:
                        outcome = 'win'
                        profit_pct = (entry - tp) / entry * 100
                    else:
                        outcome = 'loss'
                        profit_pct = (entry - sl) / entry * 100

                new_balance = balance * (1 + profit_pct / 100)

                results.append({
                    'timestamp': current_df['timestamp'].iloc[-1],
                    'strategy': strat_name,
                    'side': side,
                    'entry': entry,
                    'sl': sl,
                    'tp': tp,
                    'confidence': confidence,
                    'outcome': outcome,
                    'profit_pct': profit_pct,
                    'balance': new_balance
                })

                balance = new_balance
                signal_found = True  # Chỉ xử lý 1 tín hiệu mỗi chu kỳ
                break

    return pd.DataFrame(results)