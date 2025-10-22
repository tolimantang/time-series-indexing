#!/usr/bin/env python3
"""
Simple database setup script that handles dependencies more gracefully.
"""

import sys
import subprocess

def install_dependencies():
    """Install required dependencies."""
    try:
        import psycopg2
        print("✅ psycopg2 already installed")
        return True
    except ImportError:
        print("📦 Installing psycopg2-binary...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
            print("✅ psycopg2-binary installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install psycopg2-binary: {e}")
            return False

def create_schema():
    """Create database schema."""
    try:
        import psycopg2
        import json
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

    # Database configuration - hardcoded for simplicity
    db_config = {
        'host': 'financial-postgres.cvkuccacyqwr.us-west-1.rds.amazonaws.com',
        'port': '5432',
        'database': 'financial_postgres',
        'user': 'postgres',
        'password': 'Ty009085'
    }

    print(f"📡 Connecting to database: {db_config['host']}/{db_config['database']}")

    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()

        print("📊 Creating astrological_insights table...")
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

        print("🌟 Creating daily_astrological_conditions table...")
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

        print("🎯 Creating daily_trading_recommendations table...")
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

        conn.commit()

        # Verify tables
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('astrological_insights', 'daily_astrological_conditions', 'daily_trading_recommendations')
            ORDER BY table_name;
        """)

        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        print(f"✅ Database schema created successfully!")
        print(f"📋 Tables created: {', '.join(tables)}")

        return True

    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def main():
    """Main function."""
    print("🗄️ Setting up astrological insights database schema")

    # Install dependencies
    if not install_dependencies():
        return 1

    # Create schema
    if not create_schema():
        return 1

    print("\n🎯 Database setup complete!")
    print("Next steps:")
    print("1. Run: python3 scripts/llm_analysis/test_local_analysis.py")
    print("2. Set API key: export ANTHROPIC_API_KEY='your-key'")
    print("3. Run batch analysis: python3 scripts/llm_analysis/run_batch_analysis.py")

    return 0

if __name__ == "__main__":
    sys.exit(main())