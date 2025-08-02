# utils/risk_manager.py
from datetime import datetime, timedelta
import pandas as pd

class RiskManager:
    def __init__(self):
        # --- Quản lý tài sản ---
        self.initial_balance = 1000  # Số dư ban đầu
        self.current_balance = 1000  # Số dư hiện tại
        self.daily_pnl = 0  # Lợi nhuận/thua lỗ trong ngày
        self.peak_balance = 1000  # Đỉnh cao nhất (dùng cho Max Drawdown)
        self.total_trades = 0
        self.winning_trades = 0

        # --- Quản lý rủi ro ---
        self.max_risk_percent = 1.0  # Rủi ro tối đa 1% tài sản mỗi lệnh
        self.max_daily_drawdown = -5.0  # Dừng nếu thua >5% trong ngày
        self.max_drawdown = -15.0  # Dừng hoàn toàn nếu thua >15% từ đỉnh cao nhất
        self.max_daily_loss = -3.0  # Dừng nếu thua >3% trong ngày
        self.max_consecutive_losses = 5  # Dừng sau 5 lệnh thua liên tiếp

        # --- Quản lý chuỗi ---
        self.win_streak = 0
        self.loss_streak = 0
        self.current_day = datetime.now().date()

        # --- Quản lý tương quan cặp tiền ---
        self.correlated_pairs = {
            'BTCUSDT': ['ETHUSDT', 'ADAUSDT', 'SOLUSDT'],
            'ETHUSDT': ['SOLUSDT', 'BNBUSDT'],
            'XRPUSDT': ['ADAUSDT', 'DOTUSDT']
        }
        
        # --- Lịch sử giao dịch ---
        self.trade_history = []
        self.active_positions = []

    def can_send_signal(self, signal):
        """
        Kiểm tra rủi ro toàn diện trước khi gửi tín hiệu
        """
        # Reset daily stats nếu sang ngày mới
        self._reset_daily_if_needed()
        
        # Lớp 1: Kiểm tra Drawdown (Ngắt mạch)
        if self.daily_pnl <= self.max_daily_drawdown:
            print(f"⚠️ Dừng: Daily drawdown {self.daily_pnl:.2f}% <= {self.max_daily_drawdown}%")
            return False
            
        current_drawdown = (self.current_balance / self.peak_balance - 1) * 100
        if current_drawdown < self.max_drawdown:
            print(f"⚠️ Dừng: Max drawdown {current_drawdown:.2f}% <= {self.max_drawdown}%")
            return False

        # Lớp 2: Kiểm tra chuỗi thua
        if self.loss_streak >= self.max_consecutive_losses:
            print(f"⚠️ Dừng: Consecutive losses {self.loss_streak} >= {self.max_consecutive_losses}")
            return False

        # Lớp 3: Kiểm tra tương quan (Tránh rủi ro hệ thống)
        if self._has_conflicting_position(signal):
            print(f"⚠️ Dừng: Conflicting position với {signal['symbol']}")
            return False

        # Lớp 4: Kiểm tra điều kiện thị trường
        if not self._check_market_conditions(signal):
            return False

        return True

    def get_position_size(self, entry, sl, df):
        """
        Tính khối lượng giao dịch tối ưu (Lớp 2: Position Sizing)
        """
        # 1. Tính rủi ro động theo tài sản và chuỗi thắng/thua
        risk_amount = self._get_dynamic_risk_amount()

        # 2. Điều chỉnh theo biến động thị trường (ATR)
        volatility_adjustment = self._get_volatility_adjustment(df, entry)
        adjusted_risk = risk_amount * volatility_adjustment

        # 3. Điều chỉnh theo win rate
        win_rate_adjustment = self._get_win_rate_adjustment()
        adjusted_risk *= win_rate_adjustment

        # 4. Tính khối lượng
        risk_per_unit = abs(entry - sl)
        if risk_per_unit == 0:
            return 0.001  # Minimum position size
            
        position_size = adjusted_risk / risk_per_unit
        
        # Giới hạn min/max
        return max(0.001, min(0.1, position_size))

    def _get_dynamic_risk_amount(self):
        """
        Tính số tiền rủi ro động
        Tăng khi đang thắng, giảm khi đang thua
        """
        risk_multiplier = 1.0
        
        # Tăng rủi ro khi đang trong chuỗi thắng
        if self.win_streak >= 2:
            risk_multiplier = 1 + (self.win_streak * 0.1)  # Giảm từ 0.2 xuống 0.1
        # Giảm rủi ro khi đang trong chuỗi thua
        elif self.loss_streak >= 2:
            risk_multiplier = max(0.3, 1 - (self.loss_streak * 0.15))  # Giảm mạnh hơn
            
        # Tính số tiền rủi ro
        risk_percent = min(self.max_risk_percent * risk_multiplier, 2.0)  # Giảm từ 3% xuống 2%
        return (risk_percent / 100) * self.current_balance

    def _get_volatility_adjustment(self, df, entry):
        """
        Điều chỉnh theo biến động thị trường
        """
        try:
            from ta.volatility import AverageTrueRange
            atr = AverageTrueRange(df['high'], df['low'], df['close']).average_true_range().iloc[-1]
            volatility_ratio = atr / entry
            
            # Giảm khối lượng nếu biến động cao
            if volatility_ratio > 0.05:  # Biến động >5%
                return 0.5 / volatility_ratio
            elif volatility_ratio < 0.01:  # Biến động <1%
                return 1.2  # Tăng khối lượng
            else:
                return 1.0
        except:
            return 1.0

    def _get_win_rate_adjustment(self):
        """
        Điều chỉnh theo win rate
        """
        if self.total_trades == 0:
            return 1.0
            
        win_rate = self.winning_trades / self.total_trades
        
        if win_rate >= 0.7:  # Win rate >70%
            return 1.2
        elif win_rate >= 0.6:  # Win rate >60%
            return 1.1
        elif win_rate <= 0.4:  # Win rate <40%
            return 0.7
        else:
            return 1.0

    def _has_conflicting_position(self, signal):
        """
        Kiểm tra xem có lệnh đang mở trên cặp có tương quan không
        """
        for pos in self.active_positions:
            if signal['symbol'] in self.correlated_pairs.get(pos['symbol'], []):
                if signal['side'] == pos['side']:
                    return True
        return False

    def _check_market_conditions(self, signal):
        """
        Kiểm tra điều kiện thị trường
        """
        # Kiểm tra thời gian giao dịch (tránh thời điểm biến động cao)
        current_hour = datetime.now().hour
        if current_hour in [0, 8, 16]:  # Thời điểm news
            return False
            
        return True

    def _reset_daily_if_needed(self):
        """
        Reset daily stats nếu sang ngày mới
        """
        today = datetime.now().date()
        if today != self.current_day:
            self.daily_pnl = 0
            self.current_day = today
            print(f"🔄 Reset daily stats cho ngày {today}")

    def update_after_signal(self, signal, outcome, profit_pct):
        """
        Cập nhật trạng thái sau mỗi lệnh
        """
        # Cập nhật PNL
        self.daily_pnl += profit_pct
        
        # Cập nhật chuỗi thắng/thua
        if outcome == 'win':
            self.win_streak += 1
            self.loss_streak = 0
            self.winning_trades += 1
        else:
            self.loss_streak += 1
            self.win_streak = 0
            
        self.total_trades += 1
        
        # Cập nhật đỉnh cao nhất
        if self.current_balance > self.peak_balance:
            self.peak_balance = self.current_balance
            
        # Cập nhật số dư
        self.current_balance *= (1 + profit_pct / 100)
        
        # Ghi lại lịch sử
        self.trade_history.append({
            'timestamp': datetime.now(),
            'signal': signal,
            'outcome': outcome,
            'profit_pct': profit_pct,
            'balance': self.current_balance
        })

    def get_risk_summary(self):
        """
        Trả về tóm tắt tình trạng rủi ro
        """
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        current_drawdown = (self.current_balance / self.peak_balance - 1) * 100
        
        return {
            'current_balance': self.current_balance,
            'daily_pnl': self.daily_pnl,
            'win_rate': win_rate,
            'win_streak': self.win_streak,
            'loss_streak': self.loss_streak,
            'total_trades': self.total_trades,
            'current_drawdown': current_drawdown,
            'peak_balance': self.peak_balance
        }

    def add_active_position(self, position):
        """
        Thêm lệnh đang mở
        """
        self.active_positions.append(position)

    def remove_active_position(self, symbol):
        """
        Xóa lệnh đã đóng
        """
        self.active_positions = [p for p in self.active_positions if p['symbol'] != symbol]