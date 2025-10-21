"""
Data Access Layer for Astrological Data
Handles PostgreSQL storage and retrieval of astrological calculations.
"""

import psycopg2
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import logging
import os
import json

from ..models.data_models import AstronomicalData, PlanetaryPosition, Aspect

logger = logging.getLogger(__name__)


class AstroDataAccess:
    """Handles astrological data storage and retrieval from PostgreSQL."""

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
            logger.info("✅ Astrological database connection successful")
        except Exception as e:
            logger.error(f"❌ Astrological database connection failed: {e}")
            raise

    def create_astro_tables(self) -> None:
        """Create astrological data tables if they don't exist."""
        conn = None
        cursor = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # Main astrological data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS astrological_data (
                    id SERIAL PRIMARY KEY,
                    trade_date DATE NOT NULL UNIQUE,
                    julian_day DOUBLE PRECISION NOT NULL,
                    location VARCHAR(50) DEFAULT 'universal',

                    -- Planetary positions (JSON for flexibility)
                    planetary_positions JSONB,

                    -- Major aspects (JSON array)
                    aspects JSONB,

                    -- Lunar phase
                    lunar_phase DOUBLE PRECISION,
                    lunar_phase_name VARCHAR(50),

                    -- House data (if calculated)
                    house_data JSONB,

                    -- Significant events
                    significant_events TEXT[],

                    -- Natural language description
                    daily_description TEXT,
                    market_interpretation TEXT,

                    -- Metadata
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """)

            # Index for performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_astrological_data_date
                ON astrological_data(trade_date)
            """)

            # Quick lookup table for planetary positions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_planetary_positions (
                    id SERIAL PRIMARY KEY,
                    trade_date DATE NOT NULL,
                    planet VARCHAR(20) NOT NULL,
                    longitude DOUBLE PRECISION NOT NULL,
                    latitude DOUBLE PRECISION,
                    sign VARCHAR(20) NOT NULL,
                    degree_in_sign DOUBLE PRECISION NOT NULL,
                    speed DOUBLE PRECISION,
                    is_retrograde BOOLEAN DEFAULT FALSE,

                    UNIQUE(trade_date, planet)
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_daily_planetary_date_planet
                ON daily_planetary_positions(trade_date, planet)
            """)

            # Aspects table for detailed queries
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_aspects (
                    id SERIAL PRIMARY KEY,
                    trade_date DATE NOT NULL,
                    planet1 VARCHAR(20) NOT NULL,
                    planet2 VARCHAR(20) NOT NULL,
                    aspect_type VARCHAR(20) NOT NULL,
                    orb DOUBLE PRECISION NOT NULL,
                    exactness DOUBLE PRECISION NOT NULL,
                    angle DOUBLE PRECISION NOT NULL,
                    applying_separating VARCHAR(20),

                    INDEX(trade_date),
                    INDEX(trade_date, aspect_type)
                )
            """)

            conn.commit()
            logger.info("✅ Astrological tables created successfully")

        except Exception as e:
            logger.error(f"❌ Error creating astrological tables: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def store_astrological_data(
        self,
        astro_data: AstronomicalData,
        daily_description: str = None,
        market_interpretation: str = None
    ) -> None:
        """Store complete astrological data for a date."""
        conn = None
        cursor = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            trade_date = astro_data.date.date()

            # Prepare planetary positions for JSON storage
            positions_json = {
                planet: {
                    'longitude': pos.longitude,
                    'latitude': pos.latitude,
                    'distance': pos.distance,
                    'speed': pos.speed,
                    'sign': pos.sign,
                    'degree_in_sign': pos.degree_in_sign,
                    'degree_classification': pos.degree_classification,
                    'house': pos.house
                }
                for planet, pos in astro_data.positions.items()
            }

            # Prepare aspects for JSON storage
            aspects_json = [
                {
                    'planet1': aspect.planet1,
                    'planet2': aspect.planet2,
                    'aspect_type': aspect.aspect_type,
                    'orb': aspect.orb,
                    'exactness': aspect.exactness,
                    'angle': aspect.angle,
                    'applying_separating': aspect.applying_separating
                }
                for aspect in astro_data.aspects
            ]

            # Prepare house data
            house_data_json = None
            if astro_data.houses:
                house_data_json = {
                    'system': astro_data.houses.system,
                    'location': astro_data.houses.location,
                    'latitude': astro_data.houses.latitude,
                    'longitude': astro_data.houses.longitude,
                    'house_cusps': astro_data.houses.house_cusps,
                    'ascendant': astro_data.houses.ascendant,
                    'midheaven': astro_data.houses.midheaven,
                    'planetary_houses': astro_data.houses.planetary_houses
                }

            # Determine lunar phase name
            lunar_phase_name = self._get_lunar_phase_name(astro_data.lunar_phase) if astro_data.lunar_phase else None

            # Insert main record
            cursor.execute("""
                INSERT INTO astrological_data (
                    trade_date, julian_day, location, planetary_positions, aspects,
                    lunar_phase, lunar_phase_name, house_data, significant_events,
                    daily_description, market_interpretation
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (trade_date) DO UPDATE SET
                    julian_day = EXCLUDED.julian_day,
                    location = EXCLUDED.location,
                    planetary_positions = EXCLUDED.planetary_positions,
                    aspects = EXCLUDED.aspects,
                    lunar_phase = EXCLUDED.lunar_phase,
                    lunar_phase_name = EXCLUDED.lunar_phase_name,
                    house_data = EXCLUDED.house_data,
                    significant_events = EXCLUDED.significant_events,
                    daily_description = EXCLUDED.daily_description,
                    market_interpretation = EXCLUDED.market_interpretation,
                    updated_at = NOW()
            """, (
                trade_date,
                astro_data.julian_day,
                astro_data.location,
                json.dumps(positions_json),
                json.dumps(aspects_json),
                astro_data.lunar_phase,
                lunar_phase_name,
                json.dumps(house_data_json) if house_data_json else None,
                astro_data.significant_events,
                daily_description,
                market_interpretation
            ))

            # Store individual planetary positions
            for planet, position in astro_data.positions.items():
                cursor.execute("""
                    INSERT INTO daily_planetary_positions (
                        trade_date, planet, longitude, latitude, sign, degree_in_sign,
                        speed, is_retrograde
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (trade_date, planet) DO UPDATE SET
                        longitude = EXCLUDED.longitude,
                        latitude = EXCLUDED.latitude,
                        sign = EXCLUDED.sign,
                        degree_in_sign = EXCLUDED.degree_in_sign,
                        speed = EXCLUDED.speed,
                        is_retrograde = EXCLUDED.is_retrograde
                """, (
                    trade_date,
                    planet,
                    position.longitude,
                    position.latitude,
                    position.sign,
                    position.degree_in_sign,
                    position.speed,
                    position.speed < 0
                ))

            # Store individual aspects
            cursor.execute("DELETE FROM daily_aspects WHERE trade_date = %s", (trade_date,))
            for aspect in astro_data.aspects:
                cursor.execute("""
                    INSERT INTO daily_aspects (
                        trade_date, planet1, planet2, aspect_type, orb, exactness,
                        angle, applying_separating
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    trade_date,
                    aspect.planet1,
                    aspect.planet2,
                    aspect.aspect_type,
                    aspect.orb,
                    aspect.exactness,
                    aspect.angle,
                    aspect.applying_separating
                ))

            conn.commit()
            logger.info(f"✅ Stored astrological data for {trade_date}")

        except Exception as e:
            logger.error(f"❌ Error storing astrological data for {astro_data.date}: {e}")
            if conn:
                conn.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def get_astrological_data_for_date(self, target_date: date) -> Optional[Dict[str, Any]]:
        """Retrieve astrological data for a specific date."""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT trade_date, julian_day, location, planetary_positions, aspects,
                       lunar_phase, lunar_phase_name, house_data, significant_events,
                       daily_description, market_interpretation
                FROM astrological_data
                WHERE trade_date = %s
            """, (target_date,))

            result = cursor.fetchone()
            if result:
                return {
                    'trade_date': result[0],
                    'julian_day': result[1],
                    'location': result[2],
                    'planetary_positions': result[3],
                    'aspects': result[4],
                    'lunar_phase': result[5],
                    'lunar_phase_name': result[6],
                    'house_data': result[7],
                    'significant_events': result[8],
                    'daily_description': result[9],
                    'market_interpretation': result[10]
                }
            return None

        except Exception as e:
            logger.error(f"Error retrieving astrological data for {target_date}: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def get_astrological_data_for_trading_period(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Retrieve astrological data for a trading period."""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT trade_date, daily_description, market_interpretation,
                       significant_events, lunar_phase_name
                FROM astrological_data
                WHERE trade_date BETWEEN %s AND %s
                ORDER BY trade_date
            """, (start_date, end_date))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'trade_date': row[0],
                    'daily_description': row[1],
                    'market_interpretation': row[2],
                    'significant_events': row[3],
                    'lunar_phase_name': row[4]
                })

            return results

        except Exception as e:
            logger.error(f"Error retrieving trading period data: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def _get_lunar_phase_name(self, lunar_phase: float) -> str:
        """Convert lunar phase degrees to name."""
        phase = lunar_phase % 360

        if 0 <= phase < 45 or 315 <= phase < 360:
            return "New Moon"
        elif 45 <= phase < 135:
            return "Waxing Moon"
        elif 135 <= phase < 225:
            return "Full Moon"
        elif 225 <= phase < 315:
            return "Waning Moon"
        else:
            return "Unknown"

    def get_missing_dates(self, start_date: date, end_date: date) -> List[date]:
        """Get list of dates that don't have astrological data."""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT date_series.date
                FROM generate_series(%s::date, %s::date, interval '1 day') AS date_series(date)
                LEFT JOIN astrological_data ON date_series.date = astrological_data.trade_date
                WHERE astrological_data.trade_date IS NULL
                ORDER BY date_series.date
            """, (start_date, end_date))

            return [row[0] for row in cursor.fetchall()]

        except Exception as e:
            logger.error(f"Error finding missing dates: {e}")
            raise
        finally:
            if conn:
                conn.close()