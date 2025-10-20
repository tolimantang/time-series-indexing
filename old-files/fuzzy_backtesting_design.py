#!/usr/bin/env python3
"""
Fuzzy Backtesting System Design
Extends the current astro-financial system with trading backtests
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from dataclasses import dataclass

class FuzzyBacktestRequest(BaseModel):
    """Request model for fuzzy backtesting."""

    # Signal definition (uses existing semantic search)
    signal_query: str = "fed rate hike"  # Natural language signal

    # Trading parameters
    asset: str = "EURUSD"
    position: str = "long"  # "long" or "short"

    # Timing (fuzzy specifications)
    entry_timing: str = "1 day before"  # "1 day before", "same day", "1 day after"
    exit_timing: str = "3 days after"   # "1 day after", "1 week after", "until next signal"

    # Risk management
    position_size: float = 1.0          # Position size (% of portfolio)
    stop_loss: Optional[float] = None   # Stop loss percentage
    take_profit: Optional[float] = None # Take profit percentage

    # Analysis period
    start_date: str = "2020-01-01"
    end_date: str = "2024-12-31"

    # Advanced options
    min_signal_confidence: float = 0.7  # Minimum similarity score
    exclude_overlapping: bool = True    # Avoid overlapping positions


@dataclass
class Trade:
    """Represents a single trade in the backtest."""
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    position: str  # "long" or "short"
    pnl: float
    pnl_pct: float
    signal_confidence: float
    signal_description: str


@dataclass
class BacktestResults:
    """Complete backtest results."""
    trades: List[Trade]
    total_return: float
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    num_trades: int
    avg_trade_duration: float
    summary_stats: Dict[str, Any]


class FuzzyBacktester:
    """
    Fuzzy backtesting system that extends the existing architecture.
    Uses semantic search to find trading signals, then simulates trades.
    """

    def __init__(self, astro_pipeline, market_data_source):
        self.astro_pipeline = astro_pipeline
        self.market_data = market_data_source

    def run_backtest(self, request: FuzzyBacktestRequest) -> BacktestResults:
        """Run a complete fuzzy backtest."""

        # Step 1: Find signal dates using existing semantic search
        signal_dates = self._find_signal_dates(request)

        # Step 2: Generate trades based on timing rules
        trades = self._generate_trades(signal_dates, request)

        # Step 3: Calculate performance metrics
        results = self._calculate_performance(trades)

        return results

    def _find_signal_dates(self, request: FuzzyBacktestRequest) -> List[Dict]:
        """Find dates matching the signal using semantic search."""

        # Use existing semantic search system!
        search_results = self.astro_pipeline.search_similar_patterns(
            query=request.signal_query,
            n_results=1000  # Get all matches
        )

        # Filter by confidence and date range
        filtered_signals = []
        for result in search_results['results']:
            if (result['similarity_score'] >= request.min_signal_confidence and
                request.start_date <= result['date'] <= request.end_date):
                filtered_signals.append(result)

        return filtered_signals

    def _generate_trades(self, signal_dates: List[Dict],
                        request: FuzzyBacktestRequest) -> List[Trade]:
        """Generate trades based on signal dates and timing rules."""

        trades = []

        for signal in signal_dates:
            signal_date = datetime.strptime(signal['date'], '%Y-%m-%d')

            # Calculate entry and exit dates based on fuzzy timing
            entry_date = self._parse_fuzzy_timing(signal_date, request.entry_timing)
            exit_date = self._parse_fuzzy_timing(signal_date, request.exit_timing)

            # Get market prices for those dates
            entry_price = self._get_market_price(request.asset, entry_date)
            exit_price = self._get_market_price(request.asset, exit_date)

            if entry_price and exit_price:
                # Calculate P&L
                if request.position == "long":
                    pnl_pct = (exit_price - entry_price) / entry_price
                else:  # short
                    pnl_pct = (entry_price - exit_price) / entry_price

                pnl = pnl_pct * request.position_size

                trade = Trade(
                    entry_date=entry_date.strftime('%Y-%m-%d'),
                    exit_date=exit_date.strftime('%Y-%m-%d'),
                    entry_price=entry_price,
                    exit_price=exit_price,
                    position=request.position,
                    pnl=pnl,
                    pnl_pct=pnl_pct,
                    signal_confidence=signal['similarity_score'],
                    signal_description=signal['description'][:100]
                )
                trades.append(trade)

        return trades

    def _parse_fuzzy_timing(self, signal_date: datetime, timing_str: str) -> datetime:
        """Parse fuzzy timing strings like '1 day before' into actual dates."""

        timing_map = {
            "same day": timedelta(days=0),
            "1 day before": timedelta(days=-1),
            "2 days before": timedelta(days=-2),
            "1 day after": timedelta(days=1),
            "3 days after": timedelta(days=3),
            "1 week after": timedelta(days=7),
            "2 weeks after": timedelta(days=14),
        }

        return signal_date + timing_map.get(timing_str, timedelta(days=0))

    def _get_market_price(self, asset: str, date: datetime) -> Optional[float]:
        """Get market price for an asset on a specific date."""
        # In production, this would query your market data source
        # For now, simulate prices
        import random
        random.seed(hash(f"{asset}{date}"))  # Deterministic "prices"

        base_prices = {"EURUSD": 1.10, "SPY": 400, "VIX": 20}
        base = base_prices.get(asset, 100)
        return base * (1 + random.gauss(0, 0.02))  # +/- 2% random walk

    def _calculate_performance(self, trades: List[Trade]) -> BacktestResults:
        """Calculate backtest performance metrics."""

        if not trades:
            return BacktestResults([], 0, 0, 0, 0, 0, 0, {})

        total_return = sum(trade.pnl for trade in trades)
        winning_trades = [t for t in trades if t.pnl > 0]
        win_rate = len(winning_trades) / len(trades)

        # Calculate other metrics (simplified)
        returns = [trade.pnl for trade in trades]
        avg_return = sum(returns) / len(returns)
        return_std = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
        sharpe_ratio = avg_return / return_std if return_std > 0 else 0

        # Calculate max drawdown (simplified)
        cumulative_returns = []
        cumsum = 0
        for trade in trades:
            cumsum += trade.pnl
            cumulative_returns.append(cumsum)

        peak = cumulative_returns[0]
        max_drawdown = 0
        for ret in cumulative_returns:
            if ret > peak:
                peak = ret
            drawdown = (peak - ret) / peak if peak > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)

        avg_duration = sum(
            (datetime.strptime(t.exit_date, '%Y-%m-%d') -
             datetime.strptime(t.entry_date, '%Y-%m-%d')).days
            for t in trades
        ) / len(trades)

        return BacktestResults(
            trades=trades,
            total_return=total_return,
            win_rate=win_rate,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            num_trades=len(trades),
            avg_trade_duration=avg_duration,
            summary_stats={
                'best_trade': max(trades, key=lambda t: t.pnl).pnl,
                'worst_trade': min(trades, key=lambda t: t.pnl).pnl,
                'avg_trade_return': avg_return,
                'total_return_pct': total_return * 100
            }
        )


# Example usage in your API:
def add_backtesting_endpoint():
    """This would be added to your existing API server."""

    @app.post("/backtest/fuzzy", response_model=dict)
    async def fuzzy_backtest(request: FuzzyBacktestRequest):
        """Run a fuzzy backtest based on natural language signals."""

        backtester = FuzzyBacktester(api_instance.astro_pipeline, market_data_source)
        results = backtester.run_backtest(request)

        return {
            "query_type": "fuzzy_backtest",
            "signal": request.signal_query,
            "asset": request.asset,
            "total_return": f"{results.total_return:.2%}",
            "win_rate": f"{results.win_rate:.1%}",
            "num_trades": results.num_trades,
            "sharpe_ratio": round(results.sharpe_ratio, 2),
            "max_drawdown": f"{results.max_drawdown:.1%}",
            "trades": [
                {
                    "entry_date": trade.entry_date,
                    "exit_date": trade.exit_date,
                    "pnl_pct": f"{trade.pnl_pct:.2%}",
                    "signal_confidence": round(trade.signal_confidence, 3)
                }
                for trade in results.trades[:10]  # Show first 10 trades
            ],
            "summary": results.summary_stats
        }


if __name__ == "__main__":
    print("Fuzzy Backtesting System Design")
    print("=" * 40)
    print("✅ Leverages existing semantic search")
    print("✅ Natural language trading signals")
    print("✅ Fuzzy timing specifications")
    print("✅ Complete performance analytics")
    print("✅ Easy API integration")
    print()
    print("Example query:")
    print('curl -X POST http://localhost:8000/backtest/fuzzy \\')
    print('  -H "Content-Type: application/json" \\')
    print("  -d '{")
    print('    "signal_query": "fed rate hike",')
    print('    "asset": "EURUSD",')
    print('    "position": "long",')
    print('    "entry_timing": "1 day before",')
    print('    "exit_timing": "3 days after"')
    print("  }'")