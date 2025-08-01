#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backtest engine for testing trading strategies
"""

import pandas as pd
from datetime import datetime, timedelta
from utils.data_fetcher import get_klines_df
from strategies.ema_vwap_rsi import ema_vwap_rsi_strategy as strategy_ema_vwap
from strategies.supertrend_rsi import supertrend_rsi_strategy as strategy_supertrend_atr
from strategies.trend_momentum_volume import trend_momentum_volume_strategy as strategy_macd_signal
from strategies.breakout_volume_sr import breakout_volume_sr_strategy as strategy_bollinger_bounce
from strategies.multi_timeframe import multi_timeframe_strategy as strategy_multi_timeframe

# Strategy mapping
STRATEGIES = {
    "EMA_VWAP": strategy_ema_vwap,
    "SUPERTREND_ATR": strategy_supertrend_atr,
    "MACD_SIGNAL": strategy_macd_signal,
    "BOLLINGER_BOUNCE": strategy_bollinger_bounce,
    "MULTI_TIMEFRAME": strategy_multi_timeframe
}

def run_backtest(symbol="DOGEUSDT", interval="5m", days=90, initial_balance=1000):
    """Chạy backtest trên dữ liệu quá khứ"""
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
            result = STRATEGIES[strat_name](current_df, None)
            if result and not signal_found:
                side, entry, sl, tp, qty, confidence = result
                
                # Tính toán kết quả
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