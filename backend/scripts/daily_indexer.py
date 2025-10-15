#!/usr/bin/env python3
"""
Daily indexer script for AstroFinancial data.
Runs as a Kubernetes CronJob to process new astronomical data daily.
"""
import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import asyncpg
import chromadb
from chromadb.config import Settings

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

    async def fetch_new_data(self, conn: asyncpg.Connection, target_date: datetime) -> List[Dict[str, Any]]:
        """Fetch new astronomical data for the target date."""
        try:
            # This is a placeholder - replace with actual data fetching logic
            # In a real implementation, this would fetch from astronomical data sources
            query = """
                SELECT * FROM astronomical_events
                WHERE event_date = $1
                AND processed = FALSE
                ORDER BY event_time
                LIMIT $2
            """

            rows = await conn.fetch(query, target_date.date(), self.batch_size)
            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error fetching new data: {e}")
            return []

    def process_data_for_embedding(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process raw data into format suitable for vector embedding."""
        processed_data = []

        for item in data:
            # Create a comprehensive text representation for embedding
            text_content = f"""
            Event: {item.get('event_type', 'Unknown')}
            Date: {item.get('event_date', '')}
            Time: {item.get('event_time', '')}
            Coordinates: RA {item.get('ra_degrees', 0)}, Dec {item.get('dec_degrees', 0)}
            Magnitude: {item.get('magnitude', 'N/A')}
            Description: {item.get('description', '')}
            Constellation: {item.get('constellation', '')}
            Category: {item.get('category', '')}
            """

            processed_item = {
                'id': f"event_{item.get('id', '')}__{item.get('event_date', '')}",
                'text': text_content.strip(),
                'metadata': {
                    'event_id': item.get('id'),
                    'event_type': item.get('event_type'),
                    'event_date': str(item.get('event_date', '')),
                    'ra_degrees': float(item.get('ra_degrees', 0)),
                    'dec_degrees': float(item.get('dec_degrees', 0)),
                    'magnitude': item.get('magnitude'),
                    'constellation': item.get('constellation'),
                    'category': item.get('category', 'astronomical'),
                    'indexed_at': datetime.utcnow().isoformat()
                }
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
        """Run the daily indexing process."""
        logger.info("Starting daily indexing process")

        # Calculate target date (yesterday by default)
        target_date = datetime.utcnow() - timedelta(days=self.days_to_index)
        logger.info(f"Indexing data for date: {target_date.date()}")

        conn = None
        try:
            # Connect to database
            conn = await self.get_database_connection()

            # Fetch new data
            logger.info("Fetching new astronomical data...")
            raw_data = await self.fetch_new_data(conn, target_date)

            if not raw_data:
                logger.info("No new data found to index")
                return True

            logger.info(f"Found {len(raw_data)} new items to index")

            # Process data for embedding
            logger.info("Processing data for embedding...")
            processed_data = self.process_data_for_embedding(raw_data)

            # Index to ChromaDB
            logger.info("Indexing to ChromaDB...")
            success = await self.index_to_chroma(processed_data)

            if success:
                # Mark as processed
                data_ids = [item['id'] for item in raw_data if 'id' in item]
                await self.mark_data_processed(conn, data_ids)

                logger.info(f"Daily indexing completed successfully. Processed {len(processed_data)} items.")
                return True
            else:
                logger.error("Failed to index data to ChromaDB")
                return False

        except Exception as e:
            logger.error(f"Daily indexing failed: {e}")
            return False

        finally:
            if conn:
                await conn.close()


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