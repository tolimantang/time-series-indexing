"""Query interface for LLM-generated patterns."""

import json
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import re


class PatternQueryInterface:
    """Interface for querying financial patterns built with LLM."""

    def __init__(self, patterns_dir: Optional[str] = None):
        """Initialize pattern query interface.

        Args:
            patterns_dir: Directory containing pattern files
        """
        if patterns_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            patterns_dir = project_root / "patterns"

        self.patterns_dir = Path(patterns_dir)
        self.pattern_libraries = {}
        self.text_to_pattern_map = {
            # Fed-related queries
            "fed": "fed_rate_hikes",
            "federal reserve": "fed_rate_hikes",
            "interest rate": "fed_rate_hikes",
            "rate hike": "fed_rate_hikes",
            "rate increase": "fed_rate_hikes",
            "monetary policy": "fed_rate_hikes",
            "fomc": "fed_rate_hikes",

            # Crash-related queries
            "crash": "market_crashes",
            "decline": "market_crashes",
            "selloff": "market_crashes",
            "market crash": "market_crashes",
            "stock crash": "market_crashes",
            "financial crisis": "market_crashes",
            "bear market": "market_crashes",

            # Volatility-related queries
            "vix": "vix_spikes",
            "volatility": "vix_spikes",
            "fear": "vix_spikes",
            "panic": "vix_spikes",
            "vol spike": "vix_spikes",
            "market fear": "vix_spikes"
        }

    def load_patterns(self, asset: str = "SPY") -> bool:
        """Load pattern library for given asset.

        Args:
            asset: Asset symbol

        Returns:
            True if patterns loaded successfully
        """
        pattern_file = self.patterns_dir / f"pattern_library_{asset.lower()}.json"

        if not pattern_file.exists():
            print(f"❌ Pattern library not found: {pattern_file}")
            print(f"Run pattern builder first: python -m tsindexing.patterns.llm_pattern_builder")
            return False

        try:
            with open(pattern_file, 'r') as f:
                pattern_data = json.load(f)

            # Convert embedding lists back to numpy arrays
            for pattern_type, data in pattern_data.items():
                data["embedding"] = np.array(data["embedding"])

            self.pattern_libraries[asset] = pattern_data
            print(f"✅ Loaded {len(pattern_data)} patterns for {asset}")
            return True

        except Exception as e:
            print(f"❌ Error loading patterns: {e}")
            return False

    def text_to_embedding(self, query: str, asset: str = "SPY") -> Tuple[Optional[np.ndarray], str]:
        """Convert text query to pattern embedding.

        Args:
            query: Natural language query
            asset: Asset symbol

        Returns:
            Tuple of (embedding vector, pattern type) or (None, error message)
        """
        # Ensure patterns are loaded
        if asset not in self.pattern_libraries:
            if not self.load_patterns(asset):
                return None, f"Could not load patterns for {asset}"

        query_lower = query.lower()

        # Find matching pattern
        for text_trigger, pattern_type in self.text_to_pattern_map.items():
            if text_trigger in query_lower:
                if pattern_type in self.pattern_libraries[asset]:
                    embedding = self.pattern_libraries[asset][pattern_type]["embedding"]
                    return embedding, pattern_type

        # No pattern found
        available_patterns = list(self.pattern_libraries[asset].keys())
        available_triggers = list(self.text_to_pattern_map.keys())

        return None, f"No pattern found for '{query}'. Try: {', '.join(available_triggers[:5])}"

    def query_pattern(self, query: str, asset: str = "SPY") -> Dict:
        """Query financial patterns with natural language.

        Args:
            query: Natural language query
            asset: Asset symbol to analyze

        Returns:
            Dictionary with query results
        """
        print(f"🔍 Querying: '{query}' for {asset}")

        embedding, pattern_type_or_error = self.text_to_embedding(query, asset)

        if embedding is None:
            return {
                "success": False,
                "error": pattern_type_or_error,
                "query": query,
                "asset": asset
            }

        pattern_type = pattern_type_or_error
        pattern_data = self.pattern_libraries[asset][pattern_type]

        return {
            "success": True,
            "query": query,
            "asset": asset,
            "pattern_type": pattern_type,
            "pattern_embedding": embedding,
            "pattern_info": {
                "total_dates": len(pattern_data["dates"]),
                "valid_segments": pattern_data["valid_segments"],
                "sample_dates": pattern_data["dates"][:5],
                "embedding_shape": embedding.shape,
                "created_at": pattern_data["created_at"]
            }
        }

    def get_pattern_info(self, asset: str = "SPY") -> Dict:
        """Get information about available patterns.

        Args:
            asset: Asset symbol

        Returns:
            Dictionary with pattern information
        """
        if asset not in self.pattern_libraries:
            if not self.load_patterns(asset):
                return {"error": f"Could not load patterns for {asset}"}

        patterns = self.pattern_libraries[asset]
        info = {
            "asset": asset,
            "available_patterns": {},
            "query_examples": []
        }

        for pattern_type, data in patterns.items():
            info["available_patterns"][pattern_type] = {
                "dates_count": len(data["dates"]),
                "valid_segments": data["valid_segments"],
                "sample_dates": data["dates"][:3],
                "embedding_dimensions": len(data["embedding"])
            }

        # Add query examples
        info["query_examples"] = [
            "What happens during Fed rate hikes?",
            "Find periods similar to market crashes",
            "Show me VIX spike patterns",
            "Analyze Fed monetary policy periods",
            "Find market decline patterns"
        ]

        return info


def main():
    """Demo the pattern query interface."""
    print("🔍 Pattern Query Interface Demo")
    print("=" * 40)

    # Create query interface
    query_interface = PatternQueryInterface()

    # Show available patterns
    print("\n📋 Available Patterns:")
    pattern_info = query_interface.get_pattern_info("SPY")

    if "error" in pattern_info:
        print(f"❌ {pattern_info['error']}")
        print("\n💡 Run this first:")
        print("python -m tsindexing.patterns.llm_pattern_builder")
        return

    for pattern_type, info in pattern_info["available_patterns"].items():
        print(f"  {pattern_type}:")
        print(f"    Dates: {info['dates_count']}")
        print(f"    Valid segments: {info['valid_segments']}")
        print(f"    Sample dates: {info['sample_dates']}")

    # Test some queries
    print(f"\n🧪 Testing Queries:")
    test_queries = [
        "What happens during Fed rate hikes?",
        "Find market crash patterns",
        "Show me VIX spikes",
        "Unknown pattern"
    ]

    for query in test_queries:
        result = query_interface.query_pattern(query)

        if result["success"]:
            print(f"  ✅ '{query}' → {result['pattern_type']}")
            print(f"     Embedding shape: {result['pattern_embedding'].shape}")
        else:
            print(f"  ❌ '{query}' → {result['error']}")

    print(f"\n💡 Query Examples:")
    for example in pattern_info["query_examples"]:
        print(f"  - {example}")


if __name__ == "__main__":
    main()