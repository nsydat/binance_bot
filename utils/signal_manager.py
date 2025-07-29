# utils/signal_manager.py
from datetime import datetime, timedelta

class SignalManager:
    def __init__(self):
        self.sent_signals = []  # Lưu các tín hiệu đã gửi
        self.max_signals_per_hour = 3
        self.min_signal_gap = timedelta(minutes=15)

    def should_send_signal(self, new_signal):
        """
        Kiểm tra xem có nên gửi tín hiệu mới không
        Dựa trên số lượng và khoảng cách thời gian
        """
        now = datetime.now()
        recent_signals = [
            s for s in self.sent_signals
            if now - s['timestamp'] < timedelta(hours=1)
        ]

        # Kiểm tra số lượng tín hiệu/giờ
        if len(recent_signals) >= self.max_signals_per_hour:
            return False

        # Kiểm tra khoảng cách với tín hiệu gần nhất
        if self.sent_signals:
            last_signal = self.sent_signals[-1]
            if now - last_signal['timestamp'] < self.min_signal_gap:
                return False

        return True

    def record_signal(self, signal):
        """
        Ghi lại tín hiệu đã gửi
        """
        self.sent_signals.append(signal.copy())
        # Dọn dẹp các tín hiệu cũ hơn 2 giờ
        two_hours_ago = datetime.now() - timedelta(hours=2)
        self.sent_signals = [s for s in self.sent_signals if s['timestamp'] > two_hours_ago]