"""
Signal generation for market data.
Computes technical indicators, correlations, and market regime indicators.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MarketSignalGenerator:
    """Generates market signals and technical indicators."""

    def __init__(self):
        self.indicators = {}

    def calculate_returns(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate various return metrics."""
        df = data.copy()

        # Daily returns
        df['daily_return'] = df['close'].pct_change()

        # Cumulative returns
        df['cumulative_return'] = (1 + df['daily_return']).cumprod() - 1

        # Rolling returns
        df['return_5d'] = df['close'].pct_change(5)
        df['return_20d'] = df['close'].pct_change(20)
        df['return_60d'] = df['close'].pct_change(60)

        return df

    def calculate_volatility(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate volatility metrics."""
        df = data.copy()

        # Realized volatility (various windows)
        df['vol_5d'] = df['daily_return'].rolling(5).std() * np.sqrt(252)
        df['vol_20d'] = df['daily_return'].rolling(20).std() * np.sqrt(252)
        df['vol_60d'] = df['daily_return'].rolling(60).std() * np.sqrt(252)

        # High-Low volatility
        df['hl_vol'] = np.log(df['high'] / df['low'])
        df['hl_vol_20d'] = df['hl_vol'].rolling(20).mean()

        # Volume-weighted metrics
        df['volume_ma_20'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma_20']

        return df

    def calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators."""
        df = data.copy()

        # Moving averages
        df['ma_5'] = df['close'].rolling(5).mean()
        df['ma_20'] = df['close'].rolling(20).mean()
        df['ma_50'] = df['close'].rolling(50).mean()
        df['ma_200'] = df['close'].rolling(200).mean()

        # Moving average relationships
        df['price_vs_ma20'] = (df['close'] / df['ma_20'] - 1) * 100
        df['price_vs_ma50'] = (df['close'] / df['ma_50'] - 1) * 100
        df['ma20_vs_ma50'] = (df['ma_20'] / df['ma_50'] - 1) * 100

        # RSI
        df['rsi'] = self.calculate_rsi(df['close'])

        # Bollinger Bands
        df = self.calculate_bollinger_bands(df)

        return df

    def calculate_rsi(self, prices: pd.Series, window: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_bollinger_bands(self, data: pd.DataFrame, window: int = 20, num_std: int = 2) -> pd.DataFrame:
        """Calculate Bollinger Bands."""
        df = data.copy()
        df['bb_middle'] = df['close'].rolling(window).mean()
        bb_std = df['close'].rolling(window).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * num_std)
        df['bb_lower'] = df['bb_middle'] - (bb_std * num_std)
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        return df

    def detect_regime(self, data: pd.DataFrame) -> pd.DataFrame:
        """Detect market regime indicators."""
        df = data.copy()

        # Volatility regime
        vol_median = df['vol_20d'].rolling(252).median()
        df['vol_regime'] = np.where(df['vol_20d'] > vol_median * 1.5, 'high_vol',
                                   np.where(df['vol_20d'] < vol_median * 0.75, 'low_vol', 'normal_vol'))

        # Trend regime
        df['trend_strength'] = df['ma20_vs_ma50'].abs()
        df['trend_regime'] = np.where(df['ma20_vs_ma50'] > 2, 'strong_uptrend',
                                     np.where(df['ma20_vs_ma50'] < -2, 'strong_downtrend', 'sideways'))

        # Momentum regime
        df['momentum_regime'] = np.where(df['return_20d'] > 10, 'strong_momentum',
                                        np.where(df['return_20d'] < -10, 'strong_reversal', 'normal_momentum'))

        return df

    def calculate_market_breadth(self, multiple_assets: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """Calculate market breadth indicators across multiple assets."""
        if len(multiple_assets) < 2:
            return pd.DataFrame()

        # Get common date range
        all_dates = set()
        for df in multiple_assets.values():
            all_dates.update(df.index)

        date_range = pd.DatetimeIndex(sorted(all_dates))

        # Calculate cross-asset metrics
        breadth_data = []

        for date in date_range:
            date_metrics = {'date': date}

            # Daily returns for all assets on this date
            daily_returns = []
            for symbol, df in multiple_assets.items():
                if date in df.index and 'daily_return' in df.columns:
                    ret = df.loc[date, 'daily_return']
                    if not pd.isna(ret):
                        daily_returns.append(ret)
                        date_metrics[f'{symbol}_return'] = ret

            if daily_returns:
                date_metrics['avg_return'] = np.mean(daily_returns)
                date_metrics['return_dispersion'] = np.std(daily_returns)
                date_metrics['positive_count'] = sum(1 for r in daily_returns if r > 0)
                date_metrics['total_count'] = len(daily_returns)
                date_metrics['breadth_ratio'] = date_metrics['positive_count'] / date_metrics['total_count']

            breadth_data.append(date_metrics)

        breadth_df = pd.DataFrame(breadth_data).set_index('date')
        return breadth_df

    def generate_comprehensive_signals(self, symbol: str, data: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive market signals for a symbol."""

        # Calculate all indicators
        df = self.calculate_returns(data)
        df = self.calculate_volatility(df)
        df = self.calculate_technical_indicators(df)
        df = self.detect_regime(df)

        # Get latest values (most recent trading day)
        latest = df.iloc[-1]

        # Create comprehensive signal dictionary
        signals = {
            'symbol': symbol,
            'date': latest.name.strftime('%Y-%m-%d'),
            'price': {
                'close': latest['close'],
                'daily_return': latest['daily_return'] * 100,  # Convert to percentage
                'return_5d': latest['return_5d'] * 100,
                'return_20d': latest['return_20d'] * 100,
                'return_60d': latest['return_60d'] * 100,
            },
            'volatility': {
                'vol_5d': latest['vol_5d'],
                'vol_20d': latest['vol_20d'],
                'vol_60d': latest['vol_60d'],
                'volume_ratio': latest['volume_ratio'],
            },
            'technical': {
                'rsi': latest['rsi'],
                'price_vs_ma20': latest['price_vs_ma20'],
                'price_vs_ma50': latest['price_vs_ma50'],
                'ma20_vs_ma50': latest['ma20_vs_ma50'],
                'bb_position': latest['bb_position'],
            },
            'regime': {
                'vol_regime': latest['vol_regime'],
                'trend_regime': latest['trend_regime'],
                'momentum_regime': latest['momentum_regime'],
            },
            'levels': {
                'ma_20': latest['ma_20'],
                'ma_50': latest['ma_50'],
                'bb_upper': latest['bb_upper'],
                'bb_lower': latest['bb_lower'],
            }
        }

        return signals

    def calculate_correlations(self, assets_data: Dict[str, pd.DataFrame],
                             windows: List[int] = [30, 90, 252]) -> Dict[str, Any]:
        """Calculate rolling correlations between assets."""
        correlations = {}

        symbols = list(assets_data.keys())

        for window in windows:
            correlations[f'{window}d'] = {}

            # Create combined return matrix
            returns_matrix = pd.DataFrame()
            for symbol, df in assets_data.items():
                if 'daily_return' in df.columns:
                    returns_matrix[symbol] = df['daily_return']

            # Calculate rolling correlation
            if len(returns_matrix.columns) >= 2:
                corr_matrix = returns_matrix.rolling(window).corr()

                # Extract latest correlations
                latest_corr = corr_matrix.iloc[-len(symbols):, :]

                for i, symbol1 in enumerate(symbols):
                    for j, symbol2 in enumerate(symbols):
                        if i < j:  # Avoid duplicates
                            pair = f"{symbol1}_{symbol2}"
                            if symbol1 in latest_corr.index and symbol2 in latest_corr.columns:
                                corr_value = latest_corr.loc[symbol1, symbol2]
                                if not pd.isna(corr_value):
                                    correlations[f'{window}d'][pair] = round(corr_value, 3)

        return correlations