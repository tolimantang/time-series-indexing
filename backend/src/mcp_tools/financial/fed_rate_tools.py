"""
Federal Reserve Rate Analysis Tools

Provides precise queries for Fed rate changes that go beyond semantic similarity.
Solves the problem where "Fed cuts rate by 0.1%" vs "Fed cuts rate by 0.2%"
are treated as similar by ChromaDB.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta

from ..base.tool_base import BaseMCPTool

logger = logging.getLogger(__name__)


class FedRateChangesTool(BaseMCPTool):
    """
    Tool for precise Fed rate change queries.

    Examples:
    - Fed rate cuts greater than 0.25%
    - Rate increases between 0.1% and 0.5%
    - All rate changes in 2020-2023
    """

    def __init__(self, postgres_manager, market_data_manager=None):
        super().__init__(
            name="fed_rate_changes",
            description="Find Federal Reserve rate changes with precise numerical filters"
        )
        self.postgres_manager = postgres_manager
        self.market_data_manager = market_data_manager

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "direction": {
                    "type": "string",
                    "enum": ["increase", "decrease", "any"],
                    "description": "Direction of rate change"
                },
                "min_magnitude": {
                    "type": "number",
                    "description": "Minimum change magnitude in percentage points (e.g., 0.25 for 0.25%)"
                },
                "max_magnitude": {
                    "type": "number",
                    "description": "Maximum change magnitude in percentage points"
                },
                "start_date": {
                    "type": "string",
                    "format": "date",
                    "description": "Start date for search (YYYY-MM-DD)"
                },
                "end_date": {
                    "type": "string",
                    "format": "date",
                    "description": "End date for search (YYYY-MM-DD)"
                },
                "target_asset": {
                    "type": "string",
                    "description": "Optional: Asset symbol to analyze market impact (e.g., 'GLD', 'SPY')"
                },
                "impact_days": {
                    "type": "integer",
                    "default": 30,
                    "description": "Days to analyze market impact after each Fed decision"
                }
            },
            "required": ["direction", "start_date", "end_date"],
            "additionalProperties": False
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute Fed rate changes query."""
        try:
            # Validate parameters
            self.validate_params(**kwargs)

            direction = kwargs['direction']
            start_date = self._parse_date(kwargs['start_date'])
            end_date = self._parse_date(kwargs['end_date'])
            min_magnitude = kwargs.get('min_magnitude')
            max_magnitude = kwargs.get('max_magnitude')
            target_asset = kwargs.get('target_asset')
            impact_days = kwargs.get('impact_days', 30)

            logger.info(f"Searching Fed rate changes: {direction}, {min_magnitude}-{max_magnitude}%, "
                       f"{start_date} to {end_date}")

            # Build SQL query for precise Fed rate filtering
            query_conditions = []
            query_params = []

            # Base conditions for Fed events
            query_conditions.append("event_type = 'fed_decision'")
            query_conditions.append("event_date >= %s")
            query_params.append(start_date)
            query_conditions.append("event_date <= %s")
            query_params.append(end_date)

            # Direction filter
            if direction == "increase":
                query_conditions.append("change_amount > 0")
            elif direction == "decrease":
                query_conditions.append("change_amount < 0")
            # "any" means no additional filter

            # Magnitude filters (use absolute value for magnitude comparison)
            if min_magnitude is not None:
                query_conditions.append("ABS(change_amount) >= %s")
                query_params.append(min_magnitude)

            if max_magnitude is not None:
                query_conditions.append("ABS(change_amount) <= %s")
                query_params.append(max_magnitude)

            # Build final query
            where_clause = " AND ".join(query_conditions)
            sql_query = f"""
                SELECT
                    event_id,
                    event_date,
                    title,
                    description,
                    value,
                    previous_value,
                    change_amount,
                    change_percent,
                    importance,
                    metadata
                FROM financial_events
                WHERE {where_clause}
                ORDER BY event_date DESC
            """

            # Execute query
            fed_events = self._execute_sql_query(sql_query, query_params)

            # If target asset specified, analyze market impact
            market_impact_analysis = None
            if target_asset and self.market_data_manager and fed_events:
                market_impact_analysis = self._analyze_market_impact(
                    fed_events, target_asset, impact_days
                )

            # Format results
            result_data = {
                'query_parameters': {
                    'direction': direction,
                    'min_magnitude': min_magnitude,
                    'max_magnitude': max_magnitude,
                    'date_range': f"{start_date} to {end_date}",
                    'target_asset': target_asset
                },
                'fed_rate_events': fed_events,
                'total_events': len(fed_events),
                'market_impact_analysis': market_impact_analysis
            }

            # Calculate summary statistics
            if fed_events:
                magnitudes = [abs(event['change_amount']) for event in fed_events if event['change_amount']]
                result_data['summary_statistics'] = {
                    'average_magnitude': round(sum(magnitudes) / len(magnitudes), 3) if magnitudes else 0,
                    'largest_change': max(magnitudes) if magnitudes else 0,
                    'smallest_change': min(magnitudes) if magnitudes else 0
                }

            return self._format_result(
                success=True,
                data=result_data,
                metadata={
                    'sql_query': sql_query,
                    'execution_time': datetime.now().isoformat()
                }
            )

        except Exception as e:
            logger.error(f"Error in FedRateChangesTool: {e}")
            return self._format_result(
                success=False,
                error=str(e)
            )

    def _execute_sql_query(self, query: str, params: List[Any]) -> List[Dict[str, Any]]:
        """Execute SQL query and return results."""
        try:
            self.postgres_manager._ensure_connection()

            with self.postgres_manager.connection.cursor() as cursor:
                cursor.execute(query, params)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                # Convert rows to list of dictionaries
                results = []
                for row in rows:
                    result = {}
                    for i, value in enumerate(row):
                        # Handle different data types
                        if isinstance(value, date):
                            result[columns[i]] = value.isoformat()
                        elif isinstance(value, datetime):
                            result[columns[i]] = value.isoformat()
                        else:
                            result[columns[i]] = value
                    results.append(result)

                return results

        except Exception as e:
            logger.error(f"SQL query execution error: {e}")
            raise

    def _analyze_market_impact(self,
                             fed_events: List[Dict[str, Any]],
                             target_asset: str,
                             impact_days: int) -> Dict[str, Any]:
        """Analyze market impact of Fed events on target asset."""
        if not self.market_data_manager:
            return {"error": "Market data manager not available"}

        try:
            impact_results = []

            for event in fed_events:
                event_date = datetime.strptime(event['event_date'], '%Y-%m-%d').date()

                # Get market impact for this event
                impact = self.market_data_manager.calculate_event_impact(
                    target_asset, event_date, forward_days=impact_days
                )

                if impact:
                    impact_results.append({
                        'event_date': event['event_date'],
                        'fed_change_amount': event['change_amount'],
                        'market_impact': impact
                    })

            # Calculate aggregate statistics
            if impact_results:
                returns = []
                for result in impact_results:
                    forward_returns = result['market_impact'].get('forward_returns', {})
                    if 'return_5d' in forward_returns:
                        returns.append(forward_returns['return_5d']['return_pct'])

                aggregate_stats = {
                    'total_events_analyzed': len(impact_results),
                    'average_5d_return': round(sum(returns) / len(returns), 2) if returns else 0,
                    'positive_events': len([r for r in returns if r > 0]),
                    'negative_events': len([r for r in returns if r < 0]),
                    'success_rate': round(len([r for r in returns if r > 0]) / len(returns) * 100, 1) if returns else 0
                }

                return {
                    'individual_impacts': impact_results,
                    'aggregate_statistics': aggregate_stats,
                    'target_asset': target_asset
                }
            else:
                return {"message": "No market impact data available for the specified events"}

        except Exception as e:
            logger.error(f"Market impact analysis error: {e}")
            return {"error": f"Market impact analysis failed: {str(e)}"}