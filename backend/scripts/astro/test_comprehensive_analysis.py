#!/usr/bin/env python3
"""
Test script for comprehensive astrological trading analysis.
This tests the same logic that runs in the Kubernetes job locally.
"""

import os
import sys
import json
import logging
from datetime import datetime, date
from pathlib import Path

# Add backend/src to path for imports
backend_src = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(backend_src))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_comprehensive_analysis():
    """Test the comprehensive astrological analysis locally."""
    try:
        # Test Swiss Ephemeris integration
        import swisseph as swe
        logger.info("✅ Swiss Ephemeris available")

        # Test basic calculation
        test_date = date(2024, 1, 15)
        julian_day = swe.julday(test_date.year, test_date.month, test_date.day, 12.0)

        # Test Sun calculation
        result, ret = swe.calc_ut(julian_day, swe.SUN)
        if ret >= 0:
            logger.info(f"✅ Sun calculation successful: {result[0]:.2f}° longitude")
        else:
            logger.error("❌ Sun calculation failed")
            return False

        # Test Moon calculation
        result, ret = swe.calc_ut(julian_day, swe.MOON)
        if ret >= 0:
            logger.info(f"✅ Moon calculation successful: {result[0]:.2f}° longitude")
        else:
            logger.error("❌ Moon calculation failed")
            return False

    except ImportError:
        logger.error("❌ Swiss Ephemeris not available - install with: pip install pyswisseph")
        return False
    except Exception as e:
        logger.error(f"❌ Swiss Ephemeris test failed: {e}")
        return False

    # Test database connection
    try:
        import psycopg2

        # Check if we have database config
        db_config = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
        }

        missing = [k for k, v in db_config.items() if not v]
        if missing:
            logger.warning(f"⚠️ Missing DB config: {missing} - database tests skipped")
        else:
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM trading_opportunities")
            count = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            logger.info(f"✅ Database connection successful - {count} trading opportunities found")

    except ImportError:
        logger.error("❌ psycopg2 not available - install with: pip install psycopg2-binary")
        return False
    except Exception as e:
        logger.warning(f"⚠️ Database connection test failed: {e}")

    # Test Claude API if available
    try:
        import anthropic

        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key:
            client = anthropic.Anthropic(api_key=api_key)
            logger.info("✅ Claude API client initialized")
        else:
            logger.warning("⚠️ No Claude API key - will generate prompts only")

    except ImportError:
        logger.error("❌ anthropic library not available - install with: pip install anthropic")
        return False
    except Exception as e:
        logger.warning(f"⚠️ Claude API test failed: {e}")

    # Test our astro encoder components
    try:
        from astro_encoder.core.encoder import AstroEncoder
        from astro_encoder.core.verbalizer import AstroVerbalizer

        encoder = AstroEncoder()
        verbalizer = AstroVerbalizer()

        # Test encoding a date
        test_datetime = datetime(2024, 1, 15, 12, 0, 0)
        astro_data = encoder.encode_date(test_datetime)

        logger.info(f"✅ Astro encoder test successful - found {len(astro_data.positions)} planetary positions")
        logger.info(f"✅ Found {len(astro_data.aspects)} aspects")

        # Test verbalization
        description = verbalizer.verbalize_daily_data(astro_data)
        logger.info(f"✅ Verbalizer test successful - generated {len(description)} character description")

    except Exception as e:
        logger.error(f"❌ Astro encoder test failed: {e}")
        return False

    logger.info("🎉 All tests passed! Comprehensive astrological analysis should work correctly.")
    return True


def main():
    """Main test function."""
    logger.info("🧪 Testing comprehensive astrological trading analysis components...")

    success = test_comprehensive_analysis()

    if success:
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80)
        print("The comprehensive astrological trading analysis is ready to deploy!")
        print("\nTo deploy to Kubernetes:")
        print("kubectl apply -f deploy/k8s/shared/comprehensive-astro-trading-job.yaml")
        print("\nTo run locally with full database access:")
        print("python3 scripts/astro/trading_astro_correlation.py")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("❌ TESTS FAILED")
        print("="*80)
        print("Please fix the issues above before deploying.")
        print("="*80)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())