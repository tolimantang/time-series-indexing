"""
PostgreSQL-only Market Encoder
Minimal encoder that only stores basic market data in PostgreSQL.
No ChromaDB, no embeddings, no sentence transformers.
"""

import logging
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Optional
import os

from ..data.data_sources import MarketDataManager

logger = logging.getLogger(__name__)


class PostgresOnlyEncoder:
    """Minimal market encoder that only stores data in PostgreSQL."""

    def __init__(self, db_config: Dict[str, str] = None):
        """Initialize PostgreSQL-only encoder."""
        self.data_manager = MarketDataManager()

        # Database configuration
        self.db_config = db_config or self._get_db_config_from_env()
        logger.info(f"PostgreSQL encoder initialized for {self.db_config.get('host', 'unknown host')}")

    def _get_db_config_from_env(self) -> Dict[str, str]:
        """Get database configuration from environment variables."""
        return {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
        }

    def store_market_data_postgres(self, symbol: str, data: pd.DataFrame) -> None:
        """Store market data in PostgreSQL."""
        if data.empty:
            logger.warning(f"No data to store for {symbol}")
            return

        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # Prepare data for insertion
            records = []
            for date, row in data.iterrows():
                record = (
                    symbol,
                    date.date() if hasattr(date, 'date') else date,
                    float(row.get('open', row['close'])),
                    float(row.get('high', row['close'])),
                    float(row.get('low', row['close'])),
                    float(row['close']),
                    float(row.get('adj_close', row['close'])),
                    int(row.get('volume', 0)),
                    float(row.get('daily_return', 0)) if row.get('daily_return') is not None else None
                )
                records.append(record)

            # Insert with ON CONFLICT handling for duplicate dates
            insert_query = """
                INSERT INTO market_data (
                    symbol, trade_date, open_price, high_price, low_price,
                    close_price, adjusted_close, volume, daily_return
                ) VALUES %s
                ON CONFLICT (symbol, trade_date)
                DO UPDATE SET
                    open_price = EXCLUDED.open_price,
                    high_price = EXCLUDED.high_price,
                    low_price = EXCLUDED.low_price,
                    close_price = EXCLUDED.close_price,
                    adjusted_close = EXCLUDED.adjusted_close,
                    volume = EXCLUDED.volume,
                    daily_return = EXCLUDED.daily_return,
                    updated_at = NOW()
            """

            from psycopg2.extras import execute_values
            execute_values(cursor, insert_query, records)

            conn.commit()
            logger.info(f"✅ Stored {len(records)} records for {symbol} in PostgreSQL")

        except Exception as e:
            logger.error(f"❌ Error storing data for {symbol}: {e}")
            if 'conn' in locals():
                conn.rollback()
            raise
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()