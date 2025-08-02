#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Improved EMA VWAP RSI Strategy
- More flexible parameters
- Better signal generation
- Adaptive confidence thresholds
- Market condition awareness
"""

import pandas as pd
import ta
import numpy as np

def improved_ema_vwap_rsi_strategy(df, df_higher=None, params=None):
    """
    Improved EMA VWAP RSI Strategy with flexible parameters
    """
    if len(df) < 50:
        return None
    
    # Default parameters
    default_params = {
        'min_conditions': 5,  # Reduced from 7
        'min_rr_ratio': 2.0,  # Reduced from 2.5
        'min_confidence': 0.5,  # Reduced from 0.6
        'volume_threshold': 1.05,  # Reduced from 1.1
        'rsi_oversold': 30,
        'rsi_overbought': 70,
        'atr_multiplier_min': 1.0,  # Reduced from 1.2
        'atr_multiplier_max': 2.0,  # Reduced from 2.5
        'rr_target': 2.5
    }
    
    # Use provided parameters or defaults
    if params:
        for key, value in params.items():
            default_params[key] = value
    
    # 1. EMA (Optimized periods)
    df['ema_fast'] = ta.trend.EMAIndicator(df['close'], 8).ema_indicator()
    df['ema_slow'] = ta.trend.EMAIndicator(df['close'], 21).ema_indicator()
    df['ema_trend'] = ta.trend.EMAIndicator(df['close'], 50).ema_indicator()
    
    # 2. VWAP + VWAP bands (More flexible)
    df['tp'] = (df['high'] + df['low'] + df['close']) / 3
    df['vwap'] = (df['tp'] * df['volume']).cumsum() / df['volume'].cumsum()
    df['vwap_std'] = df['tp'].rolling(20).std()
    df['vwap_upper'] = df['vwap'] + (df['vwap_std'] * 1.5)
    df['vwap_lower'] = df['vwap'] - (df['vwap_std'] * 1.5)
    
    # 3. RSI (Multiple timeframes)
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], 14).rsi()
    df['rsi_fast'] = ta.momentum.RSIIndicator(df['close'], 7).rsi()
    
    # 4. Volume analysis (More flexible)
    df['volume_sma'] = df['volume'].rolling(20).mean()
    df['volume_ratio'] = df['volume'] / df['volume_sma']
    
    # 5. Volatility (ATR)
    atr = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], 14)
    df['atr'] = atr.average_true_range()
    
    # 6. Additional indicators for better signals
    df['sma_20'] = ta.trend.SMAIndicator(df['close'], 20).sma_indicator()
    df['sma_50'] = ta.trend.SMAIndicator(df['close'], 50).sma_indicator()
    
    # 7. Momentum indicators
    df['macd'] = ta.trend.MACD(df['close']).macd()
    df['macd_signal'] = ta.trend.MACD(df['close']).macd_signal()
    
    current = df.iloc[-1]
    prev = df.iloc[-2]
    prev2 = df.iloc[-3]
    
    # Multi-timeframe confirmation (More flexible)
    higher_trend_bullish = True
    if df_higher is not None and len(df_higher) >= 20:
        df_higher['ema_trend'] = ta.trend.EMAIndicator(df_higher['close'], 20).ema_indicator()
        higher_trend_bullish = df_higher['close'].iloc[-1] > df_higher['ema_trend'].iloc[-1]
    
    # BUY Signal - More flexible conditions
    buy_conditions = [
        # Core EMA signal (must have)
        current['ema_fast'] > current['ema_slow'],
        
        # Trend filter (flexible)
        current['close'] > current['ema_trend'] or current['close'] > current['sma_20'],
        
        # Higher timeframe (flexible)
        higher_trend_bullish,
        
        # VWAP confirmation (more flexible)
        current['close'] > current['vwap'] or current['close'] > current['vwap_lower'],
        
        # RSI conditions (more flexible)
        current['rsi'] < default_params['rsi_overbought'],
        current['rsi_fast'] > 35,  # More flexible
        
        # Volume confirmation (more flexible)
        current['volume_ratio'] > default_params['volume_threshold'],
        
        # Price action (flexible)
        current['close'] > prev['close'] or current['close'] > current['sma_20'],
        
        # MACD confirmation (optional)
        current['macd'] > current['macd_signal'] or current['macd'] > prev['macd']
    ]
    
    # SELL Signal - More flexible conditions
    sell_conditions = [
        # Core EMA signal (must have)
        current['ema_fast'] < current['ema_slow'],
        
        # Trend filter (flexible)
        current['close'] < current['ema_trend'] or current['close'] < current['sma_20'],
        
        # Higher timeframe (flexible)
        not higher_trend_bullish,
        
        # VWAP confirmation (more flexible)
        current['close'] < current['vwap'] or current['close'] < current['vwap_upper'],
        
        # RSI conditions (more flexible)
        current['rsi'] > default_params['rsi_oversold'],
        current['rsi_fast'] < 65,  # More flexible
        
        # Volume confirmation (more flexible)
        current['volume_ratio'] > default_params['volume_threshold'],
        
        # Price action (flexible)
        current['close'] < prev['close'] or current['close'] < current['sma_20'],
        
        # MACD confirmation (optional)
        current['macd'] < current['macd_signal'] or current['macd'] < prev['macd']
    ]
    
    # More flexible signal generation
    min_conditions = default_params['min_conditions']
    buy_signal = sum(buy_conditions) >= min_conditions
    sell_signal = sum(sell_conditions) >= min_conditions
    
    # Calculate SL/TP with improved logic
    if buy_signal or sell_signal:
        entry_price = current['close']
        atr_value = current['atr']
        
        # Dynamic ATR multiplier based on volatility
        volatility = df['close'].pct_change().rolling(20).std().iloc[-1]
        atr_multiplier = max(
            default_params['atr_multiplier_min'], 
            min(default_params['atr_multiplier_max'], volatility * 100)
        )
        
        if buy_signal:
            # Improved SL calculation
            swing_low = df['low'].rolling(10).min().iloc[-1]
            vwap_support = min(current['vwap'], current['vwap_lower'])
            sma_support = current['sma_20']
            
            sl_level1 = entry_price - (atr_multiplier * atr_value)
            sl_level2 = min(swing_low * 0.999, vwap_support * 0.998)
            sl_level3 = sma_support * 0.995
            sl = max(sl_level1, sl_level2, sl_level3)
            
            # Improved TP calculation
            resistance = df['high'].rolling(20).max().iloc[-1]
            tp_level1 = entry_price + (default_params['rr_target'] * atr_value)
            tp_level2 = min(resistance * 1.002, current['vwap_upper'])
            tp_level3 = entry_price + (3.0 * atr_value)  # Minimum 3:1 R:R
            tp = max(tp_level1, tp_level2, tp_level3)
            
            signal = 'BUY'
        else:
            # Improved SL calculation for SELL
            swing_high = df['high'].rolling(10).max().iloc[-1]
            vwap_resistance = max(current['vwap'], current['vwap_upper'])
            sma_resistance = current['sma_20']
            
            sl_level1 = entry_price + (atr_multiplier * atr_value)
            sl_level2 = max(swing_high * 1.001, vwap_resistance * 1.002)
            sl_level3 = sma_resistance * 1.005
            sl = min(sl_level1, sl_level2, sl_level3)
            
            # Improved TP calculation for SELL
            support = df['low'].rolling(20).min().iloc[-1]
            tp_level1 = entry_price - (default_params['rr_target'] * atr_value)
            tp_level2 = max(support * 0.998, current['vwap_lower'])
            tp_level3 = entry_price - (3.0 * atr_value)  # Minimum 3:1 R:R
            tp = min(tp_level1, tp_level2, tp_level3)
            
            signal = 'SELL'
        
        # Enhanced confidence calculation
        ema_strength = abs(current['ema_fast'] - current['ema_slow']) / current['close']
        volume_boost = min(0.2, (current['volume_ratio'] - 1.0) * 0.1)
        rsi_momentum = abs(current['rsi'] - 50) / 50 * 0.1
        macd_strength = abs(current['macd'] - current['macd_signal']) / current['close'] * 100
        
        # Calculate actual R:R ratio
        risk = abs(entry_price - sl) / entry_price
        reward = abs(tp - entry_price) / entry_price
        rr_ratio = reward / risk if risk > 0 else 0
        
        # More flexible confidence calculation
        base_confidence = 0.4 + (ema_strength / 0.01) * 0.2
        total_confidence = base_confidence + volume_boost + rsi_momentum + (macd_strength * 0.1)
        
        # Bonus for good R:R ratio
        if rr_ratio >= default_params['rr_target']:
            total_confidence += 0.1
        elif rr_ratio >= 2.0:
            total_confidence += 0.05
        
        confidence = min(0.95, total_confidence)
        
        # More flexible R:R requirement
        if rr_ratio >= default_params['min_rr_ratio']:
            return signal, entry_price, sl, tp, 0.001, confidence
    
    return None

def get_improved_ema_vwap_rsi_strategy(df, df_higher=None, market_conditions=None):
    """
    Get improved EMA VWAP RSI strategy with market condition adaptation
    """
    # Adapt parameters based on market conditions
    params = {
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
    
    if market_conditions:
        regime = market_conditions.get('regime', 'UNKNOWN')
        volatility = market_conditions.get('volatility', 0.02)
        
        # Adjust parameters based on market regime
        if regime == 'BULLISH_TRENDING':
            params['min_conditions'] = 4
            params['min_confidence'] = 0.4
            params['volume_threshold'] = 1.0
            params['rr_target'] = 3.0
        elif regime == 'BEARISH_TRENDING':
            params['min_conditions'] = 4
            params['min_confidence'] = 0.4
            params['volume_threshold'] = 1.0
            params['rr_target'] = 3.0
        elif regime == 'VOLATILE':
            params['min_conditions'] = 6
            params['min_confidence'] = 0.6
            params['volume_threshold'] = 1.1
            params['rr_target'] = 3.5
        elif regime == 'SIDEWAYS':
            params['min_conditions'] = 4
            params['min_confidence'] = 0.4
            params['volume_threshold'] = 1.0
            params['rr_target'] = 2.0
        
        # Adjust based on volatility
        if volatility > 0.05:
            params['atr_multiplier_min'] = 1.2
            params['atr_multiplier_max'] = 2.5
        elif volatility < 0.02:
            params['atr_multiplier_min'] = 0.8
            params['atr_multiplier_max'] = 1.5
    
    return improved_ema_vwap_rsi_strategy(df, df_higher, params) 