# bot.py
from binance import Client
import pandas as pd
from datetime import datetime
import time
import os

# Load config
config = {
    "symbol": "DOGEUSDT",
    "interval": "5m",
    "active_strategies": ["BREAKOUT", "RSI_REVERSAL", "SUPERTREND"]
}

# Import utilities
from utils.telegram import send_telegram
from utils.data_fetcher import get_klines_df
from strategies.ema_vwap import strategy_ema_vwap
from strategies.rsi_divergence import strategy_rsi_divergence
from strategies.supertrend_atr import strategy_supertrend_atr
from utils.chart import create_chart  # Đảm bảo đã tạo file chart.py

print(f"🚀 Bot Tín Hiệu Binance Futures khởi động lúc {datetime.now()}")

def run_bot():
    symbol = config['symbol']
    interval = config['interval']

    # ✅ Không cần API Key/Secret vì chỉ đọc dữ liệu
    client = Client()

    while True:
        try:
            # Lấy dữ liệu
            df = get_klines_df(symbol, interval)
            if df is None or len(df) < 50:
                print("❌ Không lấy được dữ liệu hoặc dữ liệu quá ít")
                time.sleep(60)
                continue

            # Chạy từng chiến lược
            for strat in config['active_strategies']:
                result = None
                if strat == "EMA_VWAP":
                    result = strategy_ema_vwap(df)
                elif strat == "RSI_DIVERGENCE":
                    result = strategy_rsi_divergence(df)
                elif strat == "SUPERTREND_ATR":
                    result = strategy_supertrend_atr(df)

                if result:
                    side, entry, sl, tp, qty = result
                    chart_path = "chart_signal.png"

                    # ✅ Vẽ biểu đồ
                    try:
                        create_chart(df, symbol, side, entry, sl, tp, chart_path)
                    except Exception as e:
                        print(f"⚠️ Lỗi vẽ biểu đồ: {e}")
                        chart_path = None

                    # ✅ Gửi tín hiệu + ảnh
                    message = f"""
🔔 **TÍN HIỆU GIAO DỊCH** 🔔
📌 Cặp: {symbol}
🎯 Chiều: *{side}*
💰 Giá vào: `{entry:.8f}`
📉 Stop-Loss: `{sl:.8f}`
📈 Take-Profit: `{tp:.8f}`
📊 Khung: {interval}
🕒 {pd.Timestamp.now().strftime('%H:%M %d/%m')}
                    """
                    send_telegram(message, chart_path)
                    print(f"[{datetime.now()}] ✅ Đã gửi tín hiệu: {side} {symbol} @ {entry:.6f}")

            # Chờ đến chu kỳ tiếp theo
            print(f"[{datetime.now()}] Đang chờ chu kỳ tiếp theo...")
            time.sleep(60 * 5)  # 5 phút

        except Exception as e:
            error_msg = f"🔴 Lỗi hệ thống: {str(e)}"
            print(error_msg)
            send_telegram(error_msg)
            time.sleep(60)

if __name__ == "__main__":
    run_bot()