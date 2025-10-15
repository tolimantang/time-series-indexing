#!/usr/bin/env python3
"""
Daily indexer script for AstroFinancial data.
Runs as a Kubernetes CronJob to process new astronomical data daily.
Uses the existing AstroEncoder and NewsEncoder for sophisticated data processing.
"""
import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import asyncpg
import chromadb
from chromadb.config import Settings

# Add the project root to the path to import encoders
sys.path.append('/app')
sys.path.append('/app/astroEncoder')
sys.path.append('/app/newsEncoder')

# Import existing encoders
try:
    from astroEncoder.encoder import AstroEncoder
    from newsEncoder.encoder import NewsEncoder
except ImportError as e:
    logger.error(f"Failed to import encoders: {e}")
    # Fallback imports if needed
    AstroEncoder = None
    NewsEncoder = None

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DailyIndexer:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        self.chroma_path = os.getenv('CHROMA_PATH', '/data/chroma')
        self.batch_size = int(os.getenv('BATCH_SIZE', '100'))
        self.days_to_index = int(os.getenv('DAYS_TO_INDEX', '1'))

        # Initialize ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=self.chroma_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=False
            )
        )

        # Initialize encoders
        self.astro_encoder = None
        self.news_encoder = None

        if AstroEncoder:
            try:
                self.astro_encoder = AstroEncoder()
                logger.info("AstroEncoder initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize AstroEncoder: {e}")

        if NewsEncoder:
            try:
                # Initialize with API keys from environment
                news_config = {
                    'newsapi_key': os.getenv('NEWSAPI_KEY'),
                    'alpha_vantage_key': os.getenv('ALPHA_VANTAGE_KEY'),
                    'tradingeconomics_key': os.getenv('TRADINGECONOMICS_KEY'),
                }
                # Only pass config if at least one key is available
                if any(news_config.values()):
                    self.news_encoder = NewsEncoder(news_config)
                else:
                    self.news_encoder = NewsEncoder()
                logger.info("NewsEncoder initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize NewsEncoder: {e}")

    async def get_database_connection(self) -> asyncpg.Connection:
        """Get database connection with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                conn = await asyncpg.connect(self.db_url)
                logger.info("Successfully connected to database")
                return conn
            except Exception as e:
                logger.error(f"Database connection attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(5)

    async def fetch_astronomical_data(self, target_date: datetime) -> Dict[str, Any]:
        """Fetch astronomical data using AstroEncoder for the target date."""
        if not self.astro_encoder:
            logger.warning("AstroEncoder not available, skipping astronomical data")
            return {}

        try:
            # Use AstroEncoder to get comprehensive astronomical data
            # Default to NYC coordinates - could be made configurable
            astro_data = self.astro_encoder.encode_date(
                target_date,
                location='nyc'  # Default location
            )

            logger.info(f"Fetched astronomical data for {target_date.date()}")
            return astro_data

        except Exception as e:
            logger.error(f"Error fetching astronomical data: {e}")
            return {}

    async def fetch_financial_news(self, target_date: datetime) -> Dict[str, Any]:
        """Fetch financial news using NewsEncoder for the target date."""
        if not self.news_encoder:
            logger.warning("NewsEncoder not available, skipping financial news")
            return {}

        try:
            # Use NewsEncoder to get financial news and economic events
            news_data = self.news_encoder.encode_date(target_date)

            logger.info(f"Fetched financial news for {target_date.date()}")
            return news_data

        except Exception as e:
            logger.error(f"Error fetching financial news: {e}")
            return {}

    def process_combined_data_for_embedding(
        self,
        astro_data: Dict[str, Any],
        news_data: Dict[str, Any],
        target_date: datetime
    ) -> List[Dict[str, Any]]:
        """Process combined astronomical and financial data for embedding."""
        processed_data = []

        # Create comprehensive text representation combining both data sources
        text_parts = []
        metadata = {
            'date': target_date.date().isoformat(),
            'indexed_at': datetime.now(timezone.utc).isoformat(),
            'data_sources': []
        }

        # Process astronomical data
        if astro_data:
            metadata['data_sources'].append('astronomical')

            # Extract key astronomical information for text representation
            if hasattr(astro_data, 'planetary_positions') and astro_data.planetary_positions:
                planet_info = []
                for planet_name, position in astro_data.planetary_positions.items():
                    if hasattr(position, 'longitude') and hasattr(position, 'sign'):
                        planet_info.append(f"{planet_name.title()} in {position.sign} at {position.longitude:.1f}°")

                if planet_info:
                    text_parts.append(f"Planetary Positions: {', '.join(planet_info)}")

            # Add aspects information
            if hasattr(astro_data, 'aspects') and astro_data.aspects:
                aspect_info = []
                for aspect in astro_data.aspects[:5]:  # Limit to top 5 aspects
                    if hasattr(aspect, 'planet1') and hasattr(aspect, 'planet2') and hasattr(aspect, 'aspect_type'):
                        aspect_info.append(f"{aspect.planet1}-{aspect.planet2} {aspect.aspect_type}")

                if aspect_info:
                    text_parts.append(f"Key Aspects: {', '.join(aspect_info)}")

            # Add lunar phase
            if hasattr(astro_data, 'lunar_phase'):
                text_parts.append(f"Lunar Phase: {astro_data.lunar_phase}")

            # Store raw astronomical data in metadata
            metadata['astronomical_data'] = astro_data.__dict__ if hasattr(astro_data, '__dict__') else str(astro_data)

        # Process financial news data
        if news_data:
            metadata['data_sources'].append('financial_news')

            # Extract financial news headlines and events
            if hasattr(news_data, 'news_articles') and news_data.news_articles:
                headlines = [article.title for article in news_data.news_articles[:3] if hasattr(article, 'title')]
                if headlines:
                    text_parts.append(f"Financial News: {'; '.join(headlines)}")

            # Add economic events
            if hasattr(news_data, 'economic_events') and news_data.economic_events:
                events = [event.title for event in news_data.economic_events[:3] if hasattr(event, 'title')]
                if events:
                    text_parts.append(f"Economic Events: {'; '.join(events)}")

            # Store raw financial data in metadata
            metadata['financial_data'] = news_data.__dict__ if hasattr(news_data, '__dict__') else str(news_data)

        # Create the final processed item
        if text_parts:
            combined_text = f"Date: {target_date.date().isoformat()}\n" + "\n".join(text_parts)

            processed_item = {
                'id': f"combined_{target_date.date().isoformat()}",
                'text': combined_text,
                'metadata': metadata
            }
            processed_data.append(processed_item)

        return processed_data

    async def index_to_chroma(self, processed_data: List[Dict[str, Any]]) -> bool:
        """Index processed data to ChromaDB."""
        try:
            if not processed_data:
                logger.info("No data to index")
                return True

            # Get or create collection
            collection_name = "astronomical_events"
            try:
                collection = self.chroma_client.get_collection(collection_name)
            except ValueError:
                collection = self.chroma_client.create_collection(
                    name=collection_name,
                    metadata={"description": "Astronomical events and data"}
                )

            # Prepare data for ChromaDB
            ids = [item['id'] for item in processed_data]
            documents = [item['text'] for item in processed_data]
            metadatas = [item['metadata'] for item in processed_data]

            # Add to collection in batches
            batch_size = 50
            for i in range(0, len(processed_data), batch_size):
                batch_ids = ids[i:i + batch_size]
                batch_docs = documents[i:i + batch_size]
                batch_metas = metadatas[i:i + batch_size]

                collection.add(
                    ids=batch_ids,
                    documents=batch_docs,
                    metadatas=batch_metas
                )

                logger.info(f"Indexed batch {i//batch_size + 1}, items {i+1}-{min(i+batch_size, len(processed_data))}")

            logger.info(f"Successfully indexed {len(processed_data)} items to ChromaDB")
            return True

        except Exception as e:
            logger.error(f"Error indexing to ChromaDB: {e}")
            return False

    async def mark_data_processed(self, conn: asyncpg.Connection, data_ids: List[int]) -> bool:
        """Mark data as processed in the database."""
        try:
            if not data_ids:
                return True

            query = """
                UPDATE astronomical_events
                SET processed = TRUE, processed_at = NOW()
                WHERE id = ANY($1)
            """

            await conn.execute(query, data_ids)
            logger.info(f"Marked {len(data_ids)} items as processed")
            return True

        except Exception as e:
            logger.error(f"Error marking data as processed: {e}")
            return False

    async def run_daily_indexing(self) -> bool:
        """Run the daily indexing process using sophisticated encoders."""
        logger.info("Starting daily indexing process with AstroEncoder and NewsEncoder")

        # Calculate target date (yesterday by default)
        target_date = datetime.now(timezone.utc) - timedelta(days=self.days_to_index)
        logger.info(f"Indexing data for date: {target_date.date()}")

        try:
            # Fetch astronomical data using AstroEncoder
            logger.info("Fetching astronomical data...")
            astro_data = await self.fetch_astronomical_data(target_date)

            # Fetch financial news using NewsEncoder
            logger.info("Fetching financial news data...")
            news_data = await self.fetch_financial_news(target_date)

            # Check if we have any data to process
            if not astro_data and not news_data:
                logger.info("No data available from encoders")
                return True

            # Process combined data for embedding
            logger.info("Processing combined data for embedding...")
            processed_data = self.process_combined_data_for_embedding(
                astro_data, news_data, target_date
            )

            if not processed_data:
                logger.info("No processed data to index")
                return True

            # Index to ChromaDB
            logger.info("Indexing to ChromaDB...")
            success = await self.index_to_chroma(processed_data)

            if success:
                logger.info(f"Daily indexing completed successfully. Processed {len(processed_data)} combined data items.")
                return True
            else:
                logger.error("Failed to index data to ChromaDB")
                return False

        except Exception as e:
            logger.error(f"Daily indexing failed: {e}")
            return False


async def main():
    """Main entry point for the daily indexer."""
    indexer = DailyIndexer()

    try:
        success = await indexer.run_daily_indexing()
        if success:
            logger.info("Daily indexing completed successfully")
            exit(0)
        else:
            logger.error("Daily indexing failed")
            exit(1)

    except Exception as e:
        logger.error(f"Fatal error in daily indexer: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())