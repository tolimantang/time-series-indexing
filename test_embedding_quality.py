"""Test if the pattern embeddings actually capture meaningful financial patterns."""

import sys
from pathlib import Path
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tsindexing.patterns.pattern_query import PatternQueryInterface


def test_embedding_quality():
    """Test if pattern embeddings are actually meaningful."""
    print("🧪 Testing Pattern Embedding Quality")
    print("=" * 50)

    # Initialize query interface
    query_interface = PatternQueryInterface()

    # Get all pattern embeddings
    patterns = {}
    pattern_types = ["fed_rate_hikes", "market_crashes", "vix_spikes"]

    for pattern_type in pattern_types:
        result = query_interface.query_pattern(f"Find {pattern_type.replace('_', ' ')}")
        if result["success"]:
            patterns[pattern_type] = result["pattern_embedding"]
            print(f"✅ Loaded {pattern_type}: {patterns[pattern_type].shape}")
        else:
            print(f"❌ Failed to load {pattern_type}")
            return

    # Test 1: Inter-pattern similarity
    print(f"\n📊 Test 1: Inter-Pattern Similarity")
    print("-" * 30)

    pattern_names = list(patterns.keys())
    similarities = {}

    for i, pattern1 in enumerate(pattern_names):
        for j, pattern2 in enumerate(pattern_names):
            if i <= j:  # Only compute upper triangle
                emb1 = patterns[pattern1].flatten().reshape(1, -1)
                emb2 = patterns[pattern2].flatten().reshape(1, -1)
                sim = cosine_similarity(emb1, emb2)[0, 0]
                similarities[(pattern1, pattern2)] = sim

                if pattern1 == pattern2:
                    print(f"  {pattern1} vs {pattern2}: {sim:.3f} (self-similarity)")
                else:
                    print(f"  {pattern1} vs {pattern2}: {sim:.3f}")

    # Test 2: Expected relationships
    print(f"\n🎯 Test 2: Expected Financial Relationships")
    print("-" * 40)

    # Market crashes and VIX spikes should be more similar (both represent market stress)
    crash_vix_sim = similarities[("market_crashes", "vix_spikes")]
    fed_crash_sim = similarities[("fed_rate_hikes", "market_crashes")]
    fed_vix_sim = similarities[("fed_rate_hikes", "vix_spikes")]

    print(f"Market crashes vs VIX spikes: {crash_vix_sim:.3f}")
    print(f"Fed hikes vs Market crashes: {fed_crash_sim:.3f}")
    print(f"Fed hikes vs VIX spikes: {fed_vix_sim:.3f}")

    # Expected: crashes and VIX should be most similar
    if crash_vix_sim > fed_crash_sim and crash_vix_sim > fed_vix_sim:
        print("✅ GOOD: Market crashes and VIX spikes are most similar (both = market stress)")
    else:
        print("⚠️  UNEXPECTED: Market stress patterns aren't clustering together")

    # Test 3: Embedding variance (are they all similar?)
    print(f"\n📈 Test 3: Embedding Distinctiveness")
    print("-" * 35)

    all_similarities = [sim for (p1, p2), sim in similarities.items() if p1 != p2]
    avg_similarity = np.mean(all_similarities)
    std_similarity = np.std(all_similarities)

    print(f"Average inter-pattern similarity: {avg_similarity:.3f}")
    print(f"Std deviation: {std_similarity:.3f}")

    if avg_similarity > 0.9:
        print("❌ BAD: Patterns are too similar - might be random/meaningless")
    elif avg_similarity < 0.3:
        print("✅ GOOD: Patterns are quite distinct")
    else:
        print("🤔 MIXED: Patterns show moderate similarity")

    # Test 4: Embedding magnitude
    print(f"\n📊 Test 4: Embedding Statistics")
    print("-" * 30)

    for pattern_name, embedding in patterns.items():
        flat_emb = embedding.flatten()
        print(f"{pattern_name}:")
        print(f"  Shape: {embedding.shape}")
        print(f"  Mean: {np.mean(flat_emb):.3f}")
        print(f"  Std: {np.std(flat_emb):.3f}")
        print(f"  Range: [{np.min(flat_emb):.3f}, {np.max(flat_emb):.3f}]")

    # Test 5: Random embedding comparison
    print(f"\n🎲 Test 5: Random Embedding Comparison")
    print("-" * 35)

    # Create random embeddings with same shapes
    random_patterns = {}
    for name, emb in patterns.items():
        random_patterns[f"random_{name}"] = np.random.randn(*emb.shape)

    # Compare real vs random
    fed_real = patterns["fed_rate_hikes"].flatten().reshape(1, -1)
    fed_random = random_patterns["random_fed_rate_hikes"].flatten().reshape(1, -1)

    real_vs_random = cosine_similarity(fed_real, fed_random)[0, 0]
    print(f"Real Fed hikes vs Random: {real_vs_random:.3f}")

    if abs(real_vs_random) < 0.1:
        print("✅ GOOD: Real embeddings are distinct from random")
    else:
        print("⚠️  WARNING: Real embeddings might be too similar to random")

    # Summary
    print(f"\n📋 Summary Assessment")
    print("-" * 20)

    if crash_vix_sim > 0.7 and avg_similarity < 0.8 and abs(real_vs_random) < 0.2:
        print("🎉 EXCELLENT: Embeddings appear to capture meaningful financial patterns!")
    elif crash_vix_sim > 0.5 and avg_similarity < 0.9:
        print("✅ GOOD: Embeddings show reasonable financial pattern structure")
    else:
        print("⚠️  CONCERNING: Embeddings may not be capturing meaningful patterns")

    return patterns, similarities


if __name__ == "__main__":
    patterns, similarities = test_embedding_quality()