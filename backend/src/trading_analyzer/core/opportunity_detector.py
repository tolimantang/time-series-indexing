"""
Trading Opportunity Detector
Analyzes historical market data to identify profitable trading opportunities
based on configurable criteria including holding period and risk management.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TradeOpportunity:
    """Represents a single trading opportunity."""
    symbol: str
    position_type: str  # 'long' or 'short'
    entry_date: datetime
    exit_date: datetime
    entry_price: float
    exit_price: float
    holding_days: int
    profit_percent: float
    max_unrealized_gain_percent: float
    max_unrealized_loss_percent: float
    max_drawdown_from_peak: float
    peak_profit_date: datetime
    peak_profit_percent: float
    trade_score: float  # Composite score for ranking


class TradingOpportunityDetector:
    """Detects and analyzes trading opportunities in historical market data."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize detector with configuration."""
        self.config = config
        self.trading_rules = config.get('trading_rules', {})
        self.min_holding_days = self.trading_rules.get('min_holding_days', 3)
        self.max_holding_days = self.trading_rules.get('max_holding_days', 30)
        self.max_unrealized_loss_percent = self.trading_rules.get('max_unrealized_loss_percent', 50.0)

        self.analyze_long = config.get('position_types', {}).get('analyze_long', True)
        self.analyze_short = config.get('position_types', {}).get('analyze_short', True)

    def analyze_symbol(self, symbol: str, price_data: pd.DataFrame) -> List[TradeOpportunity]:
        """Analyze a single symbol for trading opportunities."""
        logger.info(f"Analyzing trading opportunities for {symbol}")
        logger.info(f"Price data range: {price_data.index.min()} to {price_data.index.max()}")
        logger.info(f"Total price records: {len(price_data)}")

        opportunities = []

        # Analyze long positions
        if self.analyze_long:
            long_opportunities = self._find_long_opportunities(symbol, price_data)
            opportunities.extend(long_opportunities)
            logger.info(f"Found {len(long_opportunities)} long opportunities for {symbol}")

        # Analyze short positions
        if self.analyze_short:
            short_opportunities = self._find_short_opportunities(symbol, price_data)
            opportunities.extend(short_opportunities)
            logger.info(f"Found {len(short_opportunities)} short opportunities for {symbol}")

        # Calculate trade scores and sort
        for opportunity in opportunities:
            opportunity.trade_score = self._calculate_trade_score(opportunity)

        # Sort by trade score (best opportunities first)
        opportunities.sort(key=lambda x: x.trade_score, reverse=True)

        logger.info(f"Total opportunities found for {symbol}: {len(opportunities)}")
        return opportunities

    def _find_long_opportunities(self, symbol: str, price_data: pd.DataFrame) -> List[TradeOpportunity]:
        """Find profitable long position opportunities."""
        opportunities = []
        data = price_data.copy()

        # Add date index as column for easier access
        data['date'] = data.index

        for entry_idx in range(len(data) - self.min_holding_days):
            entry_row = data.iloc[entry_idx]
            entry_date = entry_row['date']
            entry_price = entry_row['close']

            # Look for exit opportunities within holding period
            max_exit_idx = min(entry_idx + self.max_holding_days, len(data) - 1)

            for exit_idx in range(entry_idx + self.min_holding_days, max_exit_idx + 1):
                exit_row = data.iloc[exit_idx]
                exit_date = exit_row['date']
                exit_price = exit_row['close']

                holding_days = (exit_date - entry_date).days

                # Calculate profit for long position
                profit_percent = ((exit_price - entry_price) / entry_price) * 100

                # Analyze the trade path for risk management
                trade_analysis = self._analyze_trade_path(
                    data.iloc[entry_idx:exit_idx + 1],
                    entry_price,
                    'long'
                )

                # Check if trade meets our criteria
                if self._is_valid_long_trade(trade_analysis, profit_percent):
                    opportunity = TradeOpportunity(
                        symbol=symbol,
                        position_type='long',
                        entry_date=entry_date,
                        exit_date=exit_date,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        holding_days=holding_days,
                        profit_percent=profit_percent,
                        max_unrealized_gain_percent=trade_analysis['max_gain_percent'],
                        max_unrealized_loss_percent=trade_analysis['max_loss_percent'],
                        max_drawdown_from_peak=trade_analysis['max_drawdown_from_peak'],
                        peak_profit_date=trade_analysis['peak_date'],
                        peak_profit_percent=trade_analysis['peak_profit_percent'],
                        trade_score=0.0  # Will be calculated later
                    )
                    opportunities.append(opportunity)

        return opportunities

    def _find_short_opportunities(self, symbol: str, price_data: pd.DataFrame) -> List[TradeOpportunity]:
        """Find profitable short position opportunities."""
        opportunities = []
        data = price_data.copy()
        data['date'] = data.index

        for entry_idx in range(len(data) - self.min_holding_days):
            entry_row = data.iloc[entry_idx]
            entry_date = entry_row['date']
            entry_price = entry_row['close']

            max_exit_idx = min(entry_idx + self.max_holding_days, len(data) - 1)

            for exit_idx in range(entry_idx + self.min_holding_days, max_exit_idx + 1):
                exit_row = data.iloc[exit_idx]
                exit_date = exit_row['date']
                exit_price = exit_row['close']

                holding_days = (exit_date - entry_date).days

                # Calculate profit for short position (profit when price goes down)
                profit_percent = ((entry_price - exit_price) / entry_price) * 100

                # Analyze the trade path for risk management
                trade_analysis = self._analyze_trade_path(
                    data.iloc[entry_idx:exit_idx + 1],
                    entry_price,
                    'short'
                )

                # Check if trade meets our criteria
                if self._is_valid_short_trade(trade_analysis, profit_percent):
                    opportunity = TradeOpportunity(
                        symbol=symbol,
                        position_type='short',
                        entry_date=entry_date,
                        exit_date=exit_date,
                        entry_price=entry_price,
                        exit_price=exit_price,
                        holding_days=holding_days,
                        profit_percent=profit_percent,
                        max_unrealized_gain_percent=trade_analysis['max_gain_percent'],
                        max_unrealized_loss_percent=trade_analysis['max_loss_percent'],
                        max_drawdown_from_peak=trade_analysis['max_drawdown_from_peak'],
                        peak_profit_date=trade_analysis['peak_date'],
                        peak_profit_percent=trade_analysis['peak_profit_percent'],
                        trade_score=0.0
                    )
                    opportunities.append(opportunity)

        return opportunities

    def _analyze_trade_path(self, trade_data: pd.DataFrame, entry_price: float, position_type: str) -> Dict[str, Any]:
        """Analyze the path of a trade to calculate risk metrics."""
        if len(trade_data) == 0:
            return {
                'max_gain_percent': 0,
                'max_loss_percent': 0,
                'max_drawdown_from_peak': 0,
                'peak_date': None,
                'peak_profit_percent': 0
            }

        gains = []
        losses = []
        profits = []
        dates = []

        max_gain = 0
        max_loss = 0
        peak_profit = 0
        peak_date = None
        max_drawdown_from_peak = 0

        for _, row in trade_data.iterrows():
            current_price = row['close']
            current_date = row['date'] if 'date' in row else row.name

            if position_type == 'long':
                # For long positions, profit when price goes up
                unrealized_profit_percent = ((current_price - entry_price) / entry_price) * 100
            else:
                # For short positions, profit when price goes down
                unrealized_profit_percent = ((entry_price - current_price) / entry_price) * 100

            profits.append(unrealized_profit_percent)
            dates.append(current_date)

            # Track maximum gain and loss
            if unrealized_profit_percent > max_gain:
                max_gain = unrealized_profit_percent

            if unrealized_profit_percent < max_loss:
                max_loss = unrealized_profit_percent

            # Track peak profit and drawdown
            if unrealized_profit_percent > peak_profit:
                peak_profit = unrealized_profit_percent
                peak_date = current_date

            # Calculate drawdown from peak
            if peak_profit > 0:
                drawdown = ((peak_profit - unrealized_profit_percent) / peak_profit) * 100
                if drawdown > max_drawdown_from_peak:
                    max_drawdown_from_peak = drawdown

        return {
            'max_gain_percent': max_gain,
            'max_loss_percent': abs(max_loss),
            'max_drawdown_from_peak': max_drawdown_from_peak,
            'peak_date': peak_date,
            'peak_profit_percent': peak_profit
        }

    def _is_valid_long_trade(self, trade_analysis: Dict[str, Any], final_profit: float) -> bool:
        """Check if a long trade meets our criteria."""
        # Must be profitable
        if final_profit <= 0:
            return False

        # Check maximum drawdown from peak
        if trade_analysis['max_drawdown_from_peak'] > self.max_unrealized_loss_percent:
            return False

        return True

    def _is_valid_short_trade(self, trade_analysis: Dict[str, Any], final_profit: float) -> bool:
        """Check if a short trade meets our criteria."""
        # Must be profitable
        if final_profit <= 0:
            return False

        # Check maximum drawdown from peak
        if trade_analysis['max_drawdown_from_peak'] > self.max_unrealized_loss_percent:
            return False

        return True

    def _calculate_trade_score(self, opportunity: TradeOpportunity) -> float:
        """Calculate a composite score for ranking trades."""
        # Base score is the profit percentage
        score = opportunity.profit_percent

        # Bonus for efficiency (higher profit per day held)
        daily_return = opportunity.profit_percent / opportunity.holding_days
        score += daily_return * 2  # Weight daily returns more heavily

        # Penalty for high drawdown
        drawdown_penalty = opportunity.max_drawdown_from_peak * 0.5
        score -= drawdown_penalty

        # Bonus for consistent gains (lower drawdown relative to profit)
        if opportunity.profit_percent > 0:
            consistency_bonus = (1 - (opportunity.max_drawdown_from_peak / 100)) * opportunity.profit_percent * 0.3
            score += consistency_bonus

        return score

    def get_top_opportunities(self, opportunities: List[TradeOpportunity], top_count: int) -> List[TradeOpportunity]:
        """Get the top N trading opportunities."""
        sorted_opportunities = sorted(opportunities, key=lambda x: x.trade_score, reverse=True)
        return sorted_opportunities[:top_count]