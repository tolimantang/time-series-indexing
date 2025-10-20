"""Quick start with real Yahoo Finance data."""

import yfinance as yf
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add src to path for our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import our classes directly to avoid dependency issues
sys.path.insert(0, str(Path(__file__).parent / "src" / "tsindexing" / "data"))
from loader import TimeSeriesLoader
from segmentation import TimeSeriesSegmenter

sys.path.insert(0, str(Path(__file__).parent / "src" / "tsindexing" / "embeddings"))
from feature_encoder import FeatureEncoder


def download_and_process_yahoo_data(symbol="AAPL", period="1y"):
    """Download and process Yahoo Finance data."""
    print(f"=== Processing {symbol} from Yahoo Finance ===\n")

    # 1. Download data
    print(f"Downloading {symbol} data for {period}...")
    ticker = yf.Ticker(symbol)
    data = ticker.history(period=period)

    if data.empty:
        print(f"No data found for {symbol}")
        return

    # Reset index to get Date as column
    data = data.reset_index()
    print(f"Downloaded {len(data)} trading days")
    print(f"Date range: {data['Date'].min().date()} to {data['Date'].max().date()}")

    # 2. Load with TimeSeriesLoader
    print("\nLoading data with TimeSeriesLoader...")
    data.to_csv(f"{symbol}_temp.csv", index=False)

    loader = TimeSeriesLoader()
    df = loader.load_csv(
        f"{symbol}_temp.csv",
        date_column="Date",
        value_columns=["Close", "Volume", "High", "Low"]
    )

    print(f"Loaded DataFrame shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")

    # 3. Create segments
    print("\nCreating time series segments...")
    segmenter = TimeSeriesSegmenter(
        window_size=20,  # 20 trading days (~1 month)
        stride=5,        # 5-day stride (weekly updates)
        min_periods=15   # At least 15 valid days required
    )

    segments = segmenter.create_segments_with_features(
        df,
        value_columns=["Close", "Volume"]
    )

    print(f"Created {len(segments)} segments")
    if segments:
        print(f"Each segment covers {segments[0]['window_size']} trading days")
        print(f"First segment: {segments[0]['timestamp_start'].date()} to {segments[0]['timestamp_end'].date()}")

    # 4. Create embeddings
    print("\nGenerating embeddings...")
    encoder = FeatureEncoder(
        use_fft=True,
        fft_components=5,
        use_statistical=True,
        use_pca=True,
        pca_components=15,
        normalize=True
    )

    if len(segments) > 0:
        embeddings = encoder.fit_transform(segments)
        print(f"Generated embeddings with shape: {embeddings.shape}")

        # Show some statistics
        print(f"\nEmbedding statistics:")
        print(f"  Mean: {embeddings.mean():.3f}")
        print(f"  Std: {embeddings.std():.3f}")
        print(f"  Min: {embeddings.min():.3f}")
        print(f"  Max: {embeddings.max():.3f}")

        # Show example segment analysis
        if len(segments) > 1:
            print(f"\nExample segment analysis:")
            seg = segments[0]
            features = seg.get('features', {})

            if features:
                print(f"  Segment features (sample):")
                for key, value in list(features.items())[:5]:
                    if isinstance(value, (int, float)):
                        print(f"    {key}: {value:.3f}")

            # Show price movement in first segment
            if 'values' in seg:
                close_prices = seg['values'][:, 0]  # Assuming Close is first column
                price_change = (close_prices[-1] / close_prices[0] - 1) * 100
                print(f"  Price movement: {price_change:.2f}%")
                print(f"  Price range: ${close_prices.min():.2f} - ${close_prices.max():.2f}")

        return segments, embeddings, encoder

    else:
        print("No segments created - data may be too short or have too many missing values")
        return None, None, None


def analyze_similar_segments(segments, embeddings, encoder, query_idx=0):
    """Find and analyze similar segments."""
    if not segments or embeddings is None:
        return

    print(f"\n=== Finding Similar Segments ===")

    # Use first segment as query
    query_embedding = embeddings[query_idx]
    query_segment = segments[query_idx]

    print(f"Query segment: {query_segment['timestamp_start'].date()} to {query_segment['timestamp_end'].date()}")

    # Calculate similarities (cosine similarity)
    from sklearn.metrics.pairwise import cosine_similarity

    similarities = cosine_similarity([query_embedding], embeddings)[0]

    # Get top 5 most similar (excluding the query itself)
    similar_indices = np.argsort(similarities)[::-1][1:6]

    print(f"\nTop 5 similar segments:")
    for i, idx in enumerate(similar_indices):
        sim_seg = segments[idx]
        similarity = similarities[idx]
        print(f"  {i+1}. Score: {similarity:.3f}, Period: {sim_seg['timestamp_start'].date()} to {sim_seg['timestamp_end'].date()}")

        # Show price movement comparison
        if 'values' in sim_seg:
            close_prices = sim_seg['values'][:, 0]
            price_change = (close_prices[-1] / close_prices[0] - 1) * 100
            print(f"     Price movement: {price_change:.2f}%")


def main():
    """Run the complete Yahoo Finance example."""
    print("🚀 Time Series Indexing with Real Yahoo Finance Data\n")

    # Test with a popular stock
    symbol = "AAPL"  # You can change this to any valid ticker
    segments, embeddings, encoder = download_and_process_yahoo_data(symbol, "2y")

    if segments and embeddings is not None:
        # Analyze similar segments
        analyze_similar_segments(segments, embeddings, encoder)

        print(f"\n✅ Successfully processed {symbol} data!")
        print(f"   - {len(segments)} segments created")
        print(f"   - {embeddings.shape[1]}-dimensional embeddings")
        print(f"   - Ready for vector database indexing")

        # Optional: Test with different stock
        print(f"\n" + "="*50)
        print("Testing with another stock...")
        segments2, embeddings2, encoder2 = download_and_process_yahoo_data("GOOGL", "1y")

    else:
        print("❌ Failed to process data")

    # Cleanup
    import os
    for file in [f"{symbol}_temp.csv", "GOOGL_temp.csv"]:
        if os.path.exists(file):
            os.remove(file)
            print(f"Cleaned up {file}")


if __name__ == "__main__":
    main()