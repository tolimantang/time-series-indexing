"""Test TimeSeriesLoader with provided sample CSV files."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "tsindexing" / "data"))
from loader import TimeSeriesLoader


def test_sample_data():
    """Test with the provided sample CSV files."""
    print("=== Testing with Sample CSV Files ===\n")

    loader = TimeSeriesLoader()
    data_dir = Path(__file__).parent.parent / "data"

    # Test 1: Single asset Yahoo Finance format
    print("--- Test 1: Yahoo Finance Format (Single Asset) ---")
    yahoo_file = data_dir / "sample_yahoo_finance.csv"

    if yahoo_file.exists():
        df = loader.load_csv(
            yahoo_file,
            date_column="Date",
            value_columns=["Open", "High", "Low", "Close", "Volume"]
        )

        print(f"Loaded {yahoo_file.name}")
        print(f"Shape: {df.shape}")
        print(f"Date range: {df.index.min().date()} to {df.index.max().date()}")
        print(f"Columns: {list(df.columns)}")

        # Create segments
        segments = loader.create_segments(
            df,
            window_size=5,   # 5-day windows (1 week)
            stride=1,        # Daily stride
            value_columns=["Close", "Volume"]
        )

        print(f"Created {len(segments)} segments")
        print(f"First segment: {segments[0]['timestamp_start'].date()} to {segments[0]['timestamp_end'].date()}")
        print(f"Segment shape: {segments[0]['values'].shape}")

    else:
        print(f"Sample file {yahoo_file} not found")

    # Test 2: Multi-asset format
    print("\n--- Test 2: Multi-Asset Format ---")
    multi_file = data_dir / "sample_multi_asset.csv"

    if multi_file.exists():
        df = loader.load_csv(
            multi_file,
            date_column="Date",
            symbol_column="Symbol",
            value_columns=["Close", "Volume"]
        )

        print(f"Loaded {multi_file.name}")
        print(f"Shape: {df.shape}")
        print(f"Symbols: {df['Symbol'].unique()}")

        # Create segments by symbol
        segments = loader.create_segments(
            df,
            window_size=3,   # 3-day windows
            stride=1,        # Daily stride
            value_columns=["Close", "Volume"],
            symbol_column="Symbol"
        )

        print(f"Total segments: {len(segments)}")

        # Count by symbol
        counts = {}
        for seg in segments:
            symbol = seg["symbol"]
            counts[symbol] = counts.get(symbol, 0) + 1

        print("Segments per symbol:")
        for symbol, count in counts.items():
            print(f"  {symbol}: {count} segments")

        # Show example segment
        if segments:
            seg = segments[0]
            print(f"\nExample segment ({seg['symbol']}):")
            print(f"  Period: {seg['timestamp_start'].date()} to {seg['timestamp_end'].date()}")
            print(f"  Values: {seg['values'].shape}")
            print(f"  Close prices: {seg['values'][:, 0]}")

    else:
        print(f"Sample file {multi_file} not found")

    print("\n=== Data Format Guide ===")
    print("The TimeSeriesLoader works with any CSV that has:")
    print("✅ Date column (any name, auto-detected format)")
    print("✅ Numeric columns for time series values")
    print("✅ Optional symbol/ticker column for multi-asset data")
    print("\nCommon formats supported:")
    print("• Yahoo Finance: Date,Open,High,Low,Close,Volume")
    print("• Alpha Vantage: timestamp,open,high,low,close,volume")
    print("• Custom: date,price,volume,symbol")


if __name__ == "__main__":
    test_sample_data()