"""
Market data sources for the AstroFinancial system.
Fetches price data and computes market signals.
"""

import os
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class AlphaVantageSource:
    """Alpha Vantage API data source."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_KEY')
        self.base_url = "https://www.alphavantage.co/query"

        if not self.api_key:
            logger.warning("Alpha Vantage API key not found")

    def get_daily_data(self, symbol: str, outputsize: str = "full") -> pd.DataFrame:
        """Get daily OHLCV data for a symbol."""
        try:
            params = {
                'function': 'TIME_SERIES_DAILY_ADJUSTED',
                'symbol': symbol,
                'outputsize': outputsize,
                'apikey': self.api_key
            }

            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

            if 'Time Series (Daily)' not in data:
                logger.error(f"No data found for {symbol}: {data}")
                return pd.DataFrame()

            # Convert to DataFrame
            df = pd.DataFrame(data['Time Series (Daily)']).T
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()

            # Clean column names and convert to float
            df.columns = ['open', 'high', 'low', 'close', 'adjusted_close', 'volume', 'dividend', 'split']
            df = df.astype(float)

            logger.info(f"Fetched {len(df)} days of data for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()

    def get_intraday_data(self, symbol: str, interval: str = "5min") -> pd.DataFrame:
        """Get intraday data for a symbol."""
        try:
            params = {
                'function': 'TIME_SERIES_INTRADAY',
                'symbol': symbol,
                'interval': interval,
                'outputsize': 'full',
                'apikey': self.api_key
            }

            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

            time_series_key = f'Time Series ({interval})'
            if time_series_key not in data:
                logger.error(f"No intraday data found for {symbol}")
                return pd.DataFrame()

            df = pd.DataFrame(data[time_series_key]).T
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()

            df.columns = ['open', 'high', 'low', 'close', 'volume']
            df = df.astype(float)

            return df

        except Exception as e:
            logger.error(f"Error fetching intraday data for {symbol}: {e}")
            return pd.DataFrame()


class YahooFinanceSource:
    """Yahoo Finance data source (backup/alternative)."""

    def __init__(self):
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart"

    def get_daily_data(self, symbol: str, period: str = "2y") -> pd.DataFrame:
        """Get daily data from Yahoo Finance."""
        try:
            params = {
                'symbol': symbol,
                'period1': int((datetime.now() - timedelta(days=730)).timestamp()),
                'period2': int(datetime.now().timestamp()),
                'interval': '1d'
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(f"{self.base_url}/{symbol}", params=params, headers=headers)
            response.raise_for_status()
            data = response.json()

            if 'chart' not in data or not data['chart']['result']:
                logger.error(f"No data found for {symbol}")
                return pd.DataFrame()

            result = data['chart']['result'][0]
            timestamps = result['timestamp']
            quotes = result['indicators']['quote'][0]

            df = pd.DataFrame({
                'open': quotes['open'],
                'high': quotes['high'],
                'low': quotes['low'],
                'close': quotes['close'],
                'volume': quotes['volume']
            })

            df.index = pd.to_datetime([datetime.fromtimestamp(ts) for ts in timestamps])
            df = df.dropna().sort_index()

            logger.info(f"Fetched {len(df)} days of data for {symbol} from Yahoo")
            return df

        except Exception as e:
            logger.error(f"Error fetching Yahoo data for {symbol}: {e}")
            return pd.DataFrame()


class MarketDataManager:
    """Manages multiple data sources with Yahoo Finance as primary."""

    def __init__(self, alpha_vantage_key: Optional[str] = None):
        self.yahoo = YahooFinanceSource()  # Primary source
        self.alpha_vantage = AlphaVantageSource(alpha_vantage_key)  # Fallback only

    def get_market_data(self, symbol: str, source: str = "auto") -> pd.DataFrame:
        """Get market data with Yahoo Finance as primary source."""

        if source == "yahoo" or source == "auto":
            logger.info(f"Fetching {symbol} from Yahoo Finance")
            df = self.yahoo.get_daily_data(symbol)
            if not df.empty:
                return df

        if source == "alpha_vantage" and self.alpha_vantage.api_key:
            logger.info(f"Fetching {symbol} from Alpha Vantage (fallback)")
            return self.alpha_vantage.get_daily_data(symbol)

        logger.error(f"No data source available for {symbol}")
        return pd.DataFrame()

    def get_multiple_assets(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """Fetch data for multiple assets."""
        results = {}

        for symbol in symbols:
            logger.info(f"Fetching data for {symbol}")
            data = self.get_market_data(symbol)
            if not data.empty:
                results[symbol] = data
            else:
                logger.warning(f"No data retrieved for {symbol}")

        return results