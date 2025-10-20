"""Example integration of pattern library with time-series indexing system."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
from tsindexing.patterns.pattern_query import PatternQueryInterface


def demonstrate_pattern_integration():
    """Show how to integrate pattern library with existing vector search."""
    print("🔗 Pattern Library Integration Example")
    print("=" * 50)

    # Initialize pattern query interface
    query_interface = PatternQueryInterface()

    # Example text queries that users might ask
    user_queries = [
        "What periods are similar to Fed rate hikes?",
        "Find times like market crashes",
        "Show periods similar to VIX spikes",
        "When were there major market declines?",
        "Find Fed policy tightening periods"
    ]

    print("\n📊 Converting Text Queries to Embeddings:")
    print("-" * 40)

    for query in user_queries:
        print(f"\n🔍 Query: '{query}'")

        # Convert text to pattern embedding
        result = query_interface.query_pattern(query)

        if result["success"]:
            pattern_embedding = result["pattern_embedding"]
            pattern_type = result["pattern_type"]

            print(f"   ✅ Matched pattern: {pattern_type}")
            print(f"   📐 Embedding shape: {pattern_embedding.shape}")
            print(f"   📊 Embedding preview: [{pattern_embedding[0]:.3f}, {pattern_embedding[1]:.3f}, ...]")

            # This is where you'd integrate with your existing vector search
            print(f"   🔄 Ready for similarity search with your Chronos index")

            # Example integration code (commented out since we don't have the actual index):
            """
            # Use with existing Chronos vector search system
            similar_periods = your_chronos_index.search(
                query_embedding=pattern_embedding,
                top_k=10,
                threshold=0.7
            )

            print(f"   📈 Found {len(similar_periods)} similar periods")
            for period in similar_periods:
                print(f"     - {period['timestamp']}: similarity={period['score']:.3f}")
            """
        else:
            print(f"   ❌ Error: {result['error']}")

    # Show direct embedding access
    print(f"\n🎯 Direct Embedding Access:")
    print("-" * 30)

    # Get embedding directly for programmatic use
    fed_embedding, pattern_type = query_interface.text_to_embedding("Fed rate hikes")
    if fed_embedding is not None:
        print(f"Fed rate pattern embedding: {fed_embedding.shape}")
        print(f"Pattern type: {pattern_type}")

        # You can now use this embedding directly in your similarity search
        print(f"Ready to search for similar periods in your time-series database")

    # Show available patterns
    print(f"\n📋 Available Pattern Information:")
    print("-" * 30)

    pattern_info = query_interface.get_pattern_info("SPY")
    if "error" not in pattern_info:
        for pattern_name, info in pattern_info["available_patterns"].items():
            print(f"\n{pattern_name}:")
            print(f"  - Historical dates: {info['dates_count']}")
            print(f"  - Valid segments: {info['valid_segments']}")
            print(f"  - Embedding dimensions: {info['embedding_dimensions']}")
            print(f"  - Sample dates: {', '.join(info['sample_dates'])}")

    print(f"\n💡 Integration Steps:")
    print("-" * 20)
    print("1. User asks: 'Find periods like Fed rate hikes'")
    print("2. Pattern query converts text → Fed rate hike embedding")
    print("3. Your existing Chronos index searches for similar embeddings")
    print("4. Return ranked list of historically similar periods")
    print("5. User gets relevant time-series segments for analysis")

    print(f"\n🎉 Pattern library integration ready!")


if __name__ == "__main__":
    demonstrate_pattern_integration()