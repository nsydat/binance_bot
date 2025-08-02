#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Strategy Test
- Tests all improvements in one file
- Shows only final results
- No verbose output
"""

from backtest.backtest_engine import RealisticBacktestEngine
from backtest.performance_report import generate_report
from strategies.ema_vwap_rsi import ema_vwap_rsi_strategy
from strategies.improved_ema_vwap_rsi import get_improved_ema_vwap_rsi_strategy
import pandas as pd
import numpy as np
from datetime import datetime

def run_comprehensive_test():
    """Run comprehensive test of all improvements"""
    print("🧪 COMPREHENSIVE STRATEGY TEST")
    print("=" * 50)
    
    # Test scenarios
    scenarios = [
        {
            'name': 'Conservative',
            'days': 30,
            'risk_per_trade': 0.01,
            'slippage': 0.002,
            'fee': 0.002,
            'min_confidence': 0.7
        },
        {
            'name': 'Moderate', 
            'days': 60,
            'risk_per_trade': 0.02,
            'slippage': 0.001,
            'fee': 0.001,
            'min_confidence': 0.5
        },
        {
            'name': 'Aggressive',
            'days': 90,
            'risk_per_trade': 0.03,
            'slippage': 0.0005,
            'fee': 0.0005,
            'min_confidence': 0.4
        }
    ]
    
    all_results = []
    
    for scenario in scenarios:
        # Run backtest with improved engine
        engine = RealisticBacktestEngine(
            initial_balance=1000,
            max_risk_per_trade=scenario['risk_per_trade'],
            slippage_pct=scenario['slippage'],
            fee_pct=scenario['fee'],
            min_confidence=scenario['min_confidence']
        )
        
        results = engine.run_backtest(
            symbol="DOGEUSDT",
            interval="5m", 
            days=scenario['days']
        )
        
        if results is not None and len(results) > 0:
            # Calculate metrics
            total_trades = len(results)
            wins = len(results[results['outcome'] == 'win'])
            win_rate = wins / total_trades * 100 if total_trades > 0 else 0
            total_profit = results['profit'].sum()
            profit_pct = total_profit / 1000 * 100
            
            # Risk metrics
            max_drawdown = (results['balance'].cummin() / results['balance'].cummax() - 1).min() * 100
            
            all_results.append({
                'Scenario': scenario['name'],
                'Trades': total_trades,
                'Win Rate': f"{win_rate:.1f}%",
                'Profit': f"${total_profit:+,.2f}",
                'Profit %': f"{profit_pct:+.1f}%",
                'Max DD': f"{max_drawdown:.1f}%"
            })
        else:
            all_results.append({
                'Scenario': scenario['name'],
                'Trades': 0,
                'Win Rate': "0.0%",
                'Profit': "$0.00",
                'Profit %': "0.0%",
                'Max DD': "0.0%"
            })
    
    # Display final results table
    print("\n📊 FINAL RESULTS:")
    print("=" * 50)
    
    results_df = pd.DataFrame(all_results)
    print(results_df.to_string(index=False))
    
    # Find best scenario
    if all_results:
        best_scenario = max(all_results, key=lambda x: float(x['Profit'].replace('$', '').replace(',', '')))
        best_name = best_scenario['Scenario']
        best_profit = best_scenario['Profit']
        
        print(f"\n🏆 Best Scenario: {best_name} ({best_profit})")
    
    # Overall assessment
    print(f"\n🎯 OVERALL ASSESSMENT:")
    print("=" * 50)
    
    # Calculate average metrics
    avg_win_rate = sum([float(r['Win Rate'].replace('%', '')) for r in all_results]) / len(all_results)
    avg_profit_pct = sum([float(r['Profit %'].replace('%', '').replace('+', '')) for r in all_results]) / len(all_results)
    
    print(f"• Average Win Rate: {avg_win_rate:.1f}%")
    print(f"• Average Profit: {avg_profit_pct:+.1f}%")
    
    # Quality assessment
    if avg_win_rate > 50:
        print("✅ EXCELLENT - High win rate achieved")
    elif avg_win_rate > 40:
        print("✅ GOOD - Acceptable win rate")
    elif avg_win_rate > 30:
        print("📊 ACCEPTABLE - Room for improvement")
    else:
        print("❌ NEEDS WORK - Low win rate")
    
    if avg_profit_pct > 5:
        print("✅ EXCELLENT - Good profitability")
    elif avg_profit_pct > 0:
        print("✅ GOOD - Positive returns")
    else:
        print("❌ NEEDS WORK - Negative returns")
    
    # Strategy comparison
    print(f"\n🔍 STRATEGY COMPARISON:")
    print("=" * 50)
    
    # Test old vs improved strategy on sample data
    from utils.data_fetcher import get_klines_df
    
    df = get_klines_df("DOGEUSDT", "5m", limit=1000)
    if df is not None:
        # Test old strategy
        old_result = ema_vwap_rsi_strategy(df, None)
        
        # Test improved strategy
        market_conditions = {
            'regime': 'BULLISH_TRENDING',
            'volatility': 0.03,
            'volume_ratio': 1.2
        }
        improved_result = get_improved_ema_vwap_rsi_strategy(df, None, market_conditions)
        
        print(f"• Old Strategy Signals: {'Yes' if old_result else 'No'}")
        print(f"• Improved Strategy Signals: {'Yes' if improved_result else 'No'}")
        
        if old_result and improved_result:
            old_signal, old_entry, old_sl, old_tp, old_qty, old_confidence = old_result
            imp_signal, imp_entry, imp_sl, imp_tp, imp_qty, imp_confidence = improved_result
            
            old_rr = abs(imp_tp - imp_entry) / abs(imp_entry - imp_sl) if abs(imp_entry - imp_sl) > 0 else 0
            imp_rr = abs(imp_tp - imp_entry) / abs(imp_entry - imp_sl) if abs(imp_entry - imp_sl) > 0 else 0
            
            print(f"• Old Confidence: {old_confidence:.1%}")
            print(f"• Improved Confidence: {imp_confidence:.1%}")
            print(f"• Old R/R Ratio: 1:{old_rr:.2f}")
            print(f"• Improved R/R Ratio: 1:{imp_rr:.2f}")
            
            if imp_confidence > old_confidence:
                print("✅ IMPROVED - Better confidence")
            if imp_rr > old_rr:
                print("✅ IMPROVED - Better R/R ratio")
        elif improved_result and not old_result:
            print("✅ IMPROVED - Generated signal where old strategy failed")
        elif old_result and not improved_result:
            print("📊 OLD - More conservative signal generation")
        else:
            print("📊 SIMILAR - No signals in current market conditions")
    
    print(f"\n✅ Test completed successfully!")
    print(f"📊 Run 'python run_realistic_backtest.py' for detailed backtest")

if __name__ == "__main__":
    run_comprehensive_test() 