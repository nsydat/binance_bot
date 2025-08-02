#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot Tín Hiệu Binance Futures - Phiên bản 2.2
Hỗ trợ 5 chiến thuật với quản lý rủi ro nâng cao
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
from utils.adaptive_system import AdaptiveSystem
from dashboard.app import bot_status, log, emit_update, socketio

# Import strategies
from strategies.ema_vwap_rsi import ema_vwap_rsi_strategy as strategy_ema_vwap
from strategies.supertrend_rsi import supertrend_rsi_strategy as strategy_supertrend_atr
from strategies.trend_momentum_volume import trend_momentum_volume_strategy as strategy_trend_momentum
from strategies.breakout_volume_sr import breakout_volume_sr_strategy as strategy_breakout_volume
from strategies.multi_timeframe import multi_timeframe_strategy as strategy_multi_timeframe

print(f"🚀 Bot Tín Hiệu Binance Futures (Quản Lý Rủi Ro Nâng Cao) khởi động lúc {datetime.now()}")

class TradingBot:
    def __init__(self):
        self.is_first_run = True
        self.signal_manager = SignalManager()
        self.risk_manager = RiskManager()
        self.adaptive_system = AdaptiveSystem()
        self.data_cache = {}
        self.last_cache_update = {}
        self.update_dashboard_config()
        self._update_managers_config()
        # Khởi động dashboard trong thread riêng
        Thread(target=self.run_dashboard, daemon=True).start()

    def _update_managers_config(self):
        """
        Cập nhật cấu hình cho các manager
        """
        # Cập nhật SignalManager
        signal_config = {
            'max_signals_per_hour': config['risk_management']['max_signals_per_hour'],
            'min_signal_gap_minutes': config['risk_management']['min_signal_gap_minutes']
        }
        self.signal_manager.update_config(signal_config)
        
        # Cập nhật RiskManager
        risk_config = config['risk_management']
        self.risk_manager.max_risk_percent = risk_config.get('max_risk_percent', 1.0)
        self.risk_manager.max_daily_drawdown = risk_config.get('max_daily_drawdown', -5.0)
        self.risk_manager.max_drawdown = risk_config.get('max_drawdown', -15.0)
        self.risk_manager.max_daily_loss = risk_config.get('max_daily_loss', -3.0)
        self.risk_manager.max_consecutive_losses = risk_config.get('max_consecutive_losses', 5)
        
        print("✅ Đã cập nhật cấu hình quản lý rủi ro")

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
            'max_signals_per_hour': config['risk_management']['max_signals_per_hour'],
            'risk_management': config['risk_management']
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
        
        if strategy_name not in strategy_map:
            print(f"❌ Chiến lược {strategy_name} không tồn tại")
            return None
            
        try:
            strategy_func = strategy_map[strategy_name]
            signal = strategy_func(df, df_higher)
            
            if signal:
                signal['strategy'] = strategy_name
                signal['timestamp'] = datetime.now()
                return signal
        except Exception as e:
            print(f"❌ Lỗi thực thi chiến lược {strategy_name}: {e}")
            
        return None

    def analyze_market_conditions(self, df):
        """Phân tích điều kiện thị trường với hệ thống adaptive"""
        try:
            # Sử dụng adaptive system để phân tích
            market_conditions = self.adaptive_system.detect_market_regime(df)
            
            # Thêm thông tin bổ sung
            market_conditions['current_price'] = df['close'].iloc[-1]
            market_conditions['atr'] = self.adaptive_system.calculate_volatility(df) * df['close'].iloc[-1]
            
            return market_conditions
        except Exception as e:
            print(f"❌ Lỗi phân tích điều kiện thị trường: {e}")
            return {'regime': 'UNKNOWN', 'volatility': 0.02, 'volume_ratio': 1.0}
    
    def get_adaptive_strategies(self, market_conditions):
        """
        Trả về danh sách chiến lược phù hợp với điều kiện thị trường hiện tại
        """
        # Sử dụng adaptive system để chọn chiến lược
        strategies = self.adaptive_system.get_adaptive_strategies(market_conditions)
        
        # Map strategy names to actual strategy functions
        strategy_mapping = {
            'EMA_VWAP': 'EMA_VWAP',
            'SUPERTREND_ATR': 'SUPERTREND_ATR', 
            'TREND_MOMENTUM': 'TREND_MOMENTUM',
            'BREAKOUT_VOLUME': 'BREAKOUT_VOLUME',
            'MULTI_TIMEFRAME': 'MULTI_TIMEFRAME'
        }
        
        # Convert to actual strategy names
        active_strategies = []
        for strategy in strategies:
            if strategy in strategy_mapping:
                active_strategies.append(strategy_mapping[strategy])
        
        return active_strategies

    def filter_and_rank_signals(self, signals, market_conditions):
        """Lọc và xếp hạng tín hiệu với adaptive system"""
        if not signals:
            return []
            
        for signal in signals:
            # Tính điểm tin cậy dựa trên điều kiện thị trường
            confidence = signal.get('confidence', 0.5)
            
            # Điều chỉnh theo market regime
            regime = market_conditions.get('regime', 'UNKNOWN')
            if regime in ['BULLISH_TRENDING', 'BEARISH_TRENDING']:
                if (regime == 'BULLISH_TRENDING' and signal['side'] == 'BUY') or \
                   (regime == 'BEARISH_TRENDING' and signal['side'] == 'SELL'):
                    confidence *= 1.3  # Tăng confidence trong trending markets
                else:
                    confidence *= 0.7  # Giảm confidence cho signals ngược trend
            elif regime == 'VOLATILE':
                confidence *= 0.9  # Giảm confidence trong volatile markets
            elif regime in ['SIDEWAYS', 'CONSOLIDATION']:
                confidence *= 0.8
                
            # Điều chỉnh theo volume
            volume_ratio = market_conditions.get('volume_ratio', 1.0)
            if volume_ratio > 1.5:
                confidence *= 1.1
            elif volume_ratio < 0.5:
                confidence *= 0.9
                
            # Điều chỉnh theo volatility
            volatility = market_conditions.get('volatility', 0.02)
            if volatility > 0.05:
                confidence *= 0.9  # Giảm confidence trong high volatility
            elif volatility < 0.02:
                confidence *= 1.05  # Tăng confidence trong low volatility
                
            signal['final_confidence'] = min(confidence, 1.0)
            
        # Sắp xếp theo độ tin cậy
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

                # Phân tích điều kiện thị trường với adaptive system
                market_conditions = self.analyze_market_conditions(df_main)
                print(f"📊 {symbol}: {market_conditions.get('regime', 'UNKNOWN')}, Vol: {market_conditions.get('volatility', 0):.3f}, VolRatio: {market_conditions.get('volume_ratio', 1.0):.2f}")

                # Lấy adaptive strategies
                adaptive_strategies = self.get_adaptive_strategies(market_conditions)
                print(f"🎯 Adaptive strategies cho {symbol}: {adaptive_strategies}")

                # Chạy chiến lược adaptive
                signals = []
                max_workers = len(adaptive_strategies)
                
                if config['performance']['parallel_strategy_execution']:
                    with ThreadPoolExecutor(max_workers=max_workers) as executor:
                        futures = [
                            executor.submit(self.execute_strategy, strategy, df_main, df_higher)
                            for strategy in adaptive_strategies
                        ]
                        for future in futures:
                            result = future.result()
                            if result:
                                signals.append(result)
                else:
                    for strategy in adaptive_strategies:
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

                    # Thêm thông tin symbol vào signal
                    signal['symbol'] = symbol
                    
                    # Kiểm tra quản lý rủi ro
                    if not self.risk_manager.can_send_signal(signal):
                        print(f"⚠️ Tín hiệu {signal['strategy']} bị từ chối bởi RiskManager")
                        continue
                        
                    # Kiểm tra quản lý tín hiệu
                    if not self.signal_manager.should_send_signal(signal):
                        print(f"⚠️ Tín hiệu {signal['strategy']} bị từ chối bởi SignalManager")
                        continue
                        
                    # Gửi tín hiệu
                    self.send_trading_signal(signal, market_conditions, df_main, symbol)
                    
                    # Ghi lại tín hiệu
                    self.signal_manager.record_signal(signal)
                    
                    # Cập nhật dashboard
                    self._update_dashboard_stats()
                    
                    break  # Chỉ gửi 1 tín hiệu mỗi chu kỳ

            except Exception as e:
                error_msg = f"🔴 Lỗi phân tích {symbol}: {str(e)}"
                print(error_msg)
                send_telegram(error_msg)

    def _update_dashboard_stats(self):
        """
        Cập nhật thống kê lên dashboard
        """
        try:
            # Cập nhật thống kê tín hiệu
            signal_stats = self.signal_manager.get_signal_statistics()
            risk_summary = self.risk_manager.get_risk_summary()
            
            bot_status['signal_stats'] = signal_stats
            bot_status['risk_summary'] = risk_summary
            bot_status['last_update'] = datetime.now().isoformat()
            
            emit_update()
        except Exception as e:
            print(f"⚠️ Lỗi cập nhật dashboard: {e}")

    def send_trading_signal(self, signal, market_conditions, df, symbol):
        """Gửi tín hiệu giao dịch với adaptive system"""
        try:
            # Tính toán adaptive SL/TP và R/R ratio
            atr = market_conditions.get('atr', 0.02 * signal['entry'])
            adaptive_sl, adaptive_tp = self.adaptive_system.calculate_adaptive_sl_tp(
                signal['entry'], signal['side'], market_conditions, atr
            )
            
            # Tính adaptive R/R ratio
            adaptive_rr_ratio = self.adaptive_system.calculate_adaptive_rr_ratio(market_conditions)
            
            # Cập nhật signal với adaptive values
            signal['sl'] = adaptive_sl
            signal['tp'] = adaptive_tp
            signal['rr_ratio'] = adaptive_rr_ratio
            
            chart_path = f"chart_{signal['strategy'].lower()}_{symbol}.png"
            create_chart(df, symbol, signal['side'], 
                        signal['entry'], signal['sl'], signal['tp'], chart_path)

            # Tính toán risk/reward với adaptive values
            if signal['side'] == 'BUY':
                risk = (signal['entry'] - signal['sl']) / signal['entry'] * 100
                reward = (signal['tp'] - signal['entry']) / signal['entry'] * 100
            else:
                risk = (signal['sl'] - signal['entry']) / signal['entry'] * 100
                reward = (signal['entry'] - signal['tp']) / signal['entry'] * 100
            rr_ratio = reward / risk if risk > 0 else 0

            # Lấy market insights
            market_insights = self.adaptive_system.get_market_insights(market_conditions)
            
            # Lấy thông tin quản lý rủi ro
            risk_summary = self.risk_manager.get_risk_summary()
            signal_stats = self.signal_manager.get_signal_statistics()

            # Tạo message với adaptive information
            message = f"""🔔 **TÍN HIỆU GIAO DỊCH ADAPTIVE** 🔔
📌 **Thông tin cơ bản:**
• Cặp: *{symbol}*
• Chiến lược: *{signal['strategy']}*
• Hướng: *{signal['side']}* 
• Độ tin cậy: {signal['final_confidence']:.1%} ⭐

💰 **Chi tiết lệnh (Adaptive):**
• Giá vào: `{signal['entry']:.8f}`
• Stop-Loss: `{signal['sl']:.8f}` (-{risk:.2f}%)
• Take-Profit: `{signal['tp']:.8f}` (+{reward:.2f}%)
• R/R Ratio: 1:{rr_ratio:.2f}

📊 **Điều kiện thị trường (Adaptive):**
• Market Regime: {market_conditions.get('regime', 'UNKNOWN')}
• Volatility: {market_conditions.get('volatility', 0):.3f} ({market_insights['volatility_regime']})
• Volume: {market_conditions.get('volume_ratio', 1.0):.2f}x bình thường
• Risk Level: {market_insights['risk_level']}

🎯 **Adaptive Insights:**
• Recommended R/R: 1:{adaptive_rr_ratio:.2f}
• Market Regime: {market_insights['market_regime']}
• Optimal Strategies: {', '.join(market_insights['strategy_recommendations'])}

🛡️ **Quản lý rủi ro:**
• Win Rate: {risk_summary['win_rate']:.1f}%
• Chuỗi thắng: {risk_summary['win_streak']}
• Drawdown: {risk_summary['current_drawdown']:.2f}%
• Tổng lệnh: {risk_summary['total_trades']}

📈 **Thống kê tín hiệu:**
• Tín hiệu/giờ: {signal_stats['signals_last_hour']}/{signal_stats['max_signals_per_hour']}
• Tín hiệu/ngày: {signal_stats['signals_last_day']}

⏰ **Thời gian:** {datetime.now().strftime('%H:%M:%S')}"""

            # Gửi tín hiệu
            send_telegram(message, chart_path)
            
            # Cập nhật performance history
            self.adaptive_system.update_performance_history({
                'strategy': signal['strategy'],
                'market_regime': market_conditions.get('regime'),
                'rr_ratio': rr_ratio,
                'volatility': market_conditions.get('volatility'),
                'confidence': signal['final_confidence']
            })
            
            # Log
            log_msg = f"✅ Đã gửi tín hiệu adaptive {signal['strategy']} cho {symbol} (Confidence: {signal['final_confidence']:.1%}, R/R: 1:{rr_ratio:.2f})"
            print(log_msg)
            log(log_msg)

        except Exception as e:
            error_msg = f"❌ Lỗi gửi tín hiệu {symbol}: {str(e)}"
            print(error_msg)
            send_telegram(error_msg)

    def responsive_sleep(self, total_seconds):
        """Ngủ thông minh với khả năng dừng"""
        interval = 5  # Kiểm tra mỗi 5 giây
        for _ in range(total_seconds // interval):
            time.sleep(interval)
        time.sleep(total_seconds % interval)

    def run_bot(self):
        """Chạy bot chính"""
        print("🚀 Bot đang chạy...")
        print(f"📊 Cặp tiền: {', '.join(config['symbols'])}")
        print(f"⏰ Interval: {config['interval']}")
        print(f"🎯 Chiến lược: {', '.join(config['active_strategies'])}")
        print(f"🛡️ Quản lý rủi ro: {config['risk_management']['max_signals_per_hour']} tín hiệu/giờ")
        
        while True:
            try:
                self.run_analysis_cycle()
                self.responsive_sleep(300)  # 5 phút
            except KeyboardInterrupt:
                print("\n🛑 Bot đã dừng bởi người dùng")
                break
            except Exception as e:
                error_msg = f"❌ Lỗi chính: {str(e)}"
                print(error_msg)
                send_telegram(error_msg)
                time.sleep(60)  # Chờ 1 phút trước khi thử lại

if __name__ == "__main__":
    bot = TradingBot()
    bot.run_bot()