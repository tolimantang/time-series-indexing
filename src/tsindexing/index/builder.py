"""Vector index builder for time series embeddings."""

from typing import Dict, List, Optional, Union
import numpy as np
from pathlib import Path
import json
import pickle
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http import models


class IndexBuilder:
    """Build and manage vector index for time series embeddings."""

    def __init__(
        self,
        collection_name: str = "timeseries",
        vector_size: Optional[int] = None,
        distance: Distance = Distance.COSINE,
        host: str = "localhost",
        port: int = 6333,
        use_memory: bool = True
    ):
        """Initialize index builder.

        Args:
            collection_name: Name of the Qdrant collection
            vector_size: Size of embedding vectors (auto-detected if None)
            distance: Distance metric for similarity search
            host: Qdrant host
            port: Qdrant port
            use_memory: Whether to use in-memory Qdrant instance
        """
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.distance = distance

        if use_memory:
            self.client = QdrantClient(":memory:")
        else:
            self.client = QdrantClient(host=host, port=port)

        self.is_initialized = False

    def create_collection(self, vector_size: int) -> None:
        """Create Qdrant collection.

        Args:
            vector_size: Dimension of embedding vectors
        """
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass  # Collection doesn't exist

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=self.distance
            )
        )
        self.vector_size = vector_size
        self.is_initialized = True

    def add_segments(
        self,
        segments: List[Dict],
        embeddings: np.ndarray,
        batch_size: int = 100
    ) -> None:
        """Add segments and their embeddings to the index.

        Args:
            segments: List of segment dictionaries
            embeddings: Array of embedding vectors
            batch_size: Batch size for uploading
        """
        if not self.is_initialized:
            self.create_collection(embeddings.shape[1])

        if len(segments) != len(embeddings):
            raise ValueError("Number of segments must match number of embeddings")

        points = []
        for i, (segment, embedding) in enumerate(zip(segments, embeddings)):
            # Create metadata payload
            payload = self._create_payload(segment, i)

            point = PointStruct(
                id=i,
                vector=embedding.tolist(),
                payload=payload
            )
            points.append(point)

            # Upload in batches
            if len(points) >= batch_size:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                points = []

        # Upload remaining points
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

    def _create_payload(self, segment: Dict, point_id: int) -> Dict:
        """Create payload for a segment."""
        payload = {
            "point_id": point_id,
            "timestamp_start": segment["timestamp_start"].isoformat(),
            "timestamp_end": segment["timestamp_end"].isoformat(),
            "window_size": segment["window_size"],
            "columns": segment["columns"]
        }

        if segment.get("symbol"):
            payload["symbol"] = segment["symbol"]

        # Add statistical features if available
        if "features" in segment:
            # Store a subset of key features for filtering
            features = segment["features"]
            for key, value in features.items():
                if isinstance(value, (int, float)) and not np.isnan(value):
                    # Limit to prevent payload size issues
                    if len(payload) < 50:  # Arbitrary limit
                        payload[f"feat_{key}"] = float(value)

        return payload

    def build_from_data(
        self,
        segments: List[Dict],
        embeddings: np.ndarray,
        save_path: Optional[Union[str, Path]] = None
    ) -> None:
        """Build complete index from segments and embeddings.

        Args:
            segments: List of segment dictionaries
            embeddings: Array of embedding vectors
            save_path: Optional path to save index metadata
        """
        print(f"Building index with {len(segments)} segments...")

        # Add to vector database
        self.add_segments(segments, embeddings)

        # Save metadata if path provided
        if save_path:
            self.save_metadata(save_path, segments)

        print("Index built successfully!")

    def save_metadata(
        self,
        save_path: Union[str, Path],
        segments: List[Dict]
    ) -> None:
        """Save index metadata to disk.

        Args:
            save_path: Path to save metadata
            segments: List of segment dictionaries
        """
        save_path = Path(save_path)
        save_path.mkdir(parents=True, exist_ok=True)

        # Save configuration
        config = {
            "collection_name": self.collection_name,
            "vector_size": self.vector_size,
            "distance": self.distance.value,
            "num_segments": len(segments)
        }

        with open(save_path / "config.json", "w") as f:
            json.dump(config, f, indent=2)

        # Save segments metadata (without embeddings)
        segments_metadata = []
        for i, segment in enumerate(segments):
            metadata = {
                "id": i,
                "timestamp_start": segment["timestamp_start"].isoformat(),
                "timestamp_end": segment["timestamp_end"].isoformat(),
                "symbol": segment.get("symbol"),
                "columns": segment["columns"],
                "window_size": segment["window_size"]
            }
            segments_metadata.append(metadata)

        with open(save_path / "segments.json", "w") as f:
            json.dump(segments_metadata, f, indent=2)

        print(f"Metadata saved to {save_path}")

    def get_collection_info(self) -> Dict:
        """Get information about the collection."""
        if not self.is_initialized:
            return {"status": "not_initialized"}

        info = self.client.get_collection(self.collection_name)
        return {
            "status": "ready",
            "points_count": info.points_count,
            "vector_size": info.config.params.vectors.size,
            "distance": info.config.params.vectors.distance.value
        }