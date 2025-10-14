#!/usr/bin/env python3
"""
Simple test script for NewsEncoder with specific dates.
"""

from newsEncoder import NewsEncoder
from datetime import datetime, timezone


def test_date(year, month, day):
    """Test NewsEncoder for a specific date."""
    print(f"FINANCIAL ANALYSIS FOR {year}-{month:02d}-{day:02d}")
    print("=" * 50)

    encoder = NewsEncoder()
    target_date = datetime(year, month, day, 12, 0, 0, tzinfo=timezone.utc)
    news_data = encoder.encode_date(target_date, include_market_data=True)

    print(f"Date: {target_date.strftime('%B %d, %Y')}")
    print(f"Daily Summary: {news_data.daily_summary}")
    print(f"Market Regime: {news_data.market_regime}")
    print(f"Quality Score: {news_data.quality_score:.1f}/1.0")
    print()
    print("Combined Summary:")
    print(f'"{news_data.get_combined_summary()}"')
    print()

    if news_data.market_summary:
        print("Market Changes:")
        for symbol, change in news_data.market_summary.major_indices.items():
            print(f"  {symbol}: {change:+.1f}%")
        print()

    return news_data


if __name__ == "__main__":
    # Test January 9, 2025
    test_date(2025, 1, 9)

    print("=" * 50)
    print("To test other dates, modify the test_date() call above")
    print("Examples:")
    print("  test_date(2008, 9, 15)  # Lehman collapse")
    print("  test_date(2020, 3, 23)  # COVID crash")