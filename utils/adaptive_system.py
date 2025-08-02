#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hệ thống Adaptive cho Trading Bot
- Volatility-based R/R Ratio adjustment
- Market condition-based strategy selection  
- Dynamic SL/TP adjustment
- Performance-based parameter optimization
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List, Tuple, Optional

class AdaptiveSystem:
    def __init__(self):
        self.performance_history = []
        self.market_regime_history = []
        self.strategy_performance = {}
        self.volatility_regimes = {
            'LOW': {'min': 0, 'max': 0.02, 'rr_ratio': 1.5, 'sl_multiplier': 1.0},
            'MEDIUM': {'min': 0.02, 'max': 0.05, 'rr_ratio': 2.0, 'sl_multiplier': 1.2},
            'HIGH': {'min': 0.05, 'max': 0.10, 'rr_ratio': 2.5, 'sl_multiplier': 1.5},
            'EXTREME': {'min': 0.10, 'max': float('inf'), 'rr_ratio': 3.0, 'sl_multiplier': 2.0}
        }
        
    def calculate_volatility(self, df: pd.DataFrame, window: int = 20) -> float:
        """Tính toán volatility dựa trên ATR"""
        try:
            from ta.volatility import AverageTrueRange
            
            atr = AverageTrueRange(df['high'], df['low'], df['close'], window=window)
            current_atr = atr.average_true_range().iloc[-1]
            current_price = df['close'].iloc[-1]
            
            # Volatility as percentage of price
            volatility = current_atr / current_price
            return volatility
        except Exception as e:
            print(f"❌ Lỗi tính volatility: {e}")
            return 0.02  # Default medium volatility
    
    def detect_market_regime(self, df: pd.DataFrame) -> Dict:
        """Phát hiện regime thị trường (Trending/Sideways/Volatile)"""
        try:
            from ta.trend import SMAIndicator, EMAIndicator
            from ta.momentum import RSIIndicator
            from ta.volatility import BollingerBands
            
            # Tính các chỉ báo
            sma_20 = SMAIndicator(df['close'], window=20).sma_indicator()
            sma_50 = SMAIndicator(df['close'], window=50).sma_indicator()
            ema_20 = EMAIndicator(df['close'], window=20).ema_indicator()
            
            # RSI
            rsi = RSIIndicator(df['close']).rsi()
            
            # Bollinger Bands
            bb = BollingerBands(df['close'])
            bb_upper = bb.bollinger_hband()
            bb_lower = bb.bollinger_lband()
            bb_width = (bb_upper - bb_lower) / df['close']
            
            # Volume analysis
            volume_sma = df['volume'].rolling(20).mean()
            volume_ratio = df['volume'].iloc[-1] / volume_sma.iloc[-1] if volume_sma.iloc[-1] > 0 else 1
            
            # Price position relative to moving averages
            current_price = df['close'].iloc[-1]
            price_vs_sma20 = (current_price - sma_20.iloc[-1]) / sma_20.iloc[-1]
            price_vs_sma50 = (current_price - sma_50.iloc[-1]) / sma_50.iloc[-1]
            
            # Volatility
            volatility = self.calculate_volatility(df)
            
            # Determine market regime
            regime = "SIDEWAYS"
            trend_strength = 0
            
            # Trending conditions
            if (price_vs_sma20 > 0.01 and price_vs_sma50 > 0.01 and 
                sma_20.iloc[-1] > sma_50.iloc[-1]):
                regime = "BULLISH_TRENDING"
                trend_strength = min(abs(price_vs_sma20) * 100, 1.0)
            elif (price_vs_sma20 < -0.01 and price_vs_sma50 < -0.01 and 
                  sma_20.iloc[-1] < sma_50.iloc[-1]):
                regime = "BEARISH_TRENDING"
                trend_strength = min(abs(price_vs_sma20) * 100, 1.0)
            elif volatility > 0.05:
                regime = "VOLATILE"
            elif bb_width.iloc[-1] < 0.02:
                regime = "CONSOLIDATION"
            
            return {
                'regime': regime,
                'trend_strength': trend_strength,
                'volatility': volatility,
                'volume_ratio': volume_ratio,
                'rsi': rsi.iloc[-1],
                'bb_width': bb_width.iloc[-1],
                'price_vs_sma20': price_vs_sma20,
                'price_vs_sma50': price_vs_sma50
            }
            
        except Exception as e:
            print(f"❌ Lỗi detect market regime: {e}")
            return {'regime': 'UNKNOWN', 'volatility': 0.02, 'volume_ratio': 1.0}
    
    def get_volatility_regime(self, volatility: float) -> str:
        """Xác định volatility regime"""
        for regime, config in self.volatility_regimes.items():
            if config['min'] <= volatility < config['max']:
                return regime
        return 'MEDIUM'
    
    def calculate_adaptive_rr_ratio(self, market_conditions: Dict, base_rr: float = 2.0) -> float:
        """Tính toán R/R ratio thích nghi theo volatility và market regime"""
        volatility = market_conditions['volatility']
        regime = market_conditions['regime']
        trend_strength = market_conditions.get('trend_strength', 0)
        
        # Base RR ratio từ volatility regime
        volatility_regime = self.get_volatility_regime(volatility)
        base_rr = self.volatility_regimes[volatility_regime]['rr_ratio']
        
        # Điều chỉnh theo market regime
        regime_multipliers = {
            'BULLISH_TRENDING': 1.2,
            'BEARISH_TRENDING': 1.2,
            'VOLATILE': 1.3,
            'CONSOLIDATION': 0.8,
            'SIDEWAYS': 1.0
        }
        
        multiplier = regime_multipliers.get(regime, 1.0)
        
        # Điều chỉnh theo trend strength
        if trend_strength > 0.5:
            multiplier *= 1.1
        
        # Điều chỉnh theo volume
        volume_ratio = market_conditions.get('volume_ratio', 1.0)
        if volume_ratio > 1.5:
            multiplier *= 1.05
        elif volume_ratio < 0.5:
            multiplier *= 0.95
        
        final_rr = base_rr * multiplier
        return max(1.5, min(4.0, final_rr))  # Giới hạn 1.5-4.0
    
    def calculate_adaptive_sl_tp(self, entry_price: float, side: str, 
                                market_conditions: Dict, atr: float) -> Tuple[float, float]:
        """Tính toán SL/TP thích nghi"""
        volatility = market_conditions['volatility']
        volatility_regime = self.get_volatility_regime(volatility)
        sl_multiplier = self.volatility_regimes[volatility_regime]['sl_multiplier']
        
        # Base SL distance
        base_sl_distance = atr * sl_multiplier
        
        # Điều chỉnh theo market regime
        regime = market_conditions['regime']
        if regime in ['BULLISH_TRENDING', 'BEARISH_TRENDING']:
            base_sl_distance *= 1.2  # Tighter SL in trending markets
        elif regime == 'VOLATILE':
            base_sl_distance *= 1.5  # Wider SL in volatile markets
        
        # Calculate SL and TP
        if side == 'BUY':
            sl_price = entry_price - base_sl_distance
            tp_price = entry_price + (base_sl_distance * self.calculate_adaptive_rr_ratio(market_conditions))
        else:
            sl_price = entry_price + base_sl_distance
            tp_price = entry_price - (base_sl_distance * self.calculate_adaptive_rr_ratio(market_conditions))
        
        return sl_price, tp_price
    
    def get_adaptive_strategies(self, market_conditions: Dict) -> List[str]:
        """Chọn chiến lược thích nghi theo điều kiện thị trường"""
        regime = market_conditions['regime']
        volatility = market_conditions['volatility']
        volume_ratio = market_conditions.get('volume_ratio', 1.0)
        
        strategies = []
        
        # Trending strategies
        if regime in ['BULLISH_TRENDING', 'BEARISH_TRENDING']:
            strategies.extend([
                'EMA_VWAP',           # Trend following
                'SUPERTREND_ATR',     # Trend confirmation
                'TREND_MOMENTUM'      # Momentum in trend
            ])
        
        # Volatile market strategies
        elif regime == 'VOLATILE':
            strategies.extend([
                'BREAKOUT_VOLUME',    # Breakout in volatile markets
                'MULTI_TIMEFRAME',    # Multi-timeframe confirmation
                'TREND_MOMENTUM'      # Momentum strategies
            ])
        
        # Sideways/Consolidation strategies
        elif regime in ['SIDEWAYS', 'CONSOLIDATION']:
            strategies.extend([
                'EMA_VWAP',           # Mean reversion
                'MULTI_TIMEFRAME'     # Multi-timeframe for confirmation
            ])
            
            # Only add breakout if volume is high
            if volume_ratio > 1.2:
                strategies.append('BREAKOUT_VOLUME')
        
        # Always include multi-timeframe for confirmation
        if 'MULTI_TIMEFRAME' not in strategies:
            strategies.append('MULTI_TIMEFRAME')
        
        return list(set(strategies))
    
    def adjust_strategy_parameters(self, strategy_name: str, market_conditions: Dict) -> Dict:
        """Điều chỉnh tham số chiến lược theo điều kiện thị trường"""
        regime = market_conditions['regime']
        volatility = market_conditions['volatility']
        
        base_params = {}
        
        # EMA VWAP parameters
        if strategy_name == 'EMA_VWAP':
            base_params = {
                'ema_period': 20,
                'vwap_period': 20,
                'rsi_period': 14,
                'rsi_oversold': 30,
                'rsi_overbought': 70
            }
            
            # Adjust for volatility
            if volatility > 0.05:
                base_params['ema_period'] = 15  # Faster EMA
                base_params['rsi_oversold'] = 25  # More sensitive
                base_params['rsi_overbought'] = 75
            elif volatility < 0.02:
                base_params['ema_period'] = 25  # Slower EMA
                base_params['rsi_oversold'] = 35
                base_params['rsi_overbought'] = 65
        
        # Supertrend parameters
        elif strategy_name == 'SUPERTREND_ATR':
            base_params = {
                'atr_period': 10,
                'multiplier': 3.0
            }
            
            # Adjust for volatility
            if volatility > 0.05:
                base_params['multiplier'] = 2.5  # Tighter in volatile markets
            elif volatility < 0.02:
                base_params['multiplier'] = 3.5  # Wider in stable markets
        
        # Breakout parameters
        elif strategy_name == 'BREAKOUT_VOLUME':
            base_params = {
                'lookback_period': 20,
                'volume_threshold': 1.5,
                'breakout_threshold': 0.02
            }
            
            # Adjust for volatility
            if volatility > 0.05:
                base_params['breakout_threshold'] = 0.03  # Higher threshold
                base_params['volume_threshold'] = 2.0
            elif volatility < 0.02:
                base_params['breakout_threshold'] = 0.01  # Lower threshold
                base_params['volume_threshold'] = 1.2
        
        return base_params
    
    def update_performance_history(self, signal_result: Dict):
        """Cập nhật lịch sử hiệu suất để tối ưu hóa"""
        self.performance_history.append({
            'timestamp': datetime.now(),
            'strategy': signal_result.get('strategy'),
            'market_regime': signal_result.get('market_regime'),
            'rr_ratio': signal_result.get('rr_ratio'),
            'profit_loss': signal_result.get('profit_loss', 0),
            'volatility': signal_result.get('volatility'),
            'confidence': signal_result.get('confidence')
        })
        
        # Keep only last 1000 records
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
    
    def optimize_parameters(self) -> Dict:
        """Tối ưu hóa tham số dựa trên lịch sử hiệu suất"""
        if len(self.performance_history) < 50:
            return {}
        
        df_performance = pd.DataFrame(self.performance_history)
        
        # Analyze performance by market regime
        regime_performance = df_performance.groupby('market_regime')['profit_loss'].agg(['mean', 'count'])
        
        # Analyze performance by RR ratio
        rr_performance = df_performance.groupby(pd.cut(df_performance['rr_ratio'], bins=5))['profit_loss'].mean()
        
        # Find optimal RR ratio
        optimal_rr = rr_performance.idxmax().mid if not rr_performance.empty else 2.0
        
        # Find best performing strategies per regime
        strategy_performance = df_performance.groupby(['market_regime', 'strategy'])['profit_loss'].mean()
        
        return {
            'optimal_rr_ratio': optimal_rr,
            'regime_performance': regime_performance.to_dict(),
            'strategy_performance': strategy_performance.to_dict()
        }
    
    def get_market_insights(self, market_conditions: Dict) -> Dict:
        """Phân tích insights thị trường"""
        insights = {
            'recommended_rr_ratio': self.calculate_adaptive_rr_ratio(market_conditions),
            'volatility_regime': self.get_volatility_regime(market_conditions['volatility']),
            'market_regime': market_conditions['regime'],
            'strategy_recommendations': self.get_adaptive_strategies(market_conditions),
            'risk_level': 'HIGH' if market_conditions['volatility'] > 0.05 else 'MEDIUM' if market_conditions['volatility'] > 0.02 else 'LOW'
        }
        
        # Add optimization insights if available
        optimization = self.optimize_parameters()
        if optimization:
            insights['optimization'] = optimization
        
        return insights 