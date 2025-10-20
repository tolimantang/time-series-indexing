"""
Simple Daily Market Encoder
Simplified version that fetches just daily data without technical indicators.
Perfect for daily cronjob that only needs basic price data.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

from .encoder import MarketEncoder
from ..config.config import MarketEncoderConfig, SecurityConfig

logger = logging.getLogger(__name__)


class SimpleDailyEncoder:
    """Simplified encoder for daily basic market data without technical indicators."""

    def __init__(self,
                 config_path: str = None,
                 db_config: Dict[str, str] = None):
        """Initialize simple daily encoder (PostgreSQL only)."""

        # Load configuration
        self.config = MarketEncoderConfig(config_path)
        self.config.setup_logging()

        # Initialize base encoder (PostgreSQL only)
        self.encoder = MarketEncoder(
            chroma_db_path=None,  # Skip ChromaDB for simple version
            db_config=db_config
        )

        # Processing settings from config
        self.batch_size = self.config.get_encoding_setting('batch_size', 10)
        self.max_retries = self.config.get_encoding_setting('max_retries', 3)
        self.retry_delay = self.config.get_encoding_setting('retry_delay_seconds', 5)

        logger.info("Simple daily encoder initialized")

    def process_security_simple(self, security: SecurityConfig) -> Dict[str, Any]:
        """Process a single security with just basic price data."""
        result = {
            'security': security.symbol,
            'db_symbol': security.db_symbol,
            'success': False,
            'error': None,
            'postgres_records': 0,
            'processing_time': 0
        }

        start_time = time.time()

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Processing {security.symbol} ({security.name}) - Attempt {attempt + 1}")

                # Fetch just recent market data (last 5 days to ensure we get latest trading day)
                data = self.encoder.data_manager.get_market_data(security.yahoo_symbol)

                if data.empty:
                    raise ValueError(f"No data retrieved for {security.symbol}")

                # Get just the latest trading day
                latest_data = data.tail(1).copy()

                if len(latest_data) == 0:
                    raise ValueError(f"No recent data for {security.symbol}")

                # Calculate simple daily return (just need previous day)
                if len(data) >= 2:
                    prev_close = data.iloc[-2]['close']
                    current_close = latest_data.iloc[0]['close']
                    daily_return = (current_close - prev_close) / prev_close
                    latest_data.loc[latest_data.index[0], 'daily_return'] = daily_return
                else:
                    # First day of data, no return calculation possible
                    latest_data.loc[latest_data.index[0], 'daily_return'] = 0.0

                # Store in PostgreSQL only
                self.encoder.store_market_data_postgres(security.db_symbol, latest_data)
                result['postgres_records'] = len(latest_data)

                result['success'] = True
                result['processing_time'] = time.time() - start_time

                logger.info(f"✅ Successfully processed {security.symbol}: "
                          f"{result['postgres_records']} DB records")
                break

            except Exception as e:
                error_msg = f"Attempt {attempt + 1} failed for {security.symbol}: {str(e)}"
                logger.warning(error_msg)
                result['error'] = str(e)

                if attempt < self.max_retries - 1:
                    logger.info(f"Retrying {security.symbol} in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"❌ Failed to process {security.symbol} after {self.max_retries} attempts")

        result['processing_time'] = time.time() - start_time
        return result

    def run_daily_simple_encoding(self, categories: List[str] = None) -> Dict[str, Any]:
        """Run simplified daily encoding for all enabled securities."""
        start_time = time.time()
        logger.info("🚀 Starting simple daily market encoding")

        # Get enabled securities
        enabled_securities = self.config.get_enabled_securities()

        # Filter by categories if specified
        if categories:
            filtered_securities = []
            for category in categories:
                filtered_securities.extend(self.config.get_securities_by_category(category))
            enabled_securities = [sec for sec in filtered_securities if sec.enabled]

        if not enabled_securities:
            logger.warning("No enabled securities found")
            return {
                'status': 'warning',
                'message': 'No enabled securities to process',
                'timestamp': datetime.now().isoformat(),
                'processing_time': time.time() - start_time
            }

        logger.info(f"Processing {len(enabled_securities)} securities: {[s.symbol for s in enabled_securities]}")

        # Process securities in batches
        results = []
        successful = 0
        failed = 0

        for i in range(0, len(enabled_securities), self.batch_size):
            batch = enabled_securities[i:i + self.batch_size]
            logger.info(f"Processing batch {i // self.batch_size + 1}: {[s.symbol for s in batch]}")

            # Use thread pool for concurrent processing
            with ThreadPoolExecutor(max_workers=min(len(batch), 5)) as executor:
                futures = {executor.submit(self.process_security_simple, sec): sec for sec in batch}

                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)

                    if result['success']:
                        successful += 1
                    else:
                        failed += 1

            # Small delay between batches
            if i + self.batch_size < len(enabled_securities):
                logger.info("Pausing between batches...")
                time.sleep(2)

        # Calculate totals
        total_postgres_records = sum(r['postgres_records'] for r in results)
        total_time = time.time() - start_time

        # Prepare summary
        summary = {
            'status': 'success' if failed == 0 else 'partial' if successful > 0 else 'failed',
            'timestamp': datetime.now().isoformat(),
            'processing_time': round(total_time, 2),
            'securities': {
                'total': len(enabled_securities),
                'successful': successful,
                'failed': failed
            },
            'data_stored': {
                'postgres_records': total_postgres_records
            },
            'results': results
        }

        # Log summary
        logger.info(f"✅ Simple daily encoding completed: {successful}/{len(enabled_securities)} successful, "
                   f"{total_postgres_records} DB records, {total_time:.1f}s")

        if failed > 0:
            failed_symbols = [r['security'] for r in results if not r['success']]
            logger.warning(f"❌ Failed securities: {failed_symbols}")

        return summary