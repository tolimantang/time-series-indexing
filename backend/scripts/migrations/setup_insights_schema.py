#!/usr/bin/env python3
"""
Simple script to create the astrological insights database schema.
Run this first before running the batch analysis.
"""

import os
import sys
import logging
import psycopg2

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Create the database schema for astrological insights."""
    logger.info("🗄️ Setting up astrological insights database schema")

    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
    }

    # Check required environment variables
    missing_vars = [k for k, v in db_config.items() if not v]
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {missing_vars}")
        logger.info("Please set: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD")
        return 1

    logger.info(f"📡 Connecting to database: {db_config['host']}/{db_config['database']}")

    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        # Create astrological_insights table
        logger.info("📊 Creating astrological_insights table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS astrological_insights (
                id SERIAL PRIMARY KEY,
                insight_type VARCHAR(50) NOT NULL,
                category VARCHAR(50) NOT NULL,
                pattern_name VARCHAR(100) NOT NULL,
                description TEXT NOT NULL,
                confidence_score DOUBLE PRECISION,
                success_rate DOUBLE PRECISION,
                avg_profit DOUBLE PRECISION,
                trade_count INTEGER,
                evidence JSONB,
                claude_analysis TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_astrological_insights_category
            ON astrological_insights(category);
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_astrological_insights_confidence
            ON astrological_insights(confidence_score DESC);
        """)

        # Create daily_astrological_conditions table
        logger.info("🌟 Creating daily_astrological_conditions table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_astrological_conditions (
                id SERIAL PRIMARY KEY,
                trade_date DATE NOT NULL UNIQUE,
                planetary_positions JSONB NOT NULL,
                major_aspects JSONB,
                lunar_phase_name VARCHAR(50),
                lunar_phase_angle DOUBLE PRECISION,
                significant_events TEXT[],
                daily_score DOUBLE PRECISION,
                market_outlook TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_daily_astro_conditions_date
            ON daily_astrological_conditions(trade_date);
        """)

        # Create daily_trading_recommendations table
        logger.info("🎯 Creating daily_trading_recommendations table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_trading_recommendations (
                id SERIAL PRIMARY KEY,
                recommendation_date DATE NOT NULL,
                symbol VARCHAR(25) NOT NULL,
                recommendation_type VARCHAR(20) NOT NULL,
                confidence DOUBLE PRECISION NOT NULL,
                astrological_reasoning TEXT,
                supporting_insights INTEGER[],
                target_price DOUBLE PRECISION,
                stop_loss DOUBLE PRECISION,
                holding_period_days INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                UNIQUE(recommendation_date, symbol, recommendation_type)
            );
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_daily_recommendations_date
            ON daily_trading_recommendations(recommendation_date);
        """)

        conn.commit()

        # Verify tables were created
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('astrological_insights', 'daily_astrological_conditions', 'daily_trading_recommendations')
            ORDER BY table_name;
        """)

        tables = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        logger.info(f"✅ Database schema created successfully!")
        logger.info(f"📋 Tables created: {', '.join(tables)}")

        # Show next steps
        print("\n🎯 Next Steps:")
        print("1. Run batch analysis: python3 scripts/llm_analysis/run_batch_analysis.py")
        print("2. Calculate daily conditions: python3 scripts/llm_analysis/run_daily_conditions.py")
        print("3. Generate recommendations: python3 scripts/llm_analysis/run_daily_recommendations.py")
        print("\n📊 Monitor with SQL:")
        print("SELECT COUNT(*) FROM astrological_insights;")
        print("SELECT COUNT(*) FROM daily_astrological_conditions;")
        print("SELECT COUNT(*) FROM daily_trading_recommendations;")

        return 0

    except psycopg2.Error as e:
        logger.error(f"❌ Database error: {e}")
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())