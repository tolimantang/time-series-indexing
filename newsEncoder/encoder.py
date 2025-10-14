"""
Main NewsEncoder class for financial news and economic event data collection.
"""

import requests
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import time
from urllib.parse import quote

from .data_models import FinancialNewsData, EconomicEvent, MarketSummary


class NewsEncoder:
    """
    Encodes financial news and economic events for a given date.
    Supports multiple APIs with fallback mechanisms.
    """

    def __init__(self, config: Optional[Dict[str, str]] = None):
        """
        Initialize NewsEncoder with API configurations.

        Args:
            config: Dictionary with API keys and settings
                {
                    'newsapi_key': 'your_newsapi_key',
                    'financialnews_key': 'your_financialnews_key',
                    'tradingeconomics_key': 'your_tradingeconomics_key',
                    'alpha_vantage_key': 'your_alpha_vantage_key'
                }
        """
        self.config = config or {}

        # API endpoints
        self.newsapi_url = "https://newsapi.org/v2/everything"
        self.alpha_vantage_url = "https://www.alphavantage.co/query"

        # Financial keywords for filtering
        self.financial_keywords = [
            'fed', 'federal reserve', 'interest rates', 'inflation', 'gdp',
            'employment', 'earnings', 'stock market', 'dow jones', 's&p 500',
            'nasdaq', 'oil prices', 'gold', 'dollar', 'euro', 'yen',
            'treasury', 'bond', 'yield', 'recession', 'growth'
        ]

        # Economic event categories
        self.event_categories = {
            'fed': ['fomc', 'federal reserve', 'fed decision', 'powell', 'interest rate'],
            'economic_data': ['gdp', 'inflation', 'cpi', 'unemployment', 'jobs report', 'retail sales'],
            'earnings': ['earnings', 'quarterly results', 'profit', 'revenue', 'eps'],
            'geopolitical': ['trade war', 'sanctions', 'election', 'brexit', 'china', 'russia']
        }

    def encode_date(self, date: datetime, include_market_data: bool = True) -> FinancialNewsData:
        """
        Encode financial news and events for a specific date.

        Args:
            date: Target date for data collection
            include_market_data: Whether to include market summary data

        Returns:
            FinancialNewsData object with all collected information
        """
        print(f"Encoding financial news for {date.strftime('%Y-%m-%d')}...")

        # Initialize result
        news_data = FinancialNewsData(date=date)

        try:
            # Collect news from multiple sources
            news_articles = self._collect_news_articles(date)

            # Process and categorize events
            self._process_news_articles(news_data, news_articles)

            # Get economic calendar events
            economic_events = self._get_economic_events(date)
            self._process_economic_events(news_data, economic_events)

            # Get market data if requested
            if include_market_data:
                market_summary = self._get_market_summary(date)
                news_data.market_summary = market_summary

            # Generate summaries
            self._generate_summaries(news_data)

            # Calculate quality score
            news_data.quality_score = self._calculate_quality_score(news_data)

            print(f"✓ Collected {len(news_articles)} articles, {len(economic_events)} events")

        except Exception as e:
            print(f"Warning: Error collecting data for {date}: {e}")
            news_data.daily_summary = f"Limited data available for {date.strftime('%Y-%m-%d')}"

        return news_data

    def _collect_news_articles(self, date: datetime) -> List[Dict[str, Any]]:
        """Collect news articles from available APIs."""
        articles = []

        # Try NewsAPI if key is available
        if self.config.get('newsapi_key'):
            newsapi_articles = self._get_newsapi_articles(date)
            articles.extend(newsapi_articles)
            time.sleep(0.1)  # Rate limiting

        # Try free sources if no API key
        if not articles:
            free_articles = self._get_free_news_sources(date)
            articles.extend(free_articles)

        return articles

    def _get_newsapi_articles(self, date: datetime) -> List[Dict[str, Any]]:
        """Get articles from NewsAPI."""
        try:
            # Format date for API
            date_str = date.strftime('%Y-%m-%d')

            # Build query with financial keywords
            query = ' OR '.join(self.financial_keywords[:5])  # Limit query length

            params = {
                'q': query,
                'from': date_str,
                'to': date_str,
                'language': 'en',
                'sortBy': 'relevancy',
                'pageSize': 50,
                'apiKey': self.config['newsapi_key']
            }

            response = requests.get(self.newsapi_url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return data.get('articles', [])
            else:
                print(f"NewsAPI error: {response.status_code}")
                return []

        except Exception as e:
            print(f"Error fetching NewsAPI articles: {e}")
            return []

    def _get_free_news_sources(self, date: datetime) -> List[Dict[str, Any]]:
        """Get news from free sources (mock implementation with date-specific variations)."""
        date_str = date.strftime('%Y-%m-%d')
        year = date.year
        month = date.month
        day = date.day

        # Create date-specific variations for demonstration
        sample_articles = []

        # Historical event simulation based on dates
        if year == 2008 and month == 9 and day == 15:
            sample_articles = [
                {
                    'title': 'Lehman Brothers Files for Bankruptcy',
                    'description': 'Investment bank Lehman Brothers filed for bankruptcy protection in largest failure in US history.',
                    'publishedAt': f'{date_str}T08:00:00Z',
                    'source': {'name': 'Financial Crisis News'},
                    'content': 'Global financial markets in turmoil as Lehman Brothers collapses, triggering credit crisis.'
                },
                {
                    'title': 'Markets Crash on Financial System Fears',
                    'description': 'Stock markets plummet as investors flee to safety amid banking sector collapse.',
                    'publishedAt': f'{date_str}T16:00:00Z',
                    'source': {'name': 'Market Watch'},
                    'content': 'VIX volatility index spikes above 40 as panic selling grips Wall Street.'
                }
            ]
        elif year == 2020 and month == 3 and (10 <= day <= 25):
            sample_articles = [
                {
                    'title': 'COVID-19 Pandemic Triggers Market Crash',
                    'description': 'Global markets collapse as coronavirus pandemic spreads worldwide.',
                    'publishedAt': f'{date_str}T09:00:00Z',
                    'source': {'name': 'Pandemic News'},
                    'content': 'S&P 500 down over 30% from February highs as lockdowns halt economic activity.'
                },
                {
                    'title': 'Fed Cuts Rates to Zero in Emergency Move',
                    'description': 'Federal Reserve slashes interest rates to near zero and announces QE program.',
                    'publishedAt': f'{date_str}T14:00:00Z',
                    'source': {'name': 'Fed Watch'},
                    'content': 'Powell announces unlimited bond purchases to support credit markets.'
                }
            ]
        elif year >= 2022 and month >= 3:
            # Recent period - inflation/rate hiking cycle
            sample_articles = [
                {
                    'title': 'Fed Continues Aggressive Rate Hiking Campaign',
                    'description': 'Federal Reserve raises rates by 75 basis points to combat persistent inflation.',
                    'publishedAt': f'{date_str}T14:00:00Z',
                    'source': {'name': 'Fed Policy News'},
                    'content': 'Powell emphasizes commitment to bringing inflation back to 2% target.'
                },
                {
                    'title': 'Inflation Data Shows Persistent Price Pressures',
                    'description': 'CPI remains elevated above Fed target despite rate increases.',
                    'publishedAt': f'{date_str}T08:30:00Z',
                    'source': {'name': 'Economic Data'},
                    'content': 'Core inflation readings show broad-based price increases across sectors.'
                }
            ]
        else:
            # Default sample for other dates
            market_sentiment = "mixed" if (day % 2 == 0) else "positive"
            fed_action = "holds rates steady" if (month % 2 == 0) else "signals policy patience"

            sample_articles = [
                {
                    'title': f'Market Update: Stocks Close {market_sentiment.title()} on Economic Data',
                    'description': f'Major indices showed {market_sentiment} performance as investors digested economic data releases.',
                    'publishedAt': f'{date_str}T16:00:00Z',
                    'source': {'name': 'Financial Sample'},
                    'content': f'Markets showed {market_sentiment} signals with sector rotation based on data releases.'
                },
                {
                    'title': f'Fed Officials Signal Policy Direction for {year}',
                    'description': f'Federal Reserve {fed_action} amid economic data review.',
                    'publishedAt': f'{date_str}T14:30:00Z',
                    'source': {'name': 'Economic Times Sample'},
                    'content': f'Federal Reserve officials emphasized data-dependent approach for {year} policy.'
                }
            ]

        return sample_articles

    def _get_economic_events(self, date: datetime) -> List[Dict[str, Any]]:
        """Get economic calendar events (mock implementation)."""
        # This would integrate with Trading Economics API or similar
        # For now, returning sample events

        sample_events = [
            {
                'event': 'Consumer Price Index',
                'country': 'United States',
                'actual': '3.2%',
                'forecast': '3.1%',
                'previous': '3.0%',
                'importance': 'high',
                'category': 'economic_data'
            },
            {
                'event': 'Retail Sales',
                'country': 'United States',
                'actual': '0.6%',
                'forecast': '0.4%',
                'previous': '0.2%',
                'importance': 'medium',
                'category': 'economic_data'
            }
        ]

        return sample_events

    def _get_market_summary(self, date: datetime) -> MarketSummary:
        """Get market data summary (mock implementation with date-specific variations)."""
        year = date.year
        month = date.month
        day = date.day

        # Create date-specific market scenarios
        if year == 2008 and month == 9 and day == 15:
            # Lehman collapse - massive sell-off
            return MarketSummary(
                major_indices={'SPY': -4.7, 'QQQ': -5.1, 'DIA': -4.4},
                currencies={'EUR/USD': 1.2, 'GBP/USD': -0.8, 'USD/JPY': -2.1},
                commodities={'Oil': -6.1, 'Gold': 2.8, 'Silver': 1.2},
                volatility={'VIX': 42.3},
                sector_performance={'Technology': -5.8, 'Energy': -7.2, 'Financials': -12.4}
            )
        elif year == 2020 and month == 3 and (10 <= day <= 25):
            # COVID crash
            return MarketSummary(
                major_indices={'SPY': -9.5, 'QQQ': -8.2, 'DIA': -10.1},
                currencies={'EUR/USD': -1.8, 'GBP/USD': -2.1, 'USD/JPY': 1.5},
                commodities={'Oil': -24.2, 'Gold': 1.8, 'Silver': -3.2},
                volatility={'VIX': 78.6},
                sector_performance={'Technology': -6.2, 'Energy': -18.4, 'Financials': -15.1}
            )
        elif year >= 2022 and month >= 3:
            # Inflation/rate hiking period - moderate volatility
            vix_level = 18.5 + (day % 10)  # Vary VIX by day
            return MarketSummary(
                major_indices={'SPY': 0.2 - (day % 5) * 0.3, 'QQQ': -0.8 + (day % 4) * 0.4, 'DIA': 0.1},
                currencies={'EUR/USD': -0.2, 'GBP/USD': -0.1, 'USD/JPY': 0.3},
                commodities={'Oil': 1.1 + (month % 3), 'Gold': -0.5, 'Silver': -0.8},
                volatility={'VIX': vix_level},
                sector_performance={'Technology': -1.2, 'Energy': 2.8, 'Financials': 0.5}
            )
        else:
            # Default with date-based variations
            spy_change = (day % 3) - 1  # -1, 0, or 1
            qqq_change = (day % 4) - 1.5  # -1.5 to 2.5
            vix_level = 12.5 + (month % 8) + (day % 5)

            return MarketSummary(
                major_indices={'SPY': spy_change + 0.2, 'QQQ': qqq_change + 0.8, 'DIA': (day % 3) * 0.3},
                currencies={'EUR/USD': -0.3 + (month % 3) * 0.2, 'GBP/USD': 0.1, 'USD/JPY': 0.2},
                commodities={'Oil': 2.1 - (day % 4), 'Gold': -0.8 + (month % 5) * 0.2, 'Silver': -1.2},
                volatility={'VIX': vix_level},
                sector_performance={
                    'Technology': 2.1 - (day % 6) * 0.5,
                    'Energy': -1.8 + (month % 4) * 1.0,
                    'Financials': 0.9 - (day % 3) * 0.3
                }
            )

    def _process_news_articles(self, news_data: FinancialNewsData, articles: List[Dict[str, Any]]):
        """Process and categorize news articles."""
        for article in articles:
            # Extract key information
            title = article.get('title', '')
            description = article.get('description', '')
            content = article.get('content', '')

            # Combine text for analysis
            full_text = f"{title} {description} {content}".lower()

            # Store headline
            if title:
                news_data.major_headlines.append(title)

            # Categorize event
            event_type = self._categorize_event(full_text)

            if event_type:
                event = EconomicEvent(
                    event_type=event_type,
                    title=title,
                    description=description,
                    importance=self._assess_importance(full_text)
                )

                # Add to appropriate category
                if event_type == 'fed':
                    news_data.fed_events.append(event)
                elif event_type == 'earnings':
                    news_data.earnings_events.append(event)
                elif event_type == 'geopolitical':
                    news_data.geopolitical_events.append(event)
                else:
                    news_data.economic_data.append(event)

        # Keep only top headlines
        news_data.major_headlines = news_data.major_headlines[:10]

    def _process_economic_events(self, news_data: FinancialNewsData, events: List[Dict[str, Any]]):
        """Process economic calendar events."""
        for event_data in events:
            event = EconomicEvent(
                event_type='economic_data',
                title=event_data.get('event', ''),
                description=f"{event_data.get('event', '')} - {event_data.get('country', '')}",
                importance=event_data.get('importance', 'medium'),
                actual_value=event_data.get('actual'),
                forecast_value=event_data.get('forecast'),
                previous_value=event_data.get('previous'),
                country=event_data.get('country')
            )

            news_data.economic_data.append(event)

    def _categorize_event(self, text: str) -> Optional[str]:
        """Categorize event based on text content."""
        for category, keywords in self.event_categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        return None

    def _assess_importance(self, text: str) -> str:
        """Assess importance based on keywords."""
        high_importance_keywords = ['fed', 'federal reserve', 'gdp', 'unemployment', 'inflation']
        medium_importance_keywords = ['earnings', 'retail sales', 'housing']

        if any(keyword in text for keyword in high_importance_keywords):
            return 'high'
        elif any(keyword in text for keyword in medium_importance_keywords):
            return 'medium'
        else:
            return 'low'

    def _generate_summaries(self, news_data: FinancialNewsData):
        """Generate text summaries."""
        # Fed summary
        if news_data.fed_events:
            fed_titles = [event.title for event in news_data.fed_events[:3]]
            news_data.fed_summary = " | ".join(fed_titles)

        # Overall daily summary
        summary_parts = []

        if news_data.fed_events:
            summary_parts.append(f"Fed: {len(news_data.fed_events)} events")

        if news_data.market_summary:
            market_text = news_data.market_summary.major_indices
            if market_text:
                avg_performance = sum(market_text.values()) / len(market_text)
                summary_parts.append(f"Markets: {'up' if avg_performance > 0 else 'down'} {avg_performance:.1f}%")

        if news_data.economic_data:
            summary_parts.append(f"Economic data: {len(news_data.economic_data)} releases")

        news_data.daily_summary = " | ".join(summary_parts) if summary_parts else "Limited market activity"

        # Market regime assessment
        if news_data.market_summary and news_data.market_summary.volatility:
            vix = news_data.market_summary.volatility.get('VIX', 15)
            if vix > 25:
                news_data.market_regime = 'high_volatility'
            elif vix < 12:
                news_data.market_regime = 'low_volatility'
            else:
                news_data.market_regime = 'normal_volatility'

    def _calculate_quality_score(self, news_data: FinancialNewsData) -> float:
        """Calculate data quality score (0-1)."""
        score = 0.0

        # Headlines available
        if news_data.major_headlines:
            score += 0.2

        # Economic events
        if news_data.economic_data:
            score += 0.3

        # Market data
        if news_data.market_summary:
            score += 0.2

        # Fed events
        if news_data.fed_events:
            score += 0.2

        # Combined summary
        if news_data.get_combined_summary():
            score += 0.1

        return min(score, 1.0)

    def get_current_news(self) -> FinancialNewsData:
        """Get financial news for current date."""
        return self.encode_date(datetime.now(timezone.utc))

    def batch_encode_dates(self, dates: List[datetime],
                          include_market_data: bool = True) -> List[FinancialNewsData]:
        """Encode multiple dates in batch."""
        results = []

        for i, date in enumerate(dates):
            print(f"Processing {i+1}/{len(dates)}: {date.strftime('%Y-%m-%d')}")

            try:
                news_data = self.encode_date(date, include_market_data)
                results.append(news_data)

                # Rate limiting between requests
                if i < len(dates) - 1:  # Don't sleep after last request
                    time.sleep(0.2)

            except Exception as e:
                print(f"Error processing {date}: {e}")
                # Create minimal data object for failed dates
                error_data = FinancialNewsData(date=date)
                error_data.daily_summary = f"Data collection failed: {str(e)}"
                results.append(error_data)

        return results