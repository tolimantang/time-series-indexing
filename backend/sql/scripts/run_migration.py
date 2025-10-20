#!/usr/bin/env python3
"""
SQL Migration Runner
Runs SQL migrations in order and tracks completed migrations.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from pathlib import Path

# Add parent directory to path to import database config
sys.path.append(str(Path(__file__).parent.parent.parent / "backend"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MigrationRunner:
    def __init__(self, db_config=None):
        """Initialize with database configuration."""
        if db_config is None:
            # Default config - adjust as needed
            self.db_config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': os.getenv('DB_PORT', '5432'),
                'database': os.getenv('DB_NAME', 'astrofinancial'),
                'user': os.getenv('DB_USER', 'postgres'),
                'password': os.getenv('DB_PASSWORD', 'password'),
            }
        else:
            self.db_config = db_config

        self.migrations_dir = Path(__file__).parent.parent / "migrations"

    def get_connection(self):
        """Get database connection."""
        return psycopg2.connect(**self.db_config)

    def ensure_migrations_table(self):
        """Ensure migrations tracking table exists."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        id SERIAL PRIMARY KEY,
                        migration_name VARCHAR(255) UNIQUE NOT NULL,
                        executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                """)
                conn.commit()
                logger.info("Migrations table ready")

    def get_completed_migrations(self):
        """Get list of completed migrations."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT migration_name FROM schema_migrations ORDER BY migration_name")
                return [row[0] for row in cur.fetchall()]

    def get_pending_migrations(self):
        """Get list of pending migrations."""
        completed = set(self.get_completed_migrations())
        all_migrations = []

        for file_path in sorted(self.migrations_dir.glob("*.sql")):
            migration_name = file_path.stem
            if migration_name not in completed:
                all_migrations.append(file_path)

        return all_migrations

    def run_migration(self, migration_path):
        """Run a single migration."""
        migration_name = migration_path.stem
        logger.info(f"Running migration: {migration_name}")

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                # Read and execute migration
                with open(migration_path, 'r') as f:
                    migration_sql = f.read()

                try:
                    cur.execute(migration_sql)

                    # Record migration as completed
                    cur.execute(
                        "INSERT INTO schema_migrations (migration_name) VALUES (%s)",
                        (migration_name,)
                    )

                    conn.commit()
                    logger.info(f"Migration {migration_name} completed successfully")

                except Exception as e:
                    conn.rollback()
                    logger.error(f"Migration {migration_name} failed: {e}")
                    raise

    def run_all_pending(self):
        """Run all pending migrations."""
        self.ensure_migrations_table()
        pending = self.get_pending_migrations()

        if not pending:
            logger.info("No pending migrations")
            return

        logger.info(f"Found {len(pending)} pending migrations")

        for migration_path in pending:
            self.run_migration(migration_path)

        logger.info("All migrations completed")

    def status(self):
        """Show migration status."""
        self.ensure_migrations_table()
        completed = self.get_completed_migrations()
        pending = self.get_pending_migrations()

        print("\n=== Migration Status ===")
        print(f"Completed migrations: {len(completed)}")
        for migration in completed:
            print(f"  ✓ {migration}")

        print(f"\nPending migrations: {len(pending)}")
        for migration_path in pending:
            print(f"  ○ {migration_path.stem}")

        print()


def main():
    """Main CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(description="Run SQL migrations")
    parser.add_argument('command', choices=['run', 'status'],
                       help='Command to execute')

    args = parser.parse_args()

    runner = MigrationRunner()

    if args.command == 'run':
        runner.run_all_pending()
    elif args.command == 'status':
        runner.status()


if __name__ == "__main__":
    main()