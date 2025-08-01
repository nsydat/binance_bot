#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chart utility for creating trading signal charts
"""

import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import ta

def create_chart(df, symbol, side, entry_price, sl_price, tp_price, save_path="chart_signal.png"):
    """Vẽ biểu đồ nến + EMA + đánh dấu tín hiệu"""
    try:
        # Chuẩn bị dữ liệu
        df_chart = df[-50:].copy()
        df_chart['timestamp'] = pd.to_datetime(df_chart['timestamp'], unit='ms')
        df_chart.set_index('timestamp', inplace=True)
        
        # Convert to numeric
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            df_chart[col] = pd.to_numeric(df_chart[col])

        # Tính EMA
        df_chart['ema9'] = ta.trend.EMAIndicator(df_chart['close'], window=9).ema_indicator()
        df_chart['ema21'] = ta.trend.EMAIndicator(df_chart['close'], window=21).ema_indicator()

        # Tạo các đường thêm vào biểu đồ
        apds = [
            mpf.make_addplot(df_chart['ema9'], color='orange', width=1, label='EMA 9'),
            mpf.make_addplot(df_chart['ema21'], color='purple', width=1, label='EMA 21'),
        ]

        # Thêm đường ngang: vào lệnh, SL, TP
        hlines = dict(hlines=[entry_price, sl_price, tp_price],
                      colors=['green' if side == 'BUY' else 'red', 'red', 'green'],
                      linestyle='--',
                      linewidths=[1, 1, 1])

        # Vẽ biểu đồ
        fig, axlist = mpf.plot(
            df_chart[['open', 'high', 'low', 'close', 'volume']],
            type='candle',
            volume=True,
            title=f"{symbol} - Tín hiệu {side}",
            style='charles',
            ylabel='Price',
            ylabel_lower='Volume',
            figratio=(12, 6),
            figscale=1.1,
            hlines=hlines,
            addplot=apds,
            fill_between=dict(y1=df_chart['ema9'].values, y2=df_chart['ema21'].values, color='lightgray', alpha=0.5),
            returnfig=True
        )

        # Lưu ảnh
        fig.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return save_path
        
    except Exception as e:
        print(f"⚠️ Lỗi tạo biểu đồ: {e}")
        return None