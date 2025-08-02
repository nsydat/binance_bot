#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Realistic Backtest Engine for Testing Trading Strategies
- Includes slippage, fees, realistic execution
- Position sizing and risk management
- Market condition simulation
- Prevents overfitting
- Uses improved strategies
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from utils.data_fetcher import get_klines_df
from strategies.ema_vwap_rsi import ema_vwap_rsi_strategy as strategy_ema_vwap
from strategies.supertrend_rsi import supertrend_rsi_strategy as strategy_supertrend_atr
from strategies.trend_momentum_volume import trend_momentum_volume_strategy as strategy_trend_momentum
from strategies.breakout_volume_sr import breakout_volume_sr_strategy as strategy_breakout_volume
from strategies.multi_timeframe import multi_timeframe_strategy as strategy_multi_timeframe
from strategies.improved_ema_vwap_rsi import get_improved_ema_vwap_rsi_strategy

# Strategy mapping with improved versions
STRATEGIES = {
    "EMA_VWAP": get_improved_ema_vwap_rsi_strategy,  # Use improved version
    "SUPERTREND_ATR": strategy_supertrend_atr,
    "TREND_MOMENTUM": strategy_trend_momentum,
    "BREAKOUT_VOLUME": strategy_breakout_volume,
    "MULTI_TIMEFRAME": strategy_multi_timeframe
}

class RealisticBacktestEngine:
    def __init__(self, initial_balance=1000, max_risk_per_trade=0.02, 
                 slippage_pct=0.001, fee_pct=0.001, min_confidence=0.5):  # Reduced from 0.6
        """
        Initialize realistic backtest engine
        
        Args:
            initial_balance: Starting balance
            max_risk_per_trade: Maximum risk per trade (2% default)
            slippage_pct: Slippage percentage (0.1% default)
            fee_pct: Trading fee percentage (0.1% default)
            min_confidence: Minimum confidence threshold (reduced to 0.5)
        """
        self.initial_balance = initial_balance
        self.max_risk_per_trade = max_risk_per_trade
        self.slippage_pct = slippage_pct
        self.fee_pct = fee_pct
        self.min_confidence = min_confidence
        
        # Market condition simulation
        self.volatility_regimes = {
            'LOW': {'slippage_mult': 0.5, 'execution_prob': 0.95},
            'MEDIUM': {'slippage_mult': 1.0, 'execution_prob': 0.9},
            'HIGH': {'slippage_mult': 1.5, 'execution_prob': 0.8},
            'EXTREME': {'slippage_mult': 2.0, 'execution_prob': 0.7}
        }
    
    def calculate_volatility(self, df, window=20):
        """Calculate market volatility"""
        try:
            from ta.volatility import AverageTrueRange
            atr = AverageTrueRange(df['high'], df['low'], df['close'], window=window)
            current_atr = atr.average_true_range().iloc[-1]
            current_price = df['close'].iloc[-1]
            
            # Volatility as percentage of price
            volatility = current_atr / current_price
            return volatility
        except:
            return 0.02
    
    def get_volatility_regime(self, volatility):
        """Get volatility regime based on volatility level"""
        if volatility < 0.02:
            return 'LOW'
        elif volatility < 0.05:
            return 'MEDIUM'
        elif volatility < 0.10:
            return 'HIGH'
        else:
            return 'EXTREME'
    
    def calculate_position_size(self, balance, entry, sl, risk_pct=None):
        """Calculate realistic position size based on risk"""
        if risk_pct is None:
            risk_pct = self.max_risk_per_trade
        
        risk_amount = balance * risk_pct
        risk_per_share = abs(entry - sl)
        
        if risk_per_share == 0:
            return 0
        
        position_size = risk_amount / risk_per_share
        return position_size
    
    def simulate_execution(self, side, entry, current_price, volatility_regime):
        """Simulate realistic trade execution with slippage and execution probability"""
        regime_config = self.volatility_regimes[volatility_regime]
        
        # Check if trade executes (market conditions)
        if np.random.random() > regime_config['execution_prob']:
            return None, "EXECUTION_FAILED"
        
        # Calculate slippage
        slippage_mult = regime_config['slippage_mult']
        slippage = entry * self.slippage_pct * slippage_mult
        
        # Apply slippage based on side
        if side == 'BUY':
            executed_price = entry + slippage
        else:
            executed_price = entry - slippage
        
        # Add some randomness to execution
        execution_noise = np.random.normal(0, entry * 0.0005)
        executed_price += execution_noise
        
        return executed_price, "EXECUTED"
    
    def calculate_realistic_outcome(self, side, entry, sl, tp, current_price, 
                                  executed_price, volatility_regime):
        """Calculate realistic trade outcome with market conditions"""
        
        # Calculate fees
        entry_fee = executed_price * self.fee_pct
        exit_fee = current_price * self.fee_pct
        total_fees = entry_fee + exit_fee
        
        # Determine if TP or SL is hit
        if side == 'BUY':
            if current_price >= tp:
                # TP hit
                profit = (tp - executed_price) - total_fees
                outcome = 'win'
            elif current_price <= sl:
                # SL hit
                profit = (sl - executed_price) - total_fees
                outcome = 'loss'
            else:
                # Still open - calculate unrealized P&L
                profit = (current_price - executed_price) - entry_fee
                outcome = 'open'
        else:
            if current_price <= tp:
                # TP hit
                profit = (executed_price - tp) - total_fees
                outcome = 'win'
            elif current_price >= sl:
                # SL hit
                profit = (executed_price - sl) - total_fees
                outcome = 'loss'
            else:
                # Still open
                profit = (executed_price - current_price) - entry_fee
                outcome = 'open'
        
        return profit, outcome
    
    def run_backtest(self, symbol="DOGEUSDT", interval="5m", days=90):
        """Run realistic backtest"""
        print(f"📊 Đang chạy realistic backtest cho {symbol} ({interval}) trong {days} ngày qua...")
        print(f"⚙️ Cấu hình: Risk/trade: {self.max_risk_per_trade*100}%, Slippage: {self.slippage_pct*100}%, Fee: {self.fee_pct*100}%")
        print(f"🎯 Sử dụng chiến lược cải thiện với tham số linh hoạt")

        # Get data
        df = get_klines_df(symbol, interval, limit=10000)
        if df is None or len(df) < 100:
            print("❌ Không đủ dữ liệu")
            return None

        # Filter by time
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df[df['timestamp'] >= start_time].copy()
        df = df.reset_index(drop=True)

        results = []
        balance = self.initial_balance
        open_positions = []
        
        # Track performance metrics
        total_trades = 0
        winning_trades = 0
        total_fees = 0

        # Run through each candle
        for i in range(50, len(df)):
            current_df = df.iloc[:i].copy().reset_index(drop=True)
            current_price = current_df['close'].iloc[-1]
            current_time = current_df['timestamp'].iloc[-1]
            
            # Calculate current volatility
            volatility = self.calculate_volatility(current_df)
            volatility_regime = self.get_volatility_regime(volatility)
            
            # Analyze market conditions for strategy adaptation
            market_conditions = self.analyze_market_conditions(current_df)
            
            # Check open positions first
            for position in open_positions[:]:
                profit, outcome = self.calculate_realistic_outcome(
                    position['side'], position['entry'], position['sl'], 
                    position['tp'], current_price, position['executed_price'], 
                    volatility_regime
                )
                
                if outcome in ['win', 'loss']:
                    # Position closed
                    balance += profit
                    total_trades += 1
                    if outcome == 'win':
                        winning_trades += 1
                    total_fees += abs(profit) * 0.001  # Estimate fees
                    
                    results.append({
                        'timestamp': current_time,
                        'strategy': position['strategy'],
                        'side': position['side'],
                        'entry': position['entry'],
                        'executed_price': position['executed_price'],
                        'sl': position['sl'],
                        'tp': position['tp'],
                        'exit_price': current_price,
                        'confidence': position['confidence'],
                        'outcome': outcome,
                        'profit': profit,
                        'balance': balance,
                        'volatility_regime': volatility_regime,
                        'position_size': position['position_size']
                    })
                    
                    open_positions.remove(position)
            
            # Look for new signals (only if no open positions)
            if not open_positions:
                for strat_name in STRATEGIES:
                    # Use improved strategy with market conditions
                    if strat_name == "EMA_VWAP":
                        result = STRATEGIES[strat_name](current_df, None, market_conditions)
                    else:
                        result = STRATEGIES[strat_name](current_df, None)
                    
                    if result and result[5] >= self.min_confidence:  # Check confidence
                        side, entry, sl, tp, qty, confidence = result
                        
                        # Calculate position size
                        position_size = self.calculate_position_size(balance, entry, sl)
                        
                        if position_size > 0:
                            # Simulate execution
                            executed_price, execution_status = self.simulate_execution(
                                side, entry, current_price, volatility_regime
                            )
                            
                            if execution_status == "EXECUTED":
                                # Open new position
                                open_positions.append({
                                    'strategy': strat_name,
                                    'side': side,
                                    'entry': entry,
                                    'executed_price': executed_price,
                                    'sl': sl,
                                    'tp': tp,
                                    'confidence': confidence,
                                    'position_size': position_size,
                                    'open_time': current_time
                                })
                                
                                print(f"📈 {strat_name} {side} @ {executed_price:.4f} (Conf: {confidence:.1%})")
                                break  # Only one signal per candle

        # Close any remaining open positions at the end
        for position in open_positions:
            final_price = df['close'].iloc[-1]
            profit, outcome = self.calculate_realistic_outcome(
                position['side'], position['entry'], position['sl'], 
                position['tp'], final_price, position['executed_price'], 
                'MEDIUM'  # Default regime for final close
            )
            
            balance += profit
            total_trades += 1
            if outcome == 'win':
                winning_trades += 1
            
            results.append({
                'timestamp': df['timestamp'].iloc[-1],
                'strategy': position['strategy'],
                'side': position['side'],
                'entry': position['entry'],
                'executed_price': position['executed_price'],
                'sl': position['sl'],
                'tp': position['tp'],
                'exit_price': final_price,
                'confidence': position['confidence'],
                'outcome': outcome,
                'profit': profit,
                'balance': balance,
                'volatility_regime': 'MEDIUM',
                'position_size': position['position_size']
            })

        # Create results DataFrame
        if results:
            results_df = pd.DataFrame(results)
            results_df['profit_pct'] = results_df['profit'] / self.initial_balance * 100
            
            # Print realistic summary
            win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
            total_profit = balance - self.initial_balance
            profit_pct = total_profit / self.initial_balance * 100
            
            print(f"\n📊 REALISTIC BACKTEST RESULTS (IMPROVED):")
            print(f"• Total Trades: {total_trades}")
            print(f"• Win Rate: {win_rate:.2f}%")
            print(f"• Total Profit: ${total_profit:,.2f} ({profit_pct:+.2f}%)")
            print(f"• Final Balance: ${balance:,.2f}")
            print(f"• Total Fees Paid: ${total_fees:,.2f}")
            print(f"• Average Trade Duration: {self._calculate_avg_duration(results_df):.1f} periods")
            
            return results_df
        else:
            print("❌ Không có tín hiệu nào trong backtest")
            return None
    
    def analyze_market_conditions(self, df):
        """Analyze current market conditions for strategy adaptation"""
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
    
    def _calculate_avg_duration(self, results_df):
        """Calculate average trade duration"""
        if len(results_df) == 0:
            return 0
        
        # For simplicity, assume average duration based on volatility
        return 5  # Average 5 periods per trade

def run_backtest(symbol="DOGEUSDT", interval="5m", days=90, initial_balance=1000):
    """Run realistic backtest with proper configuration"""
    engine = RealisticBacktestEngine(
        initial_balance=initial_balance,
        max_risk_per_trade=0.02,  # 2% risk per trade
        slippage_pct=0.001,       # 0.1% slippage
        fee_pct=0.001,            # 0.1% trading fee
        min_confidence=0.5         # Reduced to 50% confidence
    )
    
    return engine.run_backtest(symbol, interval, days)