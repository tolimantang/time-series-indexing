#!/usr/bin/env python3
"""
Oil Futures Historical Data Backfill Script
Fetches 30 years of oil futures daily data and stores in PostgreSQL.
Supports both WTI Crude Oil (CL=F) and Brent Crude Oil (BZ=F).
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


def get_oil_futures_config():
    """Get oil futures symbols configuration."""
    return {
        'wti': {
            'yahoo_symbol': 'CL=F',
            'db_symbol': 'CRUDE_OIL_WTI',
            'name': 'WTI Crude Oil Futures'
        },
        'brent': {
            'yahoo_symbol': 'BZ=F',
            'db_symbol': 'CRUDE_OIL_BRENT',
            'name': 'Brent Crude Oil Futures'
        }
    }


def fetch_and_store_oil_data(encoder, data_manager, symbol_config, years, batch_size):
    """Fetch and store oil futures data for a specific symbol."""
    yahoo_symbol = symbol_config['yahoo_symbol']
    db_symbol = symbol_config['db_symbol']
    name = symbol_config['name']

    logger.info(f"📈 Fetching {name} historical data ({yahoo_symbol})...")

    # Fetch historical data from Yahoo Finance
    oil_data = data_manager.get_market_data(symbol=yahoo_symbol)

    if oil_data.empty:
        logger.error(f"❌ No {name} data retrieved from Yahoo Finance")
        return False

    logger.info(f"📊 Retrieved {len(oil_data)} days of {name} data")
    logger.info(f"📅 Date range: {oil_data.index.min().date()} to {oil_data.index.max().date()}")

    # Calculate daily returns
    oil_data['daily_return'] = oil_data['close'].pct_change()

    # Process data in batches
    total_records = len(oil_data)
    processed_records = 0
    batch_count = 0

    for i in range(0, total_records, batch_size):
        batch_count += 1
        end_idx = min(i + batch_size, total_records)
        batch_data = oil_data.iloc[i:end_idx].copy()

        logger.info(f"📦 Processing {name} batch {batch_count}: {len(batch_data)} records "
                   f"({batch_data.index.min().date()} to {batch_data.index.max().date()})")

        try:
            # Store batch in PostgreSQL
            encoder.store_market_data_postgres(db_symbol, batch_data)
            processed_records += len(batch_data)

            logger.info(f"✅ {name} batch {batch_count} completed: {processed_records}/{total_records} records processed")

        except Exception as e:
            logger.error(f"❌ Error processing {name} batch {batch_count}: {e}")
            # Continue with next batch rather than failing completely
            continue

    # Summary for this symbol
    logger.info(f"🎉 {name} backfill completed!")
    logger.info(f"📊 Total records processed: {processed_records}/{total_records}")

    if processed_records < total_records:
        logger.warning(f"⚠️  Some {name} records failed to process: {total_records - processed_records} failed")
        return False

    return True


def main():
    """Main function for oil futures historical backfill."""
    parser = argparse.ArgumentParser(description='Oil Futures Historical Data Backfill')
    parser.add_argument('--years', type=int, default=30,
                       help='Number of years to backfill (default: 30)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Test configuration without processing')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--batch-size', type=int, default=500,
                       help='Number of days to process in each batch (default: 500)')
    parser.add_argument('--symbols', nargs='+', choices=['wti', 'brent', 'all'], default=['all'],
                       help='Oil futures symbols to backfill (default: all)')

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('/tmp/oil_futures_backfill.log') if os.path.exists('/tmp') else logging.NullHandler()
        ]
    )

    global logger
    logger = logging.getLogger(__name__)

    try:
        logger.info("🚀 Starting Oil Futures Historical Data Backfill")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info(f"Years to backfill: {args.years}")
        logger.info(f"Batch size: {args.batch_size}")
        logger.info(f"Symbols: {args.symbols}")
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

        # Initialize data manager
        data_manager = MarketDataManager()

        # Get oil futures configuration
        oil_config = get_oil_futures_config()

        # Determine which symbols to process
        if 'all' in args.symbols:
            symbols_to_process = ['wti', 'brent']
        else:
            symbols_to_process = args.symbols

        logger.info(f"Processing symbols: {symbols_to_process}")

        # Process each oil futures symbol
        success_count = 0
        total_symbols = len(symbols_to_process)

        for symbol_key in symbols_to_process:
            if symbol_key not in oil_config:
                logger.error(f"❌ Unknown symbol: {symbol_key}")
                continue

            logger.info(f"🛢️  Processing {symbol_key.upper()} ({oil_config[symbol_key]['name']})...")

            success = fetch_and_store_oil_data(
                encoder,
                data_manager,
                oil_config[symbol_key],
                args.years,
                args.batch_size
            )

            if success:
                success_count += 1
                logger.info(f"✅ {symbol_key.upper()} processing completed successfully")
            else:
                logger.error(f"❌ {symbol_key.upper()} processing failed")

        # Final summary
        logger.info(f"🎉 Oil Futures backfill completed!")
        logger.info(f"📊 Successfully processed: {success_count}/{total_symbols} symbols")

        if success_count < total_symbols:
            logger.warning(f"⚠️  Some symbols failed to process completely")
            return 1

        return 0

    except KeyboardInterrupt:
        logger.info("🛑 Oil Futures backfill interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"💥 Fatal error in Oil Futures backfill: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)