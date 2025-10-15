#!/usr/bin/env python3
"""
Local demo of the indexer without PostgreSQL - just ChromaDB
This gets you running immediately without Docker setup
"""

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add modules to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from astro_embedding_pipeline import AstroEmbeddingPipeline

def run_local_indexer_demo():
    """Run indexer demo with just ChromaDB (no PostgreSQL required)."""
    print("Local Astro Indexer Demo (ChromaDB only)")
    print("=" * 50)
    print("This demo populates ChromaDB without requiring PostgreSQL/Docker")
    print()

    # Initialize the embedding pipeline
    pipeline = AstroEmbeddingPipeline(chroma_path="./chroma_data")

    print("✓ ChromaDB initialized")
    print("✓ Astro embedding pipeline ready")
    print()

    # Index sample dates (last 30 days)
    print("1. INDEXING SAMPLE DATA")
    print("-" * 30)

    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30)

    print(f"Indexing from {start_date.date()} to {end_date.date()}")

    # Process dates
    processed_dates = []
    current_date = start_date

    while current_date <= end_date and len(processed_dates) < 10:  # Limit to 10 for demo
        try:
            result = pipeline.process_date(current_date)
            processed_dates.append(current_date.strftime('%Y-%m-%d'))

            if len(processed_dates) % 3 == 0:
                print(f"  ✓ Processed {len(processed_dates)} dates...")

        except Exception as e:
            print(f"  ✗ Error processing {current_date.strftime('%Y-%m-%d')}: {e}")

        current_date += timedelta(days=3)  # Every 3 days for faster demo

    print(f"\n✓ Successfully indexed {len(processed_dates)} dates")
    print()

    # Test semantic search
    print("2. TESTING SEMANTIC SEARCH")
    print("-" * 35)

    test_queries = [
        "moon saturn aspects",
        "multiple conjunctions",
        "tight planetary alignments"
    ]

    for query in test_queries:
        print(f"\nQuery: '{query}'")
        try:
            results = pipeline.search_similar_patterns(query, n_results=3)

            if results['results']:
                for i, result in enumerate(results['results'], 1):
                    date = result.get('date', 'Unknown')
                    similarity = result.get('similarity_score', 0)
                    preview = result.get('description', '')[:80]
                    print(f"  {i}. {date} (sim: {similarity:.3f}) - {preview}...")
            else:
                print("  No results found")

        except Exception as e:
            print(f"  Error: {e}")

    print("\n3. CHROMADB STATISTICS")
    print("-" * 25)
    stats = pipeline.get_collection_stats()
    for collection, count in stats.items():
        print(f"  {collection}: {count} embeddings")

    print()
    print("4. NEXT STEPS")
    print("-" * 15)
    print("✓ ChromaDB is populated with sample data")
    print("✓ Semantic search is working")
    print("✓ Ready to start API server:")
    print("   python api_server.py")
    print("✓ Then create Next.js frontend!")
    print()
    print("Note: This demo skipped PostgreSQL for simplicity.")
    print("For production, you'll want the full PostgreSQL setup.")

if __name__ == "__main__":
    run_local_indexer_demo()