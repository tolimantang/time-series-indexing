"""
NewsEncoder - Financial News and Economic Event Data Encoder

A Python package for collecting and encoding financial news, economic events,
and macro data for correlation analysis with astronomical patterns.
"""

from .encoder import NewsEncoder
from .data_models import FinancialNewsData, EconomicEvent, MarketSummary

__version__ = "0.1.0"
__author__ = "NewsEncoder Team"

__all__ = [
    "NewsEncoder",
    "FinancialNewsData",
    "EconomicEvent",
    "MarketSummary"
]