#!/usr/bin/env python3
"""
Test Enhanced FRED Event Logic

Tests the refined FRED event detection with recent 2-3 years of data
to validate quality before running 50-year backfill.
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from event_encoder.sources.fred_encoder import FredEventEncoder


def test_enhanced_fred_logic():
    """Test enhanced FRED logic with recent data."""
    print("🧪 Testing Enhanced FRED Event Detection Logic")
    print("=" * 60)

    # Initialize encoder
    try:
        fred_encoder = FredEventEncoder()
        print("✅ FRED encoder initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize FRED encoder: {e}")
        return False

    # Test connection
    if not fred_encoder.validate_connection():
        print("❌ FRED API connection failed")
        return False
    print("✅ FRED API connection validated")

    # Test with recent 3 years of data
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3*365)  # 3 years

    print(f"\n📊 Testing with data from {start_date.date()} to {end_date.date()}")
    print(f"📋 Testing {len(fred_encoder.KEY_SERIES)} series:")

    for series_id, info in fred_encoder.KEY_SERIES.items():
        print(f"   • {series_id}: {info['name']} ({info['event_type']})")

    # Fetch events
    print(f"\n🔄 Fetching events...")
    try:
        events = fred_encoder.fetch_events(start_date, end_date)
        print(f"✅ Successfully fetched {len(events)} events")
    except Exception as e:
        print(f"❌ Error fetching events: {e}")
        return False

    # Analyze results
    print(f"\n📈 Event Analysis:")
    print(f"   Total events: {len(events)}")
    print(f"   Events per year: {len(events) / 3:.1f}")
    print(f"   Events per month: {len(events) / 36:.1f}")

    # Group by event type
    by_type = {}
    by_importance = {}
    by_year = {}

    for event in events:
        # By type
        if event.event_type not in by_type:
            by_type[event.event_type] = []
        by_type[event.event_type].append(event)

        # By importance
        if event.importance not in by_importance:
            by_importance[event.importance] = []
        by_importance[event.importance].append(event)

        # By year
        year = event.date.year
        if year not in by_year:
            by_year[year] = []
        by_year[year].append(event)

    print(f"\n📊 Events by Type:")
    for event_type, type_events in sorted(by_type.items()):
        print(f"   • {event_type}: {len(type_events)} events")

    print(f"\n⭐ Events by Importance:")
    for importance, imp_events in sorted(by_importance.items(), reverse=True):
        print(f"   • {importance}: {len(imp_events)} events")

    print(f"\n📅 Events by Year:")
    for year, year_events in sorted(by_year.items()):
        print(f"   • {year}: {len(year_events)} events")

    # Show sample events
    if events:
        print(f"\n📋 Sample Recent Events:")
        recent_events = sorted(events, key=lambda x: x.date, reverse=True)[:5]

        for i, event in enumerate(recent_events, 1):
            print(f"\n   {i}. {event.date.strftime('%Y-%m-%d')} - {event.title}")
            print(f"      Type: {event.event_type} | Importance: {event.importance}")
            print(f"      Description: {event.description[:100]}...")

    # Quality assessment
    print(f"\n🎯 Quality Assessment:")

    # Check if we have Fed decisions
    fed_events = [e for e in events if e.event_type in ['fed_decision', 'fed_meeting']]
    print(f"   Fed rate decisions: {len(fed_events)} (expect 24-30 over 3 years)")

    # Check high importance events
    high_imp_events = [e for e in events if e.importance == 'high']
    print(f"   High importance events: {len(high_imp_events)} ({len(high_imp_events)/len(events)*100:.1f}%)")

    # Target range analysis
    total_events = len(events)
    if total_events < 50:
        print(f"   ✅ Event volume: EXCELLENT ({total_events} events - low noise)")
    elif total_events < 150:
        print(f"   ✅ Event volume: GOOD ({total_events} events - reasonable)")
    elif total_events < 300:
        print(f"   ⚠️  Event volume: MODERATE ({total_events} events - some noise)")
    else:
        print(f"   ❌ Event volume: HIGH ({total_events} events - too noisy)")

    # Estimate 50-year backfill
    yearly_rate = len(events) / 3
    fifty_year_estimate = int(yearly_rate * 50)
    print(f"\n📈 50-Year Backfill Estimate:")
    print(f"   Estimated total events: ~{fifty_year_estimate:,}")
    print(f"   Storage estimate: ~{fifty_year_estimate * 2:.1f}MB in ChromaDB")

    if fifty_year_estimate < 5000:
        print(f"   ✅ Backfill size: EXCELLENT (manageable size)")
    elif fifty_year_estimate < 15000:
        print(f"   ✅ Backfill size: GOOD (reasonable size)")
    else:
        print(f"   ⚠️  Backfill size: LARGE (consider reducing thresholds)")

    print(f"\n✅ Enhanced FRED logic test completed!")
    return True


if __name__ == "__main__":
    success = test_enhanced_fred_logic()
    if not success:
        sys.exit(1)

    print(f"\n🎯 Recommendation:")
    print(f"   If quality looks good above, proceed with 50-year backfill!")
    print(f"   If too many events, adjust thresholds in fred_encoder.py")