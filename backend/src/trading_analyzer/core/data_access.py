"""
Data Access Layer for Trading Opportunity Analyzer
Handles database connections and data retrieval for analysis.
"""

import psycopg2
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import os

logger = logging.getLogger(__name__)


class MarketDataAccess:
    """Handles market data retrieval from PostgreSQL database."""

    def __init__(self, db_config: Dict[str, str] = None):
        """Initialize with database configuration."""
        self.db_config = db_config or self._get_db_config_from_env()
        self._test_connection()

    def _get_db_config_from_env(self) -> Dict[str, str]:
        """Get database configuration from environment variables."""
        config = {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
        }

        missing = [k for k, v in config.items() if not v]
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")

        return config

    def _test_connection(self) -> None:
        """Test database connection."""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            logger.info("✅ Database connection successful")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise

    def get_market_data(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Retrieve market data for a symbol within date range.

        Args:
            symbol: Market symbol to retrieve
            start_date: Start date for data (None for earliest available)
            end_date: End date for data (None for latest available)

        Returns:
            DataFrame with OHLCV data indexed by date
        """
        logger.info(f"Retrieving market data for {symbol}")

        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)

            # Build query with optional date filters
            base_query = """
                SELECT trade_date, open_price, high_price, low_price,
                       close_price, adjusted_close, volume, daily_return
                FROM market_data
                WHERE symbol = %s
            """
            params = [symbol]

            if start_date:
                base_query += " AND trade_date >= %s"
                params.append(start_date.date())

            if end_date:
                base_query += " AND trade_date <= %s"
                params.append(end_date.date())

            base_query += " ORDER BY trade_date ASC"

            # Execute query
            df = pd.read_sql_query(base_query, conn, params=params, parse_dates=['trade_date'])

            if df.empty:
                logger.warning(f"No data found for symbol {symbol}")
                return pd.DataFrame()

            # Set trade_date as index
            df.set_index('trade_date', inplace=True)

            # Rename columns to standard format
            df.rename(columns={
                'open_price': 'open',
                'high_price': 'high',
                'low_price': 'low',
                'close_price': 'close',
                'adjusted_close': 'adj_close'
            }, inplace=True)

            logger.info(f"Retrieved {len(df)} records for {symbol}")
            logger.info(f"Date range: {df.index.min()} to {df.index.max()}")

            return df

        except Exception as e:
            logger.error(f"Error retrieving data for {symbol}: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def get_available_symbols(self) -> List[str]:
        """Get list of all available symbols in the database."""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            cursor.execute("SELECT DISTINCT symbol FROM market_data ORDER BY symbol")
            symbols = [row[0] for row in cursor.fetchall()]

            logger.info(f"Found {len(symbols)} symbols in database: {symbols}")
            return symbols

        except Exception as e:
            logger.error(f"Error retrieving available symbols: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def get_symbol_date_range(self, symbol: str) -> Dict[str, datetime]:
        """Get the date range available for a symbol."""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT MIN(trade_date) as start_date, MAX(trade_date) as end_date,
                       COUNT(*) as record_count
                FROM market_data
                WHERE symbol = %s
            """, (symbol,))

            result = cursor.fetchone()
            if result and result[0]:
                return {
                    'start_date': result[0],
                    'end_date': result[1],
                    'record_count': result[2]
                }
            else:
                logger.warning(f"No data found for symbol {symbol}")
                return {}

        except Exception as e:
            logger.error(f"Error getting date range for {symbol}: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def save_trading_opportunities(self, opportunities: List[Dict[str, Any]], table_name: str = "trading_opportunities") -> None:
        """Save trading opportunities to database."""
        if not opportunities:
            logger.info("No opportunities to save")
            return

        conn = None
        cursor = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # Create table if it doesn't exist
            create_table_query = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(25) NOT NULL,
                    position_type VARCHAR(10) NOT NULL,
                    entry_date DATE NOT NULL,
                    exit_date DATE NOT NULL,
                    entry_price DECIMAL(12,4) NOT NULL,
                    exit_price DECIMAL(12,4) NOT NULL,
                    holding_days INTEGER NOT NULL,
                    profit_percent DECIMAL(8,4) NOT NULL,
                    max_unrealized_gain_percent DECIMAL(8,4),
                    max_unrealized_loss_percent DECIMAL(8,4),
                    max_drawdown_from_peak DECIMAL(8,4),
                    peak_profit_date DATE,
                    peak_profit_percent DECIMAL(8,4),
                    trade_score DECIMAL(10,4),
                    analysis_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(symbol, position_type, entry_date, exit_date)
                )
            """
            cursor.execute(create_table_query)

            # Create index for performance
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_{table_name}_symbol_score
                ON {table_name}(symbol, trade_score DESC)
            """)

            # Insert opportunities
            insert_query = f"""
                INSERT INTO {table_name} (
                    symbol, position_type, entry_date, exit_date, entry_price, exit_price,
                    holding_days, profit_percent, max_unrealized_gain_percent,
                    max_unrealized_loss_percent, max_drawdown_from_peak, peak_profit_date,
                    peak_profit_percent, trade_score
                ) VALUES %s
                ON CONFLICT (symbol, position_type, entry_date, exit_date)
                DO UPDATE SET
                    entry_price = EXCLUDED.entry_price,
                    exit_price = EXCLUDED.exit_price,
                    holding_days = EXCLUDED.holding_days,
                    profit_percent = EXCLUDED.profit_percent,
                    max_unrealized_gain_percent = EXCLUDED.max_unrealized_gain_percent,
                    max_unrealized_loss_percent = EXCLUDED.max_unrealized_loss_percent,
                    max_drawdown_from_peak = EXCLUDED.max_drawdown_from_peak,
                    peak_profit_date = EXCLUDED.peak_profit_date,
                    peak_profit_percent = EXCLUDED.peak_profit_percent,
                    trade_score = EXCLUDED.trade_score,
                    analysis_date = NOW()
            """

            # Prepare data for insertion
            records = []
            for opp in opportunities:
                record = (
                    opp['symbol'],
                    opp['position_type'],
                    opp['entry_date'],
                    opp['exit_date'],
                    opp['entry_price'],
                    opp['exit_price'],
                    opp['holding_days'],
                    opp['profit_percent'],
                    opp['max_unrealized_gain_percent'],
                    opp['max_unrealized_loss_percent'],
                    opp['max_drawdown_from_peak'],
                    opp['peak_profit_date'],
                    opp['peak_profit_percent'],
                    opp['trade_score']
                )
                records.append(record)

            from psycopg2.extras import execute_values
            execute_values(cursor, insert_query, records)

            conn.commit()
            logger.info(f"✅ Successfully saved {len(opportunities)} trading opportunities to {table_name}")

        except Exception as e:
            logger.error(f"❌ Error saving trading opportunities: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()