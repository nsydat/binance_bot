from binance import Client
import pandas as pd

client = Client()

def get_klines_df(symbol, interval, limit=100):
    try:
        klines = client.get_historical_klines(symbol, interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])
        df['close'] = pd.to_numeric(df['close'])
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        df['volume'] = pd.to_numeric(df['volume'])
        return df
    except Exception as e:
        print(f"Lỗi lấy dữ liệu: {e}")
        return None
    
def get_multi_timeframe_data(symbol, main_interval, higher_interval, main_limit=200, higher_limit=100):
    """
    Lấy dữ liệu cho 2 khung thời gian
    Ví dụ: 5m (main) và 15m (higher)
    """
    df_main = get_klines_df(symbol, main_interval, main_limit)
    df_higher = get_klines_df(symbol, higher_interval, higher_limit)
    return df_main, df_higher