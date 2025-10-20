#!/usr/bin/env python3
"""
Daily Market Encoding Script
Main script for the Kubernetes cronjob to encode market data daily.
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

from src.market_encoder.core.multi_encoder import MultiSecurityEncoder
from src.market_encoder.config.config import MarketEncoderConfig


def setup_environment():
    """Setup environment variables and paths."""
    # Ensure required environment variables are set
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)

    # Set default values for optional variables
    os.environ.setdefault('DB_PORT', '5432')
    os.environ.setdefault('CHROMA_DB_PATH', '/data/chroma_market_db')


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
    """Main function for daily market encoding."""
    parser = argparse.ArgumentParser(description='Daily Market Data Encoding')
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
            logging.FileHandler('/tmp/market_encoding.log') if os.path.exists('/tmp') else logging.NullHandler()
        ]
    )

    global logger
    logger = logging.getLogger(__name__)

    try:
        logger.info("🚀 Starting Daily Market Encoding Job")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info(f"Arguments: {vars(args)}")

        # Setup environment
        setup_environment()

        # Create database configuration
        db_config = create_db_config()
        logger.info(f"Database: {db_config['host']}:{db_config['port']}/{db_config['database']}")

        # Initialize encoder
        chroma_path = os.getenv('CHROMA_DB_PATH', '/data/chroma_market_db')
        logger.info(f"ChromaDB path: {chroma_path}")

        encoder = MultiSecurityEncoder(
            config_path=args.config,
            chroma_db_path=chroma_path,
            db_config=db_config
        )

        # Show configuration summary
        config_summary = encoder.get_status()
        logger.info(f"Configuration loaded: {config_summary['config_summary']}")

        if args.dry_run:
            logger.info("🧪 DRY RUN MODE - No data will be processed")
            logger.info("Configuration test completed successfully")
            return 0

        # Run daily encoding
        logger.info("📊 Starting market data processing...")
        result = encoder.run_daily_encoding(categories=args.categories)

        # Log results
        logger.info(f"📈 Encoding completed with status: {result['status']}")
        logger.info(f"📊 Securities processed: {result['securities']}")
        logger.info(f"💾 Data stored: {result['data_stored']}")
        logger.info(f"⏱️  Processing time: {result['processing_time']}s")

        # Write detailed results to file for debugging
        results_file = '/tmp/market_encoding_results.json'
        try:
            with open(results_file, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            logger.info(f"📋 Detailed results written to: {results_file}")
        except Exception as e:
            logger.warning(f"Could not write results file: {e}")

        # Exit with appropriate code
        if result['status'] == 'success':
            logger.info("✅ Daily market encoding completed successfully")
            return 0
        elif result['status'] == 'partial':
            logger.warning("⚠️  Daily market encoding completed with some failures")
            return 1
        else:
            logger.error("❌ Daily market encoding failed")
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