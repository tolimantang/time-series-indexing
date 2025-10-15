#!/usr/bin/env python3
"""
Backfill indexer script for AstroFinancial data.
Used for historical data processing and bulk indexing operations.
"""
import os
import asyncio
import argparse
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import asyncpg
import chromadb
from chromadb.config import Settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BackfillIndexer:
    def __init__(self):
        self.db_url = os.getenv('DATABASE_URL')
        self.chroma_path = os.getenv('CHROMA_PATH', '/data/chroma')
        self.batch_size = int(os.getenv('BATCH_SIZE', '50'))

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

    async def fetch_historical_data(
        self,
        conn: asyncpg.Connection,
        start_date: datetime,
        end_date: datetime,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Fetch historical astronomical data for the date range."""
        try:
            query = """
                SELECT * FROM astronomical_events
                WHERE event_date >= $1 AND event_date <= $2
                AND (processed = FALSE OR processed IS NULL)
                ORDER BY event_date, event_time
                LIMIT $3 OFFSET $4
            """

            rows = await conn.fetch(query, start_date.date(), end_date.date(), self.batch_size, offset)
            return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return []

    async def get_total_records(
        self,
        conn: asyncpg.Connection,
        start_date: datetime,
        end_date: datetime
    ) -> int:
        """Get total number of records to process."""
        try:
            query = """
                SELECT COUNT(*) FROM astronomical_events
                WHERE event_date >= $1 AND event_date <= $2
                AND (processed = FALSE OR processed IS NULL)
            """

            result = await conn.fetchval(query, start_date.date(), end_date.date())
            return result or 0

        except Exception as e:
            logger.error(f"Error getting total record count: {e}")
            return 0

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
            Historical Data: Backfilled on {datetime.utcnow().strftime('%Y-%m-%d')}
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
                    'backfilled': True,
                    'indexed_at': datetime.utcnow().isoformat()
                }
            }
            processed_data.append(processed_item)

        return processed_data

    async def index_to_chroma(self, processed_data: List[Dict[str, Any]]) -> bool:
        """Index processed data to ChromaDB."""
        try:
            if not processed_data:
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

            # Add to collection in smaller batches for backfill
            batch_size = 25
            for i in range(0, len(processed_data), batch_size):
                batch_ids = ids[i:i + batch_size]
                batch_docs = documents[i:i + batch_size]
                batch_metas = metadatas[i:i + batch_size]

                collection.add(
                    ids=batch_ids,
                    documents=batch_docs,
                    metadatas=batch_metas
                )

                # Small delay to prevent overwhelming the system
                await asyncio.sleep(0.1)

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
            return True

        except Exception as e:
            logger.error(f"Error marking data as processed: {e}")
            return False

    async def run_backfill(
        self,
        start_date: datetime,
        end_date: datetime,
        dry_run: bool = False
    ) -> bool:
        """Run the backfill indexing process."""
        logger.info(f"Starting backfill indexing process from {start_date.date()} to {end_date.date()}")

        if dry_run:
            logger.info("DRY RUN MODE - No data will be indexed")

        conn = None
        try:
            # Connect to database
            conn = await self.get_database_connection()

            # Get total records to process
            total_records = await self.get_total_records(conn, start_date, end_date)
            logger.info(f"Total records to process: {total_records}")

            if total_records == 0:
                logger.info("No records found to process")
                return True

            # Process in batches
            processed_count = 0
            offset = 0

            while processed_count < total_records:
                logger.info(f"Processing batch {offset // self.batch_size + 1}, records {processed_count + 1}-{min(processed_count + self.batch_size, total_records)}")

                # Fetch batch
                raw_data = await self.fetch_historical_data(conn, start_date, end_date, offset)

                if not raw_data:
                    logger.info("No more data to process")
                    break

                if not dry_run:
                    # Process data for embedding
                    processed_data = self.process_data_for_embedding(raw_data)

                    # Index to ChromaDB
                    success = await self.index_to_chroma(processed_data)

                    if success:
                        # Mark as processed
                        data_ids = [item['id'] for item in raw_data if 'id' in item]
                        await self.mark_data_processed(conn, data_ids)
                        logger.info(f"Successfully indexed {len(processed_data)} items")
                    else:
                        logger.error(f"Failed to index batch starting at offset {offset}")
                        return False
                else:
                    logger.info(f"DRY RUN: Would process {len(raw_data)} items")

                processed_count += len(raw_data)
                offset += self.batch_size

                # Small delay between batches
                await asyncio.sleep(1)

            logger.info(f"Backfill indexing completed. Processed {processed_count} items.")
            return True

        except Exception as e:
            logger.error(f"Backfill indexing failed: {e}")
            return False

        finally:
            if conn:
                await conn.close()


def parse_date(date_string: str) -> datetime:
    """Parse date string in YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_string, '%Y-%m-%d')
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_string}. Use YYYY-MM-DD")


async def main():
    """Main entry point for the backfill indexer."""
    parser = argparse.ArgumentParser(description='Backfill astronomical data indexing')
    parser.add_argument('--start-date', type=parse_date, required=True,
                      help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end-date', type=parse_date, required=True,
                      help='End date in YYYY-MM-DD format')
    parser.add_argument('--dry-run', action='store_true',
                      help='Run in dry-run mode (no actual indexing)')

    args = parser.parse_args()

    # Validate date range
    if args.start_date > args.end_date:
        logger.error("Start date must be before or equal to end date")
        return 1

    if args.end_date > datetime.now():
        logger.warning("End date is in the future, adjusting to current date")
        args.end_date = datetime.now()

    indexer = BackfillIndexer()

    try:
        success = await indexer.run_backfill(args.start_date, args.end_date, args.dry_run)
        if success:
            logger.info("Backfill indexing completed successfully")
            return 0
        else:
            logger.error("Backfill indexing failed")
            return 1

    except Exception as e:
        logger.error(f"Fatal error in backfill indexer: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)