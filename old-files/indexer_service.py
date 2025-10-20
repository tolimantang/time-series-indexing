#!/usr/bin/env python3
"""
Indexer Service: Batch processes astronomical + financial data
Stores to ChromaDB + PostgreSQL for querying
"""

import os
import sys
import psycopg2
import chromadb
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from dataclasses import asdict
import json

# Add project modules to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from astro_embedding_pipeline import AstroEmbeddingPipeline
from newsEncoder import NewsEncoder


class AstroFinancialIndexer:
    """
    Production indexer that processes astronomical + financial data
    and stores in both ChromaDB (embeddings) and PostgreSQL (structured)
    """

    def __init__(self,
                 pg_connection_string: Optional[str] = None,
                 chroma_persist_directory: Optional[str] = None):
        """Initialize indexer with database connections."""

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # Initialize PostgreSQL connection
        self.pg_connection_string = (pg_connection_string or
                                   os.getenv('POSTGRES_CONNECTION_STRING',
                                            'postgresql://localhost:5432/astro_financial'))
        self.pg_conn = None

        # Initialize ChromaDB
        chroma_dir = chroma_persist_directory or './chroma_data'
        self.chroma_client = chromadb.PersistentClient(path=chroma_dir)

        # Initialize processing pipelines
        self.astro_pipeline = AstroEmbeddingPipeline(chroma_client=self.chroma_client)
        self.news_encoder = NewsEncoder()

        self.logger.info("✓ Indexer initialized")

    def connect_postgres(self):
        """Connect to PostgreSQL database."""
        try:
            self.pg_conn = psycopg2.connect(self.pg_connection_string)
            self.pg_conn.autocommit = True
            self.logger.info("✓ Connected to PostgreSQL")
        except Exception as e:
            self.logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise

    def setup_database_schema(self):
        """Create necessary PostgreSQL tables if they don't exist."""
        if not self.pg_conn:
            self.connect_postgres()

        cursor = self.pg_conn.cursor()

        # Create tables based on our storage design
        schema_sql = """
        -- Core daily record linking all domains
        CREATE TABLE IF NOT EXISTS daily_records (
            date DATE PRIMARY KEY,
            created_at TIMESTAMP DEFAULT NOW(),
            data_quality_score DECIMAL(3,2),
            has_astronomical_data BOOLEAN DEFAULT FALSE,
            has_financial_data BOOLEAN DEFAULT FALSE,
            has_market_data BOOLEAN DEFAULT FALSE
        );

        -- Astronomical data (structured)
        CREATE TABLE IF NOT EXISTS astronomical_data (
            date DATE PRIMARY KEY REFERENCES daily_records(date),
            julian_day DECIMAL(12,6),

            -- Major planetary positions (degrees 0-360)
            sun_longitude DECIMAL(8,5),
            moon_longitude DECIMAL(8,5),
            mercury_longitude DECIMAL(8,5),
            venus_longitude DECIMAL(8,5),
            mars_longitude DECIMAL(8,5),
            jupiter_longitude DECIMAL(8,5),
            saturn_longitude DECIMAL(8,5),
            uranus_longitude DECIMAL(8,5),
            neptune_longitude DECIMAL(8,5),
            pluto_longitude DECIMAL(8,5),

            -- Key derived data
            lunar_phase DECIMAL(8,5),
            jupiter_sign VARCHAR(20),
            jupiter_degree_classification VARCHAR(10),
            moon_sign VARCHAR(20),

            -- Major aspects (JSON for flexibility)
            major_conjunctions JSONB,
            all_aspects JSONB,

            -- Raw data reference
            full_astro_data JSONB
        );

        -- Financial news data (structured)
        CREATE TABLE IF NOT EXISTS financial_news_data (
            date DATE PRIMARY KEY REFERENCES daily_records(date),

            -- Fed activity
            has_fed_events BOOLEAN DEFAULT FALSE,
            fed_action_type VARCHAR(50),
            fed_rate_change DECIMAL(4,2),
            fed_summary TEXT,

            -- Economic data
            major_economic_releases JSONB,
            economic_surprise_index DECIMAL(5,2),

            -- Market regime indicators
            market_regime VARCHAR(20),
            volatility_regime VARCHAR(20),

            -- Text summaries
            daily_summary TEXT,
            combined_summary TEXT,

            -- Raw data reference
            full_news_data JSONB
        );

        -- Create indexes for common queries
        CREATE INDEX IF NOT EXISTS idx_daily_records_date ON daily_records(date);
        CREATE INDEX IF NOT EXISTS idx_astro_jupiter_sign ON astronomical_data(jupiter_sign);
        CREATE INDEX IF NOT EXISTS idx_astro_major_conjunctions ON astronomical_data USING GIN(major_conjunctions);
        CREATE INDEX IF NOT EXISTS idx_financial_market_regime ON financial_news_data(market_regime);
        """

        cursor.execute(schema_sql)
        self.logger.info("✓ Database schema created/verified")

    def process_single_date(self, date: datetime) -> Dict[str, Any]:
        """Process astronomical + financial data for a single date."""
        date_str = date.strftime('%Y-%m-%d')

        try:
            # 1. Process astronomical data (includes ChromaDB storage)
            astro_result = self.astro_pipeline.process_date(date)
            astro_data = astro_result['astro_data']

            # 2. Process financial news data
            news_data = self.news_encoder.encode_date(date, include_market_data=True)

            # 3. Store in PostgreSQL
            self._store_postgresql_data(date, astro_data, news_data)

            return {
                'date': date_str,
                'status': 'success',
                'astro_processed': True,
                'financial_processed': True,
                'postgresql_stored': True,
                'chromadb_stored': True
            }

        except Exception as e:
            self.logger.error(f"Error processing {date_str}: {e}")
            return {
                'date': date_str,
                'status': 'error',
                'error': str(e)
            }

    def _store_postgresql_data(self, date: datetime, astro_data, news_data):
        """Store structured data in PostgreSQL."""
        if not self.pg_conn:
            self.connect_postgres()

        cursor = self.pg_conn.cursor()
        date_str = date.strftime('%Y-%m-%d')

        # Calculate data quality score
        quality_score = self._calculate_quality_score(astro_data, news_data)

        # Insert core daily record
        cursor.execute("""
            INSERT INTO daily_records (date, data_quality_score, has_astronomical_data, has_financial_data, has_market_data)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (date) DO UPDATE SET
                data_quality_score = EXCLUDED.data_quality_score,
                has_astronomical_data = EXCLUDED.has_astronomical_data,
                has_financial_data = EXCLUDED.has_financial_data,
                has_market_data = EXCLUDED.has_market_data
        """, (date_str, quality_score, True, True, bool(news_data.market_summary)))

        # Insert astronomical data
        positions = astro_data.positions
        jupiter_pos = positions.get('jupiter')
        moon_pos = positions.get('moon')

        # Prepare aspects data
        major_conjunctions = [
            {
                'planets': [a.planet1, a.planet2],
                'orb': float(a.orb),
                'exactness': 1.0 - (float(a.orb) / 10.0)
            }
            for a in astro_data.aspects
            if a.aspect_type == 'conjunction' and a.orb <= 8.0
        ]

        all_aspects_data = [
            {
                'planet1': a.planet1,
                'planet2': a.planet2,
                'aspect_type': a.aspect_type,
                'orb': float(a.orb),
                'applying': a.applying
            }
            for a in astro_data.aspects
        ]

        cursor.execute("""
            INSERT INTO astronomical_data (
                date, julian_day, sun_longitude, moon_longitude, mercury_longitude,
                venus_longitude, mars_longitude, jupiter_longitude, saturn_longitude,
                uranus_longitude, neptune_longitude, pluto_longitude,
                lunar_phase, jupiter_sign, jupiter_degree_classification, moon_sign,
                major_conjunctions, all_aspects, full_astro_data
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (date) DO UPDATE SET
                julian_day = EXCLUDED.julian_day,
                sun_longitude = EXCLUDED.sun_longitude,
                moon_longitude = EXCLUDED.moon_longitude,
                mercury_longitude = EXCLUDED.mercury_longitude,
                venus_longitude = EXCLUDED.venus_longitude,
                mars_longitude = EXCLUDED.mars_longitude,
                jupiter_longitude = EXCLUDED.jupiter_longitude,
                saturn_longitude = EXCLUDED.saturn_longitude,
                uranus_longitude = EXCLUDED.uranus_longitude,
                neptune_longitude = EXCLUDED.neptune_longitude,
                pluto_longitude = EXCLUDED.pluto_longitude,
                lunar_phase = EXCLUDED.lunar_phase,
                jupiter_sign = EXCLUDED.jupiter_sign,
                jupiter_degree_classification = EXCLUDED.jupiter_degree_classification,
                moon_sign = EXCLUDED.moon_sign,
                major_conjunctions = EXCLUDED.major_conjunctions,
                all_aspects = EXCLUDED.all_aspects,
                full_astro_data = EXCLUDED.full_astro_data
        """, (
            date_str, float(astro_data.julian_day),
            float(positions['sun'].longitude), float(positions['moon'].longitude),
            float(positions['mercury'].longitude), float(positions['venus'].longitude),
            float(positions['mars'].longitude), float(positions['jupiter'].longitude),
            float(positions['saturn'].longitude), float(positions['uranus'].longitude),
            float(positions['neptune'].longitude), float(positions['pluto'].longitude),
            float(astro_data.lunar_phase),
            jupiter_pos.sign if jupiter_pos else None,
            jupiter_pos.degree_classification if jupiter_pos else None,
            moon_pos.sign if moon_pos else None,
            json.dumps(major_conjunctions),
            json.dumps(all_aspects_data),
            json.dumps(asdict(astro_data), default=str)
        ))

        # Insert financial news data
        cursor.execute("""
            INSERT INTO financial_news_data (
                date, has_fed_events, fed_summary, market_regime,
                daily_summary, combined_summary, full_news_data
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (date) DO UPDATE SET
                has_fed_events = EXCLUDED.has_fed_events,
                fed_summary = EXCLUDED.fed_summary,
                market_regime = EXCLUDED.market_regime,
                daily_summary = EXCLUDED.daily_summary,
                combined_summary = EXCLUDED.combined_summary,
                full_news_data = EXCLUDED.full_news_data
        """, (
            date_str,
            len(news_data.fed_events) > 0,
            news_data.get_fed_summary() if news_data.fed_events else None,
            news_data.market_regime,
            news_data.daily_summary,
            news_data.get_combined_summary(),
            json.dumps(asdict(news_data), default=str)
        ))

    def _calculate_quality_score(self, astro_data, news_data) -> float:
        """Calculate data quality score (0.0-1.0)."""
        score = 0.0

        # Astronomical data quality (50% of total)
        if astro_data and astro_data.positions:
            score += 0.3  # Base score for having astro data
            if len(astro_data.aspects) > 10:
                score += 0.1  # Bonus for rich aspect data
            if astro_data.houses:
                score += 0.1  # Bonus for house data

        # Financial data quality (50% of total)
        if news_data:
            score += 0.2  # Base score for having financial data
            if news_data.fed_events:
                score += 0.1  # Bonus for Fed events
            if news_data.economic_data:
                score += 0.1  # Bonus for economic data
            if news_data.market_summary:
                score += 0.1  # Bonus for market data

        return min(1.0, score)

    def batch_index(self, start_date: datetime, end_date: datetime,
                   batch_size: int = 30) -> Dict[str, Any]:
        """Batch process multiple dates."""
        self.logger.info(f"Starting batch index from {start_date.date()} to {end_date.date()}")

        # Ensure database setup
        if not self.pg_conn:
            self.setup_database_schema()

        results = []
        current_date = start_date
        processed_count = 0
        error_count = 0

        while current_date <= end_date:
            batch_dates = []

            # Collect batch of dates
            for _ in range(batch_size):
                if current_date <= end_date:
                    batch_dates.append(current_date)
                    current_date += timedelta(days=1)
                else:
                    break

            # Process batch
            self.logger.info(f"Processing batch: {len(batch_dates)} dates")

            for date in batch_dates:
                result = self.process_single_date(date)
                results.append(result)

                if result['status'] == 'success':
                    processed_count += 1
                else:
                    error_count += 1

                # Progress logging
                if processed_count % 100 == 0:
                    self.logger.info(f"Progress: {processed_count} processed, {error_count} errors")

        summary = {
            'total_processed': processed_count,
            'total_errors': error_count,
            'success_rate': processed_count / (processed_count + error_count) if (processed_count + error_count) > 0 else 0,
            'date_range': f"{start_date.date()} to {end_date.date()}",
            'results': results
        }

        self.logger.info(f"✓ Batch indexing complete: {processed_count} successful, {error_count} errors")
        return summary

    def get_indexing_stats(self) -> Dict[str, Any]:
        """Get current indexing statistics."""
        if not self.pg_conn:
            self.connect_postgres()

        cursor = self.pg_conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total_dates,
                COUNT(*) FILTER (WHERE has_astronomical_data) as astro_dates,
                COUNT(*) FILTER (WHERE has_financial_data) as financial_dates,
                MIN(date) as earliest_date,
                MAX(date) as latest_date,
                AVG(data_quality_score) as avg_quality
            FROM daily_records
        """)

        result = cursor.fetchone()

        # Get ChromaDB stats
        try:
            astro_detailed = self.astro_pipeline.astro_detailed
            astro_patterns = self.astro_pipeline.astro_patterns

            chroma_stats = {
                'astro_detailed_count': astro_detailed.count(),
                'astro_patterns_count': astro_patterns.count()
            }
        except:
            chroma_stats = {'error': 'Could not retrieve ChromaDB stats'}

        return {
            'postgresql': {
                'total_dates': result[0] if result else 0,
                'astronomical_dates': result[1] if result else 0,
                'financial_dates': result[2] if result else 0,
                'earliest_date': str(result[3]) if result and result[3] else None,
                'latest_date': str(result[4]) if result and result[4] else None,
                'avg_quality_score': float(result[5]) if result and result[5] else 0
            },
            'chromadb': chroma_stats
        }


def main():
    """Demo indexer usage."""
    print("Astro-Financial Indexer Service")
    print("=" * 40)

    # Initialize indexer
    indexer = AstroFinancialIndexer()

    # Setup database
    print("\n1. Setting up database...")
    indexer.setup_database_schema()

    # Index last 30 days as demo
    print("\n2. Indexing sample data (last 30 days)...")
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30)

    results = indexer.batch_index(start_date, end_date, batch_size=5)

    print(f"\n3. Indexing Results:")
    print(f"   ✓ Processed: {results['total_processed']}")
    print(f"   ✗ Errors: {results['total_errors']}")
    print(f"   Success Rate: {results['success_rate']:.1%}")

    # Get stats
    print("\n4. Current Index Statistics:")
    stats = indexer.get_indexing_stats()
    print(f"   PostgreSQL: {stats['postgresql']['total_dates']} total dates")
    print(f"   ChromaDB: {stats['chromadb']}")


if __name__ == "__main__":
    main()