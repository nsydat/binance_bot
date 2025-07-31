# run_multi_backtest.py
from backtest.backtest_engine import run_backtest
from backtest.performance_report import generate_report
from backtest.chart import plot_backtest_results
import pandas as pd
import os

# Danh sách để lưu tất cả báo cáo
all_reports = []

# Cấu hình thử nghiệm
symbols = ["BTCUSDT", "ETHUSDT", "DOGEUSDT", "XRPUSDT"]
intervals = ["5m", "15m", "1h"]
days_list = [30, 60, 90]
initial_balance = 1000

print("🚀 BẮT ĐẦU CHẠY BACKTEST NHIỀU CẶP & KHUNG THỜI GIAN")

# Tạo thư mục lưu kết quả
os.makedirs("backtest/results", exist_ok=True)

for symbol in symbols:
    for interval in intervals:
        for days in days_list:
            print(f"\n🔄 Chạy backtest: {symbol} | {interval} | {days} ngày")
            
            # Chạy backtest
            results = run_backtest(symbol=symbol, interval=interval, days=days, initial_balance=initial_balance)
            
            if results is not None and len(results) > 0:
                # Tạo báo cáo
                report = generate_report(results, initial_balance=initial_balance)
                
                # Thêm thông tin vào báo cáo
                report['symbol'] = symbol
                report['interval'] = interval
                report['days'] = days
                
                # Lưu vào danh sách
                all_reports.append(report)
                
                # Lưu báo cáo riêng
                report_file = f"backtest/results/report_{symbol}_{interval}_{days}d.csv"
                results.to_csv(report_file.replace('.csv', '_signals.csv'), index=False)
                plot_backtest_results(results, save_path=report_file.replace('.csv', '.png'))
            else:
                print(f"❌ Không có tín hiệu cho {symbol} ({interval}, {days} ngày)")

# Tạo báo cáo tổng hợp
if all_reports:
    summary_df = pd.DataFrame(all_reports)
    summary_df = summary_df[[
        'symbol', 'interval', 'days', 'total_signals', 'win_rate', 
        'profit_pct', 'max_drawdown', 'sharpe_ratio', 'final_balance'
    ]]
    summary_df.sort_values('profit_pct', ascending=False, inplace=True)
    
    # Lưu báo cáo tổng hợp
    summary_df.to_csv("backtest/results/summary_report.csv", index=False)
    print("\n✅ Báo cáo tổng hợp đã lưu tại: backtest/results/summary_report.csv")
    print("\n📊 TOP 10 KẾT QUẢ TỐT NHẤT:")
    print(summary_df.head(10).to_string(index=False))
else:
    print("❌ Không có báo cáo nào được tạo")

print("\n✅ HOÀN TẤT CHẠY BACKTEST NHIỀU CẶP")