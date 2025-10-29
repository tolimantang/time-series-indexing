"""
FRED Event Encoder

Fetches financial events from FRED (Federal Reserve Economic Data) API.
Converts economic data series into semantic financial events.
"""

import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging
import time

from ..core.base_encoder import BaseEventEncoder, FinancialEvent

logger = logging.getLogger(__name__)


class FredEventEncoder(BaseEventEncoder):
    """
    Event encoder for FRED (Federal Reserve Economic Data).

    Fetches key economic indicators and converts them to financial events
    suitable for semantic search and correlation analysis.
    """

    # Key FRED series for financial events - focused on high-impact, low-noise indicators
    KEY_SERIES = {
        # Federal Funds Rate and Monetary Policy (MOST IMPORTANT)
        'FEDFUNDS': {
            'name': 'Federal Funds Rate',
            'event_type': 'fed_decision',
            'importance': 'high',
            'description': 'Federal Open Market Committee target rate'
        },

        # Employment Data (MAJOR MARKET MOVERS)
        'UNRATE': {
            'name': 'Unemployment Rate',
            'event_type': 'employment_data',
            'importance': 'high',
            'description': 'Civilian unemployment rate'
        },
        'PAYEMS': {
            'name': 'Nonfarm Payrolls',
            'event_type': 'employment_data',
            'importance': 'high',
            'description': 'All employees, total nonfarm payrolls (thousands)'
        },

        # Inflation Data (CRITICAL FOR FED DECISIONS)
        'CPIAUCSL': {
            'name': 'Consumer Price Index',
            'event_type': 'inflation_data',
            'importance': 'high',
            'description': 'Consumer Price Index for All Urban Consumers: All Items'
        },
        'CPILFESL': {
            'name': 'Core CPI',
            'event_type': 'inflation_data',
            'importance': 'high',
            'description': 'Consumer Price Index for All Urban Consumers: All Items Less Food and Energy'
        },

        # GDP and Growth (QUARTERLY RELEASES)
        'GDP': {
            'name': 'Gross Domestic Product',
            'event_type': 'economic_growth',
            'importance': 'high',
            'description': 'Gross Domestic Product, seasonally adjusted annual rate'
        },

        # Treasury Rates (MARKET INDICATORS)
        'DGS10': {
            'name': '10-Year Treasury Rate',
            'event_type': 'treasury_data',
            'importance': 'medium',
            'description': '10-Year Treasury Constant Maturity Rate'
        }

        # Removed noisy series:
        # - DFF (daily fed funds - too noisy, FEDFUNDS is enough)
        # - NONFARM (incorrect series ID)
        # - GDPC1 (duplicate of GDP)
        # - TB3MS (3-month less important than 10-year)
        # - DEXUSEU (currency too volatile for daily events)
        # - USEPUINDXD (extremely noisy, even with 20% threshold)
    }

    def __init__(self, api_key: Optional[str] = None, **config):
        """
        Initialize FRED event encoder.

        Args:
            api_key: FRED API key (REQUIRED - get free key at https://fred.stlouisfed.org/docs/api/api_key.html)
            **config: Additional configuration options
        """
        super().__init__('fred', **config)

        self.api_key = api_key or os.getenv('FRED_API_KEY')
        if not self.api_key:
            raise ValueError(
                "FRED API key is required. Get a free key at: https://fred.stlouisfed.org/docs/api/api_key.html\n"
                "Then either:\n"
                "1. Pass it to FredEventEncoder(api_key='your_key')\n"
                "2. Set environment variable: FRED_API_KEY='your_key'"
            )

        self.base_url = 'https://api.stlouisfed.org/fred'

        # Rate limiting
        self.requests_per_second = config.get('requests_per_second', 5)  # Conservative limit
        self.last_request_time = 0

        logger.info(f"FRED encoder initialized with API key")

    def _rate_limit(self):
        """Implement rate limiting for FRED API."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / self.requests_per_second

        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def _make_fred_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Make a request to FRED API with rate limiting.

        Args:
            endpoint: FRED API endpoint
            params: Request parameters

        Returns:
            JSON response or None if error
        """
        self._rate_limit()

        # Add API key if available
        if self.api_key:
            params['api_key'] = self.api_key

        params['file_type'] = 'json'

        url = f"{self.base_url}/{endpoint}"

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            logger.error(f"FRED API request failed: {e}")
            return None

    def fetch_series_data(self,
                         series_id: str,
                         start_date: datetime,
                         end_date: datetime) -> Optional[pd.DataFrame]:
        """
        Fetch data for a specific FRED series.

        Args:
            series_id: FRED series identifier
            start_date: Start date for data
            end_date: End date for data

        Returns:
            DataFrame with date and value columns, or None if error
        """
        params = {
            'series_id': series_id,
            'observation_start': start_date.strftime('%Y-%m-%d'),
            'observation_end': end_date.strftime('%Y-%m-%d'),
            'output_type': 1,  # Observations only
            'sort_order': 'asc'
        }

        data = self._make_fred_request('series/observations', params)

        if not data or 'observations' not in data:
            logger.warning(f"No data returned for series {series_id}")
            return None

        observations = data['observations']

        if not observations:
            logger.warning(f"Empty observations for series {series_id}")
            return None

        # Convert to DataFrame
        df = pd.DataFrame(observations)

        # Clean data
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')

        # Remove missing values
        df = df.dropna(subset=['value'])

        if df.empty:
            logger.warning(f"No valid data for series {series_id}")
            return None

        return df[['date', 'value']].sort_values('date')

    def _detect_significant_changes(self,
                                  df: pd.DataFrame,
                                  series_info: Dict[str, Any]) -> List[Tuple[datetime, float, str]]:
        """
        Detect significant changes in a time series.

        Args:
            df: DataFrame with date and value columns
            series_info: Series metadata

        Returns:
            List of (date, value, change_description) tuples
        """
        if len(df) < 2:
            return []

        significant_events = []

        # Calculate changes
        df = df.copy()
        df['prev_value'] = df['value'].shift(1)
        df['change'] = df['value'] - df['prev_value']
        df['pct_change'] = df['change'] / df['prev_value'] * 100

        # Define significance thresholds by event type
        if series_info['event_type'] == 'fed_decision':
            # Fed funds rate changes (any change is significant)
            significant_rows = df[df['change'].abs() > 0]

            for _, row in significant_rows.iterrows():
                change = row['change']
                if change > 0:
                    description = f"Federal Reserve raises rate by {change:.2f} percentage points to {row['value']:.2f}%"
                else:
                    description = f"Federal Reserve cuts rate by {abs(change):.2f} percentage points to {row['value']:.2f}%"

                significant_events.append((row['date'], row['value'], description))

        elif series_info['event_type'] == 'employment_data':
            # Employment changes (0.1% unemployment rate or 50k jobs)
            if 'unemployment' in series_info['name'].lower():
                threshold = 0.1
                significant_rows = df[df['change'].abs() >= threshold]
            else:  # Payrolls
                threshold = 50  # 50k jobs
                significant_rows = df[df['change'].abs() >= threshold]

            for _, row in significant_rows.iterrows():
                change = row['change']
                if 'unemployment' in series_info['name'].lower():
                    direction = "rises" if change > 0 else "falls"
                    description = f"Unemployment rate {direction} by {abs(change):.1f}% to {row['value']:.1f}%"
                else:
                    direction = "increases" if change > 0 else "decreases"
                    description = f"Nonfarm payrolls {direction} by {abs(change):,.0f}k to {row['value']:,.0f}k"

                significant_events.append((row['date'], row['value'], description))

        elif series_info['event_type'] == 'inflation_data':
            # CPI changes (monthly 0.3% or more - indicates significant inflation moves)
            threshold = 0.3  # Monthly threshold
            significant_rows = df[df['pct_change'].abs() >= threshold]

            for _, row in significant_rows.iterrows():
                pct_change = row['pct_change']
                direction = "increases" if pct_change > 0 else "decreases"
                description = f"Consumer prices {direction} {abs(pct_change):.1f}% to {row['value']:.1f}"

                significant_events.append((row['date'], row['value'], description))

        elif series_info['event_type'] == 'economic_growth':
            # GDP changes (1% quarterly change or more)
            threshold = 1.0
            significant_rows = df[df['pct_change'].abs() >= threshold]

            for _, row in significant_rows.iterrows():
                pct_change = row['pct_change']
                direction = "grows" if pct_change > 0 else "contracts"
                description = f"GDP {direction} {abs(pct_change):.1f}% to ${row['value']:,.0f}B"

                significant_events.append((row['date'], row['value'], description))

        elif series_info['event_type'] == 'treasury_data':
            # Treasury rate changes (0.25% or more - significant yield moves)
            threshold = 0.25
            significant_rows = df[df['change'].abs() >= threshold]

            for _, row in significant_rows.iterrows():
                change = row['change']
                direction = "rises" if change > 0 else "falls"
                description = f"{series_info['name']} {direction} {abs(change):.2f}% to {row['value']:.2f}%"

                significant_events.append((row['date'], row['value'], description))

        elif series_info['event_type'] == 'policy_uncertainty':
            # Policy uncertainty - only very large moves (20% change in a day)
            threshold = 20.0
            significant_rows = df[df['pct_change'].abs() >= threshold]

            for _, row in significant_rows.iterrows():
                pct_change = row['pct_change']
                direction = "increases" if pct_change > 0 else "decreases"
                description = f"{series_info['name']} {direction} {abs(pct_change):.1f}% to {row['value']:.2f}"

                significant_events.append((row['date'], row['value'], description))

        else:
            # Generic threshold - much higher for other series (10% change)
            threshold = 10.0
            significant_rows = df[df['pct_change'].abs() >= threshold]

            for _, row in significant_rows.iterrows():
                pct_change = row['pct_change']
                direction = "increases" if pct_change > 0 else "decreases"
                description = f"{series_info['name']} {direction} {abs(pct_change):.1f}% to {row['value']:.2f}"

                significant_events.append((row['date'], row['value'], description))

        return significant_events

    def fetch_events(self,
                    start_date: datetime,
                    end_date: datetime,
                    series_ids: Optional[List[str]] = None,
                    **kwargs) -> List[FinancialEvent]:
        """
        Fetch FRED events for a date range.

        Args:
            start_date: Start date
            end_date: End date
            series_ids: Specific series to fetch (default: all key series)
            **kwargs: Additional parameters

        Returns:
            List of FinancialEvent objects
        """
        if series_ids is None:
            series_ids = list(self.KEY_SERIES.keys())

        all_events = []

        for series_id in series_ids:
            if series_id not in self.KEY_SERIES:
                logger.warning(f"Unknown series ID: {series_id}")
                continue

            series_info = self.KEY_SERIES[series_id]

            try:
                # Fetch series data
                df = self.fetch_series_data(series_id, start_date, end_date)

                if df is None or df.empty:
                    logger.warning(f"No data for series {series_id}")
                    continue

                # Detect significant changes
                significant_changes = self._detect_significant_changes(df, series_info)

                # Create events for significant changes
                for event_date, value, description in significant_changes:
                    # Filter to date range (significant changes might include context)
                    if start_date.date() <= event_date.date() <= end_date.date():
                        event = FinancialEvent(
                            date=event_date,
                            source='fred',
                            event_type=series_info['event_type'],
                            title=f"{series_info['name']}: {description}",
                            description=f"FRED series {series_id} shows {description}. "
                                      f"This represents a significant change in {series_info['description'].lower()}.",
                            importance=series_info['importance'],
                            series_id=series_id,
                            value=value,
                            fred_description=series_info['description']
                        )

                        all_events.append(event)

                logger.info(f"Processed series {series_id}: {len(significant_changes)} significant events")

            except Exception as e:
                logger.error(f"Error processing series {series_id}: {e}")
                continue

        logger.info(f"FRED: Generated {len(all_events)} events for {start_date.date()} to {end_date.date()}")
        return all_events

    def fetch_single_date(self, date: datetime, **kwargs) -> List[FinancialEvent]:
        """
        Fetch FRED events for a single date.

        Args:
            date: Target date
            **kwargs: Additional parameters

        Returns:
            List of FinancialEvent objects
        """
        # For single date, look at a small window to detect changes
        start_date = date - timedelta(days=5)
        end_date = date + timedelta(days=1)

        all_events = self.fetch_events(start_date, end_date, **kwargs)

        # Filter to exact date
        date_events = [event for event in all_events if event.date.date() == date.date()]

        return date_events

    def validate_connection(self) -> bool:
        """Test connection to FRED API."""
        try:
            # Try to fetch a small amount of data
            test_params = {
                'series_id': 'FEDFUNDS',
                'limit': 1,
                'sort_order': 'desc'
            }

            result = self._make_fred_request('series/observations', test_params)

            if result and 'observations' in result:
                logger.info("FRED API connection validated successfully")
                return True
            else:
                logger.error("FRED API connection validation failed")
                return False

        except Exception as e:
            logger.error(f"FRED API connection validation error: {e}")
            return False

    def get_available_date_range(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Get available date range for FRED data."""
        # FRED has data going back to 1954 for some series
        # Most key financial data starts in 1970s
        earliest = datetime(1970, 1, 1)
        latest = datetime.now()
        return earliest, latest

    def get_supported_event_types(self) -> List[str]:
        """Get list of supported event types."""
        event_types = set()
        for series_info in self.KEY_SERIES.values():
            event_types.add(series_info['event_type'])
        return list(event_types)

    def get_series_info(self, series_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a FRED series.

        Args:
            series_id: FRED series identifier

        Returns:
            Series metadata or None if not found
        """
        params = {'series_id': series_id}

        result = self._make_fred_request('series', params)

        if result and 'seriess' in result and result['seriess']:
            return result['seriess'][0]

        return None