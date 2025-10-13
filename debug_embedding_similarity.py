"""Debug why embeddings are so similar."""

import sys
from pathlib import Path
import numpy as np
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def analyze_raw_embeddings():
    """Look at the actual embedding values to understand the similarity."""

    # Load the pattern library directly
    pattern_file = Path("patterns/pattern_library_spy.json")
    with open(pattern_file, 'r') as f:
        patterns = json.load(f)

    print("🔍 Analyzing Raw Embedding Values")
    print("=" * 40)

    for pattern_name, data in patterns.items():
        embedding = np.array(data["embedding"])
        print(f"\n{pattern_name}:")
        print(f"  Shape: {embedding.shape}")
        print(f"  Mean: {np.mean(embedding):.6f}")
        print(f"  Std: {np.std(embedding):.6f}")
        print(f"  Min: {np.min(embedding):.6f}")
        print(f"  Max: {np.max(embedding):.6f}")
        print(f"  Range: {np.max(embedding) - np.min(embedding):.6f}")

        # Look at first 10 values
        print(f"  First 10 values: {embedding[:10].round(4)}")

        # Check for patterns
        near_zero = np.sum(np.abs(embedding) < 0.001)
        print(f"  Values near zero (<0.001): {near_zero}/{len(embedding)} ({near_zero/len(embedding)*100:.1f}%)")

    print(f"\n🔬 Cross-Pattern Analysis")
    print("-" * 25)

    # Compare actual embedding values
    fed_emb = np.array(patterns["fed_rate_hikes"]["embedding"])
    crash_emb = np.array(patterns["market_crashes"]["embedding"])
    vix_emb = np.array(patterns["vix_spikes"]["embedding"])

    # Element-wise differences
    fed_crash_diff = np.abs(fed_emb - crash_emb)
    fed_vix_diff = np.abs(fed_emb - vix_emb)
    crash_vix_diff = np.abs(crash_emb - vix_emb)

    print(f"Fed vs Crash - Mean absolute difference: {np.mean(fed_crash_diff):.6f}")
    print(f"Fed vs VIX - Mean absolute difference: {np.mean(fed_vix_diff):.6f}")
    print(f"Crash vs VIX - Mean absolute difference: {np.mean(crash_vix_diff):.6f}")

    # Check if they're just scaled versions of each other
    correlations = np.corrcoef([fed_emb, crash_emb, vix_emb])
    print(f"\nPearson correlations:")
    print(f"Fed vs Crash: {correlations[0,1]:.6f}")
    print(f"Fed vs VIX: {correlations[0,2]:.6f}")
    print(f"Crash vs VIX: {correlations[1,2]:.6f}")

    # Test if they're identical or near-identical
    print(f"\n🎯 Identity Tests")
    print("-" * 15)

    fed_crash_identical = np.allclose(fed_emb, crash_emb, atol=1e-6)
    fed_vix_identical = np.allclose(fed_emb, vix_emb, atol=1e-6)
    crash_vix_identical = np.allclose(crash_emb, vix_emb, atol=1e-6)

    print(f"Fed ≈ Crash (1e-6 tolerance): {fed_crash_identical}")
    print(f"Fed ≈ VIX (1e-6 tolerance): {fed_vix_identical}")
    print(f"Crash ≈ VIX (1e-6 tolerance): {crash_vix_identical}")

    # Check broader tolerances
    for tol in [1e-5, 1e-4, 1e-3, 1e-2]:
        if np.allclose(fed_emb, crash_emb, atol=tol):
            print(f"Fed ≈ Crash at tolerance {tol}")
            break

    # Generate truly random embeddings for comparison
    print(f"\n🎲 Random Embedding Comparison")
    print("-" * 30)

    random1 = np.random.randn(512)
    random2 = np.random.randn(512)

    from sklearn.metrics.pairwise import cosine_similarity

    random_similarity = cosine_similarity([random1], [random2])[0,0]
    real_similarity = cosine_similarity([fed_emb], [crash_emb])[0,0]

    print(f"Random vs Random similarity: {random_similarity:.6f}")
    print(f"Fed vs Crash similarity: {real_similarity:.6f}")
    print(f"Difference: {abs(real_similarity - random_similarity):.6f}")

    if abs(real_similarity) > 0.9:
        print("❌ WARNING: Real embeddings are suspiciously similar")
    elif abs(real_similarity - random_similarity) < 0.1:
        print("⚠️  CAUTION: Real embeddings not much different from random")
    else:
        print("✅ OK: Real embeddings show meaningful structure")


if __name__ == "__main__":
    analyze_raw_embeddings()