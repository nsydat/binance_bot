# backtest/performance_report.py
import pandas as pd
import os
from datetime import datetime

def generate_report(results, initial_balance=1000):
    """
    Tạo báo cáo hiệu suất từ kết quả backtest
    """
    if results is None or len(results) == 0:
        print("❌ Không có tín hiệu nào trong backtest")
        return None

    total_signals = len(results)
    wins = len(results[results['outcome'] == 'win'])
    win_rate = wins / total_signals * 100
    max_drawdown = (results['balance'].cummin() / results['balance'].cummax() - 1).min() * 100
    final_balance = results['balance'].iloc[-1]
    profit_pct = (final_balance - initial_balance) / initial_balance * 100
    rr_ratio = results['profit_pct'].abs().mean() / results['profit_pct'].abs().std()  # Rủi ro trên lợi nhuận

    report = {
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "total_signals": total_signals,
        "win_rate": round(win_rate, 2),
        "profit_pct": round(profit_pct, 2),
        "max_drawdown": round(max_drawdown, 2),
        "final_balance": round(final_balance, 2),
        "sharpe_ratio": round(rr_ratio, 2)
    }

    # In ra màn hình
    print(f"\n📊 BÁO CÁO BACKTEST")
    print(f"• Tổng tín hiệu: {total_signals}")
    print(f"• Win Rate: {win_rate:.2f}%")
    print(f"• Lợi nhuận: {profit_pct:+.2f}%")
    print(f"• Drawdown lớn nhất: {max_drawdown:.2f}%")
    print(f"• Sharpe Ratio: {rr_ratio:.2f}")
    print(f"• Số dư cuối: ${final_balance:,.2f}")

    # Lưu báo cáo
    report_file = f"backtest/reports/report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    pd.DataFrame([report]).to_csv(report_file, index=False)
    print(f"✅ Báo cáo đã lưu tại: {report_file}")

    return report