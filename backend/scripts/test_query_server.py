#!/usr/bin/env python3
"""
Test Financial Query Server

Tests the intelligent query capabilities with real data.
"""

import sys
import os
from pathlib import Path
import asyncio
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

# Set PYTHONPATH environment variable
os.environ['PYTHONPATH'] = str(project_root / 'src')

from query.financial_server.query_engine import FinancialQueryEngine


async def test_query_engine():
    """Test the financial query engine with sample queries."""
    print("🔍 Testing Financial Query Engine")
    print("=" * 50)

    try:
        # Initialize query engine
        engine = FinancialQueryEngine()
        print("✅ Query engine initialized")

        # Test 1: Causal Analysis - What happens after Fed rate increases?
        print("\n1️⃣ Testing Causal Analysis: What happens after Fed rate increases?")
        causal_result = engine.analyze_causal_impact(
            trigger_event_type='fed_decision',
            trigger_conditions={'change_direction': 'increase'},
            impact_timeframe_days=30,
            limit=5
        )

        print(f"Found {causal_result.get('trigger_events_found', 0)} Fed rate increases")
        if causal_result.get('patterns'):
            patterns = causal_result['patterns']
            print(f"Average subsequent events per trigger: {patterns.get('avg_subsequent_events_per_trigger', 0):.1f}")
            print(f"Pattern strength: {patterns.get('pattern_strength', 'Unknown')}")

        # Test 2: Semantic Search
        print("\n2️⃣ Testing Semantic Search: Federal Reserve decisions")
        semantic_result = engine.semantic_search(
            query="Federal Reserve interest rate decisions and monetary policy",
            n_results=5
        )

        semantic_count = semantic_result.get('semantic_results', {}).get('count', 0)
        print(f"Found {semantic_count} semantically similar events")

        # Test 3: Time Series Analysis
        print("\n3️⃣ Testing Time Series Analysis: 2020-2024 high importance events")
        from datetime import date
        timeseries_result = engine.time_series_analysis(
            start_date=date(2020, 1, 1),
            end_date=date(2024, 12, 31),
            importance=['high']
        )

        events_count = len(timeseries_result.get('events', []))
        print(f"Found {events_count} high-importance events from 2020-2024")

        stats = timeseries_result.get('statistics', {})
        if stats:
            print(f"Total events in period: {stats.get('total_events', 0)}")

        # Test 4: Show sample results
        print("\n4️⃣ Sample Query Results:")
        if causal_result.get('individual_cases'):
            print("\n📊 Fed Rate Increase Impact Examples:")
            for i, case in enumerate(causal_result['individual_cases'][:2], 1):
                trigger = case['trigger_event']
                impact_count = case['impact_count']
                print(f"   {i}. {trigger['event_date']}: {trigger['title']}")
                print(f"      → {impact_count} subsequent events in 30 days")

        if timeseries_result.get('temporal_analysis'):
            temporal = timeseries_result['temporal_analysis']
            print(f"\n📈 Event Type Distribution:")
            for event_type, count in list(temporal.get('event_type_distribution', {}).items())[:3]:
                print(f"   • {event_type}: {count} events")

        print("\n✅ Query Engine Test Complete!")
        return True

    except Exception as e:
        print(f"❌ Query engine test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_examples():
    """Show example API calls that would work."""
    print("\n🌐 Example API Calls:")
    print("=" * 30)

    examples = [
        {
            "description": "What happens after Fed rate increases?",
            "endpoint": "POST /query/causal-analysis",
            "payload": {
                "trigger_event_type": "fed_decision",
                "trigger_conditions": {"change_direction": "increase"},
                "impact_timeframe_days": 30,
                "limit": 10
            }
        },
        {
            "description": "Find unemployment-related events",
            "endpoint": "POST /query/semantic-search",
            "payload": {
                "query": "unemployment rate changes and job market data",
                "start_date": "2020-01-01",
                "end_date": "2024-12-31",
                "n_results": 10
            }
        },
        {
            "description": "Simple natural language query",
            "endpoint": "GET /query/simple",
            "params": "?q=What happens after Fed rate increases?&limit=5"
        },
        {
            "description": "Time series analysis",
            "endpoint": "POST /query/time-series",
            "payload": {
                "start_date": "2020-01-01",
                "end_date": "2024-12-31",
                "event_types": ["fed_decision", "employment_data"],
                "importance": ["high"]
            }
        }
    ]

    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['description']}")
        print(f"   {example['endpoint']}")
        if 'payload' in example:
            print(f"   Payload: {json.dumps(example['payload'], indent=6)}")
        if 'params' in example:
            print(f"   Params: {example['params']}")

    print(f"\n💡 To test these:")
    print(f"   1. Run: python src/query/financial_server/api_server.py")
    print(f"   2. Visit: http://localhost:8003/docs (Swagger UI)")
    print(f"   3. Try: curl http://localhost:8003/query/simple?q=Fed%20rate%20increases")


if __name__ == "__main__":
    print("🚀 Financial Query Server Test Suite")

    # Test core engine
    success = asyncio.run(test_query_engine())

    # Show API examples
    test_api_examples()

    if success:
        print("\n🎯 Ready to answer complex financial questions!")
        print("💫 Try: 'What happens to platinum prices after Fed raises interest rates?'")
    else:
        print("\n❌ Fix the errors above before proceeding")
        sys.exit(1)