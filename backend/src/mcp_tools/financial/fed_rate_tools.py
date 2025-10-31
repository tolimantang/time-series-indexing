"""
Federal Reserve Rate Analysis Tools

Provides precise queries for Fed rate changes that go beyond semantic similarity.
Solves the problem where "Fed cuts rate by 0.1%" vs "Fed cuts rate by 0.2%"
are treated as similar by ChromaDB.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
import json
import os
import anthropic

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

    def __init__(self, postgres_manager, market_data_manager=None, anthropic_api_key=None):
        super().__init__(
            name="fed_rate_changes",
            description="Find Federal Reserve rate changes using natural language or precise filters"
        )
        self.postgres_manager = postgres_manager
        self.market_data_manager = market_data_manager

        # Initialize Anthropic client
        api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')
        if api_key:
            try:
                self.llm_client = anthropic.Anthropic(api_key=api_key)
                logger.info("✅ Anthropic client initialized for Fed rate tool")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic client: {e}")
                self.llm_client = None
        else:
            logger.info("No Anthropic API key provided, using fallback WHERE clause generation")
            self.llm_client = None

    def get_schema(self) -> Dict[str, Any]:
        """Return JSON schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language query about Fed rate changes (e.g., 'Fed increases rates by more than 0.25% after 2020')"
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
            "required": ["query"],
            "additionalProperties": False
        }

    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute Fed rate changes query."""
        try:
            self.validate_params(**kwargs)

            query = kwargs['query']
            target_asset = kwargs.get('target_asset')
            impact_days = kwargs.get('impact_days', 30)

            logger.info(f"Processing natural language query: {query}")

            # Generate WHERE clause using LLM
            where_clause, query_params = self._generate_where_clause(query)

            # Build final SQL query
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
                    'original_query': query,
                    'generated_where_clause': where_clause,
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

    def _generate_where_clause(self, natural_language_query: str) -> tuple[str, List[Any]]:
        """Generate WHERE clause from natural language using LLM."""
        if not self.llm_client:
            # Fallback to basic parsing for simple queries
            return self._fallback_where_clause(natural_language_query)

        system_prompt = """You are a SQL WHERE clause generator for Federal Reserve rate data.

Available columns in financial_events table:
- event_type (always 'fed_decision' for Fed rate events)
- event_date (DATE format YYYY-MM-DD)
- change_amount (DECIMAL - positive for increases, negative for decreases, in percentage points)
- value (DECIMAL - the actual rate value after change)
- previous_value (DECIMAL - rate value before change)
- importance (INTEGER 1-5, 5 being most important)
- title (TEXT)
- description (TEXT)

Generate ONLY the WHERE clause conditions (without 'WHERE' keyword) and parameters.
Always include: event_type = 'fed_decision'
Use parameterized queries with %s placeholders.

Return JSON format:
{
  "where_clause": "condition1 AND condition2 AND condition3",
  "parameters": [param1, param2, param3]
}

Examples:
Query: "Fed increases rates by more than 0.25% after 2020"
Response: {
  "where_clause": "event_type = %s AND change_amount > %s AND event_date > %s",
  "parameters": ["fed_decision", 0.25, "2020-12-31"]
}

Query: "Large Fed rate cuts during 2008 financial crisis"
Response: {
  "where_clause": "event_type = %s AND change_amount < %s AND event_date BETWEEN %s AND %s",
  "parameters": ["fed_decision", -0.25, "2007-01-01", "2009-12-31"]
}"""

        try:
            response = self.llm_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                system=system_prompt,
                messages=[{"role": "user", "content": natural_language_query}]
            )

            response_text = response.content[0].text
            logger.debug(f"LLM response: {response_text}")

            result = json.loads(response_text)
            return result["where_clause"], result["parameters"]

        except Exception as e:
            logger.warning(f"LLM WHERE clause generation failed: {e}, using fallback")
            return self._fallback_where_clause(natural_language_query)

    def _fallback_where_clause(self, query: str) -> tuple[str, List[Any]]:
        """Simple fallback WHERE clause generation."""
        conditions = ["event_type = %s"]
        params = ["fed_decision"]

        # Basic keyword detection
        query_lower = query.lower()

        if "increase" in query_lower:
            conditions.append("change_amount > %s")
            params.append(0)
        elif "decrease" in query_lower or "cut" in query_lower:
            conditions.append("change_amount < %s")
            params.append(0)

        # Look for years
        import re
        years = re.findall(r'\b(19|20)\d{2}\b', query)
        if years:
            year = years[0]
            conditions.append("event_date >= %s")
            params.append(f"{year}-01-01")

        return " AND ".join(conditions), params

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