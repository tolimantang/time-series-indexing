"""
Tests for the main NewsEncoder class.
"""

import pytest
from datetime import datetime, timezone, timedelta
from newsEncoder import NewsEncoder
from newsEncoder.data_models import FinancialNewsData, EconomicEvent, MarketSummary


class TestNewsEncoder:
    """Test the main NewsEncoder functionality."""

    @pytest.fixture
    def encoder(self):
        """Create a NewsEncoder instance for testing."""
        return NewsEncoder()

    @pytest.fixture
    def encoder_with_config(self):
        """Create a NewsEncoder instance with mock configuration."""
        config = {
            'newsapi_key': 'test_key',
            'alpha_vantage_key': 'test_key'
        }
        return NewsEncoder(config)

    @pytest.fixture
    def test_date(self):
        """A known date for testing: January 15, 2024."""
        return datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

    def test_encoder_initialization(self, encoder):
        """Test that encoder initializes correctly."""
        assert encoder is not None
        assert hasattr(encoder, 'financial_keywords')
        assert hasattr(encoder, 'event_categories')
        assert len(encoder.financial_keywords) > 0
        assert 'fed' in encoder.event_categories

    def test_encoder_with_config(self, encoder_with_config):
        """Test encoder initialization with configuration."""
        assert encoder_with_config.config['newsapi_key'] == 'test_key'
        assert encoder_with_config.config['alpha_vantage_key'] == 'test_key'

    def test_encode_date_basic(self, encoder, test_date):
        """Test basic date encoding functionality."""
        result = encoder.encode_date(test_date)

        assert isinstance(result, FinancialNewsData)
        assert result.date == test_date
        assert isinstance(result.fed_events, list)
        assert isinstance(result.economic_data, list)
        assert isinstance(result.earnings_events, list)
        assert isinstance(result.geopolitical_events, list)
        assert isinstance(result.major_headlines, list)
        assert result.quality_score >= 0.0
        assert result.quality_score <= 1.0

    def test_current_news(self, encoder):
        """Test getting current news."""
        result = encoder.get_current_news()

        assert isinstance(result, FinancialNewsData)
        assert result.date is not None
        # Should be recent (within last day)
        time_diff = datetime.now(timezone.utc) - result.date
        assert time_diff.total_seconds() < 86400  # 24 hours

    def test_market_summary_structure(self, encoder, test_date):
        """Test market summary structure."""
        result = encoder.encode_date(test_date, include_market_data=True)

        assert result.market_summary is not None
        assert isinstance(result.market_summary, MarketSummary)
        assert isinstance(result.market_summary.major_indices, dict)
        assert isinstance(result.market_summary.currencies, dict)
        assert isinstance(result.market_summary.commodities, dict)
        assert isinstance(result.market_summary.volatility, dict)

    def test_event_categorization(self, encoder):
        """Test event categorization functionality."""
        # Test Fed categorization
        fed_text = "federal reserve interest rates powell"
        category = encoder._categorize_event(fed_text)
        assert category == 'fed'

        # Test earnings categorization
        earnings_text = "quarterly earnings results profit"
        category = encoder._categorize_event(earnings_text)
        assert category == 'earnings'

        # Test economic data categorization
        econ_text = "gdp inflation unemployment data"
        category = encoder._categorize_event(econ_text)
        assert category == 'economic_data'

        # Test geopolitical categorization
        geo_text = "trade war china sanctions"
        category = encoder._categorize_event(geo_text)
        assert category == 'geopolitical'

        # Test unrecognized text
        unknown_text = "random unrelated content"
        category = encoder._categorize_event(unknown_text)
        assert category is None

    def test_importance_assessment(self, encoder):
        """Test importance assessment functionality."""
        # High importance
        high_text = "federal reserve gdp unemployment"
        importance = encoder._assess_importance(high_text)
        assert importance == 'high'

        # Medium importance
        medium_text = "earnings retail sales"
        importance = encoder._assess_importance(medium_text)
        assert importance == 'medium'

        # Low importance
        low_text = "random market news"
        importance = encoder._assess_importance(low_text)
        assert importance == 'low'

    def test_combined_summary(self, encoder, test_date):
        """Test combined summary generation."""
        result = encoder.encode_date(test_date)
        summary = result.get_combined_summary()

        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_to_dict_conversion(self, encoder, test_date):
        """Test conversion to dictionary."""
        result = encoder.encode_date(test_date)
        data_dict = result.to_dict()

        assert isinstance(data_dict, dict)
        assert 'date' in data_dict
        assert 'fed_events' in data_dict
        assert 'economic_data' in data_dict
        assert 'market_summary' in data_dict
        assert 'daily_summary' in data_dict
        assert 'combined_summary' in data_dict

        # Test date serialization
        assert isinstance(data_dict['date'], str)

    def test_from_dict_conversion(self, encoder, test_date):
        """Test creation from dictionary."""
        original = encoder.encode_date(test_date)
        data_dict = original.to_dict()

        # Create new instance from dict
        restored = FinancialNewsData.from_dict(data_dict)

        assert restored.date == original.date
        assert len(restored.fed_events) == len(original.fed_events)
        assert len(restored.economic_data) == len(original.economic_data)
        assert restored.daily_summary == original.daily_summary

    def test_batch_encoding(self, encoder):
        """Test batch encoding functionality."""
        # Test with 3 consecutive dates
        base_date = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        dates = [
            base_date,
            base_date + timedelta(days=1),
            base_date + timedelta(days=2)
        ]

        results = encoder.batch_encode_dates(dates)

        assert len(results) == 3
        for i, result in enumerate(results):
            assert isinstance(result, FinancialNewsData)
            assert result.date == dates[i]

    def test_quality_score_calculation(self, encoder, test_date):
        """Test quality score calculation."""
        result = encoder.encode_date(test_date)
        quality_score = encoder._calculate_quality_score(result)

        assert isinstance(quality_score, float)
        assert 0.0 <= quality_score <= 1.0
        assert quality_score == result.quality_score

    def test_free_news_sources(self, encoder, test_date):
        """Test free news sources functionality."""
        articles = encoder._get_free_news_sources(test_date)

        assert isinstance(articles, list)
        assert len(articles) > 0

        # Check article structure
        for article in articles:
            assert 'title' in article
            assert 'description' in article
            assert 'publishedAt' in article
            assert 'source' in article

    def test_economic_events_processing(self, encoder, test_date):
        """Test economic events processing."""
        events = encoder._get_economic_events(test_date)

        assert isinstance(events, list)
        assert len(events) > 0

        # Check event structure
        for event in events:
            assert 'event' in event
            assert 'country' in event
            assert 'importance' in event


class TestFinancialNewsData:
    """Test the FinancialNewsData data model."""

    @pytest.fixture
    def sample_data(self):
        """Create sample financial news data."""
        date = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        return FinancialNewsData(date=date)

    def test_initialization(self, sample_data):
        """Test FinancialNewsData initialization."""
        assert sample_data.date is not None
        assert isinstance(sample_data.fed_events, list)
        assert isinstance(sample_data.economic_data, list)
        assert isinstance(sample_data.earnings_events, list)
        assert isinstance(sample_data.geopolitical_events, list)
        assert isinstance(sample_data.major_headlines, list)

    def test_add_events(self, sample_data):
        """Test adding events to FinancialNewsData."""
        # Add a Fed event
        fed_event = EconomicEvent(
            event_type='fed',
            title='Fed Raises Rates',
            description='Federal Reserve raises interest rates by 0.25%',
            importance='high'
        )
        sample_data.fed_events.append(fed_event)

        assert len(sample_data.fed_events) == 1
        assert sample_data.fed_events[0].title == 'Fed Raises Rates'

    def test_market_summary(self, sample_data):
        """Test market summary functionality."""
        market_summary = MarketSummary(
            major_indices={'SPY': 1.5, 'QQQ': 2.1},
            volatility={'VIX': 15.2}
        )
        sample_data.market_summary = market_summary

        assert sample_data.market_summary is not None
        assert sample_data.market_summary.major_indices['SPY'] == 1.5
        assert sample_data.market_summary.volatility['VIX'] == 15.2

    def test_combined_summary_generation(self, sample_data):
        """Test combined summary generation."""
        # Add some events
        sample_data.fed_summary = "Fed holds rates steady"
        sample_data.market_summary = MarketSummary(
            major_indices={'SPY': 1.2},
            volatility={'VIX': 15.0}
        )

        summary = sample_data.get_combined_summary()
        assert isinstance(summary, str)
        assert 'Fed' in summary or len(summary) == 0  # Could be empty if no data


class TestIntegration:
    """Integration tests for the complete system."""

    def test_end_to_end_workflow(self):
        """Test complete workflow from encoding to analysis."""
        encoder = NewsEncoder()

        # Encode a few dates
        base_date = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
        dates = [base_date + timedelta(days=i) for i in range(3)]

        results = encoder.batch_encode_dates(dates)

        # Verify results
        assert len(results) == 3

        # Test search-like functionality
        summaries = [r.get_combined_summary() for r in results]
        assert all(isinstance(s, str) for s in summaries)

        # Test serialization
        for result in results:
            data_dict = result.to_dict()
            restored = FinancialNewsData.from_dict(data_dict)
            assert restored.date == result.date

    def test_api_integration_structure(self):
        """Test that API integration structure is correct."""
        config = {
            'newsapi_key': 'test_key',
            'alpha_vantage_key': 'test_key'
        }
        encoder = NewsEncoder(config)

        # Test that encoder can handle API configuration
        assert encoder.config['newsapi_key'] == 'test_key'

        # Test that methods exist for API integration
        assert hasattr(encoder, '_get_newsapi_articles')
        assert hasattr(encoder, '_get_free_news_sources')
        assert hasattr(encoder, '_get_economic_events')
        assert hasattr(encoder, '_get_market_summary')