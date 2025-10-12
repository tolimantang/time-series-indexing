"""Time series segmentation utilities."""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats


class TimeSeriesSegmenter:
    """Advanced time series segmentation with feature extraction."""

    def __init__(
        self,
        window_size: int = 64,
        stride: int = 8,
        min_periods: int = 32
    ):
        """Initialize segmenter.

        Args:
            window_size: Size of each segment
            stride: Step size between segments
            min_periods: Minimum number of valid observations required
        """
        self.window_size = window_size
        self.stride = stride
        self.min_periods = min_periods

    def create_segments_with_features(
        self,
        df: pd.DataFrame,
        value_columns: List[str],
        symbol_column: Optional[str] = None
    ) -> List[Dict]:
        """Create segments with extracted features.

        Args:
            df: DataFrame with datetime index
            value_columns: Columns to process
            symbol_column: Optional symbol column for grouping

        Returns:
            List of segment dictionaries with features
        """
        segments = []

        if symbol_column and symbol_column in df.columns:
            for symbol in df[symbol_column].unique():
                symbol_data = df[df[symbol_column] == symbol]
                segments.extend(
                    self._segment_single_series(
                        symbol_data, value_columns, symbol
                    )
                )
        else:
            segments.extend(
                self._segment_single_series(df, value_columns)
            )

        return segments

    def _segment_single_series(
        self,
        df: pd.DataFrame,
        value_columns: List[str],
        symbol: Optional[str] = None
    ) -> List[Dict]:
        """Create segments for a single time series."""
        segments = []

        for i in range(0, len(df) - self.window_size + 1, self.stride):
            segment_data = df.iloc[i:i + self.window_size]

            # Check data quality
            if not self._is_valid_segment(segment_data, value_columns):
                continue

            # Extract features
            features = self._extract_features(segment_data, value_columns)

            segment = {
                "timestamp_start": segment_data.index[0],
                "timestamp_end": segment_data.index[-1],
                "values": segment_data[value_columns].values,
                "columns": value_columns,
                "features": features,
                "symbol": symbol,
                "window_size": self.window_size
            }

            segments.append(segment)

        return segments

    def _is_valid_segment(
        self,
        segment_data: pd.DataFrame,
        value_columns: List[str]
    ) -> bool:
        """Check if segment has sufficient valid data."""
        valid_count = segment_data[value_columns].count().min()
        return valid_count >= self.min_periods

    def _extract_features(
        self,
        segment_data: pd.DataFrame,
        value_columns: List[str]
    ) -> Dict:
        """Extract statistical and technical features from segment."""
        features = {}

        for col in value_columns:
            series = segment_data[col].dropna()

            if len(series) < 2:
                continue

            # Basic statistics
            features[f"{col}_mean"] = series.mean()
            features[f"{col}_std"] = series.std()
            features[f"{col}_min"] = series.min()
            features[f"{col}_max"] = series.max()
            features[f"{col}_skew"] = stats.skew(series)
            features[f"{col}_kurtosis"] = stats.kurtosis(series)

            # Technical features
            returns = series.pct_change().dropna()
            if len(returns) > 0:
                features[f"{col}_return_mean"] = returns.mean()
                features[f"{col}_return_std"] = returns.std()
                features[f"{col}_total_return"] = (series.iloc[-1] / series.iloc[0]) - 1

            # Trend features
            if len(series) > 1:
                x = np.arange(len(series))
                slope, intercept, r_value, _, _ = stats.linregress(x, series.values)
                features[f"{col}_trend_slope"] = slope
                features[f"{col}_trend_r2"] = r_value ** 2

            # Volatility clustering
            if len(returns) > 1:
                abs_returns = np.abs(returns)
                if len(abs_returns) > 1:
                    features[f"{col}_vol_clustering"] = abs_returns.autocorr(lag=1)

        return features