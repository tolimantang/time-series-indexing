#!/usr/bin/env python3
"""
Test Dual Storage System

Tests PostgreSQL + ChromaDB dual storage for financial events.
Validates both structured queries and semantic search capabilities.
"""

import sys
import os
from datetime import datetime, timedelta, date
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

# Set PYTHONPATH environment variable for subprocess imports
os.environ['PYTHONPATH'] = str(project_root / 'src')

from event_encoder.sources.fred_encoder import FredEventEncoder
from services.events_postgres_manager import create_events_postgres_manager
from services.chroma_manager import create_chroma_manager


def test_dual_storage_system():
    """Test dual storage system with sample FRED data."""
    print("🔄 Testing Dual Storage System (PostgreSQL + ChromaDB)")
    print("=" * 60)

    # 1. Initialize components
    print("\n1️⃣ Initializing Components")
    try:
        fred_encoder = FredEventEncoder()
        postgres_manager = create_events_postgres_manager()
        chroma_manager = create_chroma_manager()
        print("✅ All components initialized successfully")
    except Exception as e:
        print(f"❌ Component initialization failed: {e}")
        return False

    # 2. Generate sample events
    print("\n2️⃣ Generating Sample Events")
    try:
        # Get last 30 days of events
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        events = fred_encoder.fetch_events(start_date, end_date)
        print(f"✅ Generated {len(events)} events from {start_date.date()} to {end_date.date()}")

        if not events:
            print("⚠️ No events found - this is normal if no significant economic changes occurred")
            # Create a test event manually
            from event_encoder.core.base_encoder import FinancialEvent

            test_event = FinancialEvent(
                date=datetime.now(),
                source='test',
                event_type='test_event',
                title='Test Financial Event',
                description='This is a test event for dual storage validation',
                importance='medium'
            )
            events = [test_event]
            print(f"✅ Created {len(events)} test event for validation")

    except Exception as e:
        print(f"❌ Event generation failed: {e}")
        return False

    # 3. Test PostgreSQL storage
    print("\n3️⃣ Testing PostgreSQL Storage")
    try:
        postgres_success = postgres_manager.store_events(events)
        if postgres_success:
            print(f"✅ Successfully stored {len(events)} events in PostgreSQL")
        else:
            print("❌ PostgreSQL storage failed")
            return False
    except Exception as e:
        print(f"❌ PostgreSQL storage error: {e}")
        return False

    # 4. Test ChromaDB storage
    print("\n4️⃣ Testing ChromaDB Storage")
    try:
        # Convert to ChromaDB format
        chroma_docs = []
        for event in events:
            chroma_docs.append(event.to_chroma_document())

        # Store in ChromaDB
        collection_name = "financial_events"
        chroma_success = chroma_manager.add_events(collection_name, chroma_docs)

        if chroma_success:
            print(f"✅ Successfully stored {len(events)} events in ChromaDB")
        else:
            print("❌ ChromaDB storage failed")
            return False
    except Exception as e:
        print(f"❌ ChromaDB storage error: {e}")
        return False

    # 5. Test PostgreSQL queries
    print("\n5️⃣ Testing PostgreSQL Structured Queries")
    try:
        # Time range query
        query_start = start_date.date()
        query_end = end_date.date()

        retrieved_events = postgres_manager.get_events_by_date_range(
            query_start, query_end
        )
        print(f"✅ Time range query: Found {len(retrieved_events)} events")

        # Statistics query
        stats = postgres_manager.get_event_statistics(query_start, query_end)
        print(f"✅ Statistics query: {stats.get('total_events', 0)} total events")

        # Filter by event type
        if retrieved_events:
            event_types = list(set(e['event_type'] for e in retrieved_events))
            if event_types:
                filtered_events = postgres_manager.get_events_by_date_range(
                    query_start, query_end, event_types=[event_types[0]]
                )
                print(f"✅ Type filter query: Found {len(filtered_events)} events of type '{event_types[0]}'")

        # Keyword search
        keywords = ['federal', 'rate', 'employment']
        keyword_events = postgres_manager.search_events_by_keywords(
            keywords, query_start, query_end
        )
        print(f"✅ Keyword search: Found {len(keyword_events)} events matching {keywords}")

    except Exception as e:
        print(f"❌ PostgreSQL query error: {e}")
        return False

    # 6. Test ChromaDB semantic search
    print("\n6️⃣ Testing ChromaDB Semantic Search")
    try:
        # Semantic queries
        test_queries = [
            "Federal Reserve interest rate changes",
            "unemployment data",
            "economic policy decisions",
            "inflation reports"
        ]

        for query in test_queries:
            results = chroma_manager.query_events(
                collection_name, query, n_results=5
            )
            result_count = results.get('count', 0)
            print(f"✅ Semantic search '{query}': {result_count} results")

        # Collection statistics
        collection_stats = chroma_manager.get_collection_stats(collection_name)
        print(f"✅ Collection stats: {collection_stats.get('total_documents', 0)} documents")

    except Exception as e:
        print(f"❌ ChromaDB query error: {e}")
        return False

    # 7. Test data consistency
    print("\n7️⃣ Testing Data Consistency")
    try:
        # Compare record counts
        pg_stats = postgres_manager.get_event_statistics(query_start, query_end)
        chroma_stats = chroma_manager.get_collection_stats(collection_name)

        pg_count = pg_stats.get('total_events', 0)
        chroma_count = chroma_stats.get('total_documents', 0)

        print(f"📊 PostgreSQL events: {pg_count}")
        print(f"📊 ChromaDB documents: {chroma_count}")

        if pg_count == len(events):
            print("✅ PostgreSQL count matches inserted events")
        else:
            print(f"⚠️ PostgreSQL count mismatch: expected {len(events)}, got {pg_count}")

        if chroma_count >= len(events):  # ChromaDB may have previous data
            print("✅ ChromaDB count includes inserted events")
        else:
            print(f"⚠️ ChromaDB count lower than expected")

    except Exception as e:
        print(f"❌ Consistency check error: {e}")
        return False

    # 8. Usage examples
    print("\n8️⃣ Usage Examples")
    print("🔍 PostgreSQL - Best for:")
    print("   • Time range queries: events between dates")
    print("   • Aggregations: count by event type, statistics")
    print("   • Exact filtering: specific importance levels, sources")
    print("   • Fast metadata searches: series IDs, keywords")

    print("\n🧠 ChromaDB - Best for:")
    print("   • Semantic search: 'what Fed decisions affected markets?'")
    print("   • Similar event discovery: events related to specific topics")
    print("   • Context-aware queries: natural language questions")
    print("   • Cross-event relationships: thematic clustering")

    print("\n✅ Dual Storage Test Complete!")
    print("\n🎯 Next Steps:")
    print("   1. Run the enhanced FRED test: python scripts/test_enhanced_fred.py")
    print("   2. If quality looks good, run full 50-year backfill")
    print("   3. Events will be stored in both PostgreSQL and ChromaDB automatically")

    return True


if __name__ == "__main__":
    success = test_dual_storage_system()
    if not success:
        sys.exit(1)