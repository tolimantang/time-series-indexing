"""
PostgreSQL Manager for Financial Events

Handles structured storage of financial events in PostgreSQL for:
- Time range queries
- Aggregations and analytics
- Fast metadata filtering
- Relational joins with market data

Complements ChromaDB semantic search capabilities.
"""

import os
import logging
import psycopg2
import psycopg2.extras
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
import json

try:
    from ..event_encoder.core.base_encoder import FinancialEvent
except ImportError:
    # Handle direct script execution
    from event_encoder.core.base_encoder import FinancialEvent

logger = logging.getLogger(__name__)


class EventsPostgresManager:
    """
    PostgreSQL manager for financial events storage and retrieval.
    Designed to work alongside ChromaDB for dual storage strategy.
    """

    def __init__(self,
                 host: Optional[str] = None,
                 port: Optional[int] = None,
                 database: Optional[str] = None,
                 user: Optional[str] = None,
                 password: Optional[str] = None):
        """
        Initialize PostgreSQL connection for events storage.

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
        """
        # Get connection parameters from environment or parameters
        self.host = host or os.getenv('DB_HOST', 'localhost')
        self.port = port or int(os.getenv('DB_PORT', '5432'))
        self.database = database or os.getenv('DB_NAME', 'financial_postgres')
        self.user = user or os.getenv('DB_USER', 'postgres')
        self.password = password or os.getenv('DB_PASSWORD', '')

        self.connection = None
        self._connect()

        logger.info(f"EventsPostgresManager initialized for {self.host}:{self.port}/{self.database}")

    def _connect(self):
        """Establish database connection."""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self.connection.autocommit = True
            logger.info("PostgreSQL connection established")

        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    def _ensure_connection(self):
        """Ensure connection is active, reconnect if needed."""
        try:
            if self.connection is None or self.connection.closed:
                self._connect()
            else:
                # Test connection
                with self.connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
        except Exception as e:
            logger.warning(f"Connection test failed, reconnecting: {e}")
            self._connect()

    def store_events(self, events: List[FinancialEvent]) -> bool:
        """
        Store financial events in PostgreSQL.

        Args:
            events: List of FinancialEvent objects

        Returns:
            Success status
        """
        if not events:
            return True

        try:
            self._ensure_connection()

            with self.connection.cursor() as cursor:
                # Prepare bulk insert data
                insert_data = []
                for event in events:
                    # Convert event to database format
                    event_data = self._event_to_db_format(event)
                    insert_data.append(event_data)

                # Bulk insert with ON CONFLICT handling
                insert_query = """
                    INSERT INTO financial_events (
                        event_id, event_date, event_datetime, source, event_type, importance,
                        title, description, document_text, series_id, value, previous_value,
                        change_amount, change_percent, market_impact, keywords, metadata
                    ) VALUES %s
                    ON CONFLICT (event_id) DO UPDATE SET
                        updated_at = NOW(),
                        value = EXCLUDED.value,
                        previous_value = EXCLUDED.previous_value,
                        change_amount = EXCLUDED.change_amount,
                        change_percent = EXCLUDED.change_percent
                """

                psycopg2.extras.execute_values(
                    cursor, insert_query, insert_data, template=None, page_size=100
                )

                logger.info(f"Successfully stored {len(events)} events in PostgreSQL")
                return True

        except Exception as e:
            logger.error(f"Error storing events in PostgreSQL: {e}")
            return False

    def _event_to_db_format(self, event: FinancialEvent) -> Tuple:
        """
        Convert FinancialEvent to database format.

        Args:
            event: FinancialEvent object

        Returns:
            Tuple of values for database insertion
        """
        # Extract metadata
        metadata = {}
        if hasattr(event, 'series_id'):
            metadata['series_id'] = event.series_id
        if hasattr(event, 'fred_description'):
            metadata['fred_description'] = event.fred_description

        # Add any additional attributes as metadata
        for attr in dir(event):
            if not attr.startswith('_') and attr not in [
                'id', 'date', 'source', 'event_type', 'title', 'description', 'importance'
            ]:
                value = getattr(event, attr)
                if value is not None and not callable(value):
                    metadata[attr] = value

        # Extract numeric values for FRED events
        value = None
        previous_value = None
        change_amount = None
        change_percent = None

        if hasattr(event, 'value') and event.value is not None:
            value = float(event.value)

        # Extract keywords from title and description
        keywords = []
        if event.title:
            keywords.extend(event.title.lower().split())
        if event.event_type:
            keywords.extend(event.event_type.split('_'))
        if event.source:
            keywords.append(event.source.lower())

        # Clean and deduplicate keywords
        keywords = list(set([k for k in keywords if len(k) > 2]))

        # Create document text for search
        document_text = f"{event.title}\n\n{event.description or ''}"

        return (
            event.id,                                    # event_id
            event.date.date() if hasattr(event.date, 'date') else event.date,  # event_date
            event.date,                                  # event_datetime
            event.source,                                # source
            event.event_type,                           # event_type
            event.importance,                           # importance
            event.title,                                # title
            event.description,                          # description
            document_text,                              # document_text
            getattr(event, 'series_id', None),         # series_id
            value,                                      # value
            previous_value,                             # previous_value
            change_amount,                              # change_amount
            change_percent,                             # change_percent
            getattr(event, 'market_impact', None),     # market_impact
            keywords,                                   # keywords
            json.dumps(metadata) if metadata else None  # metadata
        )

    def get_events_by_date_range(self,
                                start_date: date,
                                end_date: date,
                                event_types: Optional[List[str]] = None,
                                importance: Optional[List[str]] = None,
                                sources: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve events by date range with filters.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            event_types: Filter by event types
            importance: Filter by importance levels
            sources: Filter by sources

        Returns:
            List of event dictionaries
        """
        try:
            self._ensure_connection()

            # Build query with filters
            where_conditions = ["event_date BETWEEN %s AND %s"]
            params = [start_date, end_date]

            if event_types:
                where_conditions.append("event_type = ANY(%s)")
                params.append(event_types)

            if importance:
                where_conditions.append("importance = ANY(%s)")
                params.append(importance)

            if sources:
                where_conditions.append("source = ANY(%s)")
                params.append(sources)

            query = f"""
                SELECT event_id, event_date, event_datetime, source, event_type, importance,
                       title, description, series_id, value, previous_value, change_amount,
                       change_percent, market_impact, keywords, metadata, created_at
                FROM financial_events
                WHERE {' AND '.join(where_conditions)}
                ORDER BY event_datetime DESC
            """

            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()

                events = []
                for row in results:
                    event_dict = dict(row)
                    # Parse JSON metadata if it's a string, otherwise keep as-is
                    if event_dict['metadata']:
                        if isinstance(event_dict['metadata'], str):
                            event_dict['metadata'] = json.loads(event_dict['metadata'])
                        # If it's already a dict (JSONB), keep it as-is
                    events.append(event_dict)

                logger.info(f"Retrieved {len(events)} events from {start_date} to {end_date}")
                return events

        except Exception as e:
            logger.error(f"Error retrieving events: {e}")
            return []

    def get_event_statistics(self,
                           start_date: Optional[date] = None,
                           end_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Get event statistics and aggregations.

        Args:
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Dictionary with statistics
        """
        try:
            self._ensure_connection()

            where_clause = ""
            params = []

            if start_date and end_date:
                where_clause = "WHERE event_date BETWEEN %s AND %s"
                params = [start_date, end_date]

            query = f"""
                SELECT
                    COUNT(*) as total_events,
                    COUNT(DISTINCT source) as unique_sources,
                    COUNT(DISTINCT event_type) as unique_event_types,

                    -- By importance
                    COUNT(*) FILTER (WHERE importance = 'high') as high_importance,
                    COUNT(*) FILTER (WHERE importance = 'medium') as medium_importance,
                    COUNT(*) FILTER (WHERE importance = 'low') as low_importance,

                    -- By source
                    COUNT(*) FILTER (WHERE source = 'fred') as fred_events,

                    -- Date range
                    MIN(event_date) as earliest_event,
                    MAX(event_date) as latest_event

                FROM financial_events
                {where_clause}
            """

            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute(query, params)
                stats = dict(cursor.fetchone())

                # Get breakdown by event type
                type_query = f"""
                    SELECT event_type, COUNT(*) as count
                    FROM financial_events
                    {where_clause}
                    GROUP BY event_type
                    ORDER BY count DESC
                """

                cursor.execute(type_query, params)
                type_breakdown = {row['event_type']: row['count'] for row in cursor.fetchall()}
                stats['by_event_type'] = type_breakdown

                return stats

        except Exception as e:
            logger.error(f"Error getting event statistics: {e}")
            return {}

    def search_events_by_keywords(self,
                                keywords: List[str],
                                start_date: Optional[date] = None,
                                end_date: Optional[date] = None,
                                limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search events by keywords.

        Args:
            keywords: List of keywords to search for
            start_date: Optional start date filter
            end_date: Optional end date filter
            limit: Maximum number of results

        Returns:
            List of matching events
        """
        try:
            self._ensure_connection()

            where_conditions = ["keywords && %s"]  # Array overlap operator
            params = [keywords]

            if start_date and end_date:
                where_conditions.append("event_date BETWEEN %s AND %s")
                params.extend([start_date, end_date])

            query = f"""
                SELECT event_id, event_date, event_datetime, source, event_type, importance,
                       title, description, keywords, created_at
                FROM financial_events
                WHERE {' AND '.join(where_conditions)}
                ORDER BY event_datetime DESC
                LIMIT %s
            """
            params.append(limit)

            with self.connection.cursor(cursor_factory=psycopg2.extras.DictCursor) as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()

                events = [dict(row) for row in results]
                logger.info(f"Found {len(events)} events matching keywords: {keywords}")
                return events

        except Exception as e:
            logger.error(f"Error searching events: {e}")
            return []

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("PostgreSQL connection closed")


def create_events_postgres_manager() -> EventsPostgresManager:
    """
    Factory function to create EventsPostgresManager with environment variables.

    Returns:
        Configured EventsPostgresManager instance
    """
    return EventsPostgresManager(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT', '5432')),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )