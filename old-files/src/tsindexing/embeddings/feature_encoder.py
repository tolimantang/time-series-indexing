"""Feature-based time series encoder."""

from typing import Dict, List, Optional, Union
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.pipeline import Pipeline
from scipy.fft import fft
import pandas as pd


class FeatureEncoder:
    """Encode time series segments into feature vectors."""

    def __init__(
        self,
        use_fft: bool = True,
        fft_components: int = 10,
        use_statistical: bool = True,
        use_pca: bool = True,
        pca_components: Optional[int] = None,
        normalize: bool = True
    ):
        """Initialize encoder.

        Args:
            use_fft: Whether to include FFT features
            fft_components: Number of FFT components to keep
            use_statistical: Whether to include statistical features
            use_pca: Whether to apply PCA for dimensionality reduction
            pca_components: Number of PCA components (None for auto)
            normalize: Whether to normalize features
        """
        self.use_fft = use_fft
        self.fft_components = fft_components
        self.use_statistical = use_statistical
        self.use_pca = use_pca
        self.pca_components = pca_components
        self.normalize = normalize

        self.scaler = StandardScaler() if normalize else None
        self.pca = None
        self.is_fitted = False
        self.feature_names_ = []

    def fit(self, segments: List[Dict]) -> "FeatureEncoder":
        """Fit the encoder on a list of segments.

        Args:
            segments: List of segment dictionaries

        Returns:
            Fitted encoder
        """
        features = []
        for segment in segments:
            feature_vector = self._extract_features(segment)
            features.append(feature_vector)

        features_array = np.array(features)

        # Fit scaler
        if self.scaler:
            features_array = self.scaler.fit_transform(features_array)

        # Fit PCA
        if self.use_pca:
            n_components = self.pca_components or min(
                features_array.shape[1], features_array.shape[0] // 2
            )
            self.pca = PCA(n_components=n_components)
            self.pca.fit(features_array)

        self.is_fitted = True
        return self

    def transform(self, segments: List[Dict]) -> np.ndarray:
        """Transform segments into embeddings.

        Args:
            segments: List of segment dictionaries

        Returns:
            Array of embeddings
        """
        if not self.is_fitted:
            raise ValueError("Encoder must be fitted before transform")

        features = []
        for segment in segments:
            feature_vector = self._extract_features(segment)
            features.append(feature_vector)

        features_array = np.array(features)

        # Apply scaler
        if self.scaler:
            features_array = self.scaler.transform(features_array)

        # Apply PCA
        if self.pca:
            features_array = self.pca.transform(features_array)

        return features_array

    def fit_transform(self, segments: List[Dict]) -> np.ndarray:
        """Fit encoder and transform segments.

        Args:
            segments: List of segment dictionaries

        Returns:
            Array of embeddings
        """
        return self.fit(segments).transform(segments)

    def encode_single(self, segment: Dict) -> np.ndarray:
        """Encode a single segment.

        Args:
            segment: Segment dictionary

        Returns:
            Embedding vector
        """
        return self.transform([segment])[0]

    def _extract_features(self, segment: Dict) -> np.ndarray:
        """Extract features from a single segment."""
        features = []

        values = segment["values"]
        if len(values.shape) == 1:
            values = values.reshape(-1, 1)

        # Time series features for each column
        for col_idx in range(values.shape[1]):
            series = values[:, col_idx]
            series = series[~np.isnan(series)]  # Remove NaN values

            if len(series) < 2:
                # Fill with zeros if insufficient data
                features.extend([0.0] * self._get_feature_count_per_series())
                continue

            col_features = []

            # Statistical features
            if self.use_statistical:
                col_features.extend(self._extract_statistical_features(series))

            # FFT features
            if self.use_fft:
                col_features.extend(self._extract_fft_features(series))

            features.extend(col_features)

        # Global features from segment metadata
        if "features" in segment:
            meta_features = self._extract_meta_features(segment["features"])
            features.extend(meta_features)

        return np.array(features, dtype=np.float32)

    def _extract_statistical_features(self, series: np.ndarray) -> List[float]:
        """Extract statistical features from time series."""
        features = []

        # Basic statistics
        features.append(np.mean(series))
        features.append(np.std(series))
        features.append(np.min(series))
        features.append(np.max(series))
        features.append(np.median(series))

        # Distribution features
        from scipy import stats
        features.append(stats.skew(series))
        features.append(stats.kurtosis(series))

        # Returns
        if len(series) > 1:
            returns = np.diff(series) / series[:-1]
            returns = returns[~np.isnan(returns)]
            if len(returns) > 0:
                features.append(np.mean(returns))
                features.append(np.std(returns))
            else:
                features.extend([0.0, 0.0])
        else:
            features.extend([0.0, 0.0])

        # Trend
        if len(series) > 1:
            x = np.arange(len(series))
            slope, _, r_value, _, _ = stats.linregress(x, series)
            features.append(slope)
            features.append(r_value ** 2)
        else:
            features.extend([0.0, 0.0])

        return features

    def _extract_fft_features(self, series: np.ndarray) -> List[float]:
        """Extract FFT features from time series."""
        if len(series) < 4:
            return [0.0] * (self.fft_components * 2)

        # Compute FFT
        fft_values = fft(series)
        n_components = min(self.fft_components, len(fft_values) // 2)

        features = []
        for i in range(1, n_components + 1):  # Skip DC component
            features.append(np.abs(fft_values[i]))  # Magnitude
            features.append(np.angle(fft_values[i]))  # Phase

        # Pad with zeros if needed
        while len(features) < self.fft_components * 2:
            features.append(0.0)

        return features

    def _extract_meta_features(self, features_dict: Dict) -> List[float]:
        """Extract features from metadata dictionary."""
        # Convert all numeric values from features dict
        meta_features = []
        for key, value in sorted(features_dict.items()):
            if isinstance(value, (int, float)) and not np.isnan(value):
                meta_features.append(float(value))
            else:
                meta_features.append(0.0)

        return meta_features

    def _get_feature_count_per_series(self) -> int:
        """Get the number of features extracted per time series."""
        count = 0
        if self.use_statistical:
            count += 11  # Basic stats + returns + trend
        if self.use_fft:
            count += self.fft_components * 2  # Magnitude + phase
        return count