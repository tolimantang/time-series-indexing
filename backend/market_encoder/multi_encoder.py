"""
Multi-Security Market Encoder
Handles encoding multiple securities in batch for daily cronjob.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from .encoder import MarketEncoder
from .config import MarketEncoderConfig, SecurityConfig

logger = logging.getLogger(__name__)


class MultiSecurityEncoder:
    """Encoder for multiple securities with batch processing and error handling."""

    def __init__(self,
                 config_path: str = None,
                 chroma_db_path: str = None,
                 db_config: Dict[str, str] = None):
        """Initialize multi-security encoder."""

        # Load configuration
        self.config = MarketEncoderConfig(config_path)
        self.config.setup_logging()

        # Initialize base encoder
        self.encoder = MarketEncoder(
            chroma_db_path=chroma_db_path,
            db_config=db_config
        )

        # Processing settings from config
        self.days_back = self.config.get_encoding_setting('days_back', 60)
        self.embedding_days = self.config.get_encoding_setting('embedding_days', 30)
        self.batch_size = self.config.get_encoding_setting('batch_size', 10)
        self.max_retries = self.config.get_encoding_setting('max_retries', 3)
        self.retry_delay = self.config.get_encoding_setting('retry_delay_seconds', 5)

        logger.info("Multi-security encoder initialized")

    def process_security(self, security: SecurityConfig) -> Dict[str, Any]:
        """Process a single security with retry logic."""
        result = {
            'security': security.symbol,
            'db_symbol': security.db_symbol,
            'success': False,
            'error': None,
            'postgres_records': 0,
            'chroma_records': 0,
            'processing_time': 0
        }

        start_time = time.time()

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Processing {security.symbol} ({security.name}) - Attempt {attempt + 1}")

                # Fetch market data
                logger.debug(f"Fetching {self.days_back} days of data for {security.symbol}")
                data = self.encoder.data_manager.get_market_data(security.yahoo_symbol)

                if data.empty:
                    raise ValueError(f"No data retrieved for {security.symbol}")

                # Limit to requested time period
                cutoff_date = datetime.now() - timedelta(days=self.days_back)
                data = data[data.index >= cutoff_date]

                if len(data) < 10:  # Need minimum data for indicators
                    raise ValueError(f"Insufficient data for {security.symbol}: {len(data)} days")

                # Store in PostgreSQL
                data_with_returns = self.encoder.signal_generator.calculate_returns(data)
                self.encoder.store_market_data_postgres(security.db_symbol, data_with_returns)
                result['postgres_records'] = len(data_with_returns)

                # Process for embeddings (use recent data only)
                recent_data = data.tail(self.embedding_days).copy()
                if len(recent_data) > 0:
                    processed_data = self._process_security_embeddings(security, recent_data)
                    self.encoder.store_embeddings(processed_data)
                    result['chroma_records'] = len(processed_data)

                result['success'] = True
                result['processing_time'] = time.time() - start_time

                logger.info(f"✅ Successfully processed {security.symbol}: "
                          f"{result['postgres_records']} DB records, "
                          f"{result['chroma_records']} embeddings")
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

    def _process_security_embeddings(self, security: SecurityConfig, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """Process security data for embeddings using the existing encoder logic."""
        processed_data = []

        # Calculate signals for the data
        data = self.encoder.signal_generator.calculate_returns(data)
        data = self.encoder.signal_generator.calculate_volatility(data)
        data = self.encoder.signal_generator.calculate_technical_indicators(data)
        data = self.encoder.signal_generator.detect_regime(data)

        # Process each day
        for date, row in data.iterrows():
            try:
                # Skip if essential data is missing
                if pd.isna(row['close']) or pd.isna(row['daily_return']):
                    continue

                # Create daily signals dictionary
                daily_signals = {
                    'symbol': security.db_symbol,
                    'name': security.name,
                    'date': date.strftime('%Y-%m-%d'),
                    'price': {
                        'close': float(row['close']),
                        'daily_return': float(row['daily_return']) * 100,
                        'return_5d': float(row.get('return_5d', 0)) * 100,
                        'return_20d': float(row.get('return_20d', 0)) * 100,
                    },
                    'volatility': {
                        'vol_20d': float(row.get('vol_20d', 15)),
                        'volume_ratio': float(row.get('volume_ratio', 1)),
                    },
                    'technical': {
                        'rsi': float(row.get('rsi', 50)),
                        'price_vs_ma20': float(row.get('price_vs_ma20', 0)),
                        'bb_position': float(row.get('bb_position', 0.5)),
                    },
                    'regime': {
                        'vol_regime': row.get('vol_regime', 'normal_vol'),
                        'trend_regime': row.get('trend_regime', 'sideways'),
                        'momentum_regime': row.get('momentum_regime', 'normal_momentum'),
                    }
                }

                # Generate narrative text
                narrative = self.encoder.text_generator.generate_market_narrative(
                    security.db_symbol, daily_signals
                )

                processed_data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'signals': daily_signals,
                    'narrative': narrative,
                    'symbol': security.db_symbol
                })

            except Exception as e:
                logger.warning(f"Error processing {security.symbol} data for {date}: {e}")
                continue

        return processed_data

    def run_daily_encoding(self, categories: List[str] = None) -> Dict[str, Any]:
        """Run daily encoding for all enabled securities."""
        start_time = time.time()
        logger.info("🚀 Starting daily multi-security encoding")

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

        # Process securities in batches using ThreadPoolExecutor
        results = []
        successful = 0
        failed = 0

        # Process in batches to avoid overwhelming APIs
        for i in range(0, len(enabled_securities), self.batch_size):
            batch = enabled_securities[i:i + self.batch_size]
            logger.info(f"Processing batch {i // self.batch_size + 1}: {[s.symbol for s in batch]}")

            # Use thread pool for concurrent processing
            with ThreadPoolExecutor(max_workers=min(len(batch), 5)) as executor:
                futures = {executor.submit(self.process_security, sec): sec for sec in batch}

                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)

                    if result['success']:
                        successful += 1
                    else:
                        failed += 1

            # Small delay between batches to be nice to APIs
            if i + self.batch_size < len(enabled_securities):
                logger.info("Pausing between batches...")
                time.sleep(2)

        # Calculate totals
        total_postgres_records = sum(r['postgres_records'] for r in results)
        total_chroma_records = sum(r['chroma_records'] for r in results)
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
                'postgres_records': total_postgres_records,
                'chroma_records': total_chroma_records
            },
            'results': results
        }

        # Log summary
        logger.info(f"✅ Daily encoding completed: {successful}/{len(enabled_securities)} successful, "
                   f"{total_postgres_records} DB records, {total_chroma_records} embeddings, "
                   f"{total_time:.1f}s")

        if failed > 0:
            failed_symbols = [r['security'] for r in results if not r['success']]
            logger.warning(f"❌ Failed securities: {failed_symbols}")

        return summary

    def get_status(self) -> Dict[str, Any]:
        """Get current configuration and status."""
        return {
            'config_summary': self.config.summary(),
            'encoder_stats': self.encoder.get_collection_stats(),
            'last_run': None  # Could add timestamp tracking
        }