#!/usr/bin/env python3
"""
Test script for MCP Tool integration.

Tests the Fed Rate Changes tool end-to-end to ensure:
1. Tool registration works
2. Tool execution works
3. API endpoints work
4. Results are properly formatted
"""

import os
import sys
import requests
import json
from datetime import datetime

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

try:
    from query.financial_server.query_engine import FinancialQueryEngine
    from mcp_tools.financial.fed_rate_tools import FedRateChangesTool
    from mcp_tools.base.tool_base import tool_registry
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the backend/src directory")
    sys.exit(1)


def test_tool_registration():
    """Test that tools are properly registered."""
    print("=" * 60)
    print("1. Testing Tool Registration")
    print("=" * 60)

    try:
        # Initialize query engine (this should register tools)
        engine = FinancialQueryEngine()

        # Check if tools are registered
        available_tools = tool_registry.list_tools()
        print(f"Available tools: {available_tools}")

        if 'fed_rate_changes' in available_tools:
            print("✅ Fed Rate Changes tool successfully registered")
        else:
            print("❌ Fed Rate Changes tool NOT registered")
            return False

        # Get tool schema
        schemas = tool_registry.get_all_schemas()
        fed_tool_schema = schemas.get('fed_rate_changes')
        if fed_tool_schema:
            print("✅ Tool schema available")
            print(f"Schema: {json.dumps(fed_tool_schema, indent=2)}")
        else:
            print("❌ Tool schema NOT available")
            return False

        return True

    except Exception as e:
        print(f"❌ Tool registration failed: {e}")
        return False


def test_direct_tool_execution():
    """Test direct tool execution."""
    print("\n" + "=" * 60)
    print("2. Testing Direct Tool Execution")
    print("=" * 60)

    try:
        engine = FinancialQueryEngine()

        # Test parameters
        test_params = {
            'direction': 'decrease',
            'min_magnitude': 0.1,
            'start_date': '2020-01-01',
            'end_date': '2023-12-31'
        }

        print(f"Testing with parameters: {test_params}")

        # Execute tool directly
        result = engine.execute_mcp_tool('fed_rate_changes', **test_params)

        if result.get('success'):
            print("✅ Tool execution successful")
            print(f"Found {result.get('data', {}).get('total_events', 0)} Fed rate events")

            # Print sample results
            events = result.get('data', {}).get('fed_rate_events', [])
            if events:
                print(f"Sample event: {events[0]}")
            else:
                print("ℹ️  No events found (this might be expected if no data in DB)")

        else:
            print(f"❌ Tool execution failed: {result.get('error')}")
            return False

        return True

    except Exception as e:
        print(f"❌ Direct tool execution failed: {e}")
        return False


def test_api_endpoints(base_url="http://localhost:8003"):
    """Test API endpoints."""
    print("\n" + "=" * 60)
    print("3. Testing API Endpoints")
    print("=" * 60)

    try:
        # Test listing tools
        print("Testing GET /tools...")
        response = requests.get(f"{base_url}/tools", timeout=10)

        if response.status_code == 200:
            tools_data = response.json()
            print("✅ GET /tools successful")
            print(f"Available tools: {list(tools_data.get('available_tools', {}).keys())}")
        else:
            print(f"❌ GET /tools failed: {response.status_code} - {response.text}")
            return False

        # Test executing tool via API
        print("\nTesting POST /tools/fed_rate_changes...")
        tool_params = {
            'direction': 'decrease',
            'min_magnitude': 0.25,
            'start_date': '2020-01-01',
            'end_date': '2023-12-31'
        }

        response = requests.post(
            f"{base_url}/tools/fed_rate_changes",
            json=tool_params,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ POST /tools/fed_rate_changes successful")
            print(f"Found {result.get('data', {}).get('total_events', 0)} events")
        else:
            print(f"❌ POST /tools/fed_rate_changes failed: {response.status_code} - {response.text}")
            return False

        return True

    except requests.RequestException as e:
        print(f"❌ API test failed - connection error: {e}")
        print("Make sure the FastAPI server is running on port 8003")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False


def test_schema_validation():
    """Test parameter schema validation."""
    print("\n" + "=" * 60)
    print("4. Testing Schema Validation")
    print("=" * 60)

    try:
        engine = FinancialQueryEngine()

        # Test with invalid parameters
        invalid_params = {
            'direction': 'invalid_direction',  # Should fail
            'start_date': '2020-01-01',
            'end_date': '2023-12-31'
        }

        print("Testing with invalid direction...")
        result = engine.execute_mcp_tool('fed_rate_changes', **invalid_params)

        if not result.get('success'):
            print("✅ Schema validation working - invalid params rejected")
        else:
            print("❌ Schema validation NOT working - invalid params accepted")
            return False

        # Test with missing required parameters
        missing_params = {
            'direction': 'decrease'
            # Missing required start_date and end_date
        }

        print("Testing with missing required parameters...")
        result = engine.execute_mcp_tool('fed_rate_changes', **missing_params)

        if not result.get('success'):
            print("✅ Required parameter validation working")
        else:
            print("❌ Required parameter validation NOT working")
            return False

        return True

    except Exception as e:
        print(f"❌ Schema validation test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("MCP Tool End-to-End Testing")
    print("=" * 60)

    all_passed = True

    # Test 1: Tool Registration
    if not test_tool_registration():
        all_passed = False

    # Test 2: Direct Tool Execution
    if not test_direct_tool_execution():
        all_passed = False

    # Test 3: API Endpoints (optional - server might not be running)
    print("\nTesting API endpoints (optional)...")
    print("Note: This test requires the FastAPI server to be running")
    try:
        test_api_endpoints()
    except Exception as e:
        print(f"ℹ️  API test skipped: {e}")

    # Test 4: Schema Validation
    if not test_schema_validation():
        all_passed = False

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    if all_passed:
        print("✅ ALL CORE TESTS PASSED!")
        print("\nYour MCP tool is ready for LLM integration.")
        print("\nNext steps:")
        print("1. Start the FastAPI server: python src/query/financial_server/api_server.py")
        print("2. Test via curl: curl -X POST http://localhost:8003/tools/fed_rate_changes \\")
        print("   -H 'Content-Type: application/json' \\")
        print("   -d '{\"direction\": \"decrease\", \"min_magnitude\": 0.25, \"start_date\": \"2020-01-01\", \"end_date\": \"2023-12-31\"}'")
        print("3. Configure your LLM to call the /tools/* endpoints")
    else:
        print("❌ SOME TESTS FAILED")
        print("Check the error messages above and fix the issues.")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)