#!/usr/bin/env python3
"""
Database migration script for AstroFinancial
"""
import os
import sys
import psycopg2
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration(database_url: str, migration_file: Path):
    """Run a single migration file"""
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()

        logger.info(f"Running migration: {migration_file.name}")

        with open(migration_file, 'r') as f:
            migration_sql = f.read()

        cursor.execute(migration_sql)
        logger.info(f"✓ Migration completed: {migration_file.name}")

        cursor.close()
        conn.close()

    except Exception as e:
        logger.error(f"✗ Migration failed: {migration_file.name} - {e}")
        raise

def main():
    """Run all pending migrations"""
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)

    # Find migrations directory
    migrations_dir = Path(__file__).parent.parent / "migrations"
    if not migrations_dir.exists():
        logger.error(f"Migrations directory not found: {migrations_dir}")
        sys.exit(1)

    # Get all migration files
    migration_files = sorted(migrations_dir.glob("*.sql"))
    if not migration_files:
        logger.info("No migration files found")
        return

    logger.info(f"Found {len(migration_files)} migration files")

    # Run each migration
    for migration_file in migration_files:
        run_migration(database_url, migration_file)

    logger.info("✓ All migrations completed successfully")

if __name__ == "__main__":
    main()