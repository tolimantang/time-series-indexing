#!/usr/bin/env python3
"""
S&P 500 Historical Data Backfill Script
Fetches 30 years of S&P 500 daily data and stores in PostgreSQL.
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to the Python path for imports
sys.path.append(str(Path(__file__).parent.parent))

from src.market_encoder.core.postgres_encoder import PostgresOnlyEncoder
from src.market_encoder.data.data_sources import MarketDataManager


def setup_environment():
    """Setup environment variables and paths."""
    required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)

    os.environ.setdefault('DB_PORT', '5432')


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
    """Main function for S&P 500 historical backfill."""
    parser = argparse.ArgumentParser(description='S&P 500 Historical Data Backfill')
    parser.add_argument('--years', type=int, default=30,
                       help='Number of years to backfill (default: 30)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Test configuration without processing')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--batch-size', type=int, default=500,
                       help='Number of days to process in each batch (default: 500)')

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/tmp/sp500_backfill.log') if os.path.exists('/tmp') else logging.NullHandler()
        ]
    )

    global logger
    logger = logging.getLogger(__name__)

    try:
        logger.info("🚀 Starting S&P 500 Historical Data Backfill")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info(f"Years to backfill: {args.years}")
        logger.info(f"Batch size: {args.batch_size}")
        logger.info(f"Arguments: {vars(args)}")

        # Setup environment
        setup_environment()

        # Create database configuration
        db_config = create_db_config()
        logger.info(f"Database: {db_config['host']}:{db_config['port']}/{db_config['database']}")

        # Initialize PostgreSQL-only encoder
        logger.info("Initializing PostgreSQL encoder for backfill...")
        encoder = PostgresOnlyEncoder(db_config=db_config)

        if args.dry_run:
            logger.info("🧪 DRY RUN MODE - No data will be processed")
            logger.info("Configuration test completed successfully")
            return 0

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.years * 365)

        logger.info(f"📅 Fetching S&P 500 data from {start_date.date()} to {end_date.date()}")

        # Initialize data manager
        data_manager = MarketDataManager()

        # Fetch S&P 500 historical data
        logger.info("📈 Fetching S&P 500 historical data from Yahoo Finance...")

        # Use a large period to get all historical data
        # Yahoo Finance symbol for S&P 500 is ^GSPC
        sp500_data = data_manager.get_market_data(
            symbol="^GSPC",
            period=f"{args.years}y"  # Yahoo Finance accepts "30y" format
        )

        if sp500_data.empty:
            logger.error("❌ No S&P 500 data retrieved from Yahoo Finance")
            return 1

        logger.info(f"📊 Retrieved {len(sp500_data)} days of S&P 500 data")
        logger.info(f"📅 Date range: {sp500_data.index.min().date()} to {sp500_data.index.max().date()}")

        # Calculate daily returns
        sp500_data['daily_return'] = sp500_data['close'].pct_change()

        # Process data in batches
        total_records = len(sp500_data)
        processed_records = 0
        batch_count = 0

        for i in range(0, total_records, args.batch_size):
            batch_count += 1
            end_idx = min(i + args.batch_size, total_records)
            batch_data = sp500_data.iloc[i:end_idx].copy()

            logger.info(f"📦 Processing batch {batch_count}: {len(batch_data)} records "
                       f"({batch_data.index.min().date()} to {batch_data.index.max().date()})")

            try:
                # Store batch in PostgreSQL with symbol "SPX" (our internal symbol for S&P 500)
                encoder.store_market_data_postgres("SPX", batch_data)
                processed_records += len(batch_data)

                logger.info(f"✅ Batch {batch_count} completed: {processed_records}/{total_records} records processed")

            except Exception as e:
                logger.error(f"❌ Error processing batch {batch_count}: {e}")
                # Continue with next batch rather than failing completely
                continue

        # Final summary
        logger.info(f"🎉 S&P 500 backfill completed!")
        logger.info(f"📊 Total records processed: {processed_records}/{total_records}")
        logger.info(f"📅 Date range: {sp500_data.index.min().date()} to {sp500_data.index.max().date()}")

        if processed_records < total_records:
            logger.warning(f"⚠️  Some records failed to process: {total_records - processed_records} failed")
            return 1

        return 0

    except KeyboardInterrupt:
        logger.info("🛑 S&P 500 backfill interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"💥 Fatal error in S&P 500 backfill: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)