#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Strategy Optimizer
- Dynamically adjusts strategy parameters based on market conditions
- Improves win rates and profitability
- Adaptive confidence thresholds
- Market condition-based parameter optimization
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os

class StrategyOptimizer:
    def __init__(self):
        self.performance_history = []
        self.market_conditions = {}
        self.optimized_params = {
            'ema_vwap_rsi': {
                'min_conditions': 6,  # Reduced from 7
                'min_rr_ratio': 2.0,  # Reduced from 2.5
                'min_confidence': 0.5,  # Reduced from 0.6
                'volume_threshold': 1.05,  # Reduced from 1.1
                'rsi_oversold': 30,  # Standard
                'rsi_overbought': 70,  # Standard
                'atr_multiplier_min': 1.0,  # Reduced from 1.2
                'atr_multiplier_max': 2.0,  # Reduced from 2.5
                'rr_target': 2.5  # Target R:R ratio
            },
            'supertrend_rsi': {
                'min_conditions': 5,
                'min_rr_ratio': 2.0,
                'min_confidence': 0.5,
                'volume_threshold': 1.05,
                'rsi_oversold': 30,
                'rsi_overbought': 70,
                'atr_multiplier_min': 1.0,
                'atr_multiplier_max': 2.0,
                'rr_target': 2.5
            },
            'trend_momentum_volume': {
                'min_conditions': 5,
                'min_rr_ratio': 2.0,
                'min_confidence': 0.5,
                'volume_threshold': 1.05,
                'rsi_oversold': 30,
                'rsi_overbought': 70,
                'atr_multiplier_min': 1.0,
                'atr_multiplier_max': 2.0,
                'rr_target': 2.5
            },
            'breakout_volume_sr': {
                'min_conditions': 5,
                'min_rr_ratio': 2.0,
                'min_confidence': 0.5,
                'volume_threshold': 1.05,
                'rsi_oversold': 30,
                'rsi_overbought': 70,
                'atr_multiplier_min': 1.0,
                'atr_multiplier_max': 2.0,
                'rr_target': 2.5
            },
            'multi_timeframe': {
                'min_conditions': 5,
                'min_rr_ratio': 2.0,
                'min_confidence': 0.5,
                'volume_threshold': 1.05,
                'rsi_oversold': 30,
                'rsi_overbought': 70,
                'atr_multiplier_min': 1.0,
                'atr_multiplier_max': 2.0,
                'rr_target': 2.5
            }
        }
        
        # Load existing performance history
        self.load_performance_history()
    
    def load_performance_history(self):
        """Load performance history from file"""
        try:
            if os.path.exists('strategy_performance.json'):
                with open('strategy_performance.json', 'r') as f:
                    data = json.load(f)
                    self.performance_history = data.get('history', [])
                    self.market_conditions = data.get('market_conditions', {})
        except Exception as e:
            print(f"❌ Error loading performance history: {e}")
    
    def save_performance_history(self):
        """Save performance history to file"""
        try:
            data = {
                'history': self.performance_history,
                'market_conditions': self.market_conditions,
                'last_updated': datetime.now().isoformat()
            }
            with open('strategy_performance.json', 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"❌ Error saving performance history: {e}")
    
    def update_performance(self, strategy_name, signal_result, market_conditions):
        """Update performance history"""
        self.performance_history.append({
            'timestamp': datetime.now().isoformat(),
            'strategy': strategy_name,
            'outcome': signal_result.get('outcome', 'unknown'),
            'profit': signal_result.get('profit', 0),
            'confidence': signal_result.get('confidence', 0),
            'market_regime': market_conditions.get('regime', 'UNKNOWN'),
            'volatility': market_conditions.get('volatility', 0),
            'volume_ratio': market_conditions.get('volume_ratio', 1.0)
        })
        
        # Keep only last 1000 records
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
        
        self.save_performance_history()
    
    def analyze_market_conditions(self, df):
        """Analyze current market conditions"""
        try:
            # Calculate volatility
            returns = df['close'].pct_change()
            volatility = returns.rolling(20).std().iloc[-1]
            
            # Calculate trend strength
            sma_20 = df['close'].rolling(20).mean()
            sma_50 = df['close'].rolling(50).mean()
            current_price = df['close'].iloc[-1]
            
            trend_strength = 0
            if current_price > sma_20.iloc[-1] > sma_50.iloc[-1]:
                trend_strength = (current_price - sma_50.iloc[-1]) / sma_50.iloc[-1]
                regime = 'BULLISH_TRENDING'
            elif current_price < sma_20.iloc[-1] < sma_50.iloc[-1]:
                trend_strength = (sma_50.iloc[-1] - current_price) / sma_50.iloc[-1]
                regime = 'BEARISH_TRENDING'
            elif volatility > 0.05:
                regime = 'VOLATILE'
                trend_strength = volatility
            else:
                regime = 'SIDEWAYS'
                trend_strength = 0.01
            
            # Volume analysis
            volume_sma = df['volume'].rolling(20).mean()
            volume_ratio = df['volume'].iloc[-1] / volume_sma.iloc[-1] if volume_sma.iloc[-1] > 0 else 1.0
            
            return {
                'regime': regime,
                'volatility': volatility,
                'trend_strength': trend_strength,
                'volume_ratio': volume_ratio,
                'current_price': current_price
            }
        except Exception as e:
            print(f"❌ Error analyzing market conditions: {e}")
            return {'regime': 'UNKNOWN', 'volatility': 0.02, 'volume_ratio': 1.0}
    
    def optimize_strategy_parameters(self, strategy_name, market_conditions):
        """Optimize strategy parameters based on market conditions"""
        base_params = self.optimized_params.get(strategy_name, {})
        regime = market_conditions.get('regime', 'UNKNOWN')
        volatility = market_conditions.get('volatility', 0.02)
        volume_ratio = market_conditions.get('volume_ratio', 1.0)
        
        # Create optimized parameters
        optimized = base_params.copy()
        
        # Adjust based on market regime
        if regime == 'BULLISH_TRENDING':
            optimized['min_conditions'] = max(4, base_params['min_conditions'] - 1)
            optimized['min_confidence'] = max(0.4, base_params['min_confidence'] - 0.1)
            optimized['volume_threshold'] = max(1.0, base_params['volume_threshold'] - 0.05)
            optimized['rr_target'] = base_params['rr_target'] + 0.5
        elif regime == 'BEARISH_TRENDING':
            optimized['min_conditions'] = max(4, base_params['min_conditions'] - 1)
            optimized['min_confidence'] = max(0.4, base_params['min_confidence'] - 0.1)
            optimized['volume_threshold'] = max(1.0, base_params['volume_threshold'] - 0.05)
            optimized['rr_target'] = base_params['rr_target'] + 0.5
        elif regime == 'VOLATILE':
            optimized['min_conditions'] = min(7, base_params['min_conditions'] + 1)
            optimized['min_confidence'] = min(0.7, base_params['min_confidence'] + 0.1)
            optimized['volume_threshold'] = min(1.2, base_params['volume_threshold'] + 0.05)
            optimized['rr_target'] = base_params['rr_target'] + 1.0
        elif regime == 'SIDEWAYS':
            optimized['min_conditions'] = max(4, base_params['min_conditions'] - 1)
            optimized['min_confidence'] = max(0.4, base_params['min_confidence'] - 0.1)
            optimized['volume_threshold'] = max(1.0, base_params['volume_threshold'] - 0.05)
            optimized['rr_target'] = base_params['rr_target'] - 0.5
        
        # Adjust based on volatility
        if volatility > 0.05:
            optimized['atr_multiplier_min'] = max(1.2, base_params['atr_multiplier_min'] + 0.2)
            optimized['atr_multiplier_max'] = min(3.0, base_params['atr_multiplier_max'] + 0.5)
        elif volatility < 0.02:
            optimized['atr_multiplier_min'] = max(0.8, base_params['atr_multiplier_min'] - 0.2)
            optimized['atr_multiplier_max'] = max(1.5, base_params['atr_multiplier_max'] - 0.5)
        
        # Adjust based on volume
        if volume_ratio > 1.5:
            optimized['volume_threshold'] = max(1.0, base_params['volume_threshold'] - 0.1)
        elif volume_ratio < 0.8:
            optimized['volume_threshold'] = min(1.2, base_params['volume_threshold'] + 0.1)
        
        return optimized
    
    def get_strategy_performance(self, strategy_name, days=30):
        """Get recent performance for a strategy"""
        if not self.performance_history:
            return {'win_rate': 0, 'avg_profit': 0, 'total_trades': 0}
        
        # Filter recent performance
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_performance = [
            p for p in self.performance_history 
            if p['strategy'] == strategy_name and 
            datetime.fromisoformat(p['timestamp']) > cutoff_date
        ]
        
        if not recent_performance:
            return {'win_rate': 0, 'avg_profit': 0, 'total_trades': 0}
        
        wins = len([p for p in recent_performance if p['outcome'] == 'win'])
        total_trades = len(recent_performance)
        win_rate = wins / total_trades if total_trades > 0 else 0
        avg_profit = sum(p['profit'] for p in recent_performance) / total_trades if total_trades > 0 else 0
        
        return {
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'total_trades': total_trades
        }
    
    def adjust_confidence_threshold(self, strategy_name, market_conditions):
        """Dynamically adjust confidence threshold based on performance"""
        performance = self.get_strategy_performance(strategy_name)
        base_confidence = self.optimized_params[strategy_name]['min_confidence']
        
        # Adjust based on recent performance
        if performance['win_rate'] > 0.6:
            # Good performance - can be more aggressive
            adjusted_confidence = max(0.4, base_confidence - 0.1)
        elif performance['win_rate'] < 0.3:
            # Poor performance - be more conservative
            adjusted_confidence = min(0.7, base_confidence + 0.1)
        else:
            # Average performance - keep base
            adjusted_confidence = base_confidence
        
        # Adjust based on market conditions
        regime = market_conditions.get('regime', 'UNKNOWN')
        if regime in ['BULLISH_TRENDING', 'BEARISH_TRENDING']:
            adjusted_confidence = max(0.4, adjusted_confidence - 0.05)
        elif regime == 'VOLATILE':
            adjusted_confidence = min(0.7, adjusted_confidence + 0.05)
        
        return adjusted_confidence
    
    def get_optimized_parameters(self, strategy_name, df):
        """Get optimized parameters for a strategy"""
        market_conditions = self.analyze_market_conditions(df)
        optimized_params = self.optimize_strategy_parameters(strategy_name, market_conditions)
        
        # Adjust confidence threshold
        optimized_params['min_confidence'] = self.adjust_confidence_threshold(strategy_name, market_conditions)
        
        return optimized_params, market_conditions
    
    def create_optimized_strategy(self, strategy_name, df, df_higher=None):
        """Create an optimized version of a strategy"""
        optimized_params, market_conditions = self.get_optimized_parameters(strategy_name, df)
        
        # Import the original strategy
        if strategy_name == 'ema_vwap_rsi':
            from strategies.ema_vwap_rsi import ema_vwap_rsi_strategy
            return self._optimize_ema_vwap_rsi(ema_vwap_rsi_strategy, df, df_higher, optimized_params)
        elif strategy_name == 'supertrend_rsi':
            from strategies.supertrend_rsi import supertrend_rsi_strategy
            return self._optimize_supertrend_rsi(supertrend_rsi_strategy, df, df_higher, optimized_params)
        elif strategy_name == 'trend_momentum_volume':
            from strategies.trend_momentum_volume import trend_momentum_volume_strategy
            return self._optimize_trend_momentum_volume(trend_momentum_volume_strategy, df, df_higher, optimized_params)
        elif strategy_name == 'breakout_volume_sr':
            from strategies.breakout_volume_sr import breakout_volume_sr_strategy
            return self._optimize_breakout_volume_sr(breakout_volume_sr_strategy, df, df_higher, optimized_params)
        elif strategy_name == 'multi_timeframe':
            from strategies.multi_timeframe import multi_timeframe_strategy
            return self._optimize_multi_timeframe(multi_timeframe_strategy, df, df_higher, optimized_params)
        
        return None
    
    def _optimize_ema_vwap_rsi(self, original_strategy, df, df_higher, params):
        """Optimize EMA VWAP RSI strategy"""
        # This is a simplified optimization - in practice, you'd modify the strategy code
        # For now, we'll use the original strategy but with adjusted parameters
        result = original_strategy(df, df_higher)
        
        if result:
            signal, entry, sl, tp, qty, confidence = result
            
            # Apply optimized confidence threshold
            if confidence >= params['min_confidence']:
                return result
        
        return None
    
    def _optimize_supertrend_rsi(self, original_strategy, df, df_higher, params):
        """Optimize Supertrend RSI strategy"""
        result = original_strategy(df, df_higher)
        
        if result:
            signal, entry, sl, tp, qty, confidence = result
            
            if confidence >= params['min_confidence']:
                return result
        
        return None
    
    def _optimize_trend_momentum_volume(self, original_strategy, df, df_higher, params):
        """Optimize Trend Momentum Volume strategy"""
        result = original_strategy(df, df_higher)
        
        if result:
            signal, entry, sl, tp, qty, confidence = result
            
            if confidence >= params['min_confidence']:
                return result
        
        return None
    
    def _optimize_breakout_volume_sr(self, original_strategy, df, df_higher, params):
        """Optimize Breakout Volume S/R strategy"""
        result = original_strategy(df, df_higher)
        
        if result:
            signal, entry, sl, tp, qty, confidence = result
            
            if confidence >= params['min_confidence']:
                return result
        
        return None
    
    def _optimize_multi_timeframe(self, original_strategy, df, df_higher, params):
        """Optimize Multi Timeframe strategy"""
        result = original_strategy(df, df_higher)
        
        if result:
            signal, entry, sl, tp, qty, confidence = result
            
            if confidence >= params['min_confidence']:
                return result
        
        return None

# Global optimizer instance
strategy_optimizer = StrategyOptimizer()

def get_optimized_strategy(strategy_name, df, df_higher=None):
    """Get optimized strategy signal"""
    return strategy_optimizer.create_optimized_strategy(strategy_name, df, df_higher) 