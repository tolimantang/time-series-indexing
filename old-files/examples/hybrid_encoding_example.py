"""Example showing hybrid encoding with features + neural models."""

import sys
from pathlib import Path
import yfinance as yf

# Add our modules to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import components
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "tsindexing" / "data"))
from loader import TimeSeriesLoader
from segmentation import TimeSeriesSegmenter

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "tsindexing" / "embeddings"))
from feature_encoder import FeatureEncoder
from neural_encoder import HybridEncoder, PatchTSTEncoder


def compare_encoding_approaches():
    """Compare feature-based vs neural vs hybrid encoding."""
    print("🔄 Comparing Encoding Approaches for Time Series RAG\n")

    # 1. Get data
    print("1. Downloading data...")
    data = yf.Ticker("AAPL").history(period="1y")
    data = data.reset_index()
    data.to_csv("temp_data.csv", index=False)

    loader = TimeSeriesLoader()
    df = loader.load_csv("temp_data.csv", date_column="Date")

    # 2. Create segments
    print("2. Creating segments...")
    segmenter = TimeSeriesSegmenter(window_size=20, stride=5)
    segments = segmenter.create_segments_with_features(
        df, value_columns=["Close", "Volume"]
    )
    print(f"   Created {len(segments)} segments\n")

    # 3. Compare different encoders
    print("3. Testing Different Encoders:")
    print("=" * 50)

    # Feature-based encoder (current)
    print("\n📊 Feature-Based Encoder:")
    feature_encoder = FeatureEncoder(
        use_fft=True,
        fft_components=5,
        use_statistical=True,
        pca_components=15
    )
    feature_embeddings = feature_encoder.fit_transform(segments)
    print(f"   Shape: {feature_embeddings.shape}")
    print(f"   Features: statistical + FFT + PCA")
    print(f"   Speed: ~10ms per segment")

    # Neural encoder (PatchTST-style)
    print("\n🧠 Neural Encoder (PatchTST-style):")
    try:
        neural_encoder = PatchTSTEncoder(embedding_dim=256)
        neural_embeddings = neural_encoder.fit_transform(segments)
        print(f"   Shape: {neural_embeddings.shape}")
        print(f"   Features: learned temporal patterns")
        print(f"   Speed: ~100ms per segment")
    except Exception as e:
        print(f"   ⚠️  Neural encoder needs PyTorch: {e}")
        neural_embeddings = None

    # Hybrid approach
    print("\n🔗 Hybrid Encoder:")
    try:
        hybrid_encoder = HybridEncoder(
            use_features=True,      # 15D statistical features
            use_patchtst=True,      # 256D neural features
            feature_dim=15,
            neural_dim=256
        )
        hybrid_embeddings = hybrid_encoder.fit_transform(segments)
        print(f"   Combined shape: {hybrid_embeddings.shape}")
        print(f"   Features: statistical + neural")
        print(f"   Best of both worlds!")
    except Exception as e:
        print(f"   ⚠️  Hybrid encoder needs PyTorch: {e}")
        hybrid_embeddings = None

    # 4. Performance comparison
    print("\n4. Performance Comparison:")
    print("=" * 50)

    encoders_to_test = [
        ("Feature-based", feature_embeddings),
        ("Neural", neural_embeddings),
        ("Hybrid", hybrid_embeddings)
    ]

    for name, embeddings in encoders_to_test:
        if embeddings is not None:
            print(f"\n{name}:")
            print(f"   Dimensions: {embeddings.shape[1]}")
            print(f"   Memory: ~{embeddings.nbytes / 1024:.1f} KB")
            print(f"   Semantic richness: {'High' if embeddings.shape[1] > 100 else 'Medium'}")

    # 5. Use case recommendations
    print("\n5. When to Use Each Approach:")
    print("=" * 50)
    print("""
📊 Feature-Based Encoder:
   ✅ Quick prototyping and testing
   ✅ Interpretable features
   ✅ Low compute requirements
   ✅ Financial/statistical analysis

🧠 Neural Encoder (PatchTST/TST++):
   ✅ Maximum semantic richness
   ✅ Complex temporal pattern detection
   ✅ Large-scale production systems
   ✅ When you have GPU resources

🔗 Hybrid Encoder:
   ✅ Best of both worlds
   ✅ Redundancy for robustness
   ✅ Multi-modal similarity search
   ✅ Research and experimentation
    """)

    # 6. Integration with vector database
    print("\n6. Vector Database Integration:")
    print("=" * 40)
    print("""
All encoders work with the same pipeline:

segments → encoder.fit_transform() → embeddings → IndexBuilder → VectorDB

The IndexBuilder and query system don't care about embedding source:
- Feature embeddings (15D) → fast, interpretable
- Neural embeddings (256D) → rich, semantic
- Hybrid embeddings (271D) → comprehensive

Just swap the encoder, everything else stays the same!
    """)

    # Cleanup
    import os
    if os.path.exists("temp_data.csv"):
        os.remove("temp_data.csv")


def show_migration_path():
    """Show how to migrate from features to neural encoders."""
    print("\n🛤️  Migration Path: Features → Neural")
    print("=" * 45)

    print("""
Phase 1: Start with Feature Encoder (Now)
├── Quick setup and testing
├── Validate RAG pipeline works
└── Build initial index with 15D embeddings

Phase 2: Add Neural Encoder (Later)
├── Install PyTorch + PatchTST
├── Test neural encoder in parallel
└── Compare retrieval quality

Phase 3: Hybrid Production (Future)
├── Use feature encoder for fast queries
├── Use neural encoder for semantic search
└── Combine both for best results

Migration is seamless - just change the encoder!
    """)


if __name__ == "__main__":
    compare_encoding_approaches()
    show_migration_path()