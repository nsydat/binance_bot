# backtest/performance_report.py
import pandas as pd
import numpy as np
import os
from datetime import datetime

def calculate_drawdown(balance_series):
    """Calculate maximum drawdown"""
    peak = balance_series.expanding().max()
    drawdown = (balance_series - peak) / peak * 100
    return drawdown.min()

def calculate_sharpe_ratio(returns, risk_free_rate=0.02):
    """Calculate Sharpe ratio"""
    if len(returns) == 0:
        return 0
    
    excess_returns = returns - risk_free_rate/252  # Daily risk-free rate
    if excess_returns.std() == 0:
        return 0
    
    return np.sqrt(252) * excess_returns.mean() / excess_returns.std()

def calculate_sortino_ratio(returns, risk_free_rate=0.02):
    """Calculate Sortino ratio"""
    if len(returns) == 0:
        return 0
    
    excess_returns = returns - risk_free_rate/252
    downside_returns = excess_returns[excess_returns < 0]
    
    if len(downside_returns) == 0 or downside_returns.std() == 0:
        return 0
    
    return np.sqrt(252) * excess_returns.mean() / downside_returns.std()

def generate_report(results, initial_balance=1000):
    """
    Tạo báo cáo hiệu suất realistic từ kết quả backtest
    """
    if results is None or len(results) == 0:
        print("❌ Không có tín hiệu nào trong backtest")
        return None

    # Basic metrics
    total_signals = len(results)
    wins = len(results[results['outcome'] == 'win'])
    losses = len(results[results['outcome'] == 'loss'])
    win_rate = wins / total_signals * 100 if total_signals > 0 else 0
    
    # Profit metrics
    total_profit = results['profit'].sum()
    profit_pct = total_profit / initial_balance * 100
    final_balance = initial_balance + total_profit
    
    # Risk metrics
    max_drawdown = calculate_drawdown(results['balance'])
    
    # Calculate returns for Sharpe/Sortino
    results['returns'] = results['profit'] / initial_balance
    sharpe_ratio = calculate_sharpe_ratio(results['returns'])
    sortino_ratio = calculate_sortino_ratio(results['returns'])
    
    # Trade analysis
    avg_profit_per_trade = results['profit'].mean()
    avg_win = results[results['outcome'] == 'win']['profit'].mean() if wins > 0 else 0
    avg_loss = results[results['outcome'] == 'loss']['profit'].mean() if losses > 0 else 0
    profit_factor = abs(avg_win * wins / (avg_loss * losses)) if losses > 0 and avg_loss != 0 else float('inf')
    
    # Volatility analysis
    volatility_regimes = results['volatility_regime'].value_counts()
    
    # Strategy performance
    strategy_performance = results.groupby('strategy').agg({
        'outcome': lambda x: (x == 'win').sum() / len(x) * 100,
        'profit': 'sum',
        'profit_pct': 'mean'
    }).round(2)
    
    # Risk-adjusted metrics
    total_risk = abs(results['profit']).sum()
    risk_reward_ratio = total_profit / total_risk if total_risk > 0 else 0
    
    report = {
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "total_signals": total_signals,
        "win_rate": round(win_rate, 2),
        "profit_pct": round(profit_pct, 2),
        "max_drawdown": round(max_drawdown, 2),
        "final_balance": round(final_balance, 2),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "sortino_ratio": round(sortino_ratio, 2),
        "profit_factor": round(profit_factor, 2),
        "risk_reward_ratio": round(risk_reward_ratio, 2),
        "avg_profit_per_trade": round(avg_profit_per_trade, 2),
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "total_profit": round(total_profit, 2),
        "wins": wins,
        "losses": losses
    }

    # In ra màn hình
    print(f"\n📊 REALISTIC BACKTEST REPORT")
    print(f"=" * 50)
    print(f"📈 PERFORMANCE METRICS:")
    print(f"• Tổng tín hiệu: {total_signals}")
    print(f"• Win Rate: {win_rate:.2f}% ({wins}/{total_signals})")
    print(f"• Lợi nhuận: {profit_pct:+.2f}% (${total_profit:+,.2f})")
    print(f"• Số dư cuối: ${final_balance:,.2f}")
    
    print(f"\n📊 RISK METRICS:")
    print(f"• Drawdown lớn nhất: {max_drawdown:.2f}%")
    print(f"• Sharpe Ratio: {sharpe_ratio:.2f}")
    print(f"• Sortino Ratio: {sortino_ratio:.2f}")
    print(f"• Profit Factor: {profit_factor:.2f}")
    print(f"• Risk/Reward Ratio: {risk_reward_ratio:.2f}")
    
    print(f"\n💰 TRADE ANALYSIS:")
    print(f"• Lợi nhuận trung bình/trade: ${avg_profit_per_trade:.2f}")
    print(f"• Win trung bình: ${avg_win:.2f}")
    print(f"• Loss trung bình: ${avg_loss:.2f}")
    
    print(f"\n📊 STRATEGY PERFORMANCE:")
    for strategy, perf in strategy_performance.iterrows():
        print(f"• {strategy}: {perf['outcome']:.1f}% win rate, {perf['profit']:+.2f} profit")
    
    print(f"\n🌊 VOLATILITY REGIMES:")
    for regime, count in volatility_regimes.items():
        print(f"• {regime}: {count} trades")
    
    # Quality assessment
    print(f"\n🎯 QUALITY ASSESSMENT:")
    if win_rate > 70 and profit_pct > 50 and max_drawdown < -20:
        print("⚠️  WARNING: Potential overfitting detected!")
        print("   - High win rate with high profit suggests unrealistic results")
        print("   - Consider adjusting strategy parameters or testing on different data")
    elif win_rate < 30 or profit_pct < -10:
        print("❌ Poor performance - strategy needs optimization")
    elif sharpe_ratio > 1.0 and max_drawdown > -15:
        print("✅ Good risk-adjusted performance")
    else:
        print("📊 Moderate performance - consider parameter tuning")
    
    # Lưu báo cáo
    report_file = f"backtest/reports/realistic_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    pd.DataFrame([report]).to_csv(report_file, index=False)
    print(f"\n✅ Báo cáo đã lưu tại: {report_file}")

    return report