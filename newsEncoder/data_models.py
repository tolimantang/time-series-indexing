"""
Data models for financial news and economic event data.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
import json


@dataclass
class EconomicEvent:
    """Represents a single economic event (Fed decision, data release, etc.)."""
    event_type: str  # 'fed_decision', 'earnings', 'economic_data', etc.
    title: str
    description: str
    importance: str  # 'high', 'medium', 'low'
    actual_value: Optional[str] = None
    forecast_value: Optional[str] = None
    previous_value: Optional[str] = None
    currency: Optional[str] = None
    country: Optional[str] = None


@dataclass
class MarketSummary:
    """Summary of market movements for a given day."""
    major_indices: Dict[str, float] = field(default_factory=dict)  # {'SPY': 1.2, 'QQQ': -0.5}
    currencies: Dict[str, float] = field(default_factory=dict)  # {'EUR/USD': -0.3}
    commodities: Dict[str, float] = field(default_factory=dict)  # {'Oil': 2.1, 'Gold': -0.8}
    volatility: Dict[str, float] = field(default_factory=dict)  # {'VIX': 15.2}
    sector_performance: Dict[str, float] = field(default_factory=dict)  # {'Tech': 2.1}


@dataclass
class FinancialNewsData:
    """Complete financial news and events data for a single day."""
    date: datetime

    # Economic events
    fed_events: List[EconomicEvent] = field(default_factory=list)
    economic_data: List[EconomicEvent] = field(default_factory=list)
    earnings_events: List[EconomicEvent] = field(default_factory=list)
    geopolitical_events: List[EconomicEvent] = field(default_factory=list)

    # Market summary
    market_summary: Optional[MarketSummary] = None

    # Text summaries
    daily_summary: str = ""
    fed_summary: str = ""
    market_regime: str = ""  # 'risk_on', 'risk_off', 'neutral', 'high_volatility'

    # News headlines
    major_headlines: List[str] = field(default_factory=list)

    # Metadata
    data_sources: List[str] = field(default_factory=list)
    quality_score: float = 0.0  # 0-1 score for data completeness

    def get_combined_summary(self) -> str:
        """Get a comprehensive summary for embedding/search purposes."""
        components = []

        if self.fed_summary:
            components.append(f"Fed: {self.fed_summary}")

        if self.market_summary:
            market_text = self._format_market_summary()
            if market_text:
                components.append(f"Markets: {market_text}")

        if self.economic_data:
            econ_text = self._format_economic_events()
            if econ_text:
                components.append(f"Data: {econ_text}")

        if self.geopolitical_events:
            geo_text = self._format_geopolitical_events()
            if geo_text:
                components.append(f"Geopolitical: {geo_text}")

        if self.earnings_events:
            earnings_text = self._format_earnings_events()
            if earnings_text:
                components.append(f"Earnings: {earnings_text}")

        return " | ".join(components) if components else self.daily_summary

    def _format_market_summary(self) -> str:
        """Format market summary for text representation."""
        if not self.market_summary:
            return ""

        parts = []

        # Major indices
        for symbol, change in self.market_summary.major_indices.items():
            sign = "+" if change > 0 else ""
            parts.append(f"{symbol} {sign}{change:.1f}%")

        # Volatility
        if self.market_summary.volatility:
            for symbol, level in self.market_summary.volatility.items():
                parts.append(f"{symbol} {level:.1f}")

        return ", ".join(parts)

    def _format_economic_events(self) -> str:
        """Format economic events for text representation."""
        if not self.economic_data:
            return ""

        summaries = []
        for event in self.economic_data[:3]:  # Top 3 events
            if event.actual_value:
                summaries.append(f"{event.title}: {event.actual_value}")
            else:
                summaries.append(event.title)

        return ", ".join(summaries)

    def _format_geopolitical_events(self) -> str:
        """Format geopolitical events for text representation."""
        if not self.geopolitical_events:
            return ""

        return ", ".join([event.title for event in self.geopolitical_events[:2]])

    def _format_earnings_events(self) -> str:
        """Format earnings events for text representation."""
        if not self.earnings_events:
            return ""

        return ", ".join([event.title for event in self.earnings_events[:3]])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization."""
        return {
            'date': self.date.isoformat(),
            'fed_events': [self._event_to_dict(e) for e in self.fed_events],
            'economic_data': [self._event_to_dict(e) for e in self.economic_data],
            'earnings_events': [self._event_to_dict(e) for e in self.earnings_events],
            'geopolitical_events': [self._event_to_dict(e) for e in self.geopolitical_events],
            'market_summary': self._market_summary_to_dict(),
            'daily_summary': self.daily_summary,
            'fed_summary': self.fed_summary,
            'market_regime': self.market_regime,
            'major_headlines': self.major_headlines,
            'data_sources': self.data_sources,
            'quality_score': self.quality_score,
            'combined_summary': self.get_combined_summary()
        }

    def _event_to_dict(self, event: EconomicEvent) -> Dict[str, Any]:
        """Convert EconomicEvent to dictionary."""
        return {
            'event_type': event.event_type,
            'title': event.title,
            'description': event.description,
            'importance': event.importance,
            'actual_value': event.actual_value,
            'forecast_value': event.forecast_value,
            'previous_value': event.previous_value,
            'currency': event.currency,
            'country': event.country
        }

    def _market_summary_to_dict(self) -> Optional[Dict[str, Any]]:
        """Convert MarketSummary to dictionary."""
        if not self.market_summary:
            return None

        return {
            'major_indices': self.market_summary.major_indices,
            'currencies': self.market_summary.currencies,
            'commodities': self.market_summary.commodities,
            'volatility': self.market_summary.volatility,
            'sector_performance': self.market_summary.sector_performance
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FinancialNewsData':
        """Create FinancialNewsData from dictionary."""
        # Parse date
        date = datetime.fromisoformat(data['date'].replace('Z', '+00:00'))

        # Create instance
        news_data = cls(date=date)

        # Parse events
        news_data.fed_events = [cls._event_from_dict(e) for e in data.get('fed_events', [])]
        news_data.economic_data = [cls._event_from_dict(e) for e in data.get('economic_data', [])]
        news_data.earnings_events = [cls._event_from_dict(e) for e in data.get('earnings_events', [])]
        news_data.geopolitical_events = [cls._event_from_dict(e) for e in data.get('geopolitical_events', [])]

        # Parse market summary
        if data.get('market_summary'):
            news_data.market_summary = MarketSummary(**data['market_summary'])

        # Parse other fields
        news_data.daily_summary = data.get('daily_summary', '')
        news_data.fed_summary = data.get('fed_summary', '')
        news_data.market_regime = data.get('market_regime', '')
        news_data.major_headlines = data.get('major_headlines', [])
        news_data.data_sources = data.get('data_sources', [])
        news_data.quality_score = data.get('quality_score', 0.0)

        return news_data

    @classmethod
    def _event_from_dict(cls, data: Dict[str, Any]) -> EconomicEvent:
        """Create EconomicEvent from dictionary."""
        return EconomicEvent(
            event_type=data['event_type'],
            title=data['title'],
            description=data['description'],
            importance=data['importance'],
            actual_value=data.get('actual_value'),
            forecast_value=data.get('forecast_value'),
            previous_value=data.get('previous_value'),
            currency=data.get('currency'),
            country=data.get('country')
        )