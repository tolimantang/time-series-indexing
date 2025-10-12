"""Time series data loading utilities."""

from typing import Dict, List, Optional, Union
import pandas as pd
import numpy as np
from pathlib import Path


class TimeSeriesLoader:
    """Load and preprocess time series data."""

    def __init__(self):
        pass

    def load_csv(
        self,
        file_path: Union[str, Path],
        date_column: str = "date",
        value_columns: Optional[List[str]] = None,
        symbol_column: Optional[str] = None
    ) -> pd.DataFrame:
        """Load time series data from CSV file.

        Args:
            file_path: Path to CSV file
            date_column: Name of the date column
            value_columns: List of value column names. If None, uses all numeric columns
            symbol_column: Name of symbol/ticker column for multi-asset data

        Returns:
            DataFrame with datetime index and value columns
        """
        df = pd.read_csv(file_path)

        # Convert date column to datetime
        df[date_column] = pd.to_datetime(df[date_column])
        df = df.set_index(date_column)
        df = df.sort_index()

        # Select value columns
        if value_columns is None:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if symbol_column in numeric_cols:
                numeric_cols.remove(symbol_column)
            value_columns = numeric_cols

        # Include symbol column if specified
        columns_to_keep = value_columns.copy()
        if symbol_column and symbol_column in df.columns:
            columns_to_keep.append(symbol_column)

        return df[columns_to_keep]

    def create_segments(
        self,
        df: pd.DataFrame,
        window_size: int = 64,
        stride: int = 8,
        value_columns: Optional[List[str]] = None,
        symbol_column: Optional[str] = None
    ) -> List[Dict]:
        """Create overlapping segments from time series data.

        Args:
            df: DataFrame with datetime index
            window_size: Size of each segment
            stride: Step size between segments
            value_columns: Columns to include in segments
            symbol_column: Symbol column for grouping

        Returns:
            List of segment dictionaries
        """
        segments = []

        if value_columns is None:
            value_columns = df.select_dtypes(include=[np.number]).columns.tolist()
            if symbol_column in value_columns:
                value_columns.remove(symbol_column)

        if symbol_column and symbol_column in df.columns:
            # Group by symbol
            for symbol in df[symbol_column].unique():
                symbol_data = df[df[symbol_column] == symbol][value_columns]
                segments.extend(
                    self._create_segments_for_series(
                        symbol_data, window_size, stride, symbol
                    )
                )
        else:
            # Single series
            segments.extend(
                self._create_segments_for_series(
                    df[value_columns], window_size, stride
                )
            )

        return segments

    def _create_segments_for_series(
        self,
        series_data: pd.DataFrame,
        window_size: int,
        stride: int,
        symbol: Optional[str] = None
    ) -> List[Dict]:
        """Create segments for a single time series."""
        segments = []

        for i in range(0, len(series_data) - window_size + 1, stride):
            segment_data = series_data.iloc[i:i + window_size]

            # Skip if segment has too many NaN values
            if segment_data.isnull().sum().sum() > window_size * 0.1:
                continue

            segment = {
                "timestamp_start": segment_data.index[0],
                "timestamp_end": segment_data.index[-1],
                "values": segment_data.values,
                "columns": segment_data.columns.tolist(),
                "symbol": symbol,
                "window_size": window_size
            }

            segments.append(segment)

        return segments