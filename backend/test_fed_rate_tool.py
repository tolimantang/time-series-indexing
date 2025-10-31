#!/usr/bin/env python3
"""
Test script for the enhanced FedRateChangesTool with LLM-generated WHERE clauses.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.mcp_tools.financial.fed_rate_tools import FedRateChangesTool
import json

class MockLLMClient:
    """Mock LLM client for testing."""

    class MockResponse:
        def __init__(self, text):
            self.text = text

    class MockContent:
        def __init__(self, text):
            self.content = [self.MockResponse(text)]

    class MockMessages:
        def create(self, model, max_tokens, system, messages):
            query = messages[0]["content"].lower()

            # Simple mock responses based on query content
            if "increase" in query and "2020" in query:
                response = {
                    "where_clause": "event_type = %s AND change_amount > %s AND event_date > %s",
                    "parameters": ["fed_decision", 0.0, "2020-01-01"]
                }
            elif "cut" in query or "decrease" in query:
                response = {
                    "where_clause": "event_type = %s AND change_amount < %s",
                    "parameters": ["fed_decision", 0.0]
                }
            else:
                response = {
                    "where_clause": "event_type = %s",
                    "parameters": ["fed_decision"]
                }

            return MockLLMClient.MockContent(json.dumps(response))

    def __init__(self):
        self.messages = self.MockMessages()

class MockPostgresManager:
    """Mock postgres manager for testing."""

    def __init__(self):
        self.connection = self

    def _ensure_connection(self):
        pass

    def cursor(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def execute(self, query, params):
        print(f"Executing SQL: {query}")
        print(f"Parameters: {params}")
        # Mock some results
        self.description = [
            ('event_id',), ('event_date',), ('title',), ('description',),
            ('value',), ('previous_value',), ('change_amount',), ('change_percent',),
            ('importance',), ('metadata',)
        ]

    def fetchall(self):
        # Return mock Fed rate data
        return [
            (1, '2022-03-16', 'Fed Raises Rates', 'Federal Reserve increases rates by 0.25%',
             0.50, 0.25, 0.25, 100.0, 5, '{}'),
            (2, '2022-05-04', 'Fed Raises Rates Again', 'Federal Reserve increases rates by 0.50%',
             1.00, 0.50, 0.50, 100.0, 5, '{}'),
        ]

def test_fed_rate_tool():
    """Test the enhanced FedRateChangesTool."""
    print("Testing Enhanced FedRateChangesTool")
    print("=" * 50)

    # Create mock dependencies
    postgres_manager = MockPostgresManager()
    llm_client = MockLLMClient()

    # Initialize tool
    tool = FedRateChangesTool(
        postgres_manager=postgres_manager,
        llm_client=llm_client
    )

    # Test natural language queries
    test_queries = [
        "Fed increases rates after 2020",
        "Large Fed rate cuts during crisis",
        "All Fed decisions in recent years"
    ]

    for query in test_queries:
        print(f"\nTesting query: '{query}'")
        print("-" * 30)

        try:
            result = tool.execute(query=query)

            if result['success']:
                print("✅ Query successful")
                print(f"Original query: {result['data']['query_parameters']['original_query']}")
                print(f"Generated WHERE clause: {result['data']['query_parameters']['generated_where_clause']}")
                print(f"Found {result['data']['total_events']} events")

                if result['data']['fed_rate_events']:
                    print("Sample event:")
                    event = result['data']['fed_rate_events'][0]
                    print(f"  Date: {event['event_date']}")
                    print(f"  Title: {event['title']}")
                    print(f"  Change: {event['change_amount']}%")
            else:
                print(f"❌ Query failed: {result['error']}")

        except Exception as e:
            print(f"❌ Exception: {e}")

    print("\n" + "=" * 50)
    print("Test completed!")

if __name__ == "__main__":
    test_fed_rate_tool()