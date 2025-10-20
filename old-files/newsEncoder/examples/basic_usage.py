#!/usr/bin/env python3
"""
Basic usage examples for NewsEncoder.

This script demonstrates how to use the NewsEncoder to get financial news
and economic events for specific dates.
"""

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add the newsEncoder package to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from newsEncoder import NewsEncoder


def example_current_news():
    """Example: Get current financial news."""
    print("=" * 60)
    print("CURRENT FINANCIAL NEWS")
    print("=" * 60)

    # Create encoder (works without API keys using sample data)
    encoder = NewsEncoder()

    # Get current news
    current_news = encoder.get_current_news()

    print(f"Date: {current_news.date}")
    print(f"Quality Score: {current_news.quality_score:.1f}/1.0")
    print()

    print("DAILY SUMMARY:")
    print("-" * 30)
    print(current_news.daily_summary)
    print()

    if current_news.fed_events:
        print("FED EVENTS:")
        print("-" * 20)
        for event in current_news.fed_events:
            print(f"• {event.title}")
            if event.description:
                print(f"  {event.description}")
        print()

    if current_news.economic_data:
        print("ECONOMIC DATA:")
        print("-" * 25)
        for event in current_news.economic_data[:5]:  # Top 5
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

    if current_news.market_summary:
        print("MARKET SUMMARY:")
        print("-" * 25)
        market = current_news.market_summary

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
    for i, headline in enumerate(current_news.major_headlines[:5], 1):
        print(f"{i}. {headline}")
    print()

    print("COMBINED SUMMARY (for embedding/search):")
    print("-" * 45)
    print(current_news.get_combined_summary())


def example_specific_date():
    """Example: Get news for a specific date."""
    print("\n" + "=" * 60)
    print("SPECIFIC DATE ANALYSIS")
    print("=" * 60)

    encoder = NewsEncoder()

    # Analyze a specific date: January 15, 2024
    target_date = datetime(2025, 1, 9, 12, 0, 0, tzinfo=timezone.utc)
    news_data = encoder.encode_date(target_date, include_market_data=True)

    print(f"Analysis for: {target_date.strftime('%B %d, %Y')}")
    print()

    print("EVENT BREAKDOWN:")
    print("-" * 30)
    print(f"Fed Events: {len(news_data.fed_events)}")
    print(f"Economic Data: {len(news_data.economic_data)}")
    print(f"Earnings Events: {len(news_data.earnings_events)}")
    print(f"Geopolitical Events: {len(news_data.geopolitical_events)}")
    print(f"Major Headlines: {len(news_data.major_headlines)}")
    print()

    if news_data.fed_summary:
        print("FED SUMMARY:")
        print("-" * 20)
        print(news_data.fed_summary)
        print()

    print("MARKET REGIME:")
    print("-" * 20)
    print(f"Regime: {news_data.market_regime}")
    print()

    print("COMBINED SUMMARY:")
    print("-" * 25)
    print(news_data.get_combined_summary())


def example_batch_analysis():
    """Example: Analyze multiple dates."""
    print("\n" + "=" * 60)
    print("BATCH DATE ANALYSIS")
    print("=" * 60)

    encoder = NewsEncoder()

    # Analyze last 5 days
    end_date = datetime.now(timezone.utc)
    dates = []
    for i in range(5):
        date = end_date - timedelta(days=i)
        dates.append(date)

    print("Analyzing last 5 days...")
    results = encoder.batch_encode_dates(dates)

    print()
    print("RESULTS SUMMARY:")
    print("-" * 30)
    print("Date           | Quality | Fed Events | Economic Data | Market Regime")
    print("-" * 75)

    for news_data in results:
        date_str = news_data.date.strftime('%Y-%m-%d')
        quality_str = f"{news_data.quality_score:.1f}"
        fed_count = len(news_data.fed_events)
        econ_count = len(news_data.economic_data)
        regime = news_data.market_regime or 'unknown'

        print(f"{date_str:>12} | {quality_str:>6} | {fed_count:>9} | {econ_count:>12} | {regime}")

    print()
    print("SAMPLE COMBINED SUMMARIES:")
    print("-" * 35)
    for i, news_data in enumerate(results[:3], 1):
        date_str = news_data.date.strftime('%Y-%m-%d')
        summary = news_data.get_combined_summary()
        print(f"{i}. {date_str}: {summary}")


def example_with_api_keys():
    """Example: Using NewsEncoder with API keys."""
    print("\n" + "=" * 60)
    print("USING WITH API KEYS")
    print("=" * 60)

    print("To use with real APIs, provide configuration:")
    print()
    print("config = {")
    print("    'newsapi_key': 'your_newsapi_key_here',")
    print("    'alpha_vantage_key': 'your_alpha_vantage_key_here',")
    print("    'tradingeconomics_key': 'your_tradingeconomics_key_here'")
    print("}")
    print()
    print("encoder = NewsEncoder(config)")
    print("news_data = encoder.get_current_news()")
    print()
    print("API Key Sources:")
    print("• NewsAPI: https://newsapi.org/")
    print("• Alpha Vantage: https://www.alphavantage.co/")
    print("• Trading Economics: https://tradingeconomics.com/api/")


def example_search_functionality():
    """Example: How the data would be used for search."""
    print("\n" + "=" * 60)
    print("SEARCH FUNCTIONALITY DEMO")
    print("=" * 60)

    encoder = NewsEncoder()

    # Get sample data
    current_news = encoder.get_current_news()

    print("SAMPLE SEARCH SCENARIOS:")
    print("-" * 40)

    # Sample search queries
    search_queries = [
        "Fed hiking cycle with market volatility",
        "Strong earnings with tech sector outperformance",
        "Economic data beats expectations",
        "Geopolitical tensions affecting oil prices",
        "Low volatility environment with steady growth"
    ]

    print("Your system could search for patterns like:")
    for i, query in enumerate(search_queries, 1):
        print(f"{i}. \"{query}\"")

    print()
    print("Current day summary for comparison:")
    print(f"\"{current_news.get_combined_summary()}\"")
    print()
    print("ChromaDB would find similar days based on semantic similarity")
    print("of these combined summaries!")


def main():
    """Run all examples."""
    print("NewsEncoder Examples")
    print("=" * 60)

    try:
        # example_current_news()  # Skip current news, show specific date instead
        example_specific_date()
        example_batch_analysis()
        example_with_api_keys()
        example_search_functionality()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        print()
        print("Next steps:")
        print("1. Get API keys for real data")
        print("2. Integration with ChromaDB for similarity search")
        print("3. Combine with astroEncoder for correlation analysis")

    except Exception as e:
        print(f"\nError running examples: {e}")
        print("\nMake sure you're running from the correct directory.")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())