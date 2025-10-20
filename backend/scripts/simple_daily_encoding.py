#!/usr/bin/env python3
"""
Simple Daily Market Encoding Script
Simplified version that only fetches basic daily price data without technical indicators.
Perfect for daily cronjob that just needs current price data.
"""

import os
import sys
import logging
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add the parent directory to the Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.market_encoder.core.simple_encoder import SimpleDailyEncoder
from src.market_encoder.config.config import MarketEncoderConfig


def setup_environment():
    """Setup environment variables and paths."""
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)

    os.environ.setdefault('DB_PORT', '5432')
    # No ChromaDB needed for simple version


def create_db_config():
    """Create database configuration from environment variables."""
    return {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
    }


def main():
    """Main function for simple daily market encoding."""
    parser = argparse.ArgumentParser(description='Simple Daily Market Data Encoding')
    parser.add_argument('--config', type=str, help='Path to securities config file')
    parser.add_argument('--categories', nargs='+',
                       choices=['indices', 'etfs', 'stocks', 'crypto'],
                       help='Specific categories to process')
    parser.add_argument('--dry-run', action='store_true',
                       help='Test configuration without processing')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/tmp/simple_market_encoding.log') if os.path.exists('/tmp') else logging.NullHandler()
        ]
    )

    global logger
    logger = logging.getLogger(__name__)

    try:
        logger.info("🚀 Starting Simple Daily Market Encoding Job")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info(f"Mode: Simple (no technical indicators)")
        logger.info(f"Arguments: {vars(args)}")

        # Setup environment
        setup_environment()

        # Create database configuration
        db_config = create_db_config()
        logger.info(f"Database: {db_config['host']}:{db_config['port']}/{db_config['database']}")

        # Initialize simple encoder (PostgreSQL only)
        logger.info("Initializing simple encoder (PostgreSQL only)")

        encoder = SimpleDailyEncoder(
            config_path=args.config,
            db_config=db_config
        )

        # Show configuration summary
        config_summary = encoder.config.summary()
        logger.info(f"Configuration loaded: {config_summary}")

        if args.dry_run:
            logger.info("🧪 DRY RUN MODE - No data will be processed")
            logger.info("Configuration test completed successfully")
            return 0

        # Run simple daily encoding
        logger.info("📊 Starting simple market data processing...")
        result = encoder.run_daily_simple_encoding(categories=args.categories)

        # Log results
        logger.info(f"📈 Encoding completed with status: {result['status']}")
        logger.info(f"📊 Securities processed: {result['securities']}")
        logger.info(f"💾 Data stored: {result['data_stored']}")
        logger.info(f"⏱️  Processing time: {result['processing_time']}s")

        # Write detailed results to file for debugging
        results_file = '/tmp/simple_market_encoding_results.json'
        try:
            with open(results_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            logger.info(f"📋 Detailed results written to: {results_file}")
        except Exception as e:
            logger.warning(f"Could not write results file: {e}")

        # Exit with appropriate code
        if result['status'] == 'success':
            logger.info("✅ Simple daily market encoding completed successfully")
            return 0
        elif result['status'] == 'partial':
            logger.warning("⚠️  Simple daily market encoding completed with some failures")
            return 1
        else:
            logger.error("❌ Simple daily market encoding failed")
            return 2

    except KeyboardInterrupt:
        logger.info("🛑 Market encoding interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"💥 Fatal error in market encoding: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)