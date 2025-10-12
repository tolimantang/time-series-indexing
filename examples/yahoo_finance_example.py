"""Example using real Yahoo Finance data with TimeSeriesLoader."""

import pandas as pd
import numpy as np
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import our components (without full package to avoid dependency issues)
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "tsindexing" / "data"))
from loader import TimeSeriesLoader


def download_yahoo_data(symbol="AAPL", period="2y"):
    """Download data from Yahoo Finance using yfinance (if available)."""
    try:
        import yfinance as yf

        print(f"Downloading {symbol} data for {period}...")
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period)

        # Reset index to get date as column
        data = data.reset_index()
        data.columns = [col.lower().replace(' ', '_') for col in data.columns]

        # Add symbol column for multi-asset compatibility
        data['symbol'] = symbol

        return data

    except ImportError:
        print("yfinance not installed. Install with: pip install yfinance")
        return None


def create_yahoo_compatible_csv():
    """Create sample CSV in Yahoo Finance format."""
    print("Creating sample data in Yahoo Finance format...")

    # Generate realistic stock data
    dates = pd.date_range(start="2022-01-01", end="2024-01-01", freq="D")
    n_days = len(dates)

    np.random.seed(42)

    # Simulate AAPL-like price movement
    base_price = 150
    returns = np.random.normal(0.0005, 0.02, n_days)  # Daily returns
    prices = base_price * np.exp(np.cumsum(returns))

    # Generate OHLCV data
    open_prices = prices * (1 + np.random.normal(0, 0.005, n_days))
    high_prices = np.maximum(open_prices, prices) * (1 + np.abs(np.random.normal(0, 0.01, n_days)))
    low_prices = np.minimum(open_prices, prices) * (1 - np.abs(np.random.normal(0, 0.01, n_days)))
    close_prices = prices
    volumes = np.random.lognormal(16, 0.5, n_days)  # Realistic volume distribution

    df = pd.DataFrame({
        "Date": dates,
        "Open": open_prices,
        "High": high_prices,
        "Low": low_prices,
        "Close": close_prices,
        "Volume": volumes.astype(int),
        "Symbol": "AAPL"
    })

    # Remove weekends (like real stock data)
    df = df[df['Date'].dt.dayofweek < 5]  # Monday=0, Friday=4

    df.to_csv("yahoo_finance_sample.csv", index=False)
    print(f"Created yahoo_finance_sample.csv with {len(df)} trading days")
    return df


def test_yahoo_format():
    """Test loading Yahoo Finance format data."""
    print("\n=== Testing Yahoo Finance Format ===")

    # Try to download real data first
    real_data = download_yahoo_data("AAPL", "1y")

    if real_data is not None:
        real_data.to_csv("real_yahoo_data.csv", index=False)
        test_file = "real_yahoo_data.csv"
        print("Using real Yahoo Finance data")
    else:
        create_yahoo_compatible_csv()
        test_file = "yahoo_finance_sample.csv"
        print("Using simulated Yahoo Finance format data")

    # Load with TimeSeriesLoader
    loader = TimeSeriesLoader()

    # Yahoo Finance typically uses 'Date' (capital D) and OHLCV format
    df = loader.load_csv(
        test_file,
        date_column="Date",  # Yahoo uses capital D
        value_columns=["Open", "High", "Low", "Close", "Volume"]
    )

    print(f"Loaded data shape: {df.shape}")
    print(f"Date range: {df.index.min().date()} to {df.index.max().date()}")
    print(f"Columns: {list(df.columns)}")
    print("\nFirst few rows:")
    print(df.head())

    # Create segments for analysis
    segments = loader.create_segments(
        df,
        window_size=20,  # 20 trading days (~ 1 month)
        stride=5,        # 5-day stride (weekly updates)
        value_columns=["Close", "Volume"]  # Focus on price and volume
    )

    print(f"\nCreated {len(segments)} segments")
    print(f"Each segment covers {segments[0]['window_size']} trading days")

    # Show segment example
    seg = segments[0]
    print(f"\nFirst segment:")
    print(f"Period: {seg['timestamp_start'].date()} to {seg['timestamp_end'].date()}")
    print(f"Values shape: {seg['values'].shape}")
    print(f"Close prices range: ${seg['values'][:, 0].min():.2f} - ${seg['values'][:, 0].max():.2f}")


def test_multi_stock_format():
    """Test with multiple stocks in one file."""
    print("\n=== Testing Multi-Stock Format ===")

    # Create multi-stock dataset
    symbols = ["AAPL", "GOOGL", "MSFT"]
    all_data = []

    for i, symbol in enumerate(symbols):
        # Try real data first
        real_data = download_yahoo_data(symbol, "6mo")

        if real_data is not None:
            real_data['symbol'] = symbol
            all_data.append(real_data)
        else:
            # Create synthetic data for this symbol
            dates = pd.date_range("2023-01-01", "2023-12-31", freq="D")
            dates = dates[dates.dayofweek < 5]  # Trading days only

            base_price = [150, 100, 300][i]  # Different base prices
            n_days = len(dates)

            np.random.seed(42 + i)
            returns = np.random.normal(0.0005, 0.02, n_days)
            prices = base_price * np.exp(np.cumsum(returns))

            synthetic_data = pd.DataFrame({
                "Date": dates,
                "Open": prices * (1 + np.random.normal(0, 0.005, n_days)),
                "High": prices * (1 + np.abs(np.random.normal(0, 0.01, n_days))),
                "Low": prices * (1 - np.abs(np.random.normal(0, 0.01, n_days))),
                "Close": prices,
                "Volume": np.random.lognormal(16, 0.5, n_days).astype(int),
                "symbol": symbol
            })
            all_data.append(synthetic_data)

    # Combine all stocks
    multi_stock_df = pd.concat(all_data, ignore_index=True)
    multi_stock_df.to_csv("multi_stock_data.csv", index=False)

    print(f"Created multi-stock dataset with {len(symbols)} symbols")
    print(f"Total rows: {len(multi_stock_df)}")

    # Load with symbol grouping
    loader = TimeSeriesLoader()
    df = loader.load_csv(
        "multi_stock_data.csv",
        date_column="Date",
        symbol_column="symbol",
        value_columns=["Close", "Volume"]
    )

    print(f"Loaded shape: {df.shape}")
    print(f"Symbols: {df['symbol'].unique()}")

    # Create segments by symbol
    segments = loader.create_segments(
        df,
        window_size=15,  # 15-day windows
        stride=3,        # 3-day stride
        value_columns=["Close", "Volume"],
        symbol_column="symbol"
    )

    print(f"Total segments: {len(segments)}")

    # Count by symbol
    symbol_counts = {}
    for seg in segments:
        symbol = seg["symbol"]
        symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1

    print("Segments per symbol:")
    for symbol, count in symbol_counts.items():
        print(f"  {symbol}: {count} segments")


def main():
    """Run Yahoo Finance compatibility tests."""
    print("=== Yahoo Finance Compatibility Demo ===\n")

    print("This demo shows how to use TimeSeriesLoader with:")
    print("1. Real Yahoo Finance data (if yfinance is installed)")
    print("2. Yahoo Finance CSV format")
    print("3. Multi-stock datasets\n")

    test_yahoo_format()
    test_multi_stock_format()

    print("\n=== Setup Instructions ===")
    print("To use with real Yahoo Finance data:")
    print("1. Install yfinance: pip install yfinance")
    print("2. Use any Yahoo Finance CSV export")
    print("3. Or download programmatically as shown above")

    print("\n=== Compatible Data Sources ===")
    print("✅ Yahoo Finance (Date, OHLCV format)")
    print("✅ Alpha Vantage CSV exports")
    print("✅ Quandl/NASDAQ Data Link")
    print("✅ Any CSV with date + numeric columns")
    print("✅ Multi-asset files with symbol column")

    # Cleanup
    import os
    cleanup_files = [
        "yahoo_finance_sample.csv",
        "real_yahoo_data.csv",
        "multi_stock_data.csv"
    ]

    for file in cleanup_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"Cleaned up {file}")


if __name__ == "__main__":
    main()