#!/usr/bin/env python3
"""
Setup database schema and run batch analysis locally.
This script creates the required tables and then runs the batch analysis.
"""

import os
import sys
import logging
import psycopg2
from pathlib import Path

# Add backend/src to path for imports
backend_src = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(backend_src))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_database_schema():
    """Create the required database tables."""
    logger.info("🗄️ Creating database schema...")

    db_config = {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
    }

    # Check if all required env vars are set
    missing_vars = [k for k, v in db_config.items() if not v]
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {missing_vars}")
        return False

    schema_sql = """
    -- Create astrological insights table
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

    CREATE INDEX IF NOT EXISTS idx_astrological_insights_category ON astrological_insights(category);
    CREATE INDEX IF NOT EXISTS idx_astrological_insights_confidence ON astrological_insights(confidence_score DESC);

    -- Create daily conditions table
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

    CREATE INDEX IF NOT EXISTS idx_daily_astro_conditions_date ON daily_astrological_conditions(trade_date);

    -- Create daily recommendations table
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

    CREATE INDEX IF NOT EXISTS idx_daily_recommendations_date ON daily_trading_recommendations(recommendation_date);
    """

    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute(schema_sql)
        conn.commit()

        # Check if tables were created
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('astrological_insights', 'daily_astrological_conditions', 'daily_trading_recommendations')
        """)

        tables = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        logger.info(f"✅ Database schema ready. Tables: {', '.join(tables)}")
        return True

    except Exception as e:
        logger.error(f"❌ Error creating database schema: {e}")
        return False


def run_batch_analysis():
    """Run the batch analysis."""
    logger.info("🚀 Starting batch analysis...")

    try:
        from llm_analyzer.core.analyzer import OilTradingAstroAnalyzer

        # Initialize analyzer
        analyzer = OilTradingAstroAnalyzer()

        # Run batch analysis
        summary = analyzer.run_batch_analysis_all_opportunities(batch_size=25)  # Smaller batches for local testing

        if 'error' in summary:
            logger.error(f"❌ Batch analysis failed: {summary['error']}")
            return False

        logger.info(f"✅ Batch analysis completed successfully!")
        logger.info(f"📊 Processed {summary['opportunities_analyzed']} opportunities")
        logger.info(f"💡 Extracted {summary['insights_extracted']} insights")

        return True

    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("Make sure you're running from the backend directory and the LLM analyzer is properly set up")
        return False
    except Exception as e:
        logger.error(f"❌ Error in batch analysis: {e}")
        return False


def main():
    """Main function."""
    logger.info("🌟 Setting up and running comprehensive batch analysis")

    # Step 1: Create database schema
    if not create_database_schema():
        logger.error("❌ Failed to create database schema")
        return 1

    # Step 2: Check if Claude API key is set
    if not os.getenv('ANTHROPIC_API_KEY'):
        logger.error("❌ ANTHROPIC_API_KEY environment variable not set")
        logger.info("Please set your Claude API key: export ANTHROPIC_API_KEY='your-api-key'")
        return 1

    # Step 3: Run batch analysis
    if not run_batch_analysis():
        logger.error("❌ Batch analysis failed")
        return 1

    logger.info("🎯 Setup and batch analysis completed successfully!")
    logger.info("Next steps:")
    logger.info("1. Check the astrological_insights table for extracted patterns")
    logger.info("2. Run daily conditions: python3 scripts/llm_analysis/run_daily_conditions.py")
    logger.info("3. Generate recommendations: python3 scripts/llm_analysis/run_daily_recommendations.py")

    return 0


if __name__ == "__main__":
    sys.exit(main())