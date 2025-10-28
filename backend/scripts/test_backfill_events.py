#!/usr/bin/env python3
"""
Test Events Backfill via API

Tests the backfill service API for events data.
"""

import requests
import json
import time
from datetime import datetime, timedelta

# Backfill service configuration
BACKFILL_URL = "http://localhost:8001"


def test_events_backfill():
    """Test events backfill via API."""
    print("🚀 Testing Events Backfill Service")
    print("=" * 50)

    # Check if service is running
    try:
        response = requests.get(f"{BACKFILL_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backfill service is running")
        else:
            print("❌ Backfill service health check failed")
            return
    except requests.RequestException:
        print("❌ Cannot connect to backfill service")
        print("   Make sure to run: cd backend && python src/services/backfill_service.py")
        return

    # Request events backfill for last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    backfill_request = {
        "type": "events",
        "start_date": start_date.strftime('%Y-%m-%d'),
        "end_date": end_date.strftime('%Y-%m-%d')
    }

    print(f"\n📊 Requesting events backfill...")
    print(f"Date range: {backfill_request['start_date']} to {backfill_request['end_date']}")

    try:
        # Start backfill
        response = requests.post(
            f"{BACKFILL_URL}/backfill",
            json=backfill_request,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            request_id = result['request_id']
            print(f"✅ Backfill started: {request_id}")

            # Monitor progress
            print("\n⏳ Monitoring progress...")
            max_wait = 120  # 2 minutes max
            waited = 0

            while waited < max_wait:
                time.sleep(5)
                waited += 5

                status_response = requests.get(f"{BACKFILL_URL}/backfill/{request_id}")

                if status_response.status_code == 200:
                    status = status_response.json()
                    print(f"Status: {status['status']} - {status['message']}")

                    if status['status'] == 'completed':
                        print(f"🎉 Backfill completed!")
                        print(f"Records processed: {status.get('records_processed', 'N/A')}")
                        print(f"Execution time: {status.get('execution_time_seconds', 'N/A')} seconds")
                        break
                    elif status['status'] == 'failed':
                        print(f"❌ Backfill failed: {status['message']}")
                        break
                else:
                    print(f"❌ Error checking status: {status_response.status_code}")
                    break
            else:
                print(f"⚠️ Timeout waiting for completion")

        else:
            print(f"❌ Failed to start backfill: {response.status_code}")
            print(response.text)

    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")


def test_data_summary():
    """Check data summary after backfill."""
    print("\n📈 Checking data summary...")

    try:
        response = requests.get(f"{BACKFILL_URL}/data/summary", timeout=10)

        if response.status_code == 200:
            summary = response.json()
            print("\nData Summary:")
            print(f"  Market data symbols: {summary.get('total_market_symbols', 0)}")

            astro_data = summary.get('astrological_data', {})
            if astro_data:
                positions = astro_data.get('planetary_positions', {})
                aspects = astro_data.get('planetary_aspects', {})
                print(f"  Planetary positions: {positions.get('count', 0)}")
                print(f"  Planetary aspects: {aspects.get('count', 0)}")

            # Events data would be in ChromaDB, not PostgreSQL
            print("  Events data: Stored in ChromaDB (not visible in this summary)")

        else:
            print(f"❌ Error getting summary: {response.status_code}")

    except requests.RequestException as e:
        print(f"❌ Summary request failed: {e}")


if __name__ == "__main__":
    test_events_backfill()
    test_data_summary()

    print("\n" + "=" * 50)
    print("✅ Test completed!")
    print("\nNext steps:")
    print("  1. Check ChromaDB for stored events")
    print("  2. Test semantic queries on the events")
    print("  3. Add more data sources (BLS, EODHD, etc.)")