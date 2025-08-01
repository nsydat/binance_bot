#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data fetcher utility for Binance API
"""

from binance import Client
import pandas as pd

client = Client()

def get_klines_df(symbol, interval, limit=100):
    """Lấy dữ liệu OHLCV từ Binance API"""
    try:
        klines = client.get_historical_klines(symbol, interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])
        
        # Convert to numeric
        numeric_columns = ['close', 'high', 'low', 'volume', 'open']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col])
            
        return df
    except Exception as e:
        print(f"❌ Lỗi lấy dữ liệu {symbol}: {e}")
        return None
    
def get_multi_timeframe_data(symbol, main_interval, higher_interval, main_limit=200, higher_limit=100):
    """Lấy dữ liệu cho 2 khung thời gian"""
    df_main = get_klines_df(symbol, main_interval, main_limit)
    df_higher = get_klines_df(symbol, higher_interval, higher_limit)
    return df_main, df_higher