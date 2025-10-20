"""Super simple quick start with Yahoo Finance data."""

import yfinance as yf
import sys
from pathlib import Path

# Add our modules to path
sys.path.insert(0, str(Path(__file__).parent / "src" / "tsindexing" / "data"))
from loader import TimeSeriesLoader
from segmentation import TimeSeriesSegmenter

sys.path.insert(0, str(Path(__file__).parent / "src" / "tsindexing" / "embeddings"))
from feature_encoder import FeatureEncoder


def quick_demo(symbol="AAPL"):
    """Quick 5-step demo with any stock symbol."""
    print(f"📈 Quick Demo with {symbol}")
    print("=" * 40)

    # Step 1: Download data
    print("1. Downloading data...")
    data = yf.Ticker(symbol).history(period="6mo")
    data = data.reset_index()
    print(f"   Got {len(data)} trading days")

    # Step 2: Load with TimeSeriesLoader
    print("2. Loading with TimeSeriesLoader...")
    data.to_csv("temp.csv", index=False)
    loader = TimeSeriesLoader()
    df = loader.load_csv("temp.csv", date_column="Date")
    print(f"   Shape: {df.shape}")

    # Step 3: Create segments
    print("3. Creating segments...")
    segments = loader.create_segments(
        df,
        window_size=10,  # 10-day windows
        stride=2,        # 2-day stride
        value_columns=["Close", "Volume"]
    )
    print(f"   Created {len(segments)} segments")

    # Step 4: Generate embeddings
    print("4. Generating embeddings...")
    encoder = FeatureEncoder(use_fft=True, use_statistical=True, pca_components=10)
    embeddings = encoder.fit_transform(segments)
    print(f"   Embeddings shape: {embeddings.shape}")

    # Step 5: Show results
    print("5. Results:")
    if segments:
        seg = segments[0]
        close_prices = seg['values'][:, 0]
        print(f"   First segment: {seg['timestamp_start'].date()} to {seg['timestamp_end'].date()}")
        print(f"   Price range: ${close_prices.min():.2f} - ${close_prices.max():.2f}")
        print(f"   Price change: {(close_prices[-1]/close_prices[0]-1)*100:.2f}%")

    # Cleanup
    import os
    if os.path.exists("temp.csv"):
        os.remove("temp.csv")

    print(f"\n✅ Done! Ready to build vector index with {len(segments)} segments")
    return segments, embeddings


if __name__ == "__main__":
    # Try different stocks
    symbols = ["AAPL", "GOOGL", "TSLA"]

    for symbol in symbols:
        try:
            quick_demo(symbol)
            print()
        except Exception as e:
            print(f"❌ Error with {symbol}: {e}")
            print()