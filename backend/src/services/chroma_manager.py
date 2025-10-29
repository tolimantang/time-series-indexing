"""
ChromaDB Manager for Financial Events and Market Data

Handles both local (PersistentClient) and hosted (HttpClient) ChromaDB connections.
Provides unified interface for collection management and operations.
"""

import os
import logging
from typing import Dict, Any, List, Optional
import chromadb
from chromadb.config import Settings
from chromadb import Collection
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class ChromaManager:
    """
    Unified ChromaDB manager for financial events and market data.
    Supports both local and hosted ChromaDB deployments.
    """

    def __init__(self,
                 connection_type: str = "local",
                 host: Optional[str] = None,
                 port: Optional[int] = None,
                 api_key: Optional[str] = None,
                 tenant: Optional[str] = None,
                 database: Optional[str] = None,
                 local_path: Optional[str] = None,
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize ChromaDB manager.

        Args:
            connection_type: "local", "hosted", or "cloud"
            host: ChromaDB host (for hosted)
            port: ChromaDB port (for hosted)
            api_key: API key (for hosted/cloud)
            tenant: Tenant ID (for cloud)
            database: Database name (for cloud)
            local_path: Local storage path (for local)
            embedding_model: Sentence transformer model name
        """
        self.connection_type = connection_type
        self.embedding_model_name = embedding_model

        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)

        # Initialize ChromaDB client
        if connection_type == "hosted":
            if not all([host, port, api_key]):
                raise ValueError("Host, port, and API key required for hosted connection")
            self.client = self._create_hosted_client(host, port, api_key)  # type: ignore
        elif connection_type == "cloud":
            if not all([api_key, tenant, database]):
                raise ValueError("API key, tenant, and database required for cloud connection")
            self.client = self._create_cloud_client(api_key, tenant, database)  # type: ignore
        else:
            self.client = self._create_local_client(local_path)

        # Collection cache
        self._collections: Dict[str, Collection] = {}

        logger.info(f"ChromaManager initialized with {connection_type} connection")

    def _create_hosted_client(self, host: str, port: int, api_key: str):
        """Create hosted ChromaDB client."""
        if not all([host, port, api_key]):
            raise ValueError("Host, port, and API key required for hosted connection")

        # For ChromaDB Cloud
        headers = {"Authorization": f"Bearer {api_key}"}

        client = chromadb.HttpClient(
            host=host,
            port=port,
            headers=headers,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=False
            )
        )

        logger.info(f"Connected to hosted ChromaDB at {host}:{port}")
        return client

    def _create_cloud_client(self, api_key: str, tenant: str, database: str):
        """Create ChromaDB Cloud client."""
        if not all([api_key, tenant, database]):
            raise ValueError("API key, tenant, and database required for cloud connection")

        client = chromadb.CloudClient(
            api_key=api_key,
            tenant=tenant,
            database=database
        )

        logger.info(f"Connected to ChromaDB Cloud - tenant: {tenant}, database: {database}")
        return client

    def _create_local_client(self, local_path: Optional[str]):
        """Create local ChromaDB client."""
        if local_path is None:
            local_path = os.getenv('CHROMA_PATH', '/data/chroma')

        # Ensure directory exists
        os.makedirs(local_path, exist_ok=True)

        client = chromadb.PersistentClient(
            path=local_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=False
            )
        )

        logger.info(f"Connected to local ChromaDB at {local_path}")
        return client

    def get_or_create_collection(self,
                                name: str,
                                description: Optional[str] = None,
                                metadata: Optional[Dict[str, Any]] = None) -> Collection:
        """
        Get or create a collection.

        Args:
            name: Collection name
            description: Collection description
            metadata: Collection metadata

        Returns:
            ChromaDB collection
        """
        if name in self._collections:
            return self._collections[name]

        try:
            # Try to get existing collection
            collection = self.client.get_collection(name)
            logger.info(f"Retrieved existing collection: {name}")
        except Exception as e:
            # Create new collection if it doesn't exist
            # ChromaDB Cloud may throw different exceptions than local/hosted
            logger.info(f"Collection {name} doesn't exist, creating new one. Error: {e}")
            collection_metadata = metadata or {}
            if description:
                collection_metadata["description"] = description

            collection = self.client.create_collection(
                name=name,
                metadata=collection_metadata
            )
            logger.info(f"Created new collection: {name}")

        # Cache collection
        self._collections[name] = collection
        return collection

    def add_events(self,
                   collection_name: str,
                   events: List[Dict[str, Any]],
                   batch_size: int = 50) -> bool:
        """
        Add financial events to collection.

        Args:
            collection_name: Target collection name
            events: List of event dictionaries with 'id', 'document', 'metadata'
            batch_size: Batch size for adding documents

        Returns:
            Success status
        """
        try:
            collection = self.get_or_create_collection(collection_name)

            # Process in batches
            for i in range(0, len(events), batch_size):
                batch = events[i:i + batch_size]

                ids = [event['id'] for event in batch]
                documents = [event['document'] for event in batch]
                metadatas = [event['metadata'] for event in batch]

                # Generate embeddings
                embeddings = self.embedding_model.encode(documents).tolist()

                # Add to collection
                collection.add(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas
                )

                logger.debug(f"Added batch {i//batch_size + 1}: {len(batch)} events")

            logger.info(f"Successfully added {len(events)} events to {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Error adding events to {collection_name}: {e}")
            return False

    def upsert_events(self,
                     collection_name: str,
                     events: List[Dict[str, Any]],
                     batch_size: int = 50) -> bool:
        """
        Upsert financial events to collection.

        Args:
            collection_name: Target collection name
            events: List of event dictionaries with 'id', 'document', 'metadata'
            batch_size: Batch size for upserting documents

        Returns:
            Success status
        """
        try:
            collection = self.get_or_create_collection(collection_name)

            # Process in batches
            for i in range(0, len(events), batch_size):
                batch = events[i:i + batch_size]

                ids = [event['id'] for event in batch]
                documents = [event['document'] for event in batch]
                metadatas = [event['metadata'] for event in batch]

                # Generate embeddings
                embeddings = self.embedding_model.encode(documents).tolist()

                # Upsert to collection
                collection.upsert(
                    ids=ids,
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas
                )

                logger.debug(f"Upserted batch {i//batch_size + 1}: {len(batch)} events")

            logger.info(f"Successfully upserted {len(events)} events to {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Error upserting events to {collection_name}: {e}")
            return False

    def query_events(self,
                    collection_name: str,
                    query_text: str,
                    n_results: int = 10,
                    where_filter: Optional[Dict[str, Any]] = None,
                    include: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Query financial events using semantic search.

        Args:
            collection_name: Collection to search
            query_text: Semantic query text
            n_results: Number of results to return
            where_filter: Metadata filter conditions
            include: Fields to include in results

        Returns:
            Query results
        """
        try:
            collection = self.get_or_create_collection(collection_name)

            if include is None:
                include = ['documents', 'metadatas', 'distances']

            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=where_filter,
                include=include
            )

            logger.info(f"Query '{query_text}' returned {len(results['documents'][0])} results")
            return {
                'query': query_text,
                'collection': collection_name,
                'results': results,
                'count': len(results['documents'][0]) if results['documents'] else 0
            }

        except Exception as e:
            logger.error(f"Error querying {collection_name}: {e}")
            return {
                'query': query_text,
                'collection': collection_name,
                'results': None,
                'count': 0,
                'error': str(e)
            }

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics about a collection.

        Args:
            collection_name: Collection name

        Returns:
            Collection statistics
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            count = collection.count()

            # Get sample of recent data to determine date range
            sample_results = collection.query(
                query_texts=["recent data"],
                n_results=min(count, 100),
                include=['metadatas']
            )

            stats = {
                'collection_name': collection_name,
                'total_documents': count,
                'connection_type': self.connection_type,
                'embedding_model': self.embedding_model_name
            }

            # Extract date range if metadata contains dates
            if sample_results['metadatas'] and sample_results['metadatas'][0]:
                dates = []
                sources = set()
                event_types = set()

                for metadata in sample_results['metadatas'][0]:
                    if 'date' in metadata:
                        dates.append(metadata['date'])
                    if 'source' in metadata:
                        sources.add(metadata['source'])
                    if 'event_type' in metadata:
                        event_types.add(metadata['event_type'])

                if dates:
                    stats['date_range'] = {
                        'earliest': min(dates),
                        'latest': max(dates)
                    }

                stats['sources'] = list(sources)
                stats['event_types'] = list(event_types)

            return stats

        except Exception as e:
            logger.error(f"Error getting stats for {collection_name}: {e}")
            return {
                'collection_name': collection_name,
                'error': str(e)
            }

    def list_collections(self) -> List[str]:
        """List all collections."""
        try:
            collections = self.client.list_collections()
            return [col.name for col in collections]
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []

    def delete_collection(self, collection_name: str) -> bool:
        """
        Delete a collection.

        Args:
            collection_name: Collection name to delete

        Returns:
            Success status
        """
        try:
            self.client.delete_collection(collection_name)

            # Remove from cache
            if collection_name in self._collections:
                del self._collections[collection_name]

            logger.info(f"Deleted collection: {collection_name}")
            return True

        except Exception as e:
            logger.error(f"Error deleting collection {collection_name}: {e}")
            return False


def create_chroma_manager() -> ChromaManager:
    """
    Factory function to create ChromaManager based on environment variables.

    Environment Variables:
        CHROMA_CONNECTION_TYPE: "local", "hosted", or "cloud" (default: "local")
        CHROMA_HOST: Host for hosted connection
        CHROMA_PORT: Port for hosted connection
        CHROMA_API_KEY: API key for hosted/cloud connection
        CHROMA_TENANT: Tenant ID for cloud connection
        CHROMA_DATABASE: Database name for cloud connection
        CHROMA_PATH: Local path for persistent storage
        CHROMA_EMBEDDING_MODEL: Embedding model name (default: "all-MiniLM-L6-v2")

    Returns:
        Configured ChromaManager instance
    """
    connection_type = os.getenv('CHROMA_CONNECTION_TYPE', 'local')

    if connection_type == 'hosted':
        return ChromaManager(
            connection_type='hosted',
            host=os.getenv('CHROMA_HOST'),
            port=int(os.getenv('CHROMA_PORT', '8000')),
            api_key=os.getenv('CHROMA_API_KEY'),
            embedding_model=os.getenv('CHROMA_EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        )
    elif connection_type == 'cloud':
        return ChromaManager(
            connection_type='cloud',
            api_key=os.getenv('CHROMA_API_KEY'),
            tenant=os.getenv('CHROMA_TENANT'),
            database=os.getenv('CHROMA_DATABASE'),
            embedding_model=os.getenv('CHROMA_EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        )
    else:
        return ChromaManager(
            connection_type='local',
            local_path=os.getenv('CHROMA_PATH'),
            embedding_model=os.getenv('CHROMA_EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
        )