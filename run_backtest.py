# run_backtest.py
from backtest.backtest_engine import run_backtest
from backtest.performance_report import generate_report
from backtest.chart import plot_backtest_results

# Chạy backtest
results = run_backtest(symbol="DOGEUSDT", days=60)

# Tạo báo cáo
report = generate_report(results)

# Vẽ biểu đồ
plot_backtest_results(results)