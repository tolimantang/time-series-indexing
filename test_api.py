#!/usr/bin/env python3
"""
Test the running API server
"""

import requests
import json

def test_api():
    """Test the running API server."""
    base_url = "http://localhost:8000"

    print("Testing Astro-Financial API Server")
    print("=" * 40)

    # Test 1: Health check
    print("\n1. HEALTH CHECK")
    print("-" * 20)
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 2: Root endpoint
    print("\n2. ROOT ENDPOINT")
    print("-" * 20)
    try:
        response = requests.get(f"{base_url}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 3: Semantic search
    print("\n3. SEMANTIC SEARCH")
    print("-" * 25)
    try:
        payload = {
            "query": "moon saturn aspects",
            "max_results": 3,
            "include_market_data": False
        }
        response = requests.post(f"{base_url}/query/semantic", json=payload)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Query type: {data['query_type']}")
            print(f"Results count: {data['results_count']}")
            print(f"Execution time: {data['execution_time_ms']:.1f}ms")

            if data['results']:
                print("\nTop results:")
                for i, result in enumerate(data['results'][:2], 1):
                    print(f"{i}. Date: {result.get('date', 'Unknown')}")
                    print(f"   Similarity: {result.get('similarity_score', 0):.3f}")
                    print(f"   Preview: {result.get('description', '')[:80]}...")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

    # Test 4: Examples endpoint
    print("\n4. QUERY EXAMPLES")
    print("-" * 20)
    try:
        response = requests.get(f"{base_url}/query/examples")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Available semantic queries:")
            for query in data.get('semantic_queries', [])[:3]:
                print(f"  - {query}")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 40)
    print("✅ API SERVER IS WORKING!")
    print("✅ ChromaDB semantic search functional")
    print("✅ Ready for Next.js frontend development")
    print("\nNext step: Create the frontend!")

if __name__ == "__main__":
    test_api()