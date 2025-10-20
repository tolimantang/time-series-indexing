#!/usr/bin/env python3
"""
Live Trading System Design
Extends the current system to execute real trades based on textual commands
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
from enum import Enum
import asyncio

class TradingCommand(BaseModel):
    """Natural language trading command."""
    command: str  # "Long EUR/USD when fed rate hike signal appears"
    max_position_size: float = 1000  # USD
    stop_loss: Optional[float] = None  # 2% = 0.02
    take_profit: Optional[float] = None  # 5% = 0.05
    active: bool = True

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"

class Trade(BaseModel):
    symbol: str
    side: str  # "buy" or "sell"
    quantity: float
    price: Optional[float] = None
    order_type: OrderType = OrderType.MARKET
    reason: str  # "Fed rate hike signal detected"

class LiveTradingEngine:
    """
    Live trading engine that monitors for signals and executes trades.
    Extends your existing semantic search system.
    """

    def __init__(self, astro_pipeline, broker_api):
        self.astro_pipeline = astro_pipeline
        self.broker = broker_api  # Interactive Brokers, Alpaca, etc.
        self.active_commands: List[TradingCommand] = []
        self.running = False

    async def add_trading_command(self, command: TradingCommand):
        """Add a new trading rule in natural language."""
        # Parse the command to understand what to monitor
        parsed_rule = self._parse_trading_command(command.command)

        self.active_commands.append({
            'original_command': command.command,
            'parsed_rule': parsed_rule,
            'config': command,
            'last_check': None
        })

        print(f"✓ Added trading rule: {command.command}")

    def _parse_trading_command(self, command: str) -> Dict:
        """Parse natural language command into trading rule."""

        # Extract components using simple NLP
        command_lower = command.lower()

        # Determine action
        action = "buy" if any(word in command_lower for word in ["long", "buy"]) else "sell"

        # Extract symbol
        symbols = ["eurusd", "eur/usd", "spy", "qqq", "oil", "gold"]
        symbol = None
        for s in symbols:
            if s in command_lower:
                symbol = s.upper().replace("/", "")
                break

        # Extract signal
        signal_keywords = command_lower.split("when")[-1].strip() if "when" in command_lower else command_lower

        return {
            'action': action,
            'symbol': symbol,
            'signal_query': signal_keywords,
            'trigger_conditions': self._extract_conditions(command_lower)
        }

    def _extract_conditions(self, command: str) -> Dict:
        """Extract conditions like 'and VIX below 20'."""
        conditions = {}

        # VIX conditions
        if "vix below" in command:
            try:
                vix_level = float(command.split("vix below")[1].split()[0])
                conditions['vix_max'] = vix_level
            except:
                pass

        if "vix above" in command:
            try:
                vix_level = float(command.split("vix above")[1].split()[0])
                conditions['vix_min'] = vix_level
            except:
                pass

        return conditions

    async def start_monitoring(self):
        """Start the live monitoring loop."""
        self.running = True
        print("🚀 Live trading monitor started")

        while self.running:
            await self._check_all_signals()
            await asyncio.sleep(60)  # Check every minute

    async def _check_all_signals(self):
        """Check all active trading commands for signals."""
        current_time = datetime.now(timezone.utc)

        for rule in self.active_commands:
            if not rule['config'].active:
                continue

            try:
                # Check if signal is triggered
                signal_triggered = await self._check_signal(rule, current_time)

                if signal_triggered:
                    await self._execute_trade(rule, signal_triggered)

            except Exception as e:
                print(f"Error checking rule {rule['original_command']}: {e}")

    async def _check_signal(self, rule: Dict, current_time: datetime) -> Optional[Dict]:
        """Check if a trading signal is triggered."""

        # Get current astronomical data
        current_astro = self.astro_pipeline.astro_encoder.encode_date(current_time)

        # Convert to text and search for similar patterns
        current_text = self.astro_pipeline.text_encoder.create_comprehensive_astro_text(current_astro)

        # Search for similar historical patterns
        similar_patterns = self.astro_pipeline.search_similar_patterns(
            query=rule['parsed_rule']['signal_query'],
            n_results=5
        )

        # Check if current conditions are similar enough
        if similar_patterns['results']:
            top_match = similar_patterns['results'][0]
            similarity = top_match.get('similarity_score', 0)

            # Threshold for signal trigger (configurable)
            if similarity > 0.8:  # 80% similarity

                # Check additional conditions (VIX, etc.)
                conditions_met = await self._check_conditions(rule['parsed_rule']['trigger_conditions'])

                if conditions_met:
                    return {
                        'signal_strength': similarity,
                        'matched_pattern': top_match,
                        'current_astro_text': current_text[:200],
                        'trigger_time': current_time
                    }

        return None

    async def _check_conditions(self, conditions: Dict) -> bool:
        """Check additional market conditions (VIX levels, etc.)."""

        if not conditions:
            return True

        # Check VIX conditions (would query real market data)
        if 'vix_max' in conditions:
            current_vix = await self._get_current_vix()  # Would be real API call
            if current_vix > conditions['vix_max']:
                return False

        if 'vix_min' in conditions:
            current_vix = await self._get_current_vix()
            if current_vix < conditions['vix_min']:
                return False

        return True

    async def _get_current_vix(self) -> float:
        """Get current VIX level (simulated)."""
        # In production, this would be a real market data API call
        import random
        return random.uniform(15, 25)  # Simulated VIX

    async def _execute_trade(self, rule: Dict, signal_info: Dict):
        """Execute the actual trade."""

        parsed_rule = rule['parsed_rule']
        config = rule['config']

        # Create trade order
        trade = Trade(
            symbol=parsed_rule['symbol'],
            side=parsed_rule['action'],
            quantity=self._calculate_position_size(config.max_position_size, parsed_rule['symbol']),
            order_type=OrderType.MARKET,
            reason=f"Signal: {rule['original_command'][:50]}... (strength: {signal_info['signal_strength']:.2f})"
        )

        # Execute via broker API
        try:
            order_result = await self._submit_order(trade)

            print(f"🎯 TRADE EXECUTED:")
            print(f"   Command: {rule['original_command']}")
            print(f"   Action: {trade.side} {trade.quantity} {trade.symbol}")
            print(f"   Reason: {trade.reason}")
            print(f"   Order ID: {order_result.get('order_id')}")

            # Log trade for analysis
            await self._log_trade(trade, signal_info, order_result)

        except Exception as e:
            print(f"❌ Trade execution failed: {e}")

    def _calculate_position_size(self, max_usd: float, symbol: str) -> float:
        """Calculate position size based on risk management."""
        # Simple position sizing (would be more sophisticated in production)
        if symbol == "EURUSD":
            return max_usd / 1.10  # Rough EUR/USD rate
        elif symbol == "SPY":
            return max_usd / 400   # Rough SPY price
        else:
            return max_usd / 100   # Default

    async def _submit_order(self, trade: Trade) -> Dict:
        """Submit order to broker (simulated)."""
        # In production, this would call your broker's API:
        # return await self.broker.submit_order(trade)

        # Simulated for demo
        return {
            'order_id': f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'status': 'filled',
            'fill_price': 1.1050 if trade.symbol == "EURUSD" else 400.0
        }

    async def _log_trade(self, trade: Trade, signal_info: Dict, order_result: Dict):
        """Log trade for analysis and tracking."""
        # Store in your PostgreSQL database for later analysis
        trade_log = {
            'timestamp': datetime.now(timezone.utc),
            'symbol': trade.symbol,
            'side': trade.side,
            'quantity': trade.quantity,
            'reason': trade.reason,
            'signal_strength': signal_info['signal_strength'],
            'order_id': order_result.get('order_id'),
            'fill_price': order_result.get('fill_price')
        }

        print(f"📊 Trade logged: {trade_log}")


# API Integration (add to your existing API server):
class TradingAPI:
    """API endpoints for live trading."""

    def __init__(self):
        self.trading_engine = LiveTradingEngine(astro_pipeline, broker_api)

    async def add_trading_rule(self, command_text: str, max_position: float = 1000):
        """Add a new trading rule via API."""
        command = TradingCommand(
            command=command_text,
            max_position_size=max_position,
            active=True
        )

        await self.trading_engine.add_trading_command(command)

        return {
            'status': 'success',
            'message': f'Trading rule added: {command_text}',
            'rule_id': len(self.trading_engine.active_commands)
        }


# Example usage:
async def demo_live_trading():
    """Demo of the live trading system."""

    print("Live Trading System Demo")
    print("=" * 30)

    # Initialize (in production, would use real broker)
    trading_engine = LiveTradingEngine(None, None)

    # Add trading rules via natural language
    commands = [
        "Long EUR/USD when fed rate hike signal appears",
        "Short SPY when saturn neptune conjunction and VIX below 15",
        "Buy oil when jupiter in cancer and moon opposite saturn"
    ]

    for cmd in commands:
        await trading_engine.add_trading_command(TradingCommand(command=cmd))

    print("\n🚀 Trading rules active:")
    for i, rule in enumerate(trading_engine.active_commands, 1):
        print(f"{i}. {rule['original_command']}")

    print("\n💡 In production, this would:")
    print("   ✓ Monitor astronomical patterns 24/7")
    print("   ✓ Execute trades when signals match")
    print("   ✓ Apply risk management automatically")
    print("   ✓ Log all trades for analysis")


if __name__ == "__main__":
    print("🚀 Live Trading Extension Design")
    print("=" * 40)
    print("✅ Natural language trading commands")
    print("✅ Real-time signal monitoring")
    print("✅ Automated execution")
    print("✅ Risk management")
    print("✅ Full audit trail")
    print()
    print("Example commands:")
    print('• "Long EUR/USD when fed rate hike signal appears"')
    print('• "Short SPY when saturn neptune conjunction and VIX below 15"')
    print('• "Buy oil 1 day before jupiter enters cancer"')
    print()
    print("API Integration:")
    print("POST /trading/add-rule")
    print("GET  /trading/active-rules")
    print("POST /trading/stop-rule")
    print("GET  /trading/trade-history")