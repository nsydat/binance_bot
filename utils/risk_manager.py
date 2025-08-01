#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Risk manager for controlling trading signals
"""

from datetime import datetime, timedelta

class RiskManager:
    def __init__(self):
        self.signal_history = []
        self.max_signals_per_hour = 6  # Cập nhật theo số chiến thuật
        self.max_drawdown = 10  # % (nếu có theo dõi PnL)
        self.initial_balance = 1000
        self.current_balance = 1000

    def can_send_signal(self, signal):
        """Kiểm tra xem có được phép gửi tín hiệu không"""
        now = datetime.now()

        # Lọc lịch sử trong 1 giờ qua
        one_hour_ago = now - timedelta(hours=1)
        recent_signals = [s for s in self.signal_history if s['timestamp'] > one_hour_ago]

        # Không quá max_signals_per_hour lệnh/giờ
        if len(recent_signals) >= self.max_signals_per_hour:
            return False

        # Thêm tín hiệu vào lịch sử
        signal_copy = signal.copy()
        signal_copy['timestamp'] = now
        self.signal_history.append(signal_copy)

        # Dọn dẹp lịch sử > 2 giờ
        self.signal_history = [s for s in self.signal_history if s['timestamp'] > now - timedelta(hours=2)]

        return True