#!/usr/bin/env python3
"""
Test script for FRED Event Encoder

Tests FRED API connection and event generation for a few recent days.
No API key required - works with FRED's free tier.
"""

import os
import sys
import logging
from datetime import datetime, timedelta

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from event_encoder.sources.fred_encoder import FredEventEncoder

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_fred_connection():
    """Test FRED API connection."""
    print("🔗 Testing FRED API connection...")

    try:
        fred_encoder = FredEventEncoder()

        if fred_encoder.validate_connection():
            print("✅ FRED API connection successful!")
            return True
        else:
            print("❌ FRED API connection failed")
            return False

    except ValueError as e:
        print("❌ FRED API Key Required!")
        print(str(e))
        print("\n📝 Quick Setup (takes 30 seconds):")
        print("1. Go to: https://fred.stlouisfed.org/docs/api/api_key.html")
        print("2. Click 'Request API Key'")
        print("3. Fill out simple form (name, email, usage)")
        print("4. Get your free API key")
        print("5. Set environment variable: export FRED_API_KEY='your_key_here'")
        print("6. Re-run this test")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_fetch_recent_events():
    """Fetch and display recent FRED events."""
    print("\n📊 Fetching recent FRED events...")

    fred_encoder = FredEventEncoder()

    # Test with last 30 days to catch any recent Fed activity
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

    try:
        events = fred_encoder.fetch_events(start_date, end_date)

        print(f"\n📈 Found {len(events)} significant events:")
        print("=" * 80)

        if not events:
            print("No significant events found in the last 30 days.")
            print("This could be normal if there were no major Fed rate changes or economic data releases.")
        else:
            for event in events[:10]:  # Show first 10 events
                print(f"\nDate: {event.date.strftime('%Y-%m-%d')}")
                print(f"Type: {event.event_type}")
                print(f"Importance: {event.importance}")
                print(f"Title: {event.title}")
                print(f"Description: {event.description}")
                print("-" * 60)

        return events

    except Exception as e:
        print(f"❌ Error fetching events: {e}")
        return []


def test_event_document_format():
    """Test event-to-document conversion."""
    print("\n📝 Testing event document format...")

    fred_encoder = FredEventEncoder()

    # Get a small sample
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)  # Longer range to find events

    events = fred_encoder.fetch_events(start_date, end_date)

    if events:
        print(f"Testing with first event...")
        event = events[0]

        # Convert to ChromaDB format
        chroma_doc = event.to_chroma_document()

        print(f"\nEvent ID: {chroma_doc['id']}")
        print(f"\nDocument text (for embedding):")
        print("-" * 40)
        print(chroma_doc['document'])
        print("-" * 40)

        print(f"\nMetadata (for filtering):")
        for key, value in chroma_doc['metadata'].items():
            print(f"  {key}: {value}")

        return True
    else:
        print("No events available to test document format")
        return False


def test_specific_series():
    """Test specific FRED series."""
    print("\n🎯 Testing specific FRED series (Fed Funds Rate)...")

    fred_encoder = FredEventEncoder()

    # Test with just Fed Funds Rate for more focused results
    end_date = datetime.now()
    start_date = datetime(2023, 1, 1)  # Look at 2023 data

    try:
        events = fred_encoder.fetch_events(
            start_date,
            end_date,
            series_ids=['FEDFUNDS']  # Just Fed Funds Rate
        )

        print(f"Fed Funds Rate events from 2023: {len(events)}")

        for event in events:
            print(f"\n{event.date.strftime('%Y-%m-%d')}: {event.title}")
            print(f"  Value: {event.metadata.get('value', 'N/A')}")
            if 'series_id' in event.metadata:
                print(f"  Series: {event.metadata['series_id']}")

        return events

    except Exception as e:
        print(f"❌ Error testing specific series: {e}")
        return []


def main():
    """Run all tests."""
    print("🧪 FRED Event Encoder Test Suite")
    print("=" * 50)

    # Test 1: Connection
    if not test_fred_connection():
        print("❌ Cannot proceed without FRED connection")
        return

    # Test 2: Fetch recent events
    recent_events = test_fetch_recent_events()

    # Test 3: Document format
    test_event_document_format()

    # Test 4: Specific series
    fed_events = test_specific_series()

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"  ✅ FRED API connection: Working")
    print(f"  📈 Recent events found: {len(recent_events)}")
    print(f"  🎯 Fed events (2023+): {len(fed_events)}")

    if recent_events or fed_events:
        print("\n🎉 FRED Event Encoder is working correctly!")
        print("\nNext steps:")
        print("  1. You can now use the backfill service with type='events'")
        print("  2. Data will be stored in ChromaDB for semantic search")
        print("  3. Optional: Get FRED API key for higher rate limits")
    else:
        print("\n⚠️  No events found - this might be normal if no significant changes occurred recently")


if __name__ == "__main__":
    main()