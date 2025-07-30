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
  - **EMA + VWAP**: Theo xu hướng ổn định
  - **RSI Divergence**: Phát hiện đảo chiều sớm
  - **Supertrend + ATR**: Bắt trend mạnh, ít repaint
  - **MACD Signal**: Xác nhận động lượng
  - **Bollinger Bounce**: Giao dịch ngược khi quá mức
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
