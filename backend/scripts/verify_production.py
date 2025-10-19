#!/usr/bin/env python3
"""
Production verification script for ChromaDB persistence.
Verifies that data persists across container restarts.
"""

import os
import sys
import time
import logging
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from market_encoder.encoder import MarketEncoder

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def verify_persistence(data_path: str):
    """Verify ChromaDB persistence by creating, storing, and retrieving data."""

    logger.info("🔍 Starting ChromaDB persistence verification")

    # Test 1: Initialize and store data
    logger.info("📊 Test 1: Storing initial data...")
    encoder1 = MarketEncoder(chroma_db_path=data_path)

    # Get initial stats
    initial_stats = encoder1.get_collection_stats()
    initial_count = initial_stats.get('total_records', 0)
    logger.info(f"Initial record count: {initial_count}")

    # Run update to ensure we have recent data
    if initial_count == 0:
        logger.info("No existing data, running initial update...")
        result = encoder1.run_daily_update()
        if result['status'] != 'success':
            logger.error("Failed to store initial data")
            return False

        new_stats = encoder1.get_collection_stats()
        new_count = new_stats.get('total_records', 0)
        logger.info(f"Stored {new_count} records successfully")
    else:
        new_count = initial_count
        logger.info("Using existing data for persistence test")

    # Test 2: Simulate container restart by creating new encoder instance
    logger.info("🔄 Test 2: Simulating container restart...")
    del encoder1  # Clean up first instance
    time.sleep(1)

    # Create new encoder instance (simulates container restart)
    encoder2 = MarketEncoder(chroma_db_path=data_path)

    # Verify data persisted
    persisted_stats = encoder2.get_collection_stats()
    persisted_count = persisted_stats.get('total_records', 0)

    logger.info(f"After restart - record count: {persisted_count}")

    if persisted_count == new_count:
        logger.info("✅ Data persistence verified!")
    else:
        logger.error(f"❌ Data persistence failed! Expected {new_count}, got {persisted_count}")
        return False

    # Test 3: Verify semantic search works on persisted data
    logger.info("🔍 Test 3: Testing semantic search on persisted data...")
    results = encoder2.query_similar_market_conditions("market volatility", n_results=3)

    if results['count'] > 0:
        logger.info(f"✅ Semantic search working: found {results['count']} similar conditions")

        # Show sample result
        if results['results'] and results['results']['documents']:
            sample_doc = results['results']['documents'][0][0]
            sample_meta = results['results']['metadatas'][0][0]
            logger.info(f"Sample result: {sample_meta['date']} - {sample_doc[:100]}...")
    else:
        logger.warning("⚠️  Semantic search returned no results")

    # Test 4: Verify file structure
    logger.info("📁 Test 4: Verifying file structure...")
    if os.path.exists(data_path):
        files = os.listdir(data_path)
        logger.info(f"ChromaDB files: {files}")

        sqlite_file = os.path.join(data_path, "chroma.sqlite3")
        if os.path.exists(sqlite_file):
            size = os.path.getsize(sqlite_file)
            logger.info(f"✅ SQLite database exists: {size} bytes")
        else:
            logger.error("❌ SQLite database missing")
            return False
    else:
        logger.error(f"❌ ChromaDB directory not found: {data_path}")
        return False

    logger.info("🎉 All persistence tests passed!")
    return True


def main():
    # Use production-like path
    data_path = os.getenv('CHROMA_DB_PATH', './production_chroma_data')

    logger.info(f"Using ChromaDB path: {data_path}")

    try:
        success = verify_persistence(data_path)
        if success:
            print("✅ ChromaDB persistence verification PASSED")
            sys.exit(0)
        else:
            print("❌ ChromaDB persistence verification FAILED")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Verification failed with error: {e}")
        print("❌ ChromaDB persistence verification FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()