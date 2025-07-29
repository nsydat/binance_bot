# models/strategy_selector.py
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
import joblib
import os
from binance import Client

# Cấu hình
MODEL_PATH = "models/xgb_strategy_model.pkl"
STRATEGIES = ['EMA_VWAP', 'RSI_DIVERGENCE', 'SUPERTREND_ATR', 'MACD_SIGNAL', 'BOLLINGER_BOUNCE']

client = Client()

class StrategySelector:
    def __init__(self):
        self.model = XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42
        )
        self.is_trained = False

    def add_features(self, df):
        """Trích xuất đặc trưng từ dữ liệu giá"""
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(10).std()
        df['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
        df['sma_short'] = df['close'].rolling(10).mean()
        df['sma_long'] = df['close'].rolling(30).mean()
        df['trend'] = (df['sma_short'] > df['sma_long']).astype(int)
        df['bb_high'] = ta.volatility.BollingerBands(df['close']).bollinger_hband()
        df['bb_low'] = ta.volatility.BollingerBands(df['close']).bollinger_lband()
        df['price_from_bb'] = (df['close'] - df['bb_low']) / (df['bb_high'] - df['bb_low'] + 1e-6)
        df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi_indicator()
        return df.dropna()

    def get_strategy_returns(self, df, look_ahead=5):
        """Mô phỏng lợi nhuận của từng chiến lược trong tương lai"""
        returns = {}
        close = df['close']
        future_return = (close.iloc[-1] - close.iloc[-look_ahead]) / close.iloc[-look_ahead]

        # Giả định đơn giản: nếu xu hướng phù hợp → thắng
        if future_return > 0:
            returns = {
                'EMA_VWAP': 1, 'SUPERTREND_ATR': 1, 'MACD_SIGNAL': 0.8,
                'RSI_DIVERGENCE': 0.3, 'BOLLINGER_BOUNCE': 0.2
            }
        else:
            returns = {
                'RSI_DIVERGENCE': 1, 'BOLLINGER_BOUNCE': 1,
                'EMA_VWAP': 0.2, 'SUPERTREND_ATR': 0.3, 'MACD_SIGNAL': 0.4
            }
        return max(returns, key=returns.get)

    def prepare_data(self, symbol="DOGEUSDT", interval="5m", limit=500):
        """Chuẩn bị dữ liệu huấn luyện"""
        klines = client.get_historical_klines(symbol, interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            'ts', 'o', 'h', 'l', 'c', 'v', 'ct', 'qav', 'tr', 'tb', 'tq', 'ig'
        ])
        df['close'] = pd.to_numeric(df['c'])
        df['high'] = pd.to_numeric(df['h'])
        df['low'] = pd.to_numeric(df['l'])
        df['volume'] = pd.to_numeric(df['v'])

        df = self.add_features(df)
        df['target_strategy'] = [self.get_strategy_returns(df.iloc[i:i+50]) 
                               for i in range(len(df)-50)] + [STRATEGIES[0]] * 50

        features = ['volatility', 'volume_ratio', 'trend', 'price_from_bb', 'rsi']
        X = df[features].iloc[:-50]
        y = df['target_strategy'].iloc[:-50].map({s: i for i, s in enumerate(STRATEGIES)})

        return X, y

    def train(self, symbol="DOGEUSDT"):
        print("🔄 Đang chuẩn bị dữ liệu...")
        X, y = self.prepare_data(symbol)

        print("🚀 Đang huấn luyện XGBoost...")
        self.model.fit(X, y)

        joblib.dump(self.model, MODEL_PATH)
        self.is_trained = True
        print(f"✅ Đã lưu mô hình tại: {MODEL_PATH}")

    def load(self):
        if os.path.exists(MODEL_PATH):
            self.model = joblib.load(MODEL_PATH)
            self.is_trained = True
            print("✅ Đã tải mô hình AI")
        else:
            print("❌ Không tìm thấy mô hình, sẽ huấn luyện lại")

    def predict(self, market_conditions, current_features):
        """
        Dự đoán chiến lược tốt nhất dựa trên điều kiện thị trường
        """
        if not self.is_trained:
            return ['EMA_VWAP', 'RSI_DIVERGENCE']  # Fallback

        # Chuyển điều kiện thị trường thành vector
        features_df = pd.DataFrame([[
            market_conditions['volatility'],
            market_conditions['volume_ratio'],
            1 if market_conditions['trend'] == 'BULLISH' else 0,
            0.5,  # price_from_bb (giả định)
            50    # RSI trung bình
        ]], columns=['volatility', 'volume_ratio', 'trend', 'price_from_bb', 'rsi'])

        pred = self.model.predict(features_df)[0]
        confidence = self.model.predict_proba(features_df).max()

        return [STRATEGIES[pred]], confidence  # Trả về danh sách chiến lược được chọn