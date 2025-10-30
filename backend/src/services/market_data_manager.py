"""
Market Data Manager for Asset Price Analysis

Handles storage and retrieval of daily market data (OHLCV) for causal analysis.
Supports querying price movements before/after financial events.
"""

import logging
import os
from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import time

logger = logging.getLogger(__name__)


class MarketDataManager:
    """
    Manager for market data storage and retrieval.

    Supports:
    - Daily OHLCV data storage
    - Price movement analysis around events
    - Forward/backward returns calculation
    - Multiple data source integration
    """

    def __init__(self,
                 db_host: str,
                 db_port: int,
                 db_name: str,
                 db_user: str,
                 db_password: str,
                 alpha_vantage_api_key: Optional[str] = None):
        """
        Initialize market data manager.

        Args:
            db_host: PostgreSQL host
            db_port: PostgreSQL port
            db_name: Database name
            db_user: Database user
            db_password: Database password
            alpha_vantage_api_key: Optional Alpha Vantage API key for data fetching
        """
        self.db_config = {
            'host': db_host,
            'port': db_port,
            'database': db_name,
            'user': db_user,
            'password': db_password
        }
        self.alpha_vantage_api_key = alpha_vantage_api_key

        logger.info(f"MarketDataManager initialized for database {db_name}")

    def get_connection(self):
        """Get database connection."""
        return psycopg2.connect(**self.db_config)

    def store_daily_data(self,
                        symbol: str,
                        data: List[Dict[str, Any]],
                        source: str = 'unknown') -> bool:
        """
        Store daily market data.

        Args:
            symbol: Asset symbol (e.g., 'GLD', 'SPY')
            data: List of daily data dictionaries with keys:
                  date, open, high, low, close, volume, adjusted_close
            source: Data source identifier

        Returns:
            Success status
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Prepare data for insertion
                    insert_data = []
                    for record in data:
                        insert_data.append((
                            symbol,
                            record['date'],
                            record.get('open'),
                            record.get('high'),
                            record.get('low'),
                            record.get('close'),
                            record.get('volume'),
                            record.get('adjusted_close', record.get('close')),
                            source
                        ))

                    # Insert with ON CONFLICT UPDATE
                    insert_sql = """
                        INSERT INTO market_data
                        (symbol, date, open_price, high_price, low_price, close_price,
                         volume, adjusted_close, source, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (symbol, date)
                        DO UPDATE SET
                            open_price = EXCLUDED.open_price,
                            high_price = EXCLUDED.high_price,
                            low_price = EXCLUDED.low_price,
                            close_price = EXCLUDED.close_price,
                            volume = EXCLUDED.volume,
                            adjusted_close = EXCLUDED.adjusted_close,
                            source = EXCLUDED.source,
                            updated_at = CURRENT_TIMESTAMP
                    """

                    cursor.executemany(insert_sql, insert_data)
                    conn.commit()

                    logger.info(f"Stored {len(insert_data)} daily records for {symbol}")
                    return True

        except Exception as e:
            logger.error(f"Error storing market data for {symbol}: {e}")
            return False

    def get_price_data(self,
                      symbol: str,
                      start_date: date,
                      end_date: date) -> List[Dict[str, Any]]:
        """
        Get price data for a symbol within date range.

        Args:
            symbol: Asset symbol
            start_date: Start date
            end_date: End date

        Returns:
            List of daily price records
        """
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute("""
                        SELECT symbol, trade_date as date, open_price, high_price, low_price,
                               close_price, volume, adjusted_close, 'market_data' as source
                        FROM market_data
                        WHERE symbol = %s AND trade_date BETWEEN %s AND %s
                        ORDER BY trade_date ASC
                    """, (symbol, start_date, end_date))

                    results = cursor.fetchall()
                    return [dict(row) for row in results]

        except Exception as e:
            logger.error(f"Error getting price data for {symbol}: {e}")
            return []

    def calculate_event_impact(self,
                             symbol: str,
                             event_date: date,
                             lookback_days: int = 5,
                             forward_days: int = 20) -> Dict[str, Any]:
        """
        Calculate price impact around an event date.

        Args:
            symbol: Asset symbol
            event_date: Date of the event
            lookback_days: Days before event to include
            forward_days: Days after event to analyze

        Returns:
            Price impact analysis
        """
        try:
            # Get price data around the event
            start_date = event_date - timedelta(days=lookback_days + 5)  # Buffer for weekends
            end_date = event_date + timedelta(days=forward_days + 5)

            price_data = self.get_price_data(symbol, start_date, end_date)

            if not price_data:
                return {'error': f'No price data found for {symbol} around {event_date}'}

            # Find the closest trading day to event_date
            event_price = None
            pre_event_price = None

            for i, record in enumerate(price_data):
                record_date = record['date']

                if record_date <= event_date:
                    pre_event_price = record
                    if i + 1 < len(price_data):
                        event_price = price_data[i + 1]  # Next trading day
                    else:
                        event_price = record

            if not event_price or not pre_event_price:
                return {'error': f'Could not find trading data around {event_date}'}

            # Calculate forward returns
            event_close = float(event_price['close_price'])
            forward_returns = {}

            for days in [1, 5, 10, 20]:
                target_date = event_date + timedelta(days=days)
                # Find closest trading day
                future_price = None
                for record in price_data:
                    if record['date'] >= target_date:
                        future_price = record
                        break

                if future_price:
                    future_close = float(future_price['close_price'])
                    return_pct = ((future_close - event_close) / event_close) * 100
                    forward_returns[f'return_{days}d'] = {
                        'return_pct': round(return_pct, 2),
                        'price_start': event_close,
                        'price_end': future_close,
                        'actual_days': (future_price['date'] - event_price['date']).days
                    }

            return {
                'symbol': symbol,
                'event_date': event_date.isoformat(),
                'event_close_price': event_close,
                'pre_event_close_price': float(pre_event_price['close_price']),
                'forward_returns': forward_returns,
                'price_data': price_data  # Full data for charting
            }

        except Exception as e:
            logger.error(f"Error calculating event impact for {symbol} on {event_date}: {e}")
            return {'error': str(e)}

    def analyze_multiple_events_impact(self,
                                     symbol: str,
                                     event_dates: List[date],
                                     forward_days: int = 20) -> Dict[str, Any]:
        """
        Analyze price impact across multiple similar events.

        Args:
            symbol: Asset symbol
            event_dates: List of event dates
            forward_days: Days after each event to analyze

        Returns:
            Aggregated impact analysis
        """
        try:
            individual_impacts = []

            for event_date in event_dates:
                impact = self.calculate_event_impact(symbol, event_date, forward_days=forward_days)
                if 'error' not in impact:
                    individual_impacts.append(impact)

            if not individual_impacts:
                return {'error': f'No valid impact data found for {symbol}'}

            # Aggregate statistics
            aggregated_returns = {}
            for days in [1, 5, 10, 20]:
                returns_key = f'return_{days}d'
                returns = [impact['forward_returns'][returns_key]['return_pct']
                          for impact in individual_impacts
                          if returns_key in impact['forward_returns']]

                if returns:
                    aggregated_returns[returns_key] = {
                        'average_return': round(sum(returns) / len(returns), 2),
                        'positive_events': len([r for r in returns if r > 0]),
                        'negative_events': len([r for r in returns if r < 0]),
                        'total_events': len(returns),
                        'success_rate': round(len([r for r in returns if r > 0]) / len(returns) * 100, 1),
                        'all_returns': returns
                    }

            return {
                'symbol': symbol,
                'total_events_analyzed': len(individual_impacts),
                'aggregated_returns': aggregated_returns,
                'individual_events': individual_impacts
            }

        except Exception as e:
            logger.error(f"Error analyzing multiple events impact: {e}")
            return {'error': str(e)}

    # Data fetching methods (for future use)
    def fetch_alpha_vantage_data(self, symbol: str, outputsize: str = 'full') -> bool:
        """
        Fetch data from Alpha Vantage API (if API key available).

        Args:
            symbol: Asset symbol
            outputsize: 'compact' or 'full'

        Returns:
            Success status
        """
        if not self.alpha_vantage_api_key:
            logger.warning("Alpha Vantage API key not configured")
            return False

        try:
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': 'TIME_SERIES_DAILY_ADJUSTED',
                'symbol': symbol,
                'outputsize': outputsize,
                'apikey': self.alpha_vantage_api_key
            }

            response = requests.get(url, params=params)
            data = response.json()

            if 'Time Series (Daily)' not in data:
                logger.error(f"No time series data in Alpha Vantage response for {symbol}")
                return False

            # Convert to our format
            daily_data = []
            time_series = data['Time Series (Daily)']

            for date_str, values in time_series.items():
                daily_data.append({
                    'date': datetime.strptime(date_str, '%Y-%m-%d').date(),
                    'open': float(values['1. open']),
                    'high': float(values['2. high']),
                    'low': float(values['3. low']),
                    'close': float(values['4. close']),
                    'adjusted_close': float(values['5. adjusted close']),
                    'volume': int(values['6. volume'])
                })

            # Store the data
            return self.store_daily_data(symbol, daily_data, 'alpha_vantage')

        except Exception as e:
            logger.error(f"Error fetching Alpha Vantage data for {symbol}: {e}")
            return False


def create_market_data_manager() -> MarketDataManager:
    """
    Factory function to create MarketDataManager from environment variables.

    Environment Variables:
        DB_HOST: PostgreSQL host
        DB_PORT: PostgreSQL port
        DB_NAME: Database name
        DB_USER: Database user
        DB_PASSWORD: Database password
        ALPHA_VANTAGE_API_KEY: Optional Alpha Vantage API key

    Returns:
        Configured MarketDataManager instance
    """
    return MarketDataManager(
        db_host=os.getenv('DB_HOST', 'localhost'),
        db_port=int(os.getenv('DB_PORT', '5432')),
        db_name=os.getenv('DB_NAME', 'financial_postgres'),
        db_user=os.getenv('DB_USER', 'postgres'),
        db_password=os.getenv('DB_PASSWORD', ''),
        alpha_vantage_api_key=os.getenv('ALPHA_VANTAGE_API_KEY')
    )