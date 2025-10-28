"""
Base Event Encoder for Financial Events

Abstract base class for all event encoders (FRED, BLS, EODHD, etc.)
Provides consistent interface for fetching, processing, and formatting financial events.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class FinancialEvent:
    """
    Standardized financial event data structure.
    Used across all event encoders for consistent format.
    """

    def __init__(self,
                 date: datetime,
                 source: str,
                 event_type: str,
                 title: str,
                 description: str,
                 importance: str = "medium",
                 **kwargs):
        """
        Initialize financial event.

        Args:
            date: Event date
            source: Data source (fred, bls, eodhd, etc.)
            event_type: Type of event (fed_decision, employment_data, etc.)
            title: Event title
            description: Event description
            importance: Event importance (high, medium, low)
            **kwargs: Additional event-specific data
        """
        self.date = date
        self.source = source
        self.event_type = event_type
        self.title = title
        self.description = description
        self.importance = importance

        # Store additional data
        self.metadata = kwargs

        # Generate unique ID
        self.id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate unique event ID."""
        date_str = self.date.strftime('%Y_%m_%d')
        # Create safe title for ID
        safe_title = ''.join(c if c.isalnum() else '_' for c in self.title.lower())[:50]
        return f"{self.source}_{date_str}_{self.event_type}_{safe_title}"

    def to_chroma_document(self) -> Dict[str, Any]:
        """
        Convert to ChromaDB document format.

        Returns:
            Dictionary with id, document, metadata for ChromaDB
        """
        # Create rich document text for embedding
        document_text = self._create_document_text()

        # Create metadata for filtering and analysis
        metadata = {
            'date': self.date.strftime('%Y-%m-%d'),
            'source': self.source,
            'event_type': self.event_type,
            'importance': self.importance,
            'title': self.title,
            'created_at': datetime.now().isoformat(),
            **self._create_chroma_metadata()
        }

        return {
            'id': self.id,
            'document': document_text,
            'metadata': metadata
        }

    def _create_document_text(self) -> str:
        """
        Create rich document text for semantic embedding.
        This text will be used for semantic search.
        """
        # Standard template for consistent embedding quality
        template = f"""
Financial Event - {self.date.strftime('%B %d, %Y')}

Source: {self.source.upper()}
Type: {self.event_type.replace('_', ' ').title()}
Importance: {self.importance.upper()}

Title: {self.title}

Description: {self.description}

Context: {self._create_context_text()}

Market Impact: {self._assess_market_impact()}

Keywords: {self._extract_keywords()}
"""
        return template.strip()

    def _create_context_text(self) -> str:
        """Create contextual information for the event."""
        context_parts = []

        # Add temporal context
        if self.date.weekday() < 5:  # Weekday
            context_parts.append("Trading day event")
        else:
            context_parts.append("Weekend event")

        # Add source-specific context
        if self.source == 'fred':
            context_parts.append("Official Federal Reserve economic data")
        elif self.source == 'bls':
            context_parts.append("Bureau of Labor Statistics employment data")

        # Add event type context
        if 'fed' in self.event_type:
            context_parts.append("Monetary policy implications")
        elif 'employment' in self.event_type:
            context_parts.append("Labor market implications")
        elif 'inflation' in self.event_type:
            context_parts.append("Price stability implications")

        return ". ".join(context_parts)

    def _assess_market_impact(self) -> str:
        """Assess potential market impact based on event characteristics."""
        if self.importance == 'high':
            return "High market impact expected"
        elif self.importance == 'medium':
            return "Moderate market impact possible"
        else:
            return "Limited market impact anticipated"

    def _extract_keywords(self) -> str:
        """Extract key terms for search optimization."""
        keywords = set()

        # Add source-specific keywords
        keywords.add(self.source)
        keywords.add(self.event_type)

        # Extract from title and description
        text = f"{self.title} {self.description}".lower()

        # Common financial keywords
        financial_terms = [
            'rate', 'interest', 'fed', 'federal reserve', 'employment', 'unemployment',
            'inflation', 'cpi', 'gdp', 'growth', 'recession', 'expansion',
            'monetary policy', 'fiscal policy', 'bond', 'yield', 'dollar',
            'market', 'stock', 'equity', 'currency', 'forex'
        ]

        for term in financial_terms:
            if term in text:
                keywords.add(term)

        return ", ".join(sorted(keywords))

    def _create_chroma_metadata(self) -> Dict[str, Any]:
        """Create additional metadata specific to ChromaDB storage."""
        chroma_metadata = {}

        # Add numeric fields for filtering
        if 'value' in self.metadata:
            try:
                chroma_metadata['numeric_value'] = float(self.metadata['value'])
            except (ValueError, TypeError):
                pass

        # Add date components for temporal filtering
        chroma_metadata.update({
            'year': self.date.year,
            'month': self.date.month,
            'day': self.date.day,
            'weekday': self.date.weekday(),
            'timestamp': self.date.timestamp()
        })

        # Add importance as numeric for filtering
        importance_map = {'low': 1, 'medium': 2, 'high': 3}
        chroma_metadata['importance_level'] = importance_map.get(self.importance, 2)

        return chroma_metadata

    def to_postgres_dict(self) -> Dict[str, Any]:
        """
        Convert to PostgreSQL-compatible dictionary.

        Returns:
            Dictionary for PostgreSQL storage
        """
        return {
            'event_date': self.date.date(),
            'event_time': self.date.time() if self.date.time() != datetime.min.time() else None,
            'event_type': self.event_type,
            'title': self.title,
            'description': self.description,
            'importance': self.importance,
            'data_source': self.source,
            'chroma_id': self.id,
            'metadata': self.metadata
        }

    def __repr__(self) -> str:
        return f"FinancialEvent({self.date.strftime('%Y-%m-%d')}, {self.source}, {self.event_type}, {self.title[:50]}...)"


class BaseEventEncoder(ABC):
    """
    Abstract base class for financial event encoders.

    All event encoders (FRED, BLS, EODHD, etc.) should inherit from this class
    and implement the required methods.
    """

    def __init__(self, source_name: str, **config):
        """
        Initialize event encoder.

        Args:
            source_name: Name of the data source (fred, bls, etc.)
            **config: Source-specific configuration
        """
        self.source_name = source_name
        self.config = config
        logger.info(f"Initialized {source_name} event encoder")

    @abstractmethod
    def fetch_events(self,
                    start_date: datetime,
                    end_date: datetime,
                    **kwargs) -> List[FinancialEvent]:
        """
        Fetch events from the data source for a date range.

        Args:
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            **kwargs: Source-specific parameters

        Returns:
            List of FinancialEvent objects
        """
        pass

    @abstractmethod
    def fetch_single_date(self, date: datetime, **kwargs) -> List[FinancialEvent]:
        """
        Fetch events for a single date.

        Args:
            date: Target date
            **kwargs: Source-specific parameters

        Returns:
            List of FinancialEvent objects for the date
        """
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """
        Test connection to the data source.

        Returns:
            True if connection is successful, False otherwise
        """
        pass

    def get_available_date_range(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Get the available date range for this data source.

        Returns:
            Tuple of (earliest_date, latest_date). None if unknown.
        """
        # Default implementation - subclasses should override if known
        return None, None

    def get_supported_event_types(self) -> List[str]:
        """
        Get list of event types supported by this encoder.

        Returns:
            List of supported event type strings
        """
        # Default implementation - subclasses should override
        return []

    def batch_fetch_events(self,
                          start_date: datetime,
                          end_date: datetime,
                          batch_size_days: int = 30,
                          **kwargs) -> List[FinancialEvent]:
        """
        Fetch events in batches to handle large date ranges efficiently.

        Args:
            start_date: Start date
            end_date: End date
            batch_size_days: Number of days per batch
            **kwargs: Source-specific parameters

        Returns:
            Combined list of FinancialEvent objects
        """
        all_events = []
        current_date = start_date

        while current_date <= end_date:
            batch_end = min(current_date + timedelta(days=batch_size_days), end_date)

            try:
                batch_events = self.fetch_events(current_date, batch_end, **kwargs)
                all_events.extend(batch_events)
                logger.info(f"{self.source_name}: Fetched {len(batch_events)} events "
                           f"for {current_date.strftime('%Y-%m-%d')} to {batch_end.strftime('%Y-%m-%d')}")

            except Exception as e:
                logger.error(f"{self.source_name}: Error fetching batch "
                           f"{current_date.strftime('%Y-%m-%d')} to {batch_end.strftime('%Y-%m-%d')}: {e}")

            current_date = batch_end + timedelta(days=1)

        logger.info(f"{self.source_name}: Total events fetched: {len(all_events)}")
        return all_events

    def create_daily_summary_event(self,
                                  date: datetime,
                                  events: List[FinancialEvent]) -> Optional[FinancialEvent]:
        """
        Create a daily summary event from multiple events on the same day.

        Args:
            date: Target date
            events: List of events for the day

        Returns:
            Summary FinancialEvent or None if no events
        """
        if not events:
            return None

        # Create summary
        event_types = [event.event_type for event in events]
        high_importance_events = [event for event in events if event.importance == 'high']

        title = f"{self.source_name.upper()} Daily Summary - {len(events)} events"

        description = f"Daily summary of {self.source_name} events: "
        if high_importance_events:
            description += f"{len(high_importance_events)} high-importance events including "
            description += ", ".join([event.title[:30] + "..." for event in high_importance_events[:3]])
        else:
            description += f"Events: {', '.join(set(event_types))}"

        importance = "high" if high_importance_events else "medium"

        return FinancialEvent(
            date=date,
            source=self.source_name,
            event_type=f"{self.source_name}_daily_summary",
            title=title,
            description=description,
            importance=importance,
            event_count=len(events),
            high_importance_count=len(high_importance_events),
            event_types=event_types
        )