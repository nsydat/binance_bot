# backtest/chart.py
import matplotlib.pyplot as plt
import pandas as pd

def plot_backtest_results(results, save_path="backtest/results.png"):
    """
    Vẽ biểu đồ hiệu suất backtest
    """
    if results is None or len(results) == 0:
        return

    plt.figure(figsize=(12, 6))
    plt.plot(results['timestamp'], results['balance'], label='Số dư', color='green')
    plt.title('📈 Hiệu suất Backtest')
    plt.xlabel('Thời gian')
    plt.ylabel('Số dư (USD)')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    print(f"📊 Biểu đồ backtest đã lưu tại: {save_path}")