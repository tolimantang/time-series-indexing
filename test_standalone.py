"""Standalone test for TimeSeriesLoader."""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Import the loader class directly
sys.path.insert(0, str(Path(__file__).parent / "src" / "tsindexing" / "data"))
from loader import TimeSeriesLoader


def main():
    """Test the TimeSeriesLoader functionality."""
    print("=== TimeSeriesLoader Demo ===\n")

    # Create sample data
    dates = pd.date_range("2023-01-01", periods=50, freq="D")
    np.random.seed(42)

    # Simulate stock price with trend and noise
    trend = np.linspace(100, 120, 50)
    noise = np.random.normal(0, 2, 50)
    price = trend + noise

    df = pd.DataFrame({
        "date": dates,
        "price": price,
        "volume": np.random.randint(1000000, 5000000, 50),
        "high": price * 1.02,
        "low": price * 0.98
    })

    print("Sample data created:")
    print(df.head())
    print(f"Shape: {df.shape}")

    # Test the loader
    loader = TimeSeriesLoader()

    # Save and load CSV
    df.to_csv("sample.csv", index=False)
    loaded_df = loader.load_csv("sample.csv", date_column="date")

    print(f"\nAfter loading:")
    print(f"Shape: {loaded_df.shape}")
    print(f"Index type: {type(loaded_df.index)}")
    print(f"Columns: {list(loaded_df.columns)}")

    # Create segments
    segments = loader.create_segments(
        loaded_df,
        window_size=10,  # 10-day windows
        stride=3,        # 3-day overlap
        value_columns=["price", "volume"]
    )

    print(f"\nSegmentation results:")
    print(f"Created {len(segments)} segments")

    # Show details of first segment
    seg = segments[0]
    print(f"\nFirst segment details:")
    print(f"Period: {seg['timestamp_start']} to {seg['timestamp_end']}")
    print(f"Window size: {seg['window_size']}")
    print(f"Columns: {seg['columns']}")
    print(f"Values shape: {seg['values'].shape}")
    print(f"First 3 rows of values:")
    print(seg['values'][:3])

    # Test with multi-asset data
    print(f"\n--- Multi-Asset Test ---")

    # Create data for two assets
    df_aapl = df.copy()
    df_aapl['symbol'] = 'AAPL'

    df_googl = df.copy()
    df_googl['symbol'] = 'GOOGL'
    df_googl['price'] = df_googl['price'] * 0.8  # Different price level

    df_multi = pd.concat([df_aapl, df_googl], ignore_index=True)
    df_multi.to_csv("multi_asset.csv", index=False)

    loaded_multi = loader.load_csv("multi_asset.csv", symbol_column="symbol")
    print(f"Multi-asset data shape: {loaded_multi.shape}")
    print(f"Symbols: {loaded_multi['symbol'].unique()}")

    # Create segments by symbol
    segments_multi = loader.create_segments(
        loaded_multi,
        window_size=8,
        stride=2,
        value_columns=["price", "volume"],
        symbol_column="symbol"
    )

    print(f"Total segments: {len(segments_multi)}")

    # Count by symbol
    counts = {}
    for s in segments_multi:
        symbol = s['symbol']
        counts[symbol] = counts.get(symbol, 0) + 1

    for symbol, count in counts.items():
        print(f"{symbol}: {count} segments")

    print(f"\nDemo completed successfully!")

    # Cleanup
    import os
    for f in ["sample.csv", "multi_asset.csv"]:
        if os.path.exists(f):
            os.remove(f)


if __name__ == "__main__":
    main()