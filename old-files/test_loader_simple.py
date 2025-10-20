"""Simple test for TimeSeriesLoader without external dependencies."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path and import only the loader
sys.path.insert(0, str(Path(__file__).parent / "src"))


def create_test_data():
    """Create sample time series data directly."""
    dates = pd.date_range(start="2023-01-01", periods=100, freq="D")

    # Create synthetic price data
    np.random.seed(42)
    base_price = 100
    returns = np.random.normal(0.001, 0.02, 100)  # Daily returns
    prices = base_price * np.exp(np.cumsum(returns))

    df = pd.DataFrame({
        "date": dates,
        "price": prices,
        "volume": np.random.lognormal(15, 0.3, 100),
        "symbol": "AAPL"
    })

    return df


def test_loader_manually():
    """Test the loader functionality step by step."""
    print("=== Testing TimeSeriesLoader Step by Step ===\n")

    # Import just the loader class
    from tsindexing.data.loader import TimeSeriesLoader

    # Create test data
    df = create_test_data()
    print(f"Created test data with shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")

    # Save to CSV and load back
    df.to_csv("test_data.csv", index=False)

    # Test 1: Basic CSV loading
    print("\n--- Test 1: Basic CSV Loading ---")
    loader = TimeSeriesLoader()
    loaded_df = loader.load_csv("test_data.csv", date_column="date")

    print(f"Loaded DataFrame shape: {loaded_df.shape}")
    print(f"Index type: {type(loaded_df.index)}")
    print(f"Columns: {list(loaded_df.columns)}")
    print(f"First few rows:")
    print(loaded_df.head(3))

    # Test 2: Create segments
    print("\n--- Test 2: Creating Segments ---")
    segments = loader.create_segments(
        loaded_df,
        window_size=10,  # 10-day windows
        stride=3,        # 3-day stride
        value_columns=["price", "volume"]
    )

    print(f"Created {len(segments)} segments")
    print(f"Window size: {segments[0]['window_size']}")
    print(f"Segment columns: {segments[0]['columns']}")

    # Show first segment details
    first_segment = segments[0]
    print(f"\nFirst segment:")
    print(f"  Period: {first_segment['timestamp_start']} to {first_segment['timestamp_end']}")
    print(f"  Values shape: {first_segment['values'].shape}")
    print(f"  Sample values (first 3 rows):")
    print(first_segment['values'][:3])

    # Test 3: Multi-symbol handling
    print("\n--- Test 3: Multi-Symbol Data ---")

    # Create multi-symbol data
    df_multi = pd.concat([
        df.assign(symbol="AAPL"),
        df.assign(symbol="GOOGL", price=df['price'] * 0.7, volume=df['volume'] * 1.2)
    ]).reset_index(drop=True)

    df_multi.to_csv("multi_symbol_data.csv", index=False)

    loaded_multi = loader.load_csv(
        "multi_symbol_data.csv",
        date_column="date",
        symbol_column="symbol"
    )

    print(f"Multi-symbol data shape: {loaded_multi.shape}")
    print(f"Unique symbols: {loaded_multi['symbol'].unique()}")

    segments_multi = loader.create_segments(
        loaded_multi,
        window_size=8,
        stride=2,
        value_columns=["price", "volume"],
        symbol_column="symbol"
    )

    print(f"Created {len(segments_multi)} segments total")

    # Count by symbol
    symbol_counts = {}
    for seg in segments_multi:
        symbol = seg["symbol"]
        symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1

    for symbol, count in symbol_counts.items():
        print(f"  {symbol}: {count} segments")

    print("\n=== TimeSeriesLoader tests completed successfully! ===")

    # Cleanup
    import os
    for f in ["test_data.csv", "multi_symbol_data.csv"]:
        if os.path.exists(f):
            os.remove(f)


if __name__ == "__main__":
    test_loader_manually()