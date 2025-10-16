"""
Test script for the Market Encoder.
Tests S&P 500 data fetching, processing, and embedding storage.
"""

import logging
import sys
import os
from datetime import datetime

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from market_encoder.encoder import MarketEncoder

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_market_encoder():
    """Test the complete market encoder pipeline."""
    try:
        logger.info("Starting Market Encoder test")

        # Initialize encoder
        encoder = MarketEncoder(chroma_db_path="./test_chroma_db")

        # Test data fetching
        logger.info("Testing S&P 500 data fetching...")
        data = encoder.fetch_sp500_data(days_back=30)
        logger.info(f"Fetched {len(data)} days of data")
        logger.info(f"Date range: {data.index.min()} to {data.index.max()}")
        logger.info(f"Latest close: ${data['close'].iloc[-1]:.2f}")

        # Test data processing
        logger.info("Testing data processing...")
        processed_data = encoder.process_daily_data(data)
        logger.info(f"Processed {len(processed_data)} days")

        if processed_data:
            # Show sample narrative
            latest = processed_data[-1]
            logger.info(f"Sample narrative: {latest['narrative']}")

        # Test embedding storage
        logger.info("Testing embedding storage...")
        encoder.store_embeddings(processed_data)

        # Test collection stats
        stats = encoder.get_collection_stats()
        logger.info(f"Collection stats: {stats}")

        # Test querying
        logger.info("Testing market condition queries...")
        query_results = encoder.query_similar_market_conditions(
            "high volatility market decline",
            n_results=3
        )
        logger.info(f"{query_results}")
        logger.info(f"Query returned {query_results['count']} results")

        # Test daily update
        logger.info("Testing daily update process...")
        update_result = encoder.run_daily_update()
        logger.info(f"Daily update result: {update_result['status']}")

        logger.info("All tests completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_market_encoder()
    if success:
        print("✅ Market Encoder test passed!")
    else:
        print("❌ Market Encoder test failed!")
        sys.exit(1)