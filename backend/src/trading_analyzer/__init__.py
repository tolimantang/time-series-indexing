"""
Trading Opportunity Analyzer
Analyzes historical market data to identify profitable trading opportunities.
"""

from .core.opportunity_detector import TradingOpportunityDetector, TradeOpportunity
from .core.data_access import MarketDataAccess

__version__ = "1.0.0"
__all__ = ["TradingOpportunityDetector", "TradeOpportunity", "MarketDataAccess"]