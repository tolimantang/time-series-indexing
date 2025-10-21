"""
Data retrieval from trading opportunities database.
"""

import os
import logging
import psycopg2
import json
from typing import List, Dict, Any, Optional
from datetime import date

from ..models.trading_data import TradingOpportunity

logger = logging.getLogger(__name__)


class TradingDataRetriever:
    """Retrieves trading opportunity data from PostgreSQL database."""

    def __init__(self, db_config: Optional[Dict[str, str]] = None):
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
            logger.info("✅ Trading data database connection successful")
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise

    def get_all_trading_opportunities(self) -> List[TradingOpportunity]:
        """Retrieve all trading opportunities with astrological analysis."""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    id, symbol, position_type, entry_date, exit_date,
                    entry_price, exit_price, holding_days, profit_percent, trade_score,
                    astrological_score, entry_astro_description, exit_astro_description,
                    entry_planetary_data, exit_planetary_data, astro_analysis_summary,
                    claude_analysis
                FROM trading_opportunities
                WHERE astro_analyzed_at IS NOT NULL
                ORDER BY astrological_score DESC
            """)

            opportunities = []
            for row in cursor.fetchall():
                opportunity = TradingOpportunity(
                    id=row[0],
                    symbol=row[1],
                    position_type=row[2],
                    entry_date=row[3],
                    exit_date=row[4],
                    entry_price=float(row[5]),
                    exit_price=float(row[6]),
                    holding_days=row[7],
                    profit_percent=float(row[8]),
                    trade_score=float(row[9]),
                    astrological_score=float(row[10]),
                    entry_astro_description=row[11] or "",
                    exit_astro_description=row[12] or "",
                    entry_planetary_data=row[13] or {},
                    exit_planetary_data=row[14] or {},
                    astro_analysis_summary=row[15] or "",
                    claude_analysis=row[16]
                )
                opportunities.append(opportunity)

            cursor.close()
            conn.close()

            logger.info(f"Retrieved {len(opportunities)} trading opportunities with astrological data")
            return opportunities

        except Exception as e:
            logger.error(f"Error retrieving trading opportunities: {e}")
            raise

    def get_opportunities_by_criteria(
        self,
        min_profit: float = None,
        min_astro_score: float = None,
        position_type: str = None,
        symbol: str = None,
        limit: int = None
    ) -> List[TradingOpportunity]:
        """Retrieve trading opportunities with specific criteria."""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # Build query with filters
            query = """
                SELECT
                    id, symbol, position_type, entry_date, exit_date,
                    entry_price, exit_price, holding_days, profit_percent, trade_score,
                    astrological_score, entry_astro_description, exit_astro_description,
                    entry_planetary_data, exit_planetary_data, astro_analysis_summary,
                    claude_analysis
                FROM trading_opportunities
                WHERE astro_analyzed_at IS NOT NULL
            """

            params = []

            if min_profit is not None:
                query += " AND profit_percent >= %s"
                params.append(min_profit)

            if min_astro_score is not None:
                query += " AND astrological_score >= %s"
                params.append(min_astro_score)

            if position_type:
                query += " AND position_type = %s"
                params.append(position_type)

            if symbol:
                query += " AND symbol = %s"
                params.append(symbol)

            query += " ORDER BY astrological_score DESC"

            if limit:
                query += " LIMIT %s"
                params.append(limit)

            cursor.execute(query, params)

            opportunities = []
            for row in cursor.fetchall():
                opportunity = TradingOpportunity(
                    id=row[0],
                    symbol=row[1],
                    position_type=row[2],
                    entry_date=row[3],
                    exit_date=row[4],
                    entry_price=float(row[5]),
                    exit_price=float(row[6]),
                    holding_days=row[7],
                    profit_percent=float(row[8]),
                    trade_score=float(row[9]),
                    astrological_score=float(row[10]),
                    entry_astro_description=row[11] or "",
                    exit_astro_description=row[12] or "",
                    entry_planetary_data=row[13] or {},
                    exit_planetary_data=row[14] or {},
                    astro_analysis_summary=row[15] or "",
                    claude_analysis=row[16]
                )
                opportunities.append(opportunity)

            cursor.close()
            conn.close()

            logger.info(f"Retrieved {len(opportunities)} trading opportunities matching criteria")
            return opportunities

        except Exception as e:
            logger.error(f"Error retrieving filtered trading opportunities: {e}")
            raise

    def get_trading_statistics(self) -> Dict[str, Any]:
        """Get overall trading statistics with astrological breakdown."""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # Overall statistics
            cursor.execute("""
                SELECT
                    COUNT(*) as total_trades,
                    AVG(profit_percent) as avg_profit,
                    AVG(astrological_score) as avg_astro_score,
                    COUNT(CASE WHEN position_type = 'long' THEN 1 END) as long_trades,
                    COUNT(CASE WHEN position_type = 'short' THEN 1 END) as short_trades,
                    MIN(entry_date) as earliest_trade,
                    MAX(exit_date) as latest_trade
                FROM trading_opportunities
                WHERE astro_analyzed_at IS NOT NULL
            """)

            stats = cursor.fetchone()

            # Top performing lunar phases
            cursor.execute("""
                SELECT
                    entry_planetary_data->'lunar_phase'->>'name' as lunar_phase,
                    COUNT(*) as trade_count,
                    AVG(profit_percent) as avg_profit,
                    AVG(astrological_score) as avg_astro_score
                FROM trading_opportunities
                WHERE astro_analyzed_at IS NOT NULL
                  AND entry_planetary_data->'lunar_phase'->>'name' IS NOT NULL
                GROUP BY entry_planetary_data->'lunar_phase'->>'name'
                ORDER BY avg_profit DESC
            """)

            lunar_phases = cursor.fetchall()

            cursor.close()
            conn.close()

            return {
                'total_trades': stats[0],
                'avg_profit': float(stats[1]) if stats[1] else 0,
                'avg_astrological_score': float(stats[2]) if stats[2] else 0,
                'long_trades': stats[3],
                'short_trades': stats[4],
                'earliest_trade': stats[5],
                'latest_trade': stats[6],
                'lunar_phase_performance': [
                    {
                        'phase': row[0],
                        'trade_count': row[1],
                        'avg_profit': float(row[2]),
                        'avg_astro_score': float(row[3])
                    }
                    for row in lunar_phases
                ]
            }

        except Exception as e:
            logger.error(f"Error retrieving trading statistics: {e}")
            raise