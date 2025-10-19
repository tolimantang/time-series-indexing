#!/usr/bin/env python3
"""
Local test script for Market Encoder
Test the multi-security encoder locally before deploying to Kubernetes.
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add the parent directory to the Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from market_encoder.multi_encoder import MultiSecurityEncoder


def setup_test_environment():
    """Setup test environment variables."""
    # Set default test values if not already set
    test_config = {
        'DB_HOST': 'localhost',
        'DB_PORT': '5432',
        'DB_NAME': 'astrofinancial_test',
        'DB_USER': 'postgres',
        'DB_PASSWORD': 'password',
        'CHROMA_DB_PATH': './test_chroma_db'
    }

    for key, value in test_config.items():
        if not os.getenv(key):
            os.environ[key] = value
            print(f"Set {key}={value}")


def test_configuration():
    """Test configuration loading."""
    print("\n🧪 Testing Configuration Loading...")

    try:
        encoder = MultiSecurityEncoder()
        status = encoder.get_status()

        print("✅ Configuration loaded successfully")
        print(f"   Enabled securities: {status['config_summary']['enabled_securities']}")
        print(f"   Total securities: {status['config_summary']['total_securities']}")
        print(f"   Categories: {status['config_summary']['enabled_by_category']}")

        return encoder
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return None


def test_single_security(encoder):
    """Test processing a single security."""
    print("\n🧪 Testing Single Security Processing...")

    try:
        # Get one enabled security for testing
        enabled_securities = encoder.config.get_enabled_securities()
        if not enabled_securities:
            print("❌ No enabled securities found for testing")
            return False

        test_security = enabled_securities[0]
        print(f"   Testing: {test_security.symbol} ({test_security.name})")

        result = encoder.process_security(test_security)

        if result['success']:
            print(f"✅ Single security test passed")
            print(f"   PostgreSQL records: {result['postgres_records']}")
            print(f"   ChromaDB records: {result['chroma_records']}")
            print(f"   Processing time: {result['processing_time']:.2f}s")
            return True
        else:
            print(f"❌ Single security test failed: {result['error']}")
            return False

    except Exception as e:
        print(f"❌ Single security test error: {e}")
        return False


def test_p_and_l_calculation(encoder):
    """Test P&L calculation functionality."""
    print("\n🧪 Testing P&L Calculation...")

    try:
        # Test with SPX (should be available)
        pnl_result = encoder.encoder.calculate_hypothetical_pnl(
            symbol='SPX',
            entry_date='2024-01-01',
            exit_date='2024-01-31',
            quantity=100,
            position_type='long'
        )

        if 'error' not in pnl_result:
            print("✅ P&L calculation test passed")
            print(f"   Entry price: ${pnl_result['entry_price']}")
            print(f"   Exit price: ${pnl_result['exit_price']}")
            print(f"   P&L: ${pnl_result['pnl_amount']} ({pnl_result['pnl_percentage']:.2f}%)")
            return True
        else:
            print(f"❌ P&L calculation failed: {pnl_result['error']}")
            return False

    except Exception as e:
        print(f"❌ P&L calculation test error: {e}")
        return False


def test_dry_run(encoder):
    """Test dry run functionality."""
    print("\n🧪 Testing Dry Run Mode...")

    try:
        # Test with just indices to keep it quick
        result = encoder.run_daily_encoding(categories=['indices'])

        print(f"✅ Dry run completed with status: {result['status']}")
        print(f"   Securities processed: {result['securities']}")
        print(f"   Data stored: {result['data_stored']}")
        print(f"   Processing time: {result['processing_time']}s")

        return result['status'] in ['success', 'partial']

    except Exception as e:
        print(f"❌ Dry run test error: {e}")
        return False


def main():
    """Main test function."""
    print("🚀 Market Encoder Local Testing")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 50)

    # Setup logging for tests
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Setup test environment
    setup_test_environment()

    # Test sequence
    tests_passed = 0
    total_tests = 4

    # Test 1: Configuration
    encoder = test_configuration()
    if encoder:
        tests_passed += 1
    else:
        print("\n❌ Configuration test failed - stopping tests")
        return 1

    # Test 2: Single security processing
    if test_single_security(encoder):
        tests_passed += 1

    # Test 3: P&L calculation
    if test_p_and_l_calculation(encoder):
        tests_passed += 1

    # Test 4: Full dry run
    if test_dry_run(encoder):
        tests_passed += 1

    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} passed")

    if tests_passed == total_tests:
        print("✅ All tests passed! Ready for deployment.")
        return 0
    else:
        print("❌ Some tests failed. Please check configuration and dependencies.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)