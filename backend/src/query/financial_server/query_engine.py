"""
Financial Query Engine

Core engine that combines PostgreSQL and ChromaDB to answer complex financial questions.
Handles queries like "What happens to platinum prices after Fed raises interest rates?"
"""

import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Tuple
import json

try:
    from ...services.events_postgres_manager import create_events_postgres_manager
    from ...services.chroma_manager import create_chroma_manager
    from ...services.market_data_manager import create_market_data_manager
except ImportError:
    # Handle direct script execution
    from services.events_postgres_manager import create_events_postgres_manager
    from services.chroma_manager import create_chroma_manager
    from services.market_data_manager import create_market_data_manager

logger = logging.getLogger(__name__)


class FinancialQueryEngine:
    """
    Intelligent financial query engine that combines structured and semantic search.

    Capabilities:
    - Causal analysis: What happens after X event?
    - Time-based queries: Events in specific periods
    - Semantic search: Natural language questions
    - Cross-market analysis: How does X affect Y?
    """

    def __init__(self):
        """Initialize the query engine with both storage systems."""
        self.postgres_manager = create_events_postgres_manager()
        self.chroma_manager = create_chroma_manager()
        self.market_data_manager = create_market_data_manager()

        logger.info("FinancialQueryEngine initialized with dual storage + market data")

    def analyze_causal_impact(self,
                            trigger_event_type: Optional[str] = None,
                            trigger_conditions: Dict[str, Any] = None,
                            trigger_query: Optional[str] = None,
                            impact_timeframe_days: int = 30,
                            limit: int = 20,
                            target_asset: Optional[str] = None,
                            time_range: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Analyze what happens after specific types of events.

        Example: What happens to gold prices after Fed rate increases?

        Args:
            trigger_event_type: Type of triggering event (e.g., 'fed_decision') - optional if trigger_query provided
            trigger_conditions: Conditions for the trigger (e.g., {'change_direction': 'increase'})
            trigger_query: Natural language description of trigger events (e.g., 'Fed raises interest rates')
            impact_timeframe_days: Days to look ahead for impacts (ignored if time_range specified)
            limit: Maximum number of trigger events to analyze
            target_asset: Optional asset symbol for price impact analysis (e.g., 'GLD', 'SPY')
            time_range: Optional specific date range to analyze {"start_date": "2020-01-01", "end_date": "2024-12-31"}

        Returns:
            Analysis results with trigger events and market price movements.
            If target_asset provided, returns actual price data for charting + summary statistics.
        """
        try:
            logger.info(f"Analyzing causal impact: {trigger_query or trigger_event_type} -> {target_asset or 'events'}")

            # 1. Determine date range for trigger event search
            if time_range:
                search_start = datetime.strptime(time_range['start_date'], '%Y-%m-%d').date()
                search_end = datetime.strptime(time_range['end_date'], '%Y-%m-%d').date()
                logger.info(f"Using specified time range: {search_start} to {search_end}")
            else:
                # Default: search last few years
                search_end = date.today()
                search_start = date(search_end.year - 5, 1, 1)
                logger.info(f"Using default time range: {search_start} to {search_end}")

            # 2. Find trigger events - support both structured and semantic queries
            if trigger_query:
                # Use ChromaDB semantic search to find relevant events
                logger.info(f"Using semantic search for trigger query: '{trigger_query}'")
                trigger_events = self._find_trigger_events_semantic(
                    trigger_query, search_start, search_end, limit
                )
                trigger_source = "semantic_search"
            elif trigger_event_type:
                # Use PostgreSQL structured search
                logger.info(f"Using structured search for event type: {trigger_event_type}")
                trigger_events = self._find_trigger_events_in_range(
                    trigger_event_type, trigger_conditions or {}, search_start, search_end, limit
                )
                trigger_source = "structured_search"
            else:
                return {
                    'error': 'Either trigger_event_type or trigger_query must be provided'
                }

            if not trigger_events:
                return {
                    'trigger_type': trigger_event_type,
                    'trigger_query': trigger_query,
                    'trigger_conditions': trigger_conditions,
                    'trigger_source': trigger_source,
                    'time_range': {'start_date': search_start.isoformat(), 'end_date': search_end.isoformat()},
                    'trigger_events_found': 0,
                    'analysis': 'No trigger events found matching criteria'
                }

            # 3. If target_asset specified, get market data directly
            if target_asset:
                logger.info(f"Getting market data for {target_asset}")

                # For each trigger event, get market data in a simple range after the event
                market_analysis = []

                for trigger in trigger_events:
                    event_date = trigger['event_date']
                    # Get market data from event date to event_date + impact_timeframe_days
                    market_start = event_date
                    market_end = event_date + timedelta(days=impact_timeframe_days + 10)  # Buffer for weekends

                    market_data = self.market_data_manager.get_price_data(
                        target_asset, market_start, market_end
                    )

                    if market_data:
                        # Calculate simple returns for this event
                        impact = self.market_data_manager.calculate_event_impact(
                            target_asset, event_date, forward_days=impact_timeframe_days
                        )

                        market_analysis.append({
                            'trigger_event': trigger,
                            'market_impact': impact,
                            'raw_market_data': market_data[:50]  # Limit data for response size
                        })

                # Aggregate statistics across all events
                aggregated_stats = self._aggregate_market_statistics(market_analysis)

                return {
                    'trigger_type': trigger_event_type,
                    'trigger_conditions': trigger_conditions,
                    'time_range': {'start_date': search_start.isoformat(), 'end_date': search_end.isoformat()},
                    'trigger_events_found': len(trigger_events),
                    'target_asset': target_asset,
                    'impact_timeframe_days': impact_timeframe_days,
                    'market_data_available': True,
                    'individual_market_impacts': market_analysis,
                    'aggregated_statistics': aggregated_stats,
                    'analysis_timestamp': datetime.now().isoformat()
                }
            else:
                # Traditional event-based analysis (fallback)
                impact_analysis = self._analyze_event_based_impacts(trigger_events, impact_timeframe_days)
                patterns = self._analyze_impact_patterns(impact_analysis)

                return {
                    'trigger_type': trigger_event_type,
                    'trigger_conditions': trigger_conditions,
                    'time_range': {'start_date': search_start.isoformat(), 'end_date': search_end.isoformat()},
                    'trigger_events_found': len(trigger_events),
                    'impact_timeframe_days': impact_timeframe_days,
                    'individual_cases': impact_analysis,
                    'patterns': patterns,
                    'analysis_timestamp': datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Error in causal impact analysis: {e}")
            return {'error': str(e)}

    def semantic_search(self,
                       query: str,
                       date_range: Optional[Tuple[date, date]] = None,
                       event_types: Optional[List[str]] = None,
                       n_results: int = 10) -> Dict[str, Any]:
        """
        Perform semantic search across financial events.

        Args:
            query: Natural language query
            date_range: Optional date range filter
            event_types: Optional event type filter
            n_results: Number of results to return

        Returns:
            Semantic search results with context
        """
        try:
            logger.info(f"Semantic search: '{query}'")

            # Perform semantic search with ChromaDB
            semantic_results = self.chroma_manager.query_events(
                "financial_events", query, n_results=n_results
            )

            # If date range specified, filter with PostgreSQL
            if date_range or event_types:
                structured_results = self.postgres_manager.get_events_by_date_range(
                    date_range[0] if date_range else date(1970, 1, 1),
                    date_range[1] if date_range else date.today(),
                    event_types=event_types
                )

                # Cross-reference results
                structured_ids = {event['event_id'] for event in structured_results}
                filtered_semantic = self._filter_semantic_by_structured(
                    semantic_results, structured_ids
                )

                return {
                    'query': query,
                    'semantic_results': filtered_semantic,
                    'structured_filter_applied': True,
                    'date_range': date_range,
                    'event_types': event_types
                }

            return {
                'query': query,
                'semantic_results': semantic_results,
                'structured_filter_applied': False
            }

        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return {'error': str(e)}

    def time_series_analysis(self,
                           start_date: date,
                           end_date: date,
                           event_types: Optional[List[str]] = None,
                           importance: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyze events over a time period with aggregations.

        Args:
            start_date: Start date
            end_date: End date
            event_types: Optional event type filter
            importance: Optional importance filter

        Returns:
            Time series analysis with statistics
        """
        try:
            logger.info(f"Time series analysis: {start_date} to {end_date}")

            # Get events from PostgreSQL
            events = self.postgres_manager.get_events_by_date_range(
                start_date, end_date, event_types, importance
            )

            # Get statistics
            stats = self.postgres_manager.get_event_statistics(start_date, end_date)

            # Analyze temporal patterns
            temporal_analysis = self._analyze_temporal_patterns(events)

            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': (end_date - start_date).days
                },
                'filters': {
                    'event_types': event_types,
                    'importance': importance
                },
                'events': events,
                'statistics': stats,
                'temporal_analysis': temporal_analysis
            }

        except Exception as e:
            logger.error(f"Error in time series analysis: {e}")
            return {'error': str(e)}

    def cross_market_analysis(self,
                            financial_event_query: str,
                            market_symbol: str,
                            correlation_days: int = 5) -> Dict[str, Any]:
        """
        Analyze how financial events correlate with market movements.

        Args:
            financial_event_query: Query for financial events
            market_symbol: Market symbol to analyze (if market data available)
            correlation_days: Days to look for correlation

        Returns:
            Cross-market correlation analysis
        """
        try:
            logger.info(f"Cross-market analysis: '{financial_event_query}' vs {market_symbol}")

            # Find relevant financial events
            events = self.semantic_search(financial_event_query, n_results=50)

            # TODO: Integrate with market data when available
            # For now, return framework for future market data integration

            return {
                'financial_query': financial_event_query,
                'market_symbol': market_symbol,
                'correlation_days': correlation_days,
                'financial_events': events,
                'market_analysis': 'Market data integration pending',
                'note': 'This will correlate financial events with actual market price movements'
            }

        except Exception as e:
            logger.error(f"Error in cross-market analysis: {e}")
            return {'error': str(e)}

    # Helper methods

    def _find_trigger_events_semantic(self,
                                     trigger_query: str,
                                     start_date: date,
                                     end_date: date,
                                     limit: int) -> List[Dict[str, Any]]:
        """Find events using semantic search with date range filtering."""
        try:
            # 1. Create ChromaDB metadata filter for date range using timestamps
            # Convert dates to timestamps for ChromaDB filtering
            start_timestamp = datetime.combine(start_date, datetime.min.time()).timestamp()
            end_timestamp = datetime.combine(end_date, datetime.max.time()).timestamp()

            where_filter = {
                "$and": [
                    {"timestamp": {"$gte": start_timestamp}},
                    {"timestamp": {"$lte": end_timestamp}}
                ]
            }

            # 2. Use ChromaDB semantic search with metadata filtering
            semantic_results = self.chroma_manager.query_events(
                "financial_events",
                trigger_query,
                n_results=limit,
                where_filter=where_filter
            )

            if 'error' in semantic_results or not semantic_results.get('results'):
                logger.warning(f"Semantic search failed or returned no results for: {trigger_query}")
                return []

            # 3. Convert ChromaDB results to standardized event format
            trigger_events = []
            results = semantic_results['results']

            # ChromaDB results structure: results['metadatas'][0] contains list of metadata
            if results.get('metadatas') and results['metadatas'][0]:
                for i, metadata in enumerate(results['metadatas'][0]):
                    if not metadata:
                        continue

                    # Create event from ChromaDB metadata and document
                    event = {
                        'event_id': metadata.get('event_id', f"semantic_{i}"),
                        'event_date': datetime.strptime(metadata.get('date', '1970-01-01'), '%Y-%m-%d').date(),
                        'title': results['documents'][0][i] if results.get('documents') and len(results['documents'][0]) > i else '',
                        'event_type': metadata.get('event_type', 'unknown'),
                        'source': metadata.get('source', 'chromadb'),
                        'importance': metadata.get('importance', 'medium'),
                        'metadata': metadata,
                        'semantic_score': results['distances'][0][i] if results.get('distances') and len(results['distances'][0]) > i else 0.0
                    }

                    trigger_events.append(event)

            logger.info(f"Semantic search found {len(trigger_events)} trigger events for '{trigger_query}' in date range {start_date} to {end_date}")
            return trigger_events

        except Exception as e:
            logger.error(f"Error in semantic trigger event search: {e}")
            return []

    def _find_trigger_events_in_range(self,
                                     event_type: str,
                                     conditions: Dict[str, Any],
                                     start_date: date,
                                     end_date: date,
                                     limit: int) -> List[Dict[str, Any]]:
        """Find events that match trigger conditions within a specific date range."""
        # Get all events of the specified type within the date range
        events = self.postgres_manager.get_events_by_date_range(
            start_date, end_date, event_types=[event_type]
        )

        # Apply additional conditions
        filtered_events = []
        for event in events:
            if self._event_matches_conditions(event, conditions):
                filtered_events.append(event)
                if len(filtered_events) >= limit:
                    break

        return filtered_events

    def _aggregate_market_statistics(self, market_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate market statistics across multiple events."""
        if not market_analysis:
            return {}

        # Extract returns for aggregation
        returns_1d = []
        returns_5d = []
        returns_10d = []
        returns_20d = []

        for analysis in market_analysis:
            market_impact = analysis.get('market_impact', {})
            forward_returns = market_impact.get('forward_returns', {})

            if 'return_1d' in forward_returns:
                returns_1d.append(forward_returns['return_1d']['return_pct'])
            if 'return_5d' in forward_returns:
                returns_5d.append(forward_returns['return_5d']['return_pct'])
            if 'return_10d' in forward_returns:
                returns_10d.append(forward_returns['return_10d']['return_pct'])
            if 'return_20d' in forward_returns:
                returns_20d.append(forward_returns['return_20d']['return_pct'])

        def calc_stats(returns_list):
            if not returns_list:
                return {}
            return {
                'average_return': round(sum(returns_list) / len(returns_list), 2),
                'positive_events': len([r for r in returns_list if r > 0]),
                'negative_events': len([r for r in returns_list if r < 0]),
                'total_events': len(returns_list),
                'success_rate': round(len([r for r in returns_list if r > 0]) / len(returns_list) * 100, 1)
            }

        return {
            'return_1d': calc_stats(returns_1d),
            'return_5d': calc_stats(returns_5d),
            'return_10d': calc_stats(returns_10d),
            'return_20d': calc_stats(returns_20d),
            'total_events_with_market_data': len(market_analysis)
        }

    def _analyze_event_based_impacts(self,
                                   trigger_events: List[Dict[str, Any]],
                                   impact_timeframe_days: int) -> List[Dict[str, Any]]:
        """Analyze impacts using traditional event-based approach."""
        impact_analysis = []
        for trigger in trigger_events:
            impacts = self._find_subsequent_events(
                trigger['event_date'], impact_timeframe_days
            )

            impact_analysis.append({
                'trigger_event': trigger,
                'subsequent_events': impacts,
                'impact_count': len(impacts)
            })
        return impact_analysis

    def _find_trigger_events(self,
                           event_type: str,
                           conditions: Dict[str, Any],
                           limit: int) -> List[Dict[str, Any]]:
        """Find events that match trigger conditions."""
        # Get all events of the specified type
        events = self.postgres_manager.get_events_by_date_range(
            date(1970, 1, 1), date.today(),
            event_types=[event_type]
        )

        # Apply additional conditions
        filtered_events = []
        for event in events:
            if self._event_matches_conditions(event, conditions):
                filtered_events.append(event)
                if len(filtered_events) >= limit:
                    break

        return filtered_events

    def _event_matches_conditions(self,
                                event: Dict[str, Any],
                                conditions: Dict[str, Any]) -> bool:
        """Check if an event matches the specified conditions."""
        # Example conditions:
        # {'change_direction': 'increase'} - for rate increases
        # {'magnitude_threshold': 0.25} - for changes above threshold

        if 'change_direction' in conditions:
            direction = conditions['change_direction']
            title = event.get('title', '').lower()

            if direction == 'increase' and any(word in title for word in ['raises', 'increases', 'rises', 'surge']):
                return True
            elif direction == 'decrease' and any(word in title for word in ['cuts', 'decreases', 'falls', 'decline']):
                return True

        # Add more condition types as needed
        return True

    def _find_subsequent_events(self,
                              trigger_date: date,
                              timeframe_days: int) -> List[Dict[str, Any]]:
        """Find events that occurred after a trigger event."""
        start_date = trigger_date + timedelta(days=1)
        end_date = trigger_date + timedelta(days=timeframe_days)

        return self.postgres_manager.get_events_by_date_range(start_date, end_date)

    def _analyze_impact_patterns(self,
                               impact_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns across multiple trigger-impact pairs."""
        total_triggers = len(impact_analysis)
        total_subsequent_events = sum(case['impact_count'] for case in impact_analysis)

        # Analyze common subsequent event types
        subsequent_types = {}
        for case in impact_analysis:
            for event in case['subsequent_events']:
                event_type = event['event_type']
                subsequent_types[event_type] = subsequent_types.get(event_type, 0) + 1

        return {
            'total_trigger_events': total_triggers,
            'total_subsequent_events': total_subsequent_events,
            'avg_subsequent_events_per_trigger': total_subsequent_events / total_triggers if total_triggers > 0 else 0,
            'common_subsequent_event_types': dict(sorted(subsequent_types.items(), key=lambda x: x[1], reverse=True)),
            'pattern_strength': 'High' if total_subsequent_events / total_triggers > 3 else 'Medium' if total_subsequent_events / total_triggers > 1 else 'Low'
        }

    def _analyze_temporal_patterns(self,
                                 events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze temporal patterns in events."""
        if not events:
            return {}

        # Group by month
        monthly_counts = {}
        for event in events:
            month = event['event_date'].strftime('%Y-%m')
            monthly_counts[month] = monthly_counts.get(month, 0) + 1

        # Group by event type
        type_distribution = {}
        for event in events:
            event_type = event['event_type']
            type_distribution[event_type] = type_distribution.get(event_type, 0) + 1

        return {
            'total_events': len(events),
            'monthly_distribution': monthly_counts,
            'event_type_distribution': type_distribution,
            'date_range': {
                'earliest': min(events, key=lambda x: x['event_date'])['event_date'].isoformat(),
                'latest': max(events, key=lambda x: x['event_date'])['event_date'].isoformat()
            }
        }

    def _filter_semantic_by_structured(self,
                                     semantic_results: Dict[str, Any],
                                     structured_ids: set) -> Dict[str, Any]:
        """Filter semantic search results by structured query results."""
        # This would require event_id matching between ChromaDB and PostgreSQL
        # For now, return semantic results as-is
        return semantic_results