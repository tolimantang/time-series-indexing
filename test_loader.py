"""Test script for TimeSeriesLoader functionality."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tsindexing.data.loader import TimeSeriesLoader


def create_test_csv():
    """Create a test CSV file with sample data."""
    # Generate 200 days of sample data
    dates = pd.date_range(start="2023-01-01", periods=200, freq="D")

    # Create synthetic stock data
    np.random.seed(42)
    aapl_price = 150 + np.cumsum(np.random.normal(0, 2, 200))
    googl_price = 100 + np.cumsum(np.random.normal(0, 1.5, 200))

    df = pd.DataFrame({
        "date": dates,
        "symbol": ["AAPL"] * 100 + ["GOOGL"] * 100,
        "price": np.concatenate([aapl_price[:100], googl_price[:100]]),
        "volume": np.random.randint(1000000, 5000000, 200),
        "high": np.concatenate([aapl_price[:100] * 1.02, googl_price[:100] * 1.02]),
        "low": np.concatenate([aapl_price[:100] * 0.98, googl_price[:100] * 0.98])
    })

    df.to_csv("sample_data.csv", index=False)
    print("Created sample_data.csv with 200 rows")
    return df


def test_single_asset_loading():
    """Test loading single asset data."""
    print("\n=== Testing Single Asset Loading ===")

    # Create simple single-asset data
    dates = pd.date_range("2023-01-01", periods=50, freq="D")
    df_single = pd.DataFrame({
        "date": dates,
        "price": 100 + np.random.randn(50) * 2,
        "volume": np.random.randint(100000, 500000, 50)
    })
    df_single.to_csv("single_asset.csv", index=False)

    loader = TimeSeriesLoader()

    # Load the data
    loaded_df = loader.load_csv("single_asset.csv")
    print(f"Loaded DataFrame shape: {loaded_df.shape}")
    print(f"Columns: {loaded_df.columns.tolist()}")
    print(f"Index type: {type(loaded_df.index)}")
    print(f"Date range: {loaded_df.index.min()} to {loaded_df.index.max()}")

    # Create segments
    segments = loader.create_segments(
        loaded_df,
        window_size=10,  # 10-day windows
        stride=2,        # 2-day stride
        value_columns=["price", "volume"]
    )

    print(f"\nCreated {len(segments)} segments")
    print(f"First segment:")
    print(f"  - Period: {segments[0]['timestamp_start']} to {segments[0]['timestamp_end']}")
    print(f"  - Shape: {segments[0]['values'].shape}")
    print(f"  - Columns: {segments[0]['columns']}")


def test_multi_asset_loading():
    """Test loading multi-asset data."""
    print("\n=== Testing Multi-Asset Loading ===")

    loader = TimeSeriesLoader()

    # Load multi-asset data
    loaded_df = loader.load_csv(
        "sample_data.csv",
        symbol_column="symbol"
    )

    print(f"Loaded DataFrame shape: {loaded_df.shape}")
    print(f"Columns: {loaded_df.columns.tolist()}")
    print(f"Unique symbols: {loaded_df['symbol'].unique()}")

    # Create segments with symbol grouping
    segments = loader.create_segments(
        loaded_df,
        window_size=20,  # 20-day windows
        stride=5,        # 5-day stride
        value_columns=["price", "volume", "high", "low"],
        symbol_column="symbol"
    )

    print(f"\nCreated {len(segments)} segments total")

    # Count segments by symbol
    symbol_counts = {}
    for segment in segments:
        symbol = segment["symbol"]
        symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1

    print("Segments per symbol:")
    for symbol, count in symbol_counts.items():
        print(f"  {symbol}: {count} segments")

    # Show example segment
    print(f"\nExample segment (symbol: {segments[0]['symbol']}):")
    print(f"  - Period: {segments[0]['timestamp_start']} to {segments[0]['timestamp_end']}")
    print(f"  - Values shape: {segments[0]['values'].shape}")
    print(f"  - First few values:\n{segments[0]['values'][:3]}")


def test_data_quality_filtering():
    """Test filtering of segments with missing data."""
    print("\n=== Testing Data Quality Filtering ===")

    # Create data with some NaN values
    dates = pd.date_range("2023-01-01", periods=30, freq="D")
    price_data = 100 + np.random.randn(30) * 2

    # Introduce some NaN values
    price_data[5:8] = np.nan  # 3 consecutive NaN
    price_data[15] = np.nan   # 1 isolated NaN

    df_with_nan = pd.DataFrame({
        "date": dates,
        "price": price_data,
        "volume": np.random.randint(100000, 500000, 30)
    })
    df_with_nan.to_csv("data_with_nan.csv", index=False)

    loader = TimeSeriesLoader()
    loaded_df = loader.load_csv("data_with_nan.csv")

    print(f"Data has NaN values: {loaded_df.isnull().sum().sum()} total")

    # Create segments - should filter out segments with too much missing data
    segments = loader.create_segments(
        loaded_df,
        window_size=10,
        stride=2,
        value_columns=["price", "volume"]
    )

    print(f"Created {len(segments)} segments (after filtering)")
    print("Segments should exclude windows with >10% missing data")


def main():
    """Run all tests."""
    print("Testing TimeSeriesLoader functionality...\n")

    # Create test data
    create_test_csv()

    # Run tests
    test_single_asset_loading()
    test_multi_asset_loading()
    test_data_quality_filtering()

    print("\n=== All tests completed! ===")

    # Cleanup
    import os
    for file in ["sample_data.csv", "single_asset.csv", "data_with_nan.csv"]:
        if os.path.exists(file):
            os.remove(file)
            print(f"Cleaned up {file}")


if __name__ == "__main__":
    main()