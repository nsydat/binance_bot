# 🤖 Bot Tín Hiệu Binance Futures

Bot tự động phân tích thị trường và gửi tín hiệu giao dịch chất lượng cao cho Binance Futures.

## 🚀 Tính Năng Chính

### 📊 **Chiến Thuật Giao Dịch (5 Chiến Thuật)**
- **EMA + VWAP + RSI**: Kết hợp đường trung bình động với VWAP và RSI
- **Supertrend + RSI**: Chiến thuật trend-following với xác nhận RSI
- **Trend + Momentum + Volume**: Phân tích xu hướng, momentum và khối lượng
- **Breakout + Volume + S/R**: Giao dịch breakout với xác nhận khối lượng
- **Multi-Timeframe**: Xác nhận đa khung thời gian

### 🛡️ **Quản Lý Rủi Ro Nâng Cao**
- **Position Sizing**: Tính toán khối lượng tối ưu dựa trên rủi ro
- **Drawdown Protection**: Bảo vệ khỏi thua lỗ quá mức
- **Correlation Check**: Tránh rủi ro hệ thống từ các cặp tương quan
- **Win Rate Adjustment**: Điều chỉnh theo hiệu suất giao dịch
- **Volatility Adjustment**: Thích ứng với biến động thị trường
- **Market Condition Check**: Kiểm tra điều kiện thị trường

### 📈 **Quản Lý Tín Hiệu Thông Minh**
- **Signal Quality Filter**: Lọc tín hiệu theo độ tin cậy
- **Frequency Control**: Kiểm soát số lượng tín hiệu/giờ
- **Duplicate Prevention**: Tránh tín hiệu trùng lặp
- **Symbol-Specific Limits**: Giới hạn tín hiệu theo cặp tiền
- **Signal History**: Lưu trữ và phân tích lịch sử tín hiệu

### 🎯 **Tính Năng Nâng Cao**
- **Multi-Timeframe Confirmation**: Xác nhận đa khung thời gian
- **Real-time Dashboard**: Giao diện web theo dõi real-time
- **Telegram Integration**: Gửi tín hiệu và biểu đồ qua Telegram
- **Performance Analytics**: Phân tích hiệu suất chi tiết
- **Adaptive System**: Hệ thống thích nghi thông minh
  - Volatility-based R/R Ratio adjustment
  - Market condition-based strategy selection
  - Dynamic SL/TP calculation
  - Performance-based parameter optimization

## 📋 Yêu Cầu Hệ Thống

```bash
Python 3.8+
pandas
numpy
ta (Technical Analysis)
python-binance
flask
flask-socketio
requests
python-telegram-bot
```

## 🚀 Cài Đặt

### 1. Clone Repository
```bash
git clone <repository-url>
cd trading-bot
```

### 2. Cài Đặt Dependencies
```bash
pip install -r requirements.txt
```

### 3. Cấu Hình
Chỉnh sửa `config.json`:
```json
{
  "symbols": ["BTCUSDT", "ETHUSDT", "XRPUSDT"],
  "interval": "5m",
  "active_strategies": ["EMA_VWAP", "SUPERTREND_ATR", "TREND_MOMENTUM", "BREAKOUT_VOLUME", "MULTI_TIMEFRAME"],
  "risk_management": {
    "max_signals_per_hour": 5,
    "min_signal_gap_minutes": 15,
    "max_risk_percent": 1.0,
    "max_daily_drawdown": -5.0,
    "max_drawdown": -15.0,
    "signal_quality_threshold": 0.6
  }
}
```

### 4. Cấu Hình Telegram
Tạo file `.env`:
```
TELEGRAM_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 5. Chạy Bot
```bash
python bot.py
```

## 📊 Dashboard

Truy cập dashboard tại: `http://localhost:5000`

### Tính Năng Dashboard:
- **Real-time Monitoring**: Theo dõi trạng thái bot real-time
- **Signal Statistics**: Thống kê tín hiệu theo thời gian
- **Risk Management**: Hiển thị thông tin quản lý rủi ro
- **Performance Metrics**: Chỉ số hiệu suất chi tiết
- **Configuration Control**: Điều chỉnh cấu hình trực tiếp

## 🛡️ Quản Lý Rủi Ro

### **RiskManager Features:**
- **Dynamic Position Sizing**: Tính toán khối lượng dựa trên rủi ro và hiệu suất
- **Drawdown Protection**: Dừng giao dịch khi thua lỗ quá mức
- **Correlation Management**: Tránh rủi ro từ các cặp tương quan
- **Win Rate Adjustment**: Tăng/giảm rủi ro theo win rate
- **Volatility Adaptation**: Điều chỉnh theo biến động thị trường
- **Market Condition Filter**: Lọc theo điều kiện thị trường

### **SignalManager Features:**
- **Quality Filter**: Lọc tín hiệu theo độ tin cậy (≥60%)
- **Frequency Control**: Tối đa 5 tín hiệu/giờ
- **Gap Control**: Khoảng cách tối thiểu 15 phút
- **Duplicate Prevention**: Tránh tín hiệu trùng lặp
- **Symbol Limits**: Tối đa 2 tín hiệu/cặp/giờ
- **Signal History**: Lưu trữ và phân tích lịch sử

## 📈 Chiến Thuật Chi Tiết

### **1. EMA + VWAP + RSI**
- **Entry**: Giá cắt EMA + VWAP + RSI oversold/overbought
- **Exit**: RSI divergence hoặc trend reversal
- **Risk**: 1-2% per trade

### **2. Supertrend + RSI**
- **Entry**: Supertrend signal + RSI confirmation
- **Exit**: Supertrend reversal
- **Risk**: 1-2% per trade

### **3. Trend + Momentum + Volume**
- **Entry**: Trend alignment + momentum + volume spike
- **Exit**: Momentum exhaustion
- **Risk**: 1-2% per trade

### **4. Breakout + Volume + S/R**
- **Entry**: Breakout với volume confirmation
- **Exit**: Support/Resistance levels
- **Risk**: 1-2% per trade

### **5. Multi-Timeframe**
- **Entry**: Higher timeframe trend + lower timeframe signal
- **Exit**: Multi-timeframe reversal
- **Risk**: 1-2% per trade

## 🔧 Cấu Hình Nâng Cao

### **Risk Management Parameters:**
```json
{
  "max_risk_percent": 1.0,           // Rủi ro tối đa mỗi lệnh
  "max_daily_drawdown": -5.0,        // Dừng nếu thua >5%/ngày
  "max_drawdown": -15.0,             // Dừng nếu thua >15% từ đỉnh
  "max_consecutive_losses": 5,       // Dừng sau 5 lệnh thua liên tiếp
  "signal_quality_threshold": 0.6    // Ngưỡng chất lượng tín hiệu
}
```

### **Performance Parameters:**
```json
{
  "data_cache_minutes": 2,           // Cache dữ liệu 2 phút
  "parallel_strategy_execution": true, // Chạy song song các chiến thuật
  "enable_signal_history": true,     // Lưu lịch sử tín hiệu
  "enable_risk_logging": true        // Log quản lý rủi ro
}
```

## 📊 Backtesting

### **Chạy Comprehensive Test:**
```bash
python test_strategy_improvements.py
```

### **Chạy Realistic Backtest:**
```bash
python run_realistic_backtest.py
```

### **Backtest Features:**
- **Realistic Simulation**: Slippage, fees, execution failures
- **Strategy Performance**: Hiệu suất từng chiến thuật
- **Risk Analysis**: Phân tích rủi ro chi tiết
- **Portfolio Simulation**: Mô phỏng danh mục
- **Performance Metrics**: Sharpe ratio, drawdown, win rate
- **Overfitting Detection**: Tự động phát hiện overfitting

## 🚨 Cảnh Báo Rủi Ro

⚠️ **QUAN TRỌNG**: 
- Bot này chỉ cung cấp tín hiệu, không tự động giao dịch
- Luôn quản lý rủi ro và không đầu tư quá khả năng
- Past performance không đảm bảo future results
- Cryptocurrency trading có rủi ro cao

## 📝 Version History

### **Version 2.3: Hệ Thống Adaptive**
- ✅ Tích hợp AdaptiveSystem với volatility analysis
- ✅ Volatility-based R/R ratio adjustment
- ✅ Market condition-based strategy selection
- ✅ Dynamic SL/TP calculation
- ✅ Performance-based parameter optimization
- ✅ Dashboard integration với adaptive insights
- ✅ Comprehensive testing và documentation

### **Version 2.2: Quản Lý Rủi Ro Nâng Cao**
- ✅ Cải tiến RiskManager với position sizing động
- ✅ Nâng cấp SignalManager với quality filter
- ✅ Tích hợp đầy đủ quản lý rủi ro vào bot
- ✅ Thêm thống kê và analytics nâng cao
- ✅ Cải tiến dashboard với risk monitoring
- ✅ Tối ưu hóa performance và error handling

### **Version 2.1: Mở Rộng 6 Chiến Thuật**
- ✅ Thêm 2 chiến thuật mới
- ✅ Cải tiến multi-timeframe confirmation
- ✅ Tối ưu hóa performance
- ✅ Cải tiến error handling

### **Version 2.0: Clean Code & Optimization**
- ✅ Refactor toàn bộ codebase
- ✅ Tối ưu hóa performance
- ✅ Cải tiến error handling
- ✅ Thêm comprehensive logging
- ✅ Cải tiến documentation

## 🤝 Đóng Góp

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## 📞 Liên Hệ

- **Email**: [your-email@example.com]
- **Telegram**: [@your-telegram]
- **GitHub**: [your-github-profile]

---

⭐ **Nếu project này hữu ích, hãy cho một star!** ⭐
