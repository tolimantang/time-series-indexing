"""
Data models for trading opportunity analysis.
"""

from dataclasses import dataclass
from datetime import date
from typing import Dict, Any, Optional


@dataclass
class TradingOpportunity:
    """Represents a trading opportunity with astrological analysis."""
    id: int
    symbol: str
    position_type: str
    entry_date: date
    exit_date: date
    entry_price: float
    exit_price: float
    holding_days: int
    profit_percent: float
    trade_score: float
    astrological_score: float
    entry_astro_description: str
    exit_astro_description: str
    entry_planetary_data: Dict[str, Any]
    exit_planetary_data: Dict[str, Any]
    astro_analysis_summary: str
    claude_analysis: Optional[str] = None


@dataclass
class AstrologicalPattern:
    """Represents an identified astrological pattern."""
    pattern_type: str  # e.g., "lunar_phase", "planetary_aspect", "sign_position"
    pattern_value: str  # e.g., "Full Moon", "Mars-Jupiter trine", "Sun in Aries"
    trade_count: int
    avg_profit: float
    avg_astrological_score: float
    success_rate: float
    examples: list


@dataclass
class LLMAnalysisRequest:
    """Request for LLM analysis of trading patterns."""
    trading_opportunities: list
    analysis_focus: str  # e.g., "oil_market_patterns", "lunar_correlations"
    prompt_template: str
    include_planetary_data: bool = True
    include_aspects: bool = True
    max_opportunities: int = 30