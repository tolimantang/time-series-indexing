#!/usr/bin/env python3
"""
Demo: How an LLM would interact with the MCP Fed Rate Changes tool.

This shows the complete workflow:
1. LLM receives user query
2. LLM detects need for precise numerical query
3. LLM calls the MCP tool with correct parameters
4. Tool returns structured results
5. LLM presents results to user
"""

import json

# Simulate the tool schema that would be provided to the LLM
FED_RATE_TOOL_SCHEMA = {
    "name": "fed_rate_changes",
    "description": "Find Federal Reserve rate changes with precise numerical filters",
    "parameters": {
        "type": "object",
        "properties": {
            "direction": {
                "type": "string",
                "enum": ["increase", "decrease", "any"],
                "description": "Direction of rate change"
            },
            "min_magnitude": {
                "type": "number",
                "description": "Minimum change magnitude in percentage points (e.g., 0.25 for 0.25%)"
            },
            "max_magnitude": {
                "type": "number",
                "description": "Maximum change magnitude in percentage points"
            },
            "start_date": {
                "type": "string",
                "format": "date",
                "description": "Start date for search (YYYY-MM-DD)"
            },
            "end_date": {
                "type": "string",
                "format": "date",
                "description": "End date for search (YYYY-MM-DD)"
            },
            "target_asset": {
                "type": "string",
                "description": "Optional: Asset symbol to analyze market impact (e.g., 'GLD', 'SPY')"
            }
        },
        "required": ["direction", "start_date", "end_date"]
    }
}

# Simulate tool responses for different queries
MOCK_TOOL_RESPONSES = {
    "fed_cuts_025": {
        "success": True,
        "data": {
            "query_parameters": {
                "direction": "decrease",
                "min_magnitude": 0.25,
                "date_range": "2020-01-01 to 2023-12-31",
                "target_asset": "GLD"
            },
            "fed_rate_events": [
                {
                    "event_date": "2020-03-03",
                    "title": "Federal Funds Rate: Federal Reserve cuts rate by 0.50 percentage points to 1.25%",
                    "change_amount": -0.50,
                    "value": 1.25,
                    "previous_value": 1.75
                },
                {
                    "event_date": "2020-03-15",
                    "title": "Federal Funds Rate: Federal Reserve cuts rate by 1.00 percentage points to 0.25%",
                    "change_amount": -1.00,
                    "value": 0.25,
                    "previous_value": 1.25
                }
            ],
            "total_events": 2,
            "summary_statistics": {
                "average_magnitude": 0.75,
                "largest_change": 1.00,
                "smallest_change": 0.50
            },
            "market_impact_analysis": {
                "aggregate_statistics": {
                    "total_events_analyzed": 2,
                    "average_5d_return": 3.2,
                    "positive_events": 2,
                    "negative_events": 0,
                    "success_rate": 100.0
                }
            }
        }
    },
    "fed_cuts_small": {
        "success": True,
        "data": {
            "query_parameters": {
                "direction": "decrease",
                "max_magnitude": 0.1,
                "date_range": "2020-01-01 to 2023-12-31"
            },
            "fed_rate_events": [],
            "total_events": 0,
            "summary_statistics": {
                "average_magnitude": 0,
                "largest_change": 0,
                "smallest_change": 0
            }
        }
    }
}


def simulate_llm_query_processing(user_query: str):
    """Simulate how an LLM would process different user queries."""
    print(f"🤖 User Query: \"{user_query}\"")
    print("=" * 80)

    # LLM analysis and tool calling logic
    if "fed" in user_query.lower() and "cut" in user_query.lower():

        # Extract numerical constraints from query
        if "more than 0.25%" in user_query or "above 0.25%" in user_query:
            print("🧠 LLM Analysis: User wants Fed cuts LARGER than 0.25%")
            print("🔧 Tool Selection: Using fed_rate_changes tool with min_magnitude=0.25")

            tool_params = {
                "direction": "decrease",
                "min_magnitude": 0.25,
                "start_date": "2020-01-01",
                "end_date": "2023-12-31",
                "target_asset": "GLD" if "gold" in user_query.lower() else None
            }

            response_key = "fed_cuts_025"

        elif "less than 0.1%" in user_query or "smaller than 0.1%" in user_query:
            print("🧠 LLM Analysis: User wants Fed cuts SMALLER than 0.1%")
            print("🔧 Tool Selection: Using fed_rate_changes tool with max_magnitude=0.1")

            tool_params = {
                "direction": "decrease",
                "max_magnitude": 0.1,
                "start_date": "2020-01-01",
                "end_date": "2023-12-31"
            }

            response_key = "fed_cuts_small"

        else:
            print("🧠 LLM Analysis: General Fed cuts query - using semantic search")
            print("❌ This would go to ChromaDB semantic search (less precise)")
            return

        # Simulate tool call
        print(f"📡 Tool Call: fed_rate_changes({json.dumps(tool_params, indent=2)})")

        # Simulate tool response
        tool_response = MOCK_TOOL_RESPONSES[response_key]
        print(f"📥 Tool Response: {json.dumps(tool_response, indent=2)}")

        # LLM processes results and responds to user
        if tool_response["success"]:
            data = tool_response["data"]
            events = data["fed_rate_events"]

            print("\n💬 LLM Response to User:")
            print("-" * 40)

            if events:
                print(f"I found {data['total_events']} Federal Reserve rate cuts meeting your criteria:")

                for event in events:
                    print(f"• {event['event_date']}: Cut by {abs(event['change_amount']):.2f}% to {event['value']:.2f}%")

                print(f"\nSummary:")
                print(f"• Average cut size: {data['summary_statistics']['average_magnitude']:.2f}%")
                print(f"• Largest cut: {data['summary_statistics']['largest_change']:.2f}%")

                if data.get("market_impact_analysis"):
                    impact = data["market_impact_analysis"]["aggregate_statistics"]
                    print(f"• Average 5-day gold return after cuts: {impact['average_5d_return']:.1f}%")
                    print(f"• Success rate: {impact['success_rate']:.0f}%")

            else:
                print("I found no Federal Reserve rate cuts matching your specific criteria.")
                print("This shows the precision advantage of structured queries over semantic search!")

        print("\n" + "=" * 80)

    else:
        print("🧠 LLM Analysis: Not a precise Fed rate query - would use semantic search")
        print("❌ This would go to ChromaDB")


def main():
    """Demo different query types and LLM responses."""
    print("🚀 MCP Tool Demo: LLM + Fed Rate Changes Tool")
    print("=" * 80)
    print("This demo shows how an LLM would use the MCP tool for precise queries")
    print("that ChromaDB similarity search cannot handle well.\n")

    # Demo queries that showcase the numerical precision advantage
    demo_queries = [
        "What happens to gold when the Fed cuts rates by more than 0.25%?",
        "Show me Fed rate cuts smaller than 0.1% in the last few years",
        "How did markets react to large Fed rate cuts during COVID?",
        "Fed cuts interest rate"  # This would go to semantic search
    ]

    for i, query in enumerate(demo_queries, 1):
        print(f"\n🎯 Demo {i}")
        simulate_llm_query_processing(query)

        if i < len(demo_queries):
            print("\n" + "⏳" * 20)

    print("\n🎉 Demo Complete!")
    print("\nKey Advantages Demonstrated:")
    print("✅ Precise numerical filtering (0.25% vs 0.1%)")
    print("✅ Structured query parameters")
    print("✅ Consistent result format")
    print("✅ Market impact analysis integration")
    print("✅ Clear distinction from semantic search use cases")


if __name__ == "__main__":
    main()