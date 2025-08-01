# 🚀 Bot Tín Hiệu Binance Futures (Cải Tiến)

Bot giám sát thị trường crypto (BTC, ETH, DOGE, XRP...) và **gửi tín hiệu mua/bán về Telegram** – **chỉ cảnh báo, không tự động giao dịch**, đảm bảo **an toàn tuyệt đối**.

Dùng để:
- Theo dõi cơ hội giao dịch 24/7
- Hỗ trợ ra quyết định giao dịch
- Học hỏi chiến lược từ các hệ thống quant

---

## 📦 Tính năng chính

- ✅ Quét nhiều cặp: `BTCUSDT`, `ETHUSDT`, `DOGEUSDT`, `XRPUSDT`
- ✅ 5 chiến lược hiệu quả:
  - **EMA + VWAP + RSI**: Theo xu hướng ổn định với xác nhận RSI
  - **Supertrend + RSI**: Bắt trend mạnh với RSI quá mua/bán
  - **Trend + Momentum + Volume**: Kết hợp xu hướng, động lượng và khối lượng
  - **Breakout + Volume + S/R**: Phát hiện breakout với xác nhận khối lượng
  - **Multi-Timeframe**: Chiến lược đa khung thời gian với weighted voting
- ✅ Đa khung thời gian: Xác nhận tín hiệu từ khung lớn hơn
- ✅ Quản lý rủi ro: Giới hạn tín hiệu/giờ, khoảng cách giữa tín hiệu
- ✅ Phân tích thị trường: Tự động nhận diện xu hướng, volatility, volume
- ✅ Gửi **tin nhắn + biểu đồ** lên Telegram
- ✅ Cache dữ liệu & xử lý song song → hiệu suất cao
- ✅ Dashboard theo dõi realtime (Flask + SocketIO)

---

## 📅 Lịch sử Phiên bản (Version History)

### **Version 1.0: Khởi tạo với 3 chiến thuật cơ bản**
- ✅ Tích hợp 3 chiến lược đơn giản: EMA Cross, RSI Range, Breakout
- ✅ Gửi tín hiệu cơ bản qua Telegram
- ✅ Cấu trúc OOP cơ bản
- ✅ Cache dữ liệu đơn giản

### **Version 2.0: Nâng cấp chuyên nghiệp**
- ✅ Thêm 2 chiến lược phức tạp: **RSI Divergence**, **Bollinger Bounce**
- ✅ Tích hợp **quản lý rủi ro**: giới hạn tín hiệu/giờ, khoảng cách
- ✅ **Phân tích điều kiện thị trường**: xu hướng, volatility, volume
- ✅ **Đa khung thời gian**: xác nhận tín hiệu bằng khung lớn hơn
- ✅ **Xử lý song song** (`ThreadPoolExecutor`)
- ✅ **Dashboard realtime** với điều khiển từ xa
- ✅ **Tối ưu hiệu suất** và cấu trúc code

### **Version 2.1: Mở rộng 6 chiến thuật**
- ✅ **Nâng cấp lên 6 chiến thuật**: Thêm **Multi-Timeframe Strategy**
- ✅ **Cải tiến các chiến thuật hiện có**: Tối ưu hóa logic và tham số
- ✅ **Hỗ trợ đầy đủ multi-timeframe**: Tất cả chiến thuật đều hỗ trợ xác nhận từ khung thời gian cao hơn
- ✅ **Tăng cường ThreadPoolExecutor**: Từ 3 lên 6 workers để xử lý song song hiệu quả hơn
- ✅ **Cập nhật risk management**: Tăng max_signals_per_hour lên 6 để phù hợp với số lượng chiến thuật

### **Version 2.2: Clean Code & Optimization**
- ✅ **Làm sạch source code**: Loại bỏ imports và code dư thừa
- ✅ **Cải tiến error handling**: Thêm try-catch và logging tốt hơn
- ✅ **Tối ưu hóa performance**: Sử dụng strategy mapping thay vì if-elif
- ✅ **Cải tiến Telegram**: Thêm parse_mode Markdown và error handling
- ✅ **Cải tiến data fetcher**: Tối ưu hóa việc convert numeric data
- ✅ **Xóa code không cần thiết**: Loại bỏ models/strategy_selector.py và test files
- ✅ **Cập nhật documentation**: Cải tiến comments và docstrings

### **Version 3.0 (Coming Soon): AI & Machine Learning**
- ✅ **AI chọn chiến lược**: Dùng XGBoost để chọn chiến lược tốt nhất theo thị trường
- ✅ **Tự học (Self-learning)**: Cập nhật mô hình hàng ngày
- ✅ **Backtest tự động**: Chạy thử hiệu suất trên dữ liệu quá khứ
- ✅ **Tích hợp TradingView Webhook**
- ✅ **Báo cáo hiệu suất định kỳ** (tuần, tháng)

---

## 🛠 Cài đặt

```bash
git clone https://github.com/yourname/binance-signal-bot.git
cd binance-signal-bot
pip install -r requirements.txt
