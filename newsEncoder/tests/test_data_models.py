"""
Tests for data models.
"""

import pytest
from datetime import datetime, timezone
from newsEncoder.data_models import EconomicEvent, MarketSummary, FinancialNewsData


class TestEconomicEvent:
    """Test the EconomicEvent data model."""

    def test_economic_event_creation(self):
        """Test creating an EconomicEvent."""
        event = EconomicEvent(
            event_type='fed',
            title='Fed Rate Decision',
            description='Federal Reserve decides on interest rates',
            importance='high',
            actual_value='5.25%',
            forecast_value='5.00%',
            previous_value='4.75%'
        )

        assert event.event_type == 'fed'
        assert event.title == 'Fed Rate Decision'
        assert event.importance == 'high'
        assert event.actual_value == '5.25%'

    def test_economic_event_optional_fields(self):
        """Test EconomicEvent with minimal required fields."""
        event = EconomicEvent(
            event_type='earnings',
            title='Company Earnings',
            description='Q4 earnings report',
            importance='medium'
        )

        assert event.actual_value is None
        assert event.forecast_value is None
        assert event.previous_value is None
        assert event.currency is None
        assert event.country is None


class TestMarketSummary:
    """Test the MarketSummary data model."""

    def test_market_summary_creation(self):
        """Test creating a MarketSummary."""
        summary = MarketSummary(
            major_indices={'SPY': 1.2, 'QQQ': 0.8},
            currencies={'EUR/USD': -0.3, 'GBP/USD': 0.1},
            commodities={'Oil': 2.1, 'Gold': -0.8},
            volatility={'VIX': 15.2},
            sector_performance={'Technology': 2.1, 'Energy': -1.8}
        )

        assert summary.major_indices['SPY'] == 1.2
        assert summary.currencies['EUR/USD'] == -0.3
        assert summary.commodities['Oil'] == 2.1
        assert summary.volatility['VIX'] == 15.2
        assert summary.sector_performance['Technology'] == 2.1

    def test_market_summary_defaults(self):
        """Test MarketSummary with default values."""
        summary = MarketSummary()

        assert summary.major_indices == {}
        assert summary.currencies == {}
        assert summary.commodities == {}
        assert summary.volatility == {}
        assert summary.sector_performance == {}


class TestFinancialNewsData:
    """Test the FinancialNewsData data model."""

    @pytest.fixture
    def sample_date(self):
        """Sample date for testing."""
        return datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

    @pytest.fixture
    def sample_financial_news_data(self, sample_date):
        """Create sample FinancialNewsData for testing."""
        return FinancialNewsData(date=sample_date)

    def test_financial_news_data_creation(self, sample_financial_news_data, sample_date):
        """Test creating FinancialNewsData."""
        data = sample_financial_news_data

        assert data.date == sample_date
        assert isinstance(data.fed_events, list)
        assert isinstance(data.economic_data, list)
        assert isinstance(data.earnings_events, list)
        assert isinstance(data.geopolitical_events, list)
        assert isinstance(data.major_headlines, list)
        assert data.market_summary is None
        assert data.daily_summary == ""
        assert data.quality_score == 0.0

    def test_add_events(self, sample_financial_news_data):
        """Test adding events to FinancialNewsData."""
        data = sample_financial_news_data

        # Add Fed event
        fed_event = EconomicEvent(
            event_type='fed',
            title='Fed Decision',
            description='Interest rate decision',
            importance='high'
        )
        data.fed_events.append(fed_event)

        # Add economic event
        econ_event = EconomicEvent(
            event_type='economic_data',
            title='CPI Release',
            description='Consumer Price Index',
            importance='high',
            actual_value='3.2%'
        )
        data.economic_data.append(econ_event)

        assert len(data.fed_events) == 1
        assert len(data.economic_data) == 1
        assert data.fed_events[0].title == 'Fed Decision'
        assert data.economic_data[0].actual_value == '3.2%'

    def test_market_summary_integration(self, sample_financial_news_data):
        """Test integrating market summary."""
        data = sample_financial_news_data

        market_summary = MarketSummary(
            major_indices={'SPY': 1.5, 'QQQ': -0.3},
            volatility={'VIX': 18.5}
        )
        data.market_summary = market_summary

        assert data.market_summary is not None
        assert data.market_summary.major_indices['SPY'] == 1.5
        assert data.market_summary.volatility['VIX'] == 18.5

    def test_combined_summary_empty(self, sample_financial_news_data):
        """Test combined summary with no data."""
        data = sample_financial_news_data
        summary = data.get_combined_summary()

        # Should return daily_summary (empty string) when no data
        assert summary == ""

    def test_combined_summary_with_data(self, sample_financial_news_data):
        """Test combined summary with data."""
        data = sample_financial_news_data

        # Add data
        data.fed_summary = "Fed holds rates steady"
        data.market_summary = MarketSummary(
            major_indices={'SPY': 1.2, 'QQQ': 0.8},
            volatility={'VIX': 15.0}
        )

        econ_event = EconomicEvent(
            event_type='economic_data',
            title='GDP Growth',
            description='Q4 GDP',
            importance='high'
        )
        data.economic_data.append(econ_event)

        summary = data.get_combined_summary()

        assert isinstance(summary, str)
        assert len(summary) > 0
        assert 'Fed:' in summary
        assert 'Markets:' in summary
        assert 'Data:' in summary

    def test_format_market_summary(self, sample_financial_news_data):
        """Test market summary formatting."""
        data = sample_financial_news_data

        data.market_summary = MarketSummary(
            major_indices={'SPY': 1.2, 'QQQ': -0.5},
            volatility={'VIX': 15.8}
        )

        formatted = data._format_market_summary()

        assert 'SPY +1.2%' in formatted
        assert 'QQQ -0.5%' in formatted
        assert 'VIX 15.8' in formatted

    def test_format_economic_events(self, sample_financial_news_data):
        """Test economic events formatting."""
        data = sample_financial_news_data

        # Add multiple events
        events = [
            EconomicEvent('economic_data', 'CPI', 'Consumer Price Index', 'high', '3.2%'),
            EconomicEvent('economic_data', 'GDP', 'Gross Domestic Product', 'high', '2.1%'),
            EconomicEvent('economic_data', 'Unemployment', 'Jobs Report', 'high', '3.8%'),
            EconomicEvent('economic_data', 'Retail Sales', 'Monthly Sales', 'medium', '0.5%')
        ]
        data.economic_data.extend(events)

        formatted = data._format_economic_events()

        # Should include top 3 events
        assert 'CPI: 3.2%' in formatted
        assert 'GDP: 2.1%' in formatted
        assert 'Unemployment: 3.8%' in formatted
        # Should not include 4th event
        assert 'Retail Sales' not in formatted

    def test_to_dict(self, sample_financial_news_data, sample_date):
        """Test conversion to dictionary."""
        data = sample_financial_news_data

        # Add some data
        data.daily_summary = "Market activity summary"
        data.fed_summary = "Fed maintains rates"
        data.quality_score = 0.8

        fed_event = EconomicEvent('fed', 'Fed Decision', 'Rate decision', 'high')
        data.fed_events.append(fed_event)

        data.market_summary = MarketSummary(major_indices={'SPY': 1.0})

        # Convert to dict
        data_dict = data.to_dict()

        assert isinstance(data_dict, dict)
        assert data_dict['date'] == sample_date.isoformat()
        assert data_dict['daily_summary'] == 'Market activity summary'
        assert data_dict['fed_summary'] == 'Fed maintains rates'
        assert data_dict['quality_score'] == 0.8
        assert len(data_dict['fed_events']) == 1
        assert data_dict['market_summary'] is not None
        assert 'combined_summary' in data_dict

    def test_from_dict(self, sample_date):
        """Test creation from dictionary."""
        # Create test dictionary
        test_dict = {
            'date': sample_date.isoformat(),
            'fed_events': [{
                'event_type': 'fed',
                'title': 'Fed Decision',
                'description': 'Interest rate decision',
                'importance': 'high',
                'actual_value': None,
                'forecast_value': None,
                'previous_value': None,
                'currency': None,
                'country': None
            }],
            'economic_data': [],
            'earnings_events': [],
            'geopolitical_events': [],
            'market_summary': {
                'major_indices': {'SPY': 1.5},
                'currencies': {},
                'commodities': {},
                'volatility': {'VIX': 16.0},
                'sector_performance': {}
            },
            'daily_summary': 'Test summary',
            'fed_summary': 'Fed test',
            'market_regime': 'normal_volatility',
            'major_headlines': ['Test headline'],
            'data_sources': ['test_source'],
            'quality_score': 0.9
        }

        # Create from dict
        data = FinancialNewsData.from_dict(test_dict)

        assert data.date == sample_date
        assert data.daily_summary == 'Test summary'
        assert data.fed_summary == 'Fed test'
        assert data.market_regime == 'normal_volatility'
        assert data.quality_score == 0.9
        assert len(data.fed_events) == 1
        assert data.fed_events[0].title == 'Fed Decision'
        assert data.market_summary is not None
        assert data.market_summary.major_indices['SPY'] == 1.5
        assert data.market_summary.volatility['VIX'] == 16.0
        assert data.major_headlines == ['Test headline']

    def test_roundtrip_serialization(self, sample_financial_news_data):
        """Test that to_dict -> from_dict preserves data."""
        # Add comprehensive data
        data = sample_financial_news_data

        data.daily_summary = "Test daily summary"
        data.fed_summary = "Test fed summary"
        data.market_regime = "high_volatility"
        data.quality_score = 0.75

        # Add events
        fed_event = EconomicEvent('fed', 'Fed Rate Hike', 'Raised by 0.25%', 'high')
        data.fed_events.append(fed_event)

        econ_event = EconomicEvent('economic_data', 'CPI', 'Inflation data', 'high', '3.1%')
        data.economic_data.append(econ_event)

        # Add market summary
        data.market_summary = MarketSummary(
            major_indices={'SPY': 1.2, 'QQQ': -0.3},
            currencies={'EUR/USD': 0.5},
            volatility={'VIX': 20.1}
        )

        data.major_headlines = ['Headline 1', 'Headline 2']

        # Convert to dict and back
        data_dict = data.to_dict()
        restored_data = FinancialNewsData.from_dict(data_dict)

        # Verify all data is preserved
        assert restored_data.date == data.date
        assert restored_data.daily_summary == data.daily_summary
        assert restored_data.fed_summary == data.fed_summary
        assert restored_data.market_regime == data.market_regime
        assert restored_data.quality_score == data.quality_score

        assert len(restored_data.fed_events) == len(data.fed_events)
        assert len(restored_data.economic_data) == len(data.economic_data)

        assert restored_data.market_summary.major_indices == data.market_summary.major_indices
        assert restored_data.market_summary.currencies == data.market_summary.currencies
        assert restored_data.market_summary.volatility == data.market_summary.volatility

        assert restored_data.major_headlines == data.major_headlines