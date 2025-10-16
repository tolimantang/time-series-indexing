"""
Text generation for market signals.
Converts quantitative market data into natural language descriptions for ChromaDB embeddings.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MarketTextGenerator:
    """Generates natural language descriptions from market signals."""

    def __init__(self):
        self.templates = self._load_templates()

    def _load_templates(self) -> Dict[str, Any]:
        """Load text generation templates."""
        return {
            'price_action': {
                'strong_gain': "Strong upward movement with {return_pct:.1f}% gain",
                'moderate_gain': "Moderate upward movement with {return_pct:.1f}% gain",
                'weak_gain': "Slight upward movement with {return_pct:.1f}% gain",
                'flat': "Sideways price action with minimal {return_pct:.1f}% change",
                'weak_loss': "Slight downward movement with {return_pct:.1f}% decline",
                'moderate_loss': "Moderate downward movement with {return_pct:.1f}% decline",
                'strong_loss': "Strong downward movement with {return_pct:.1f}% decline"
            },
            'volatility': {
                'very_low': "extremely low volatility environment",
                'low': "low volatility conditions",
                'normal': "normal volatility levels",
                'elevated': "elevated volatility conditions",
                'high': "high volatility environment",
                'extreme': "extreme volatility conditions"
            },
            'trend': {
                'strong_uptrend': "strong bullish trend with price well above moving averages",
                'uptrend': "bullish trend with price above key moving averages",
                'sideways': "sideways trend with mixed signals from moving averages",
                'downtrend': "bearish trend with price below key moving averages",
                'strong_downtrend': "strong bearish trend with price well below moving averages"
            },
            'momentum': {
                'oversold': "oversold conditions with RSI below 30",
                'sold': "bearish momentum with RSI below 40",
                'neutral': "neutral momentum with RSI around 50",
                'bought': "bullish momentum with RSI above 60",
                'overbought': "overbought conditions with RSI above 70"
            },
            'volume': {
                'very_high': "very high trading volume",
                'high': "above-average trading volume",
                'normal': "normal trading volume",
                'low': "below-average trading volume",
                'very_low': "very low trading volume"
            }
        }

    def _classify_price_action(self, return_pct: float) -> str:
        """Classify price action based on return percentage."""
        if return_pct >= 3:
            return 'strong_gain'
        elif return_pct >= 1:
            return 'moderate_gain'
        elif return_pct >= 0.25:
            return 'weak_gain'
        elif return_pct >= -0.25:
            return 'flat'
        elif return_pct >= -1:
            return 'weak_loss'
        elif return_pct >= -3:
            return 'moderate_loss'
        else:
            return 'strong_loss'

    def _classify_volatility(self, vol_20d: float) -> str:
        """Classify volatility level."""
        if vol_20d < 10:
            return 'very_low'
        elif vol_20d < 15:
            return 'low'
        elif vol_20d < 25:
            return 'normal'
        elif vol_20d < 35:
            return 'elevated'
        elif vol_20d < 50:
            return 'high'
        else:
            return 'extreme'

    def _classify_momentum(self, rsi: float) -> str:
        """Classify momentum based on RSI."""
        if rsi < 30:
            return 'oversold'
        elif rsi < 40:
            return 'sold'
        elif rsi < 60:
            return 'neutral'
        elif rsi < 70:
            return 'bought'
        else:
            return 'overbought'

    def _classify_volume(self, volume_ratio: float) -> str:
        """Classify volume relative to average."""
        if volume_ratio >= 2.0:
            return 'very_high'
        elif volume_ratio >= 1.3:
            return 'high'
        elif volume_ratio >= 0.7:
            return 'normal'
        elif volume_ratio >= 0.5:
            return 'low'
        else:
            return 'very_low'

    def generate_market_narrative(self, symbol: str, signals: Dict[str, Any]) -> str:
        """Generate comprehensive market narrative from signals."""
        try:
            date_str = signals['date']
            price_data = signals['price']
            vol_data = signals['volatility']
            tech_data = signals['technical']
            regime_data = signals['regime']

            # Extract key metrics
            daily_return = price_data['daily_return']
            return_5d = price_data.get('return_5d', 0)
            return_20d = price_data.get('return_20d', 0)

            vol_20d = vol_data['vol_20d']
            volume_ratio = vol_data['volume_ratio']

            rsi = tech_data['rsi']
            price_vs_ma20 = tech_data['price_vs_ma20']
            bb_position = tech_data.get('bb_position', 0.5)

            # Classify market conditions
            price_action = self._classify_price_action(daily_return)
            vol_level = self._classify_volatility(vol_20d)
            momentum_state = self._classify_momentum(rsi)
            volume_state = self._classify_volume(volume_ratio)

            # Build narrative components
            narrative_parts = []

            # Date and symbol
            narrative_parts.append(f"On {date_str}, {symbol}")

            # Price action
            price_template = self.templates['price_action'][price_action]
            narrative_parts.append(price_template.format(return_pct=daily_return))

            # Add context about recent performance
            if abs(return_5d) > 2:
                narrative_parts.append(f"over the past 5 days with {return_5d:.1f}% total return")

            if abs(return_20d) > 5:
                narrative_parts.append(f"and {return_20d:.1f}% over the past 20 days")

            # Volatility context
            vol_desc = self.templates['volatility'][vol_level]
            narrative_parts.append(f"The stock traded in {vol_desc}")

            # Volume context
            volume_desc = self.templates['volume'][volume_state]
            if volume_ratio != 1.0:
                narrative_parts.append(f"with {volume_desc} ({volume_ratio:.1f}x average)")

            # Technical indicators
            momentum_desc = self.templates['momentum'][momentum_state]
            narrative_parts.append(f"Technical indicators show {momentum_desc}")

            # Price relative to moving averages
            if price_vs_ma20 > 5:
                narrative_parts.append(f"trading {price_vs_ma20:.1f}% above its 20-day moving average")
            elif price_vs_ma20 < -5:
                narrative_parts.append(f"trading {abs(price_vs_ma20):.1f}% below its 20-day moving average")

            # Bollinger Bands position
            if bb_position > 0.8:
                narrative_parts.append("near the upper Bollinger Band")
            elif bb_position < 0.2:
                narrative_parts.append("near the lower Bollinger Band")

            # Market regime information
            if 'vol_regime' in regime_data:
                vol_regime = regime_data['vol_regime']
                if vol_regime == 'high_vol':
                    narrative_parts.append("during a high volatility market regime")
                elif vol_regime == 'low_vol':
                    narrative_parts.append("during a low volatility market regime")

            if 'trend_regime' in regime_data:
                trend_regime = regime_data['trend_regime']
                if trend_regime == 'strong_uptrend':
                    narrative_parts.append("within a strong uptrend environment")
                elif trend_regime == 'strong_downtrend':
                    narrative_parts.append("within a strong downtrend environment")

            # Join narrative parts
            narrative = ". ".join(narrative_parts) + "."

            # Clean up formatting
            narrative = narrative.replace(". .", ".").replace("  ", " ")

            return narrative

        except Exception as e:
            logger.error(f"Error generating narrative for {symbol}: {e}")
            return f"Market data for {symbol} on {signals.get('date', 'unknown date')}: price {signals.get('price', {}).get('close', 'N/A')}"

    def generate_correlation_narrative(self, correlations: Dict[str, Any],
                                     primary_symbol: str,
                                     date: str) -> List[str]:
        """Generate narratives about asset correlations."""
        narratives = []

        for window, corr_data in correlations.items():
            for pair, correlation in corr_data.items():
                if primary_symbol in pair:
                    symbols = pair.split('_')
                    other_symbol = symbols[1] if symbols[0] == primary_symbol else symbols[0]

                    # Classify correlation strength
                    if abs(correlation) > 0.7:
                        strength = "strong"
                    elif abs(correlation) > 0.4:
                        strength = "moderate"
                    elif abs(correlation) > 0.2:
                        strength = "weak"
                    else:
                        strength = "minimal"

                    direction = "positive" if correlation > 0 else "negative"

                    narrative = f"Over the {window} period ending {date}, {primary_symbol} shows {strength} {direction} correlation ({correlation:.3f}) with {other_symbol}"
                    narratives.append(narrative)

        return narratives

    def generate_breadth_narrative(self, breadth_data: pd.DataFrame, date: str) -> str:
        """Generate market breadth narrative."""
        if breadth_data.empty or date not in breadth_data.index:
            return f"No market breadth data available for {date}"

        try:
            row = breadth_data.loc[date]

            breadth_ratio = row.get('breadth_ratio', 0.5)
            avg_return = row.get('avg_return', 0) * 100
            return_dispersion = row.get('return_dispersion', 0) * 100

            # Classify market breadth
            if breadth_ratio > 0.7:
                breadth_desc = "broad-based rally with most assets advancing"
            elif breadth_ratio > 0.6:
                breadth_desc = "positive market breadth with majority of assets up"
            elif breadth_ratio > 0.4:
                breadth_desc = "mixed market performance"
            elif breadth_ratio > 0.3:
                breadth_desc = "negative market breadth with majority of assets down"
            else:
                breadth_desc = "broad-based decline with most assets falling"

            # Dispersion context
            if return_dispersion > 3:
                dispersion_desc = "high dispersion indicating divergent performance"
            elif return_dispersion > 1.5:
                dispersion_desc = "moderate dispersion in returns"
            else:
                dispersion_desc = "low dispersion with similar performance across assets"

            narrative = f"Market breadth on {date} shows {breadth_desc}. Average return of {avg_return:.1f}% with {dispersion_desc} ({return_dispersion:.1f}% standard deviation)"

            return narrative

        except Exception as e:
            logger.error(f"Error generating breadth narrative: {e}")
            return f"Market breadth data available for {date} but unable to generate narrative"