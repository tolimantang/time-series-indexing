#!/usr/bin/env python3
"""
Test NewsEncoder for a specific date with full details.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

# Add the newsEncoder package to the path
# This works from any directory by going up to the time-series-indexing folder
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent
sys.path.insert(0, str(project_root))

from newsEncoder import NewsEncoder


def analyze_date(year, month, day):
    """Analyze a specific date with full details."""
    print(f"DETAILED FINANCIAL ANALYSIS")
    print("=" * 60)

    encoder = NewsEncoder()
    target_date = datetime(year, month, day, 12, 0, 0, tzinfo=timezone.utc)
    news_data = encoder.encode_date(target_date, include_market_data=True)

    print(f"Date: {target_date.strftime('%B %d, %Y')}")
    print(f"Quality Score: {news_data.quality_score:.1f}/1.0")
    print()

    print("DAILY SUMMARY:")
    print("-" * 30)
    print(news_data.daily_summary)
    print()

    if news_data.fed_events:
        print("FED EVENTS:")
        print("-" * 20)
        for event in news_data.fed_events:
            print(f"• {event.title}")
            if event.description:
                print(f"  {event.description}")
        print()

    if news_data.economic_data:
        print("ECONOMIC DATA:")
        print("-" * 25)
        for event in news_data.economic_data[:5]:
            print(f"• {event.title} [{event.importance}]")
            if event.actual_value:
                parts = []
                if event.actual_value:
                    parts.append(f"Actual: {event.actual_value}")
                if event.forecast_value:
                    parts.append(f"Forecast: {event.forecast_value}")
                if event.previous_value:
                    parts.append(f"Previous: {event.previous_value}")
                if parts:
                    print(f"  {', '.join(parts)}")
        print()

    if news_data.market_summary:
        print("MARKET SUMMARY:")
        print("-" * 25)
        market = news_data.market_summary

        if market.major_indices:
            print("Indices:")
            for symbol, change in market.major_indices.items():
                sign = "+" if change > 0 else ""
                print(f"  {symbol}: {sign}{change:.1f}%")

        if market.currencies:
            print("Currencies:")
            for symbol, change in market.currencies.items():
                sign = "+" if change > 0 else ""
                print(f"  {symbol}: {sign}{change:.1f}%")

        if market.commodities:
            print("Commodities:")
            for symbol, change in market.commodities.items():
                sign = "+" if change > 0 else ""
                print(f"  {symbol}: {sign}{change:.1f}%")

        if market.volatility:
            print("Volatility:")
            for symbol, level in market.volatility.items():
                print(f"  {symbol}: {level:.1f}")
        print()

    print("MAJOR HEADLINES:")
    print("-" * 25)
    for i, headline in enumerate(news_data.major_headlines[:5], 1):
        print(f"{i}. {headline}")
    print()

    print("COMBINED SUMMARY (for embedding/search):")
    print("-" * 45)
    print(f'"{news_data.get_combined_summary()}"')
    print()

    print(f"MARKET REGIME: {news_data.market_regime}")


if __name__ == "__main__":
    # Default to January 9, 2025 - change these values as needed
    analyze_date(2025, 1, 9)

    print("\n" + "=" * 60)
    print("To test other dates, modify the analyze_date() call above")
    print("Examples:")
    print("  analyze_date(2008, 9, 15)  # Lehman collapse")
    print("  analyze_date(2020, 3, 23)  # COVID crash")
    print("  analyze_date(2024, 12, 1)  # Recent date")