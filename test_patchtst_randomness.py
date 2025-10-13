"""Test if PatchTST is actually using input data or generating random numbers."""

import sys
from pathlib import Path
import numpy as np
import torch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tsindexing.patterns.llm_pattern_builder import LLMPatternBuilder


def test_patchtst_responds_to_input():
    """Test if PatchTST embeddings actually change based on input."""
    print("🧪 Testing if PatchTST Uses Input Data")
    print("=" * 45)

    builder = LLMPatternBuilder()

    # Test 1: Same input should give same embedding
    print("\n📊 Test 1: Reproducibility")
    print("-" * 25)

    # Create identical fake segments (512 length for pre-trained model)
    fake_segment = {
        "values": np.array([[100 + i*0.1, 1000] for i in range(512)]),
    }

    segments1 = [fake_segment]
    segments2 = [fake_segment]

    embedding1 = builder.create_pattern_embedding(segments1)
    embedding2 = builder.create_pattern_embedding(segments2)

    # Should be identical
    are_identical = np.allclose(embedding1, embedding2, atol=1e-6)
    print(f"Same input produces same embedding: {are_identical}")

    if are_identical:
        print("✅ GOOD: Model is deterministic")
    else:
        print("❌ BAD: Model is non-deterministic (random)")

    # Test 2: Different inputs should give different embeddings
    print("\n📊 Test 2: Input Sensitivity")
    print("-" * 30)

    # Create very different fake segments (512 length)
    flat_segment = {
        "values": np.array([[100, 1000]] * 512),  # Completely flat
    }

    volatile_segment = {
        "values": np.array([[100 + 50*np.sin(i*0.1), 1000] for i in range(512)]),  # Volatile sine wave
    }

    linear_up_segment = {
        "values": np.array([[100 + i*0.5, 1000] for i in range(512)]),  # Linear uptrend
    }

    linear_down_segment = {
        "values": np.array([[356 - i*0.5, 1000] for i in range(512)]),  # Linear downtrend
    }

    # Get embeddings
    flat_emb = builder.create_pattern_embedding([flat_segment])
    volatile_emb = builder.create_pattern_embedding([volatile_segment])
    up_emb = builder.create_pattern_embedding([linear_up_segment])
    down_emb = builder.create_pattern_embedding([linear_down_segment])

    from sklearn.metrics.pairwise import cosine_similarity

    # Compare similarities
    flat_vs_volatile = cosine_similarity([flat_emb], [volatile_emb])[0, 0]
    flat_vs_up = cosine_similarity([flat_emb], [up_emb])[0, 0]
    flat_vs_down = cosine_similarity([flat_emb], [down_emb])[0, 0]
    up_vs_down = cosine_similarity([up_emb], [down_emb])[0, 0]

    print(f"Flat vs Volatile: {flat_vs_volatile:.6f}")
    print(f"Flat vs Up trend: {flat_vs_up:.6f}")
    print(f"Flat vs Down trend: {flat_vs_down:.6f}")
    print(f"Up trend vs Down trend: {up_vs_down:.6f}")

    avg_diff_similarity = np.mean([flat_vs_volatile, flat_vs_up, flat_vs_down, up_vs_down])

    if avg_diff_similarity > 0.95:
        print("❌ BAD: Very different inputs produce very similar embeddings")
        print("     This suggests the model is not using input meaningfully")
    elif avg_diff_similarity > 0.8:
        print("⚠️  CONCERNING: Different inputs are still quite similar")
    else:
        print("✅ GOOD: Different inputs produce meaningfully different embeddings")

    # Test 3: Scaling sensitivity
    print("\n📊 Test 3: Scale Sensitivity")
    print("-" * 30)

    normal_segment = {
        "values": np.array([[100 + i*0.1, 1000] for i in range(512)]),
    }

    scaled_segment = {
        "values": np.array([[1000 + i, 1000] for i in range(512)]),  # 10x scaled
    }

    normal_emb = builder.create_pattern_embedding([normal_segment])
    scaled_emb = builder.create_pattern_embedding([scaled_segment])

    scale_similarity = cosine_similarity([normal_emb], [scaled_emb])[0, 0]
    print(f"Normal vs 10x scaled (same shape): {scale_similarity:.6f}")

    if scale_similarity > 0.99:
        print("✅ GOOD: Model is scale-invariant (focuses on shape)")
    elif scale_similarity > 0.9:
        print("🤔 OK: Model has some scale invariance")
    else:
        print("⚠️  WARNING: Model is very scale-sensitive")

    # Test 4: Compare to actual random embeddings
    print("\n📊 Test 4: vs True Random")
    print("-" * 30)

    random_emb1 = np.random.randn(5504)  # Match PatchTST embedding size
    random_emb2 = np.random.randn(5504)

    random_vs_random = cosine_similarity([random_emb1], [random_emb2])[0, 0]
    real_vs_real = flat_vs_volatile  # Use our most different real embeddings

    print(f"True random vs True random: {random_vs_random:.6f}")
    print(f"Real different vs Real different: {real_vs_real:.6f}")

    if abs(real_vs_real - random_vs_random) < 0.1:
        print("❌ CRITICAL: Real embeddings are no different from random!")
    elif real_vs_real > 0.95:
        print("❌ BAD: Real embeddings are too similar (possibly meaningless)")
    else:
        print("✅ GOOD: Real embeddings show more structure than random")

    # Final assessment
    print(f"\n📋 Final Assessment")
    print("-" * 20)

    if are_identical and avg_diff_similarity < 0.8:
        print("🎉 EXCELLENT: PatchTST is deterministic and input-sensitive")
    elif are_identical and avg_diff_similarity < 0.95:
        print("✅ GOOD: PatchTST works but has limited discrimination")
    elif are_identical:
        print("⚠️  CONCERNING: PatchTST is deterministic but not discriminative")
    else:
        print("❌ CRITICAL: PatchTST appears to be generating random numbers")

    return {
        "deterministic": are_identical,
        "avg_different_similarity": avg_diff_similarity,
        "scale_similarity": scale_similarity,
        "random_similarity": random_vs_random,
        "real_similarity": real_vs_real
    }


if __name__ == "__main__":
    results = test_patchtst_responds_to_input()