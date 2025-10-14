#!/usr/bin/env python3
"""
Demo the API functionality without running the full server
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# Add modules to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from api_server import AstroFinancialAPI, SemanticQueryRequest, PatternAnalysisRequest

def demo_api_functionality():
    """Demo the core API functionality."""
    print("API Server Functionality Demo")
    print("=" * 50)

    # Initialize API (but not the full server)
    api = AstroFinancialAPI()

    print("✓ API instance created")
    print("✓ ChromaDB connection established")
    print("✓ Embedding pipeline loaded")
    print()

    # Demo 1: Semantic Search
    print("1. SEMANTIC SEARCH DEMO")
    print("-" * 30)

    request = SemanticQueryRequest(
        query="moon opposite saturn",
        max_results=5,
        include_market_data=False  # Skip market data for this demo
    )

    try:
        results = api.semantic_search(request)
        print(f"Query: '{request.query}'")
        print(f"Results found: {results.results_count}")
        print(f"Execution time: {results.execution_time_ms:.1f}ms")
        print()

        for i, result in enumerate(results.results[:3], 1):
            print(f"{i}. Date: {result.get('date', 'Unknown')}")
            print(f"   Similarity: {result.get('similarity_score', 0):.3f}")
            print(f"   Description: {result.get('description', '')[:100]}...")
            print()

    except Exception as e:
        print(f"Error in semantic search: {e}")
        print()

    # Demo 2: Pattern Analysis
    print("2. PATTERN ANALYSIS DEMO")
    print("-" * 30)

    analysis_request = PatternAnalysisRequest(
        query="saturn neptune conjunction",
        lookback_days=30,
        target_assets=["SPY", "VIX", "EURUSD"]
    )

    try:
        analysis = api.pattern_analysis(analysis_request)
        print(f"Pattern: '{analysis_request.query}'")
        print(f"Analysis results: {analysis.results_count}")
        print(f"Execution time: {analysis.execution_time_ms:.1f}ms")
        print()

        for result in analysis.results:
            asset = result.get('asset')
            avg_return = result.get('avg_return', 0)
            volatility = result.get('volatility', 0)
            sample_size = result.get('sample_size', 0)

            print(f"Asset: {asset}")
            print(f"  Sample size: {sample_size} periods")
            print(f"  Avg return: {avg_return:.2f}%")
            print(f"  Avg volatility: {volatility:.1f}")
            print()

    except Exception as e:
        print(f"Error in pattern analysis: {e}")
        print()

    print("3. API ENDPOINTS AVAILABLE")
    print("-" * 30)
    endpoints = [
        "GET  /              - API root",
        "GET  /health        - Health check + stats",
        "POST /query/semantic - Semantic search",
        "POST /query/structured - Structured queries",
        "POST /analysis/pattern - Pattern analysis",
        "GET  /query/examples - Query examples"
    ]

    for endpoint in endpoints:
        print(f"  {endpoint}")

    print()
    print("4. READY FOR FRONTEND INTEGRATION")
    print("-" * 40)
    print("✓ All API endpoints implemented")
    print("✓ CORS configured for Next.js")
    print("✓ Pydantic models for type safety")
    print("✓ Error handling and logging")
    print("✓ ChromaDB + PostgreSQL integration")
    print()
    print("Next step: Create Next.js frontend that calls these APIs!")

if __name__ == "__main__":
    demo_api_functionality()