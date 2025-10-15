#!/usr/bin/env python3
"""
Comprehensive Testing Strategy for Astro-Financial System
"""

import pytest
import asyncio
import requests
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import time

class SystemTester:
    """Complete system testing framework."""

    def __init__(self):
        self.api_base = "http://localhost:8000"
        self.test_results = []

    def run_all_tests(self):
        """Run complete test suite."""
        print("🧪 ASTRO-FINANCIAL SYSTEM TEST SUITE")
        print("=" * 50)

        tests = [
            ("Unit Tests", self.test_unit_components),
            ("Integration Tests", self.test_integration),
            ("API Tests", self.test_api_endpoints),
            ("Performance Tests", self.test_performance),
            ("End-to-End Tests", self.test_e2e_workflow),
            ("Data Quality Tests", self.test_data_quality)
        ]

        total_passed = 0
        total_tests = 0

        for test_name, test_func in tests:
            print(f"\n🔍 {test_name}")
            print("-" * 30)

            try:
                results = test_func()
                passed = sum(1 for r in results if r['status'] == 'PASS')
                total = len(results)

                total_passed += passed
                total_tests += total

                print(f"   Results: {passed}/{total} passed")

                for result in results:
                    status_icon = "✅" if result['status'] == 'PASS' else "❌"
                    print(f"   {status_icon} {result['test']}")
                    if result['status'] == 'FAIL':
                        print(f"      Error: {result.get('error', 'Unknown')}")

            except Exception as e:
                print(f"   ❌ Test suite failed: {e}")

        print(f"\n📊 OVERALL RESULTS")
        print(f"   Total: {total_passed}/{total_tests} tests passed")
        print(f"   Success Rate: {total_passed/total_tests*100:.1f}%")

        if total_passed == total_tests:
            print(f"   🎉 ALL TESTS PASSED! System is ready for production.")
        else:
            print(f"   ⚠️  Some tests failed. Review and fix before deployment.")

    def test_unit_components(self):
        """Test individual components."""
        results = []

        # Test astroEncoder
        try:
            from astroEncoder import AstroEncoder
            encoder = AstroEncoder()
            test_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
            astro_data = encoder.encode_date(test_date)

            assert astro_data.positions
            assert astro_data.aspects
            assert astro_data.julian_day > 0

            results.append({'test': 'astroEncoder basic functionality', 'status': 'PASS'})
        except Exception as e:
            results.append({'test': 'astroEncoder basic functionality', 'status': 'FAIL', 'error': str(e)})

        # Test newsEncoder
        try:
            from newsEncoder import NewsEncoder
            news_encoder = NewsEncoder()
            test_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
            news_data = news_encoder.encode_date(test_date)

            assert news_data.daily_summary
            assert news_data.quality_score > 0
            assert news_data.market_regime

            results.append({'test': 'newsEncoder basic functionality', 'status': 'PASS'})
        except Exception as e:
            results.append({'test': 'newsEncoder basic functionality', 'status': 'FAIL', 'error': str(e)})

        # Test embedding pipeline
        try:
            from astro_embedding_pipeline import AstroEmbeddingPipeline
            pipeline = AstroEmbeddingPipeline()
            test_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
            result = pipeline.process_date(test_date)

            assert result['text_length'] > 1000
            assert result['embedding_dimension'] == 384
            assert result['date']

            results.append({'test': 'Embedding pipeline functionality', 'status': 'PASS'})
        except Exception as e:
            results.append({'test': 'Embedding pipeline functionality', 'status': 'FAIL', 'error': str(e)})

        return results

    def test_integration(self):
        """Test component integration."""
        results = []

        # Test astro → text → embedding flow
        try:
            from astro_embedding_pipeline import AstroEmbeddingPipeline
            pipeline = AstroEmbeddingPipeline()

            # Test multiple dates
            test_dates = [
                datetime(2024, 1, 15, tzinfo=timezone.utc),
                datetime(2024, 6, 20, tzinfo=timezone.utc),
                datetime(2024, 12, 5, tzinfo=timezone.utc)
            ]

            for date in test_dates:
                result = pipeline.process_date(date)
                assert result['text_length'] > 500
                assert result['embedding_dimension'] == 384

            results.append({'test': 'Multi-date processing', 'status': 'PASS'})
        except Exception as e:
            results.append({'test': 'Multi-date processing', 'status': 'FAIL', 'error': str(e)})

        # Test semantic search
        try:
            search_results = pipeline.search_similar_patterns("moon saturn aspects", n_results=3)

            assert 'results' in search_results
            assert len(search_results['results']) <= 3
            assert search_results['query'] == "moon saturn aspects"

            results.append({'test': 'Semantic search functionality', 'status': 'PASS'})
        except Exception as e:
            results.append({'test': 'Semantic search functionality', 'status': 'FAIL', 'error': str(e)})

        return results

    def test_api_endpoints(self):
        """Test API endpoints."""
        results = []

        # Test health endpoint
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert 'status' in data

            results.append({'test': 'Health endpoint', 'status': 'PASS'})
        except Exception as e:
            results.append({'test': 'Health endpoint', 'status': 'FAIL', 'error': str(e)})

        # Test root endpoint
        try:
            response = requests.get(f"{self.api_base}/", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert data['message'] == "Astro-Financial API"

            results.append({'test': 'Root endpoint', 'status': 'PASS'})
        except Exception as e:
            results.append({'test': 'Root endpoint', 'status': 'FAIL', 'error': str(e)})

        # Test semantic search endpoint
        try:
            payload = {
                "query": "moon saturn aspects",
                "max_results": 3,
                "include_market_data": False
            }
            response = requests.post(f"{self.api_base}/query/semantic", json=payload, timeout=10)
            assert response.status_code == 200
            data = response.json()
            assert data['query_type'] == 'semantic_search'
            assert 'results_count' in data
            assert 'execution_time_ms' in data

            results.append({'test': 'Semantic search API', 'status': 'PASS'})
        except Exception as e:
            results.append({'test': 'Semantic search API', 'status': 'FAIL', 'error': str(e)})

        # Test pattern analysis endpoint
        try:
            payload = {
                "query": "saturn aspects",
                "lookback_days": 30,
                "target_assets": ["SPY", "VIX"]
            }
            response = requests.post(f"{self.api_base}/analysis/pattern", json=payload, timeout=10)
            assert response.status_code == 200
            data = response.json()
            assert data['query_type'] == 'pattern_analysis'
            assert 'results' in data

            results.append({'test': 'Pattern analysis API', 'status': 'PASS'})
        except Exception as e:
            results.append({'test': 'Pattern analysis API', 'status': 'FAIL', 'error': str(e)})

        # Test query examples endpoint
        try:
            response = requests.get(f"{self.api_base}/query/examples", timeout=5)
            assert response.status_code == 200
            data = response.json()
            assert 'semantic_queries' in data

            results.append({'test': 'Query examples API', 'status': 'PASS'})
        except Exception as e:
            results.append({'test': 'Query examples API', 'status': 'FAIL', 'error': str(e)})

        return results

    def test_performance(self):
        """Test system performance."""
        results = []

        # Test API response times
        try:
            queries = [
                "moon saturn aspects",
                "jupiter in cancer",
                "multiple conjunctions",
                "tight planetary alignments"
            ]

            response_times = []
            for query in queries:
                start_time = time.time()
                payload = {"query": query, "max_results": 5}
                response = requests.post(f"{self.api_base}/query/semantic", json=payload)
                end_time = time.time()

                assert response.status_code == 200
                response_time = (end_time - start_time) * 1000  # ms
                response_times.append(response_time)

            avg_response_time = sum(response_times) / len(response_times)
            assert avg_response_time < 2000  # Under 2 seconds

            results.append({'test': f'API response time (avg: {avg_response_time:.0f}ms)', 'status': 'PASS'})
        except Exception as e:
            results.append({'test': 'API response time', 'status': 'FAIL', 'error': str(e)})

        # Test embedding generation speed
        try:
            from astro_embedding_pipeline import AstroEmbeddingPipeline
            pipeline = AstroEmbeddingPipeline()

            start_time = time.time()
            test_date = datetime(2024, 1, 15, tzinfo=timezone.utc)
            result = pipeline.process_date(test_date)
            end_time = time.time()

            processing_time = (end_time - start_time) * 1000
            assert processing_time < 10000  # Under 10 seconds

            results.append({'test': f'Embedding generation (time: {processing_time:.0f}ms)', 'status': 'PASS'})
        except Exception as e:
            results.append({'test': 'Embedding generation speed', 'status': 'FAIL', 'error': str(e)})

        return results

    def test_e2e_workflow(self):
        """Test complete end-to-end workflows."""
        results = []

        # Test complete query workflow
        try:
            # 1. Query similar patterns
            payload = {"query": "moon saturn opposition", "max_results": 5}
            response = requests.post(f"{self.api_base}/query/semantic", json=payload)
            assert response.status_code == 200

            search_data = response.json()
            assert search_data['results_count'] >= 0

            # 2. Analyze patterns if results found
            if search_data['results_count'] > 0:
                analysis_payload = {
                    "query": "moon saturn opposition",
                    "target_assets": ["SPY", "EURUSD"]
                }
                analysis_response = requests.post(f"{self.api_base}/analysis/pattern", json=analysis_payload)
                assert analysis_response.status_code == 200

                analysis_data = analysis_response.json()
                assert 'results' in analysis_data

            results.append({'test': 'Complete query workflow', 'status': 'PASS'})
        except Exception as e:
            results.append({'test': 'Complete query workflow', 'status': 'FAIL', 'error': str(e)})

        return results

    def test_data_quality(self):
        """Test data quality and consistency."""
        results = []

        # Test astronomical data consistency
        try:
            from astroEncoder import AstroEncoder
            encoder = AstroEncoder()

            # Test same date multiple times
            test_date = datetime(2024, 6, 21, tzinfo=timezone.utc)  # Summer solstice

            data1 = encoder.encode_date(test_date)
            data2 = encoder.encode_date(test_date)

            # Should be identical
            assert data1.julian_day == data2.julian_day
            assert data1.positions['sun'].longitude == data2.positions['sun'].longitude
            assert len(data1.aspects) == len(data2.aspects)

            results.append({'test': 'Astronomical data consistency', 'status': 'PASS'})
        except Exception as e:
            results.append({'test': 'Astronomical data consistency', 'status': 'FAIL', 'error': str(e)})

        # Test embedding consistency
        try:
            from astro_embedding_pipeline import AstroEmbeddingPipeline
            pipeline = AstroEmbeddingPipeline()

            # Same date should produce same text (deterministic)
            test_date = datetime(2024, 6, 21, tzinfo=timezone.utc)

            result1 = pipeline.process_date(test_date)
            result2 = pipeline.process_date(test_date)

            # Text should be identical
            assert result1['text_description'] == result2['text_description']
            assert result1['text_length'] == result2['text_length']

            results.append({'test': 'Embedding consistency', 'status': 'PASS'})
        except Exception as e:
            results.append({'test': 'Embedding consistency', 'status': 'FAIL', 'error': str(e)})

        return results

    def check_prerequisites(self):
        """Check system prerequisites before running tests."""
        print("🔍 Checking prerequisites...")

        # Check if API server is running
        try:
            response = requests.get(f"{self.api_base}/health", timeout=5)
            print("   ✅ API server is running")
        except:
            print("   ❌ API server is not running. Start with: python api_server.py")
            return False

        # Check required packages
        required_packages = ['astroEncoder', 'newsEncoder', 'chromadb', 'sentence_transformers']
        for package in required_packages:
            try:
                __import__(package)
                print(f"   ✅ {package} is available")
            except ImportError:
                print(f"   ❌ {package} is missing. Install with: pip install {package}")
                return False

        print("   ✅ All prerequisites met")
        return True


def create_test_configuration():
    """Create pytest configuration."""

    pytest_ini = """
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --strict-markers
    --disable-warnings
markers =
    unit: Unit tests
    integration: Integration tests
    api: API tests
    performance: Performance tests
    e2e: End-to-end tests
"""

    with open('pytest.ini', 'w') as f:
        f.write(pytest_ini)

    print("✅ Created pytest.ini configuration")


def main():
    """Run the complete test suite."""

    # Create test configuration
    create_test_configuration()

    # Initialize tester
    tester = SystemTester()

    # Check prerequisites
    if not tester.check_prerequisites():
        print("\n❌ Prerequisites not met. Please fix and try again.")
        return

    # Run all tests
    tester.run_all_tests()


if __name__ == "__main__":
    main()