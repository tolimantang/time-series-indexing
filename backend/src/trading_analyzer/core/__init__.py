"""
Core modules for trading opportunity analysis.
"""

from .opportunity_detector import TradingOpportunityDetector, TradeOpportunity
from .data_access import MarketDataAccess

__all__ = ["TradingOpportunityDetector", "TradeOpportunity", "MarketDataAccess"]