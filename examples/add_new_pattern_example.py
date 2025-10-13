"""Example: How to add new pattern types to the pattern library."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tsindexing.patterns.llm_pattern_builder import LLMPatternBuilder


def add_earnings_pattern():
    """Example of adding a new 'earnings_beats' pattern."""

    print("📝 How to Add New Pattern Types")
    print("=" * 40)

    print("\n1️⃣ Edit llm_pattern_builder.py:")
    print("-" * 30)

    new_pattern_code = '''
# Add to curated_patterns dictionary around line 137:

"earnings_beats": [
    # Major tech earnings beats
    "2021-01-27",  # AAPL beats Q1 2021
    "2021-04-28",  # GOOGL beats Q1 2021
    "2021-07-27",  # AAPL beats Q2 2021
    "2021-10-26",  # GOOGL beats Q3 2021
    "2022-01-27",  # AAPL beats Q4 2021
    "2022-04-26",  # GOOGL beats Q1 2022
    "2022-07-26",  # AAPL beats Q2 2022
    "2023-01-26",  # AAPL beats Q4 2022
    "2023-04-25",  # GOOGL beats Q1 2023
    "2023-07-27",  # AAPL beats Q2 2023
],

"fed_rate_cuts": [
    # Federal Reserve rate decreases
    "2020-03-03",  # Emergency cut COVID
    "2020-03-15",  # Emergency cut to 0%
    "2019-07-31",  # First cut in decade
    "2019-09-18",  # Second cut
    "2019-10-30",  # Third cut
    "2008-10-08",  # Financial crisis cuts
    "2008-10-29",
    "2008-12-16",
    "2007-09-18",  # Pre-crisis cuts
    "2007-10-31",
    "2007-12-11",
],
'''

    print(new_pattern_code)

    print("\n2️⃣ Update the pattern loop in build_pattern_library():")
    print("-" * 50)

    loop_code = '''
# Around line 269, change from:
for pattern_type in ["fed_rate_hikes", "market_crashes", "vix_spikes"]:

# To:
for pattern_type in ["fed_rate_hikes", "market_crashes", "vix_spikes", "earnings_beats", "fed_rate_cuts"]:
'''

    print(loop_code)

    print("\n3️⃣ Update pattern_query.py text mapping:")
    print("-" * 40)

    query_code = '''
# Add to text_to_pattern_map around line 25:

# Earnings-related queries
"earnings": "earnings_beats",
"beat estimates": "earnings_beats",
"earnings surprise": "earnings_beats",
"tech earnings": "earnings_beats",

# Rate cut queries
"rate cut": "fed_rate_cuts",
"rate decrease": "fed_rate_cuts",
"monetary easing": "fed_rate_cuts",
"emergency cuts": "fed_rate_cuts",
'''

    print(query_code)

    print("\n4️⃣ Rebuild the pattern library:")
    print("-" * 30)
    print("python run_pattern_builder.py")

    print("\n5️⃣ Test the new patterns:")
    print("-" * 25)
    test_code = '''
from tsindexing.patterns.pattern_query import PatternQueryInterface

query_interface = PatternQueryInterface()

# Test new patterns
result1 = query_interface.query_pattern("Find periods like earnings beats")
result2 = query_interface.query_pattern("Show Fed rate cutting cycles")

print(result1["pattern_type"])  # Should be "earnings_beats"
print(result2["pattern_type"])  # Should be "fed_rate_cuts"
'''

    print(test_code)


def manual_pattern_generation():
    """Show how to manually generate patterns."""

    print("\n🛠️ Manual Pattern Generation")
    print("=" * 30)

    manual_code = '''
from tsindexing.patterns.llm_pattern_builder import LLMPatternBuilder

# Create builder
builder = LLMPatternBuilder()

# Manual approach: override the get_llm_pattern_dates method
def custom_get_dates(pattern_type):
    if pattern_type == "crypto_crashes":
        return [
            "2018-01-16",  # Crypto crash start
            "2018-02-05",  # Major decline
            "2022-05-09",  # Terra Luna collapse
            "2022-06-13",  # Celsius crisis
            "2022-11-08",  # FTX collapse
        ]
    return builder.get_llm_pattern_dates(pattern_type)

# Replace method temporarily
builder.get_llm_pattern_dates = custom_get_dates

# Build with custom pattern
# (You'd need to also add "crypto_crashes" to the loop)
'''

    print(manual_code)


def direct_json_modification():
    """Show how to directly modify the JSON file."""

    print("\n📄 Direct JSON Modification")
    print("=" * 25)

    json_code = '''
# You can also directly edit patterns/pattern_library_spy.json:

{
  "fed_rate_hikes": { ... existing ... },
  "market_crashes": { ... existing ... },
  "vix_spikes": { ... existing ... },

  "new_pattern_type": {
    "dates": [
      "2023-01-01",
      "2023-02-01",
      "2023-03-01"
    ],
    "valid_segments": 3,
    "embedding": [0.1, 0.2, 0.3, ...],  # 512 values
    "asset": "SPY",
    "created_at": "2024-01-01T00:00:00"
  }
}

# But you'd still need to:
# 1. Calculate proper embeddings (run through Chronos)
# 2. Update pattern_query.py text mappings
# 3. Test the integration
'''

    print(json_code)


if __name__ == "__main__":
    add_earnings_pattern()
    manual_pattern_generation()
    direct_json_modification()

    print("\n🎯 Summary:")
    print("=" * 10)
    print("1. Edit curated_patterns in llm_pattern_builder.py")
    print("2. Update pattern loop in build_pattern_library()")
    print("3. Add text mappings in pattern_query.py")
    print("4. Run: python run_pattern_builder.py")
    print("5. Test with new queries")