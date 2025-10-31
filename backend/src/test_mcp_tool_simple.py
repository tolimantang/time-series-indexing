#!/usr/bin/env python3
"""
Simple test for MCP Tool structure without database dependencies.

Tests:
1. Tool schema generation
2. Tool parameter validation
3. Tool registry functionality
"""

import os
import sys
import json

# Add the src directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

try:
    from mcp_tools.base.tool_base import BaseMCPTool, ToolRegistry
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the backend/src directory")
    sys.exit(1)


class MockPostgresManager:
    """Mock PostgreSQL manager for testing."""
    def __init__(self):
        self.connection = None

    def _ensure_connection(self):
        pass


class MockMarketDataManager:
    """Mock market data manager for testing."""
    def calculate_event_impact(self, symbol, date, forward_days):
        return {
            'forward_returns': {
                'return_5d': {'return_pct': 2.5}
            }
        }


def test_tool_schema():
    """Test tool schema generation."""
    print("=" * 60)
    print("1. Testing Tool Schema Generation")
    print("=" * 60)

    try:
        from mcp_tools.financial.fed_rate_tools import FedRateChangesTool

        # Create tool with mock managers
        tool = FedRateChangesTool(
            postgres_manager=MockPostgresManager(),
            market_data_manager=MockMarketDataManager()
        )

        # Get schema
        schema = tool.get_schema()
        print("✅ Tool schema generated successfully")
        print(f"Tool name: {tool.name}")
        print(f"Tool description: {tool.description}")
        print(f"Schema: {json.dumps(schema, indent=2)}")

        # Validate schema structure
        required_fields = ['type', 'properties', 'required']
        for field in required_fields:
            if field not in schema:
                print(f"❌ Missing required schema field: {field}")
                return False

        print("✅ Schema structure valid")
        return True

    except Exception as e:
        print(f"❌ Tool schema test failed: {e}")
        return False


def test_tool_registry():
    """Test tool registry functionality."""
    print("\n" + "=" * 60)
    print("2. Testing Tool Registry")
    print("=" * 60)

    try:
        from mcp_tools.financial.fed_rate_tools import FedRateChangesTool

        # Create new registry for testing
        registry = ToolRegistry()

        # Create and register tool
        tool = FedRateChangesTool(
            postgres_manager=MockPostgresManager(),
            market_data_manager=MockMarketDataManager()
        )

        registry.register(tool)
        print("✅ Tool registered successfully")

        # Test registry functions
        tools = registry.list_tools()
        print(f"Registered tools: {tools}")

        if 'fed_rate_changes' in tools:
            print("✅ Tool found in registry")
        else:
            print("❌ Tool NOT found in registry")
            return False

        # Test get_tool
        retrieved_tool = registry.get_tool('fed_rate_changes')
        if retrieved_tool and retrieved_tool.name == 'fed_rate_changes':
            print("✅ Tool retrieval successful")
        else:
            print("❌ Tool retrieval failed")
            return False

        # Test get_all_schemas
        schemas = registry.get_all_schemas()
        if 'fed_rate_changes' in schemas:
            print("✅ Schema retrieval successful")
        else:
            print("❌ Schema retrieval failed")
            return False

        return True

    except Exception as e:
        print(f"❌ Tool registry test failed: {e}")
        return False


def test_parameter_validation():
    """Test parameter validation."""
    print("\n" + "=" * 60)
    print("3. Testing Parameter Validation")
    print("=" * 60)

    try:
        from mcp_tools.financial.fed_rate_tools import FedRateChangesTool

        tool = FedRateChangesTool(
            postgres_manager=MockPostgresManager(),
            market_data_manager=MockMarketDataManager()
        )

        # Test valid parameters
        valid_params = {
            'direction': 'decrease',
            'start_date': '2020-01-01',
            'end_date': '2023-12-31',
            'min_magnitude': 0.25
        }

        try:
            tool.validate_params(**valid_params)
            print("✅ Valid parameters accepted")
        except Exception as e:
            print(f"❌ Valid parameters rejected: {e}")
            return False

        # Test missing required parameters
        invalid_params = {
            'direction': 'decrease'
            # Missing required start_date and end_date
        }

        try:
            tool.validate_params(**invalid_params)
            print("❌ Invalid parameters accepted (should have failed)")
            return False
        except ValueError:
            print("✅ Invalid parameters correctly rejected")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

        return True

    except Exception as e:
        print(f"❌ Parameter validation test failed: {e}")
        return False


def test_date_parsing():
    """Test date parsing utility."""
    print("\n" + "=" * 60)
    print("4. Testing Date Parsing")
    print("=" * 60)

    try:
        from mcp_tools.financial.fed_rate_tools import FedRateChangesTool

        tool = FedRateChangesTool(
            postgres_manager=MockPostgresManager(),
            market_data_manager=MockMarketDataManager()
        )

        # Test valid date
        date_obj = tool._parse_date('2023-12-31')
        print(f"✅ Date parsing successful: {date_obj}")

        # Test invalid date
        try:
            tool._parse_date('invalid-date')
            print("❌ Invalid date accepted (should have failed)")
            return False
        except ValueError:
            print("✅ Invalid date correctly rejected")

        return True

    except Exception as e:
        print(f"❌ Date parsing test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("MCP Tool Simple Testing (No Database Required)")
    print("=" * 60)

    all_passed = True

    # Test 1: Tool Schema
    if not test_tool_schema():
        all_passed = False

    # Test 2: Tool Registry
    if not test_tool_registry():
        all_passed = False

    # Test 3: Parameter Validation
    if not test_parameter_validation():
        all_passed = False

    # Test 4: Date Parsing
    if not test_date_parsing():
        all_passed = False

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    if all_passed:
        print("✅ ALL TESTS PASSED!")
        print("\nThe MCP tool structure is working correctly.")
        print("\nNext steps:")
        print("1. Set up database connections for full testing")
        print("2. Start the FastAPI server")
        print("3. Test with actual data")
        print("4. Configure LLM to call the tool")
    else:
        print("❌ SOME TESTS FAILED")
        print("Check the error messages above and fix the issues.")

    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)