#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot Tín Hiệu Binance Futures - Phiên bản 2.1
Hỗ trợ 6 chiến thuật với multi-timeframe confirmation
"""

import pandas as pd
from datetime import datetime, timedelta
import time
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Thread

# Load config
try:
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    print("✅ Đã tải cấu hình từ config.json")
except FileNotFoundError:
    print("❌ Không tìm thấy config.json")
    exit(1)

# Import utilities
from utils.telegram import send_telegram
from utils.data_fetcher import get_klines_df
from utils.chart import create_chart
from utils.signal_manager import SignalManager
from utils.risk_manager import RiskManager
from dashboard.app import bot_status, log, emit_update, socketio

# Import strategies
from strategies.ema_vwap_rsi import ema_vwap_rsi_strategy as strategy_ema_vwap
from strategies.supertrend_rsi import supertrend_rsi_strategy as strategy_supertrend_atr
from strategies.trend_momentum_volume import trend_momentum_volume_strategy as strategy_trend_momentum
from strategies.breakout_volume_sr import breakout_volume_sr_strategy as strategy_breakout_volume
from strategies.multi_timeframe import multi_timeframe_strategy as strategy_multi_timeframe

print(f"🚀 Bot Tín Hiệu Binance Futures (Cải Tiến) khởi động lúc {datetime.now()}")

class TradingBot:
    def __init__(self):
        self.is_first_run = True
        self.signal_manager = SignalManager()
        self.risk_manager = RiskManager()
        self.data_cache = {}
        self.last_cache_update = {}
        self.update_dashboard_config()
        # Khởi động dashboard trong thread riêng
        Thread(target=self.run_dashboard, daemon=True).start()

    def run_dashboard(self):
        """
        Khởi động Flask-SocketIO server
        """
        try:
            socketio.run(
                host='0.0.0.0',
                port=5000,
                debug=False,
                use_reloader=False
            )
        except Exception as e:
            print(f"❌ Lỗi khởi động dashboard: {e}")
            log(f"❌ Lỗi dashboard: {e}")

    def update_dashboard_config(self):
        """
        Cập nhật cấu hình hiện tại lên dashboard
        """
        bot_status['config'] = {
            'symbols': config['symbols'],
            'interval': config['interval'],
            'active_strategies': config['active_strategies'],
            'max_signals_per_hour': config['risk_management']['max_signals_per_hour']
        }
        log("✅ Cấu hình đã được cập nhật lên dashboard")
        emit_update()

    def get_cached_data(self, symbol, interval, limit=200):
        """Cache dữ liệu để tránh gọi API liên tục"""
        cache_key = f"{symbol}_{interval}"
        now = datetime.now()
        if (cache_key in self.data_cache and 
            cache_key in self.last_cache_update and
            (now - self.last_cache_update[cache_key]).seconds < config['performance']['data_cache_minutes'] * 60):
            return self.data_cache[cache_key]
        df = get_klines_df(symbol, interval, limit)
        if df is not None:
            self.data_cache[cache_key] = df
            self.last_cache_update[cache_key] = now
        return df

    def execute_strategy(self, strategy_name, df, df_higher=None):
        """Thực thi một chiến lược với xác nhận multi-timeframe"""
        # Strategy mapping
        strategy_map = {
            "EMA_VWAP": strategy_ema_vwap,
            "SUPERTREND_ATR": strategy_supertrend_atr,
            "TREND_MOMENTUM": strategy_trend_momentum,
            "BREAKOUT_VOLUME": strategy_breakout_volume,
            "MULTI_TIMEFRAME": strategy_multi_timeframe
        }
        
        try:
            if strategy_name not in strategy_map:
                print(f"⚠️ Chiến lược {strategy_name} không tồn tại")
                return None
                
            result = strategy_map[strategy_name](df, df_higher)
            
            if result:
                side, entry, sl, tp, qty, confidence = result
                return {
                    'strategy': strategy_name,
                    'side': side,
                    'entry': entry,
                    'sl': sl,
                    'tp': tp,
                    'qty': qty,
                    'confidence': confidence,
                    'timestamp': datetime.now()
                }
        except Exception as e:
            print(f"⚠️ Lỗi chiến lược {strategy_name}: {e}")
        return None

    def analyze_market_conditions(self, df):
        """Phân tích điều kiện thị trường"""
        df['returns'] = df['close'].pct_change()
        volatility = df['returns'].rolling(20).std().iloc[-1]
        avg_volume = df['volume'].rolling(20).mean().iloc[-1]
        current_volume = df['volume'].iloc[-1]
        volume_ratio = current_volume / avg_volume
        sma_short = df['close'].rolling(10).mean().iloc[-1]
        sma_long = df['close'].rolling(30).mean().iloc[-1]
        trend = "BULLISH" if sma_short > sma_long else "BEARISH"
        return {
            'volatility': volatility,
            'volume_ratio': volume_ratio,
            'trend': trend,
            'market_strength': min(volume_ratio * 2, 3.0)
        }

    def filter_and_rank_signals(self, signals, market_conditions):
        """Lọc và xếp hạng tín hiệu"""
        if not signals:
            return []
        for signal in signals:
            base_confidence = signal['confidence']
            market_bonus = 0
            if market_conditions['volume_ratio'] > 1.2:
                market_bonus += 0.1
            if market_conditions['volatility'] > 0.02:
                market_bonus += 0.05
            if ((signal['side'] == 'BUY' and market_conditions['trend'] == 'BULLISH') or
                (signal['side'] == 'SELL' and market_conditions['trend'] == 'BEARISH')):
                market_bonus += 0.1
            signal['final_confidence'] = base_confidence + market_bonus
        signals.sort(key=lambda x: x['final_confidence'], reverse=True)
        return [s for s in signals if s['final_confidence'] >= 0.6]

    def run_analysis_cycle(self):
        """Một chu kỳ phân tích hoàn chỉnh cho tất cả các cặp tiền"""
        interval = config['interval']

        for symbol in config['symbols']:
            print(f"\n🔍 Đang phân tích {symbol}...")

            try:
                # Lấy dữ liệu
                df_main = self.get_cached_data(symbol, interval, 200)
                df_higher = None
                if config['risk_management']['enable_multi_timeframe']:
                    higher_interval = "15m" if interval == "5m" else "1h"
                    df_higher = self.get_cached_data(symbol, higher_interval, 100)

                if df_main is None or len(df_main) < 50:
                    print(f"❌ {symbol}: Không đủ dữ liệu")
                    continue

                # Phân tích điều kiện thị trường
                market_conditions = self.analyze_market_conditions(df_main)
                print(f"📊 {symbol}: {market_conditions['trend']}, Vol: {market_conditions['volume_ratio']:.2f}")

                # Chạy chiến lược
                signals = []
                max_workers = len(config['active_strategies'])
                
                if config['performance']['parallel_strategy_execution']:
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        futures = [
                            executor.submit(self.execute_strategy, strategy, df_main, df_higher)
                            for strategy in config['active_strategies']
                        ]
                        for future in futures:
                            result = future.result()
                            if result:
                                signals.append(result)
                else:
                    for strategy in config['active_strategies']:
                        result = self.execute_strategy(strategy, df_main, df_higher)
                        if result:
                            signals.append(result)

                # Lọc tín hiệu
                qualified_signals = self.filter_and_rank_signals(signals, market_conditions)

                # Gửi tín hiệu tốt nhất
                for signal in qualified_signals:
                    # ✅ Bỏ qua tín hiệu ở lần chạy đầu tiên
                    if self.is_first_run:
                        print("🟡 Lần chạy đầu tiên - Không gửi tín hiệu cũ")
                        self.is_first_run = False
                        break

                    if self.risk_manager.can_send_signal(signal):
                        if self.signal_manager.should_send_signal(signal):
                            self.send_trading_signal(signal, market_conditions, df_main, symbol)
                            break  # Chỉ gửi 1 tín hiệu mỗi chu kỳ

            except Exception as e:
                error_msg = f"🔴 Lỗi phân tích {symbol}: {str(e)}"
                print(error_msg)
                send_telegram(error_msg)

    def send_trading_signal(self, signal, market_conditions, df, symbol):
        """Gửi tín hiệu giao dịch với thông tin chi tiết"""
        try:
            chart_path = f"chart_{signal['strategy'].lower()}_{symbol}.png"
            create_chart(df, symbol, signal['side'], 
                        signal['entry'], signal['sl'], signal['tp'], chart_path)

            # Tính toán risk/reward
            if signal['side'] == 'BUY':
                risk = (signal['entry'] - signal['sl']) / signal['entry'] * 100
                reward = (signal['tp'] - signal['entry']) / signal['entry'] * 100
            else:
                risk = (signal['sl'] - signal['entry']) / signal['entry'] * 100
                reward = (signal['entry'] - signal['tp']) / signal['entry'] * 100
            rr_ratio = reward / risk if risk > 0 else 0

            # Tạo message
            message = f"""🔔 **TÍN HIỆU GIAO DỊCH CHẤT LƯỢNG CAO** 🔔
📌 **Thông tin cơ bản:**
• Cặp: *{symbol}*
• Chiến lược: *{signal['strategy']}*
• Hướng: *{signal['side']}* 
• Độ tin cậy: {signal['final_confidence']:.1%} ⭐

💰 **Chi tiết lệnh:**
• Giá vào: `{signal['entry']:.8f}`
• Stop-Loss: `{signal['sl']:.8f}` (-{risk:.2f}%)
• Take-Profit: `{signal['tp']:.8f}` (+{reward:.2f}%)
• R/R Ratio: 1:{rr_ratio:.2f}

📊 **Điều kiện thị trường:**
• Xu hướng: {market_conditions['trend']}
• Volume: {market_conditions['volume_ratio']:.2f}x bình thường
• Volatility: {market_conditions['volatility']:.4f}

🕒 {datetime.now().strftime('%H:%M:%S - %d/%m/%Y')}
⚠️ *Luôn quản lý rủi ro và không đầu tư quá khả năng chịu đựng*"""

            send_telegram(message, chart_path)
            self.signal_manager.record_signal(signal)
            print(f"[{datetime.now()}] ✅ Đã gửi tín hiệu {signal['strategy']} cho {symbol}: {signal['side']} @ {signal['entry']:.6f}")
        except Exception as e:
            print(f"⚠️ Lỗi gửi tín hiệu: {e}")

    def responsive_sleep(self, total_seconds):
        """Sleep có thể bị interrupt khi bot_status thay đổi"""
        check_interval = 5
        elapsed = 0
        while elapsed < total_seconds and bot_status['is_running']:
            sleep_time = min(check_interval, total_seconds - elapsed)
            time.sleep(sleep_time)
            elapsed += sleep_time
            emit_update()

    def run_bot(self):
        print("🎯 Bot đã sẵn sàng...")
        while True:
            if not bot_status['is_running']:
                print("⏸️ Bot đã được tạm dừng")
                while not bot_status['is_running']:
                    time.sleep(2)
                    emit_update()
                print("▶️ Bot tiếp tục hoạt động")
            try:
                cycle_start = time.time()
                self.run_analysis_cycle()
                processing_time = time.time() - cycle_start
                sleep_time = max(60, 300 - processing_time)
                print(f"😴 Chờ {sleep_time:.0f}s... (Nhấn STOP để dừng)")
                self.responsive_sleep(sleep_time)
            except KeyboardInterrupt:
                print("🛑 Dừng bởi Ctrl+C")
                bot_status['is_running'] = False
                break
            except Exception as e:
                print(f"🔴 Lỗi: {e}")
                if bot_status['is_running']:
                    self.responsive_sleep(60)

if __name__ == "__main__":
    bot = TradingBot()
    bot.run_bot()