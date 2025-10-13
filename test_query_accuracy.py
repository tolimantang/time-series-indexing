"""Test query accuracy - does querying 'fed hike' actually return fed hike patterns?"""

import sys
from pathlib import Path
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tsindexing.patterns.pattern_query import PatternQueryInterface


def test_query_accuracy():
    """Test if queries actually return the correct pattern types."""
    print("🎯 Testing Query Accuracy")
    print("=" * 40)

    # Initialize query interface
    query_interface = PatternQueryInterface()

    # Test queries with expected pattern types
    test_cases = [
        ("Find Fed rate hikes", "fed_rate_hikes"),
        ("Show me market crashes", "market_crashes"),
        ("VIX spike patterns", "vix_spikes"),
        ("Low volatility periods", "low_volatility"),
        ("Bull market steady climb", "bull_market_steady"),
        ("Federal Reserve interest rate increases", "fed_rate_hikes"),
        ("Market decline events", "market_crashes"),
        ("Calm market conditions", "low_volatility"),
    ]

    print("\n📝 Text-to-Pattern Mapping Test:")
    print("-" * 35)

    correct_mappings = 0
    total_mappings = len(test_cases)

    for query, expected_pattern in test_cases:
        result = query_interface.query_pattern(query)

        if result["success"]:
            actual_pattern = result["pattern_type"]
            is_correct = actual_pattern == expected_pattern
            status = "✅" if is_correct else "❌"

            print(f"  {status} '{query}' → {actual_pattern} (expected: {expected_pattern})")
            if is_correct:
                correct_mappings += 1
        else:
            print(f"  ❌ '{query}' → FAILED: {result['error']}")

    mapping_accuracy = correct_mappings / total_mappings
    print(f"\nMapping Accuracy: {correct_mappings}/{total_mappings} = {mapping_accuracy:.1%}")

    # Test similarity-based retrieval accuracy
    print(f"\n🔍 Similarity-Based Retrieval Test:")
    print("-" * 40)

    # Load all pattern embeddings
    patterns = {}
    for pattern_type in ["fed_rate_hikes", "market_crashes", "vix_spikes", "low_volatility", "bull_market_steady"]:
        result = query_interface.query_pattern(f"Find {pattern_type.replace('_', ' ')}")
        if result["success"]:
            patterns[pattern_type] = result["pattern_embedding"]

    if len(patterns) < 5:
        print("❌ Could not load all patterns for similarity test")
        return

    # Test: For each pattern, find its most similar pattern
    print("\nFor each pattern, finding most similar pattern:")

    retrieval_results = {}
    pattern_names = list(patterns.keys())

    for query_pattern in pattern_names:
        query_embedding = patterns[query_pattern]

        # Calculate similarities to all patterns (including itself)
        similarities = {}
        for target_pattern in pattern_names:
            target_embedding = patterns[target_pattern]
            sim = cosine_similarity([query_embedding], [target_embedding])[0, 0]
            similarities[target_pattern] = sim

        # Sort by similarity (highest first)
        sorted_patterns = sorted(similarities.items(), key=lambda x: x[1], reverse=True)

        # The most similar should be itself, second most similar is the retrieval result
        most_similar = sorted_patterns[0][0]
        second_most_similar = sorted_patterns[1][0] if len(sorted_patterns) > 1 else None

        retrieval_results[query_pattern] = {
            "most_similar": most_similar,
            "second_most_similar": second_most_similar,
            "similarities": sorted_patterns
        }

        # Check if it correctly identifies itself as most similar
        self_correct = most_similar == query_pattern
        status = "✅" if self_correct else "❌"

        print(f"  {status} Query: {query_pattern}")
        print(f"      Most similar: {most_similar} ({similarities[most_similar]:.3f})")
        print(f"      2nd similar: {second_most_similar} ({similarities[second_most_similar]:.3f})")

    # Test cross-regime retrieval
    print(f"\n🌊 Cross-Regime Retrieval Test:")
    print("-" * 35)

    stress_patterns = ["fed_rate_hikes", "market_crashes", "vix_spikes"]
    calm_patterns = ["low_volatility", "bull_market_steady"]

    print("Testing if stress patterns are most similar to other stress patterns:")

    correct_regime_retrievals = 0
    total_regime_tests = 0

    for stress_pattern in stress_patterns:
        similarities = retrieval_results[stress_pattern]["similarities"]

        # Find the most similar pattern that's NOT itself
        second_most = similarities[1][0]
        second_sim = similarities[1][1]

        is_stress = second_most in stress_patterns
        status = "✅" if is_stress else "❌"

        print(f"  {status} {stress_pattern} → {second_most} ({second_sim:.3f})")

        if is_stress:
            correct_regime_retrievals += 1
        total_regime_tests += 1

    print("\nTesting if calm patterns are most similar to other calm patterns:")

    for calm_pattern in calm_patterns:
        similarities = retrieval_results[calm_pattern]["similarities"]

        # Find the most similar pattern that's NOT itself
        second_most = similarities[1][0]
        second_sim = similarities[1][1]

        is_calm = second_most in calm_patterns
        status = "✅" if is_calm else "❌"

        print(f"  {status} {calm_pattern} → {second_most} ({second_sim:.3f})")

        if is_calm:
            correct_regime_retrievals += 1
        total_regime_tests += 1

    regime_accuracy = correct_regime_retrievals / total_regime_tests
    print(f"\nRegime Accuracy: {correct_regime_retrievals}/{total_regime_tests} = {regime_accuracy:.1%}")

    # Overall assessment
    print(f"\n📊 Overall Query Accuracy Assessment:")
    print("-" * 40)

    print(f"Text Mapping Accuracy: {mapping_accuracy:.1%}")
    print(f"Regime Retrieval Accuracy: {regime_accuracy:.1%}")

    if mapping_accuracy >= 0.8 and regime_accuracy >= 0.6:
        print("🎉 GOOD: Query system works reasonably well!")
    elif mapping_accuracy >= 0.8:
        print("🤔 MIXED: Text mapping works, but similarity retrieval is poor")
    elif regime_accuracy >= 0.6:
        print("🤔 MIXED: Similarity works somewhat, but text mapping fails")
    else:
        print("⚠️  POOR: Both text mapping and similarity retrieval have issues")

    return retrieval_results


if __name__ == "__main__":
    results = test_query_accuracy()