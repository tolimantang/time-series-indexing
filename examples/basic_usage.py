"""Basic usage example for time series indexing."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tsindexing import TimeSeriesLoader, FeatureEncoder, IndexBuilder, IndexQuery
from tsindexing.data.segmentation import TimeSeriesSegmenter


def create_sample_data() -> pd.DataFrame:
    """Create sample time series data for demonstration."""
    print("Creating sample time series data...")

    # Generate sample data
    dates = pd.date_range(start="2020-01-01", end="2023-12-31", freq="D")
    n_days = len(dates)

    # Create synthetic price data with trends and noise
    np.random.seed(42)

    # Base price trends
    trend1 = np.cumsum(np.random.normal(0.001, 0.02, n_days)) + 100
    trend2 = np.cumsum(np.random.normal(0.0005, 0.015, n_days)) + 50

    # Add some volatility clustering
    vol = np.random.normal(0.01, 0.005, n_days)
    vol = np.abs(vol)

    price1 = trend1 * (1 + np.random.normal(0, vol))
    price2 = trend2 * (1 + np.random.normal(0, vol * 0.8))

    df = pd.DataFrame({
        "date": dates,
        "AAPL": price1,
        "GOOGL": price2,
        "volume_AAPL": np.random.lognormal(15, 0.5, n_days),
        "volume_GOOGL": np.random.lognormal(14, 0.3, n_days)
    })

    return df


def main():
    """Run the complete example workflow."""
    print("=== Time Series Indexing Example ===\n")

    # 1. Create sample data
    df = create_sample_data()
    print(f"Created sample data with shape: {df.shape}")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}\n")

    # 2. Load and segment the data
    print("Loading and segmenting time series...")
    loader = TimeSeriesLoader()

    # Set date as index
    df_indexed = df.set_index("date")

    # Create segments
    segmenter = TimeSeriesSegmenter(window_size=30, stride=5)
    segments = segmenter.create_segments_with_features(
        df_indexed,
        value_columns=["AAPL", "GOOGL", "volume_AAPL", "volume_GOOGL"]
    )

    print(f"Created {len(segments)} segments\n")

    # 3. Encode segments into embeddings
    print("Encoding segments into embeddings...")
    encoder = FeatureEncoder(
        use_fft=True,
        fft_components=5,
        use_statistical=True,
        use_pca=True,
        pca_components=20
    )

    embeddings = encoder.fit_transform(segments)
    print(f"Generated embeddings with shape: {embeddings.shape}\n")

    # 4. Build vector index
    print("Building vector index...")
    index_builder = IndexBuilder(
        collection_name="stock_timeseries",
        use_memory=True  # Use in-memory for demo
    )

    index_builder.build_from_data(segments, embeddings)
    print(f"Index info: {index_builder.get_collection_info()}\n")

    # 5. Query similar segments
    print("Querying for similar segments...")
    query_interface = IndexQuery(
        collection_name="stock_timeseries",
        use_memory=True
    )

    # Use the last segment as a query
    query_segment = segments[-1]
    print(f"Query segment: {query_segment['timestamp_start']} to {query_segment['timestamp_end']}")

    similar_segments = query_interface.find_similar_contexts(
        current_segment=query_segment,
        encoder=encoder,
        top_k=5
    )

    print(f"\nFound {len(similar_segments)} similar segments:")
    for i, result in enumerate(similar_segments):
        metadata = result["metadata"]
        print(f"  {i+1}. Score: {result['score']:.3f}, "
              f"Period: {metadata['timestamp_start']} to {metadata['timestamp_end']}")

    # 6. Aggregate features from similar segments
    print("\nAggregating features from similar segments...")
    aggregated_features = query_interface.aggregate_features(similar_segments)

    if aggregated_features:
        print("Key aggregated features:")
        for feature_name, stats in list(aggregated_features.items())[:5]:
            print(f"  {feature_name}: mean={stats['mean']:.3f}, std={stats['std']:.3f}")
    else:
        print("  No features found in metadata")

    print("\n=== Example completed successfully! ===")


if __name__ == "__main__":
    main()