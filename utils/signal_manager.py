# utils/signal_manager.py
from datetime import datetime, timedelta
import json

class SignalManager:
    def __init__(self):
        self.sent_signals = []  # Lưu các tín hiệu đã gửi
        self.max_signals_per_hour = 5
        self.min_signal_gap = timedelta(minutes=15)
        self.max_signals_per_symbol = 2  # Tối đa 2 tín hiệu/cặp/giờ
        self.signal_quality_threshold = 0.6  # Ngưỡng chất lượng tín hiệu
        self.signal_history_file = "signal_history.json"
        self._load_signal_history()

    def should_send_signal(self, new_signal):
        """
        Kiểm tra xem có nên gửi tín hiệu mới không
        Dựa trên số lượng, khoảng cách thời gian và chất lượng
        """
        now = datetime.now()
        
        # 1. Kiểm tra chất lượng tín hiệu
        if new_signal.get('final_confidence', 0) < self.signal_quality_threshold:
            print(f"⚠️ Tín hiệu bị từ chối: Confidence {new_signal.get('final_confidence', 0):.2f} < {self.signal_quality_threshold}")
            return False

        # 2. Kiểm tra số lượng tín hiệu trong 1 giờ qua
        recent_signals = [
            s for s in self.sent_signals
            if now - s['timestamp'] < timedelta(hours=1)
        ]
        if len(recent_signals) >= self.max_signals_per_hour:
            print(f"⚠️ Đã đạt giới hạn {self.max_signals_per_hour} tín hiệu/giờ")
            return False

        # 3. Kiểm tra số lượng tín hiệu cho cặp tiền cụ thể
        symbol_signals = [
            s for s in recent_signals
            if s.get('symbol') == new_signal.get('symbol')
        ]
        if len(symbol_signals) >= self.max_signals_per_symbol:
            print(f"⚠️ Đã đạt giới hạn {self.max_signals_per_symbol} tín hiệu cho {new_signal.get('symbol')}")
            return False

        # 4. Kiểm tra khoảng cách với tín hiệu gần nhất
        if self.sent_signals:
            last_signal = self.sent_signals[-1]
            if now - last_signal['timestamp'] < self.min_signal_gap:
                remaining_time = self.min_signal_gap - (now - last_signal['timestamp'])
                print(f"⏳ Chờ thêm {remaining_time.seconds//60} phút trước khi gửi tín hiệu mới")
                return False

        # 5. Kiểm tra trùng lặp tín hiệu
        if self._is_duplicate_signal(new_signal):
            print(f"⚠️ Tín hiệu trùng lặp cho {new_signal.get('symbol')}")
            return False

        return True

    def _is_duplicate_signal(self, new_signal):
        """
        Kiểm tra xem có phải tín hiệu trùng lặp không
        """
        recent_signals = [
            s for s in self.sent_signals
            if datetime.now() - s['timestamp'] < timedelta(hours=2)
        ]
        
        for signal in recent_signals:
            if (signal.get('symbol') == new_signal.get('symbol') and
                signal.get('side') == new_signal.get('side') and
                signal.get('strategy') == new_signal.get('strategy')):
                return True
        return False

    def record_signal(self, signal):
        """
        Ghi lại tín hiệu đã gửi
        """
        signal_with_timestamp = signal.copy()
        signal_with_timestamp['timestamp'] = datetime.now()
        signal_with_timestamp['sent'] = True
        
        self.sent_signals.append(signal_with_timestamp)
        self._save_signal_history()
        
        # Dọn dẹp các tín hiệu cũ hơn 24 giờ
        one_day_ago = datetime.now() - timedelta(hours=24)
        self.sent_signals = [s for s in self.sent_signals if s['timestamp'] > one_day_ago]

    def get_signal_statistics(self):
        """
        Trả về thống kê tín hiệu
        """
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(hours=24)
        
        recent_signals = [s for s in self.sent_signals if s['timestamp'] > one_hour_ago]
        daily_signals = [s for s in self.sent_signals if s['timestamp'] > one_day_ago]
        
        # Thống kê theo chiến lược
        strategy_stats = {}
        for signal in daily_signals:
            strategy = signal.get('strategy', 'Unknown')
            if strategy not in strategy_stats:
                strategy_stats[strategy] = 0
            strategy_stats[strategy] += 1
        
        # Thống kê theo cặp tiền
        symbol_stats = {}
        for signal in daily_signals:
            symbol = signal.get('symbol', 'Unknown')
            if symbol not in symbol_stats:
                symbol_stats[symbol] = 0
            symbol_stats[symbol] += 1
        
        return {
            'signals_last_hour': len(recent_signals),
            'signals_last_day': len(daily_signals),
            'strategy_distribution': strategy_stats,
            'symbol_distribution': symbol_stats,
            'max_signals_per_hour': self.max_signals_per_hour,
            'min_signal_gap_minutes': self.min_signal_gap.seconds // 60
        }

    def get_recent_signals(self, hours=1):
        """
        Lấy danh sách tín hiệu gần đây
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [s for s in self.sent_signals if s['timestamp'] > cutoff_time]

    def _load_signal_history(self):
        """
        Tải lịch sử tín hiệu từ file
        """
        try:
            with open(self.signal_history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.sent_signals = []
                for signal_data in data:
                    # Convert string timestamp back to datetime
                    signal_data['timestamp'] = datetime.fromisoformat(signal_data['timestamp'])
                    self.sent_signals.append(signal_data)
            print(f"✅ Đã tải {len(self.sent_signals)} tín hiệu từ lịch sử")
        except FileNotFoundError:
            print("📝 Tạo file lịch sử tín hiệu mới")
        except Exception as e:
            print(f"⚠️ Lỗi tải lịch sử tín hiệu: {e}")

    def _save_signal_history(self):
        """
        Lưu lịch sử tín hiệu vào file
        """
        try:
            # Convert datetime to string for JSON serialization
            data_to_save = []
            for signal in self.sent_signals:
                signal_copy = signal.copy()
                signal_copy['timestamp'] = signal_copy['timestamp'].isoformat()
                data_to_save.append(signal_copy)
            
            with open(self.signal_history_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Lỗi lưu lịch sử tín hiệu: {e}")

    def clear_old_signals(self, days=7):
        """
        Xóa tín hiệu cũ hơn số ngày chỉ định
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        old_count = len(self.sent_signals)
        self.sent_signals = [s for s in self.sent_signals if s['timestamp'] > cutoff_time]
        new_count = len(self.sent_signals)
        print(f"🧹 Đã xóa {old_count - new_count} tín hiệu cũ")
        self._save_signal_history()

    def update_config(self, new_config):
        """
        Cập nhật cấu hình từ config.json
        """
        if 'max_signals_per_hour' in new_config:
            self.max_signals_per_hour = new_config['max_signals_per_hour']
        if 'min_signal_gap_minutes' in new_config:
            self.min_signal_gap = timedelta(minutes=new_config['min_signal_gap_minutes'])
        print(f"✅ Đã cập nhật cấu hình SignalManager")