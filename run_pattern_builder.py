"""Quick start script for building and testing financial patterns."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    """Build and test financial pattern library."""
    print("🚀 Financial Pattern Builder & Tester")
    print("=" * 50)

    # Step 1: Build patterns
    print("\n📊 Step 1: Building Pattern Library")
    print("-" * 30)

    try:
        from tsindexing.patterns.llm_pattern_builder import LLMPatternBuilder

        builder = LLMPatternBuilder()
        patterns = builder.build_pattern_library("SPY")

        print(f"✅ Built {len(patterns)} patterns successfully!")

    except Exception as e:
        print(f"❌ Error building patterns: {e}")
        print("\n💡 Make sure you have the required dependencies:")
        print("pip install yfinance chronos-forecasting torch")
        return

    # Step 2: Test query interface
    print("\n🔍 Step 2: Testing Query Interface")
    print("-" * 30)

    try:
        from tsindexing.patterns.pattern_query import PatternQueryInterface

        query_interface = PatternQueryInterface()

        # Test queries
        test_queries = [
            "What happens during Fed rate hikes?",
            "Find market crash patterns",
            "Show me VIX spike periods",
            "Analyze Fed policy changes"
        ]

        for query in test_queries:
            result = query_interface.query_pattern(query)

            if result["success"]:
                info = result["pattern_info"]
                print(f"✅ '{query}'")
                print(f"   → Pattern: {result['pattern_type']}")
                print(f"   → Dates: {info['total_dates']} total, {info['valid_segments']} valid")
                print(f"   → Embedding: {info['embedding_shape']}")
                print(f"   → Sample dates: {', '.join(info['sample_dates'])}")
            else:
                print(f"❌ '{query}' → {result['error']}")
            print()

    except Exception as e:
        print(f"❌ Error testing queries: {e}")
        return

    # Step 3: Show integration example
    print("\n🔗 Step 3: Integration Example")
    print("-" * 30)

    print("""
# How to use in your main system:

from tsindexing.patterns.pattern_query import PatternQueryInterface

# Initialize
query_interface = PatternQueryInterface()

# Convert text query to embedding
embedding, pattern_type = query_interface.text_to_embedding("Fed rate hikes")

# Use with your existing Chronos vector search
results = your_chronos_index.search(
    query_embedding=embedding,
    top_k=10
)

# Now you have similar historical periods!
    """)

    print("\n🎉 Pattern Library Setup Complete!")
    print("=" * 50)
    print("Your pattern library is ready to use!")
    print("\nNext steps:")
    print("1. Integrate with your existing Chronos vector search")
    print("2. Add more pattern types as needed")
    print("3. Test with real user queries")


if __name__ == "__main__":
    main()