"""Query interface for time series vector index."""

from typing import Dict, List, Optional, Union, Any
import numpy as np
from datetime import datetime
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
import pandas as pd


class IndexQuery:
    """Query interface for time series similarity search."""

    def __init__(
        self,
        collection_name: str = "timeseries",
        host: str = "localhost",
        port: int = 6333,
        use_memory: bool = True
    ):
        """Initialize query interface.

        Args:
            collection_name: Name of the Qdrant collection
            host: Qdrant host
            port: Qdrant port
            use_memory: Whether to use in-memory Qdrant instance
        """
        self.collection_name = collection_name

        if use_memory:
            self.client = QdrantClient(":memory:")
        else:
            self.client = QdrantClient(host=host, port=port)

    def similarity_search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        filters: Optional[Dict] = None,
        score_threshold: Optional[float] = None
    ) -> List[Dict]:
        """Search for similar time series segments.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            filters: Optional filters for metadata
            score_threshold: Minimum similarity score

        Returns:
            List of similar segments with metadata and scores
        """
        # Build filters
        query_filter = self._build_filter(filters) if filters else None

        # Perform search
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding.tolist(),
            query_filter=query_filter,
            limit=top_k,
            score_threshold=score_threshold
        )

        # Format results
        results = []
        for hit in search_result:
            result = {
                "id": hit.id,
                "score": hit.score,
                "metadata": hit.payload
            }
            results.append(result)

        return results

    def find_similar_contexts(
        self,
        current_segment: Dict,
        encoder,
        top_k: int = 5,
        symbol_filter: Optional[str] = None,
        time_range: Optional[tuple] = None
    ) -> List[Dict]:
        """Find historically similar market contexts.

        Args:
            current_segment: Current time series segment
            encoder: Trained encoder to generate embeddings
            top_k: Number of similar contexts to return
            symbol_filter: Optional symbol to filter by
            time_range: Optional (start_date, end_date) tuple

        Returns:
            List of similar historical contexts
        """
        # Encode current segment
        query_embedding = encoder.encode_single(current_segment)

        # Build filters
        filters = {}
        if symbol_filter:
            filters["symbol"] = symbol_filter

        if time_range:
            start_date, end_date = time_range
            filters["timestamp_start"] = {
                "gte": start_date.isoformat() if isinstance(start_date, datetime) else start_date,
                "lte": end_date.isoformat() if isinstance(end_date, datetime) else end_date
            }

        return self.similarity_search(query_embedding, top_k, filters)

    def get_segment_by_id(self, segment_id: int) -> Optional[Dict]:
        """Retrieve a specific segment by ID.

        Args:
            segment_id: Segment ID

        Returns:
            Segment metadata or None if not found
        """
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[segment_id]
            )
            if result:
                return {
                    "id": result[0].id,
                    "metadata": result[0].payload
                }
        except Exception:
            pass

        return None

    def aggregate_features(
        self,
        similar_segments: List[Dict],
        feature_prefix: str = "feat_"
    ) -> Dict:
        """Aggregate features from similar segments.

        Args:
            similar_segments: List of similar segments from search
            feature_prefix: Prefix for feature keys in metadata

        Returns:
            Aggregated feature statistics
        """
        if not similar_segments:
            return {}

        # Collect features
        features = {}
        for segment in similar_segments:
            metadata = segment["metadata"]
            for key, value in metadata.items():
                if key.startswith(feature_prefix):
                    feature_name = key[len(feature_prefix):]
                    if feature_name not in features:
                        features[feature_name] = []
                    features[feature_name].append(value)

        # Compute statistics
        aggregated = {}
        for feature_name, values in features.items():
            if values:
                aggregated[feature_name] = {
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "min": np.min(values),
                    "max": np.max(values),
                    "count": len(values)
                }

        return aggregated

    def _build_filter(self, filters: Dict) -> Filter:
        """Build Qdrant filter from dictionary.

        Args:
            filters: Filter dictionary

        Returns:
            Qdrant Filter object
        """
        conditions = []

        for key, value in filters.items():
            if isinstance(value, dict):
                # Range filter
                if "gte" in value or "lte" in value or "gt" in value or "lt" in value:
                    range_filter = {}
                    if "gte" in value:
                        range_filter["gte"] = value["gte"]
                    if "lte" in value:
                        range_filter["lte"] = value["lte"]
                    if "gt" in value:
                        range_filter["gt"] = value["gt"]
                    if "lt" in value:
                        range_filter["lt"] = value["lt"]

                    conditions.append(
                        FieldCondition(key=key, range=Range(**range_filter))
                    )
            else:
                # Exact match
                conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )

        return Filter(must=conditions) if conditions else None

    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection.

        Returns:
            Collection statistics
        """
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "points_count": info.points_count,
                "vector_size": info.config.params.vectors.size,
                "distance_metric": info.config.params.vectors.distance.value,
                "status": "ready"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }