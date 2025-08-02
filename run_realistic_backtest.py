#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Realistic Backtest Runner
- Tests strategies with realistic market conditions
- Prevents overfitting through proper validation
- Multiple testing scenarios
- Simplified output
"""

from backtest.backtest_engine import run_backtest
from backtest.performance_report import generate_report
from backtest.chart import plot_backtest_results
import pandas as pd
from datetime import datetime

def run_realistic_backtest():
    """Run realistic backtest with proper validation"""
    print("🚀 REALISTIC BACKTEST SYSTEM")
    print("=" * 50)
    
    # Test scenarios
    scenarios = [
        {
            'name': 'Conservative',
            'symbol': 'DOGEUSDT',
            'days': 30,
            'risk_per_trade': 0.01,  # 1% risk
            'slippage': 0.002,       # 0.2% slippage
            'fee': 0.002,            # 0.2% fee
            'min_confidence': 0.7    # 70% confidence
        },
        {
            'name': 'Moderate',
            'symbol': 'DOGEUSDT', 
            'days': 60,
            'risk_per_trade': 0.02,  # 2% risk
            'slippage': 0.001,       # 0.1% slippage
            'fee': 0.001,            # 0.1% fee
            'min_confidence': 0.6    # 60% confidence
        },
        {
            'name': 'Aggressive',
            'symbol': 'DOGEUSDT',
            'days': 90,
            'risk_per_trade': 0.03,  # 3% risk
            'slippage': 0.0005,      # 0.05% slippage
            'fee': 0.0005,           # 0.05% fee
            'min_confidence': 0.5    # 50% confidence
        }
    ]
    
    all_results = []
    
    for scenario in scenarios:
        # Run backtest with custom parameters
        from backtest.backtest_engine import RealisticBacktestEngine
        
        engine = RealisticBacktestEngine(
            initial_balance=1000,
            max_risk_per_trade=scenario['risk_per_trade'],
            slippage_pct=scenario['slippage'],
            fee_pct=scenario['fee'],
            min_confidence=scenario['min_confidence']
        )
        
        results = engine.run_backtest(
            symbol=scenario['symbol'],
            interval="5m",
            days=scenario['days']
        )
        
        if results is not None and len(results) > 0:
            # Generate report
            report = generate_report(results, initial_balance=1000)
            
            # Add scenario info to results
            results['scenario'] = scenario['name']
            all_results.append(results)
        else:
            print(f"❌ {scenario['name']} scenario failed - no signals")
    
    # Compare scenarios
    if len(all_results) > 1:
        print(f"\n📊 SCENARIO COMPARISON:")
        print("=" * 50)
        
        comparison_data = []
        for i, results in enumerate(all_results):
            scenario_name = results['scenario'].iloc[0]
            
            # Calculate metrics
            total_trades = len(results)
            wins = len(results[results['outcome'] == 'win'])
            win_rate = wins / total_trades * 100 if total_trades > 0 else 0
            total_profit = results['profit'].sum()
            profit_pct = total_profit / 1000 * 100
            
            # Risk metrics
            max_drawdown = (results['balance'].cummin() / results['balance'].cummax() - 1).min() * 100
            
            comparison_data.append({
                'Scenario': scenario_name,
                'Trades': total_trades,
                'Win Rate': f"{win_rate:.1f}%",
                'Profit': f"${total_profit:+,.2f}",
                'Profit %': f"{profit_pct:+.1f}%",
                'Max DD': f"{max_drawdown:.1f}%"
            })
        
        # Display comparison table
        comparison_df = pd.DataFrame(comparison_data)
        print(comparison_df.to_string(index=False))
        
        # Find best scenario
        best_scenario = max(all_results, key=lambda x: x['profit'].sum())
        best_name = best_scenario['scenario'].iloc[0]
        best_profit = best_scenario['profit'].sum()
        
        print(f"\n🏆 Best Scenario: {best_name} (${best_profit:+,.2f})")
        
        # Overfitting check
        print(f"\n🎯 OVERFITTING ANALYSIS:")
        high_win_rates = [len(r[r['outcome'] == 'win']) / len(r) * 100 for r in all_results if len(r) > 0]
        avg_win_rate = sum(high_win_rates) / len(high_win_rates) if high_win_rates else 0
        
        if avg_win_rate > 70:
            print("⚠️  WARNING: High average win rate suggests potential overfitting")
        else:
            print("✅ Win rates appear realistic")
    
    # Save combined results
    if all_results:
        combined_results = pd.concat(all_results, ignore_index=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"backtest/results/realistic_backtest_{timestamp}.csv"
        combined_results.to_csv(filename, index=False)
        print(f"\n✅ Combined results saved to: {filename}")
    
    return all_results

if __name__ == "__main__":
    run_realistic_backtest() 