"""
Prompt templates specifically for oil futures trading astrological analysis.
"""

from typing import List, Dict, Any
from ..models.trading_data import TradingOpportunity


class OilTradingPrompts:
    """Generate prompts for analyzing oil futures trading with astrological data."""

    @staticmethod
    def generate_comprehensive_oil_analysis_prompt(opportunities: List[TradingOpportunity]) -> str:
        """Generate comprehensive prompt for oil market astrological analysis."""

        # Separate by position type
        long_trades = [opp for opp in opportunities if opp.position_type == 'long']
        short_trades = [opp for opp in opportunities if opp.position_type == 'short']

        # Sort by astrological score
        long_trades.sort(key=lambda x: x.astrological_score, reverse=True)
        short_trades.sort(key=lambda x: x.astrological_score, reverse=True)

        prompt_parts = [
            "# Comprehensive Astrological Analysis for Oil Futures Trading",
            "",
            "You are an expert financial astrologer analyzing real trading data from oil futures markets (WTI and Brent crude oil).",
            "Below are actual profitable trading opportunities with their corresponding astrological conditions at entry and exit.",
            "",
            "## Your Mission:",
            "Identify specific astrological patterns, planetary positions, aspects, and lunar phases that correlate with profitable oil trading.",
            "Focus on actionable insights that traders can use to time their entries and exits in oil futures markets.",
            "",
            f"## Dataset Overview:",
            f"- Total Analyzed Trades: {len(opportunities)}",
            f"- Long Positions: {len(long_trades)}",
            f"- Short Positions: {len(short_trades)}",
            f"- Average Profit: {sum(opp.profit_percent for opp in opportunities) / len(opportunities):.1f}%",
            f"- Average Astrological Score: {sum(opp.astrological_score for opp in opportunities) / len(opportunities):.1f}/100",
            "",
            "## Profitable Long Positions (Oil Price Rising):",
            ""
        ]

        # Add top long trades
        for i, trade in enumerate(long_trades[:15], 1):
            prompt_parts.extend([
                f"### Long Trade {i}: {trade.symbol} - {trade.profit_percent:.1f}% profit in {trade.holding_days} days",
                f"**Astrological Score:** {trade.astrological_score}/100",
                f"**Entry ({trade.entry_date}):** {trade.entry_astro_description}",
                f"**Exit ({trade.exit_date}):** {trade.exit_astro_description}",
                f"**Summary:** {trade.astro_analysis_summary}",
                ""
            ])

        prompt_parts.extend([
            "## Profitable Short Positions (Oil Price Falling):",
            ""
        ])

        # Add top short trades
        for i, trade in enumerate(short_trades[:15], 1):
            prompt_parts.extend([
                f"### Short Trade {i}: {trade.symbol} - {trade.profit_percent:.1f}% profit in {trade.holding_days} days",
                f"**Astrological Score:** {trade.astrological_score}/100",
                f"**Entry ({trade.entry_date}):** {trade.entry_astro_description}",
                f"**Exit ({trade.exit_date}):** {trade.exit_astro_description}",
                f"**Summary:** {trade.astro_analysis_summary}",
                ""
            ])

        prompt_parts.extend([
            "## Specific Analysis Questions:",
            "",
            "### 1. Planetary Positions & Signs",
            "- Which zodiac signs for major planets (Sun, Moon, Mars, Jupiter, Saturn) appear most frequently in profitable oil trades?",
            "- Are there specific planetary sign combinations that favor oil price increases vs. decreases?",
            "- Do retrograde planets correlate with oil market volatility or direction?",
            "",
            "### 2. Lunar Phases & Oil Trading",
            "- Which lunar phases (New Moon, Waxing, Full Moon, Waning) show the highest success rates for oil trades?",
            "- Do long positions perform better during certain lunar phases vs. short positions?",
            "- Is there a correlation between Full Moons and oil price volatility?",
            "",
            "### 3. Planetary Aspects & Market Movements",
            "- Which planetary aspects (conjunctions, trines, squares, oppositions) correlate with profitable oil trades?",
            "- Do Mars aspects indicate increased oil market volatility?",
            "- Are Jupiter aspects associated with oil price expansion/growth?",
            "- Do Saturn aspects correspond to oil price restrictions/contractions?",
            "",
            "### 4. Seasonal & Cyclical Patterns",
            "- Are there specific times of year (Sun signs/seasons) that favor oil trading?",
            "- Do you see patterns related to Mercury retrograde periods?",
            "- Are there longer planetary cycles (Jupiter-Saturn, etc.) that affect oil markets?",
            "",
            "### 5. Entry vs. Exit Timing",
            "- What astrological conditions signal optimal entry points for oil trades?",
            "- What astrological changes indicate it's time to exit profitable positions?",
            "- Are there warning signs of trend reversals in the astrological data?",
            "",
            "### 6. Oil-Specific Astrological Insights",
            "- Given that oil is ruled by Pluto (transformation) and Mars (energy), do Pluto and Mars aspects show special significance?",
            "- Do earth signs (Taurus, Virgo, Capricorn) correlate with oil market stability?",
            "- Are there differences between WTI and Brent crude in astrological timing?",
            "",
            "## Deliverables:",
            "",
            "Please provide:",
            "",
            "### A. Top 10 Astrological Indicators for Oil Trading",
            "Rank the most reliable astrological signals for profitable oil trades.",
            "",
            "### B. Oil Trading Calendar",
            "Identify the best astrological timing for:",
            "- Long positions (expecting oil prices to rise)",
            "- Short positions (expecting oil prices to fall)",
            "- Avoiding trades (high-risk astrological periods)",
            "",
            "### C. Practical Trading Rules",
            "Create specific, actionable rules like:",
            "- 'Enter long oil positions when Mars is in fire signs during Waxing Moon'",
            "- 'Avoid oil trading during Mercury retrograde in earth signs'",
            "- 'Exit profitable positions when lunar phase changes from X to Y'",
            "",
            "### D. Risk Management Guidelines",
            "Astrological warning signs that indicate:",
            "- Increased volatility periods",
            "- Potential trend reversals",
            "- Times to reduce position sizes",
            "",
            "Focus on patterns that appear multiple times in the data and provide specific, actionable guidance for oil futures traders.",
            "Remember: These are real trades with real profits - identify what astrological factors contributed to their success!"
        ])

        return "\n".join(prompt_parts)

    @staticmethod
    def generate_lunar_phase_analysis_prompt(opportunities: List[TradingOpportunity]) -> str:
        """Generate focused prompt for lunar phase analysis."""

        # Group by lunar phases
        lunar_phases = {}
        for opp in opportunities:
            if opp.entry_planetary_data and 'lunar_phase' in opp.entry_planetary_data:
                phase = opp.entry_planetary_data['lunar_phase'].get('name', 'Unknown')
                if phase not in lunar_phases:
                    lunar_phases[phase] = []
                lunar_phases[phase].append(opp)

        prompt_parts = [
            "# Lunar Phase Analysis for Oil Futures Trading",
            "",
            "Analyze how different lunar phases correlate with profitable oil trading opportunities.",
            "Focus specifically on timing entries and exits based on lunar cycles.",
            "",
            "## Lunar Phase Breakdown:",
            ""
        ]

        for phase, trades in lunar_phases.items():
            if trades:
                avg_profit = sum(t.profit_percent for t in trades) / len(trades)
                avg_score = sum(t.astrological_score for t in trades) / len(trades)

                prompt_parts.extend([
                    f"### {phase} ({len(trades)} trades)",
                    f"- Average Profit: {avg_profit:.1f}%",
                    f"- Average Astrological Score: {avg_score:.1f}/100",
                    f"- Long vs Short: {len([t for t in trades if t.position_type == 'long'])} long, {len([t for t in trades if t.position_type == 'short'])} short",
                    ""
                ])

                # Show top 3 trades for this phase
                top_trades = sorted(trades, key=lambda x: x.profit_percent, reverse=True)[:3]
                for i, trade in enumerate(top_trades, 1):
                    prompt_parts.append(
                        f"  **Example {i}:** {trade.symbol} {trade.position_type.upper()} - {trade.profit_percent:.1f}% profit in {trade.holding_days} days"
                    )
                prompt_parts.append("")

        prompt_parts.extend([
            "## Analysis Questions:",
            "",
            "1. **Which lunar phase shows the highest success rate for oil trading?**",
            "2. **Do long positions perform better during waxing phases (growth) vs. short positions during waning phases (decline)?**",
            "3. **Are there optimal holding periods based on lunar cycles?**",
            "4. **Should traders enter positions at specific lunar phases and exit at others?**",
            "5. **Do Full Moons correlate with oil price volatility peaks?**",
            "6. **Are New Moons better for initiating new oil trading strategies?**",
            "",
            "Provide specific trading recommendations based on lunar phases for oil futures traders."
        ])

        return "\n".join(prompt_parts)

    @staticmethod
    def generate_planetary_aspects_prompt(opportunities: List[TradingOpportunity]) -> str:
        """Generate focused prompt for planetary aspects analysis."""

        # Collect all aspects from entry data
        aspects_data = {}
        for opp in opportunities:
            if opp.entry_planetary_data and 'aspects' in opp.entry_planetary_data:
                for aspect in opp.entry_planetary_data['aspects']:
                    aspect_key = f"{aspect.get('planet1', '')}-{aspect.get('planet2', '')} {aspect.get('aspect', '')}"
                    if aspect_key not in aspects_data:
                        aspects_data[aspect_key] = []
                    aspects_data[aspect_key].append(opp)

        prompt_parts = [
            "# Planetary Aspects Analysis for Oil Trading",
            "",
            "Analyze how specific planetary aspects at trade entry correlate with oil trading profitability.",
            "",
            "## Most Frequent Aspects in Profitable Trades:",
            ""
        ]

        # Sort aspects by frequency and profitability
        sorted_aspects = sorted(
            [(aspect, trades) for aspect, trades in aspects_data.items() if len(trades) >= 2],
            key=lambda x: (len(x[1]), sum(t.profit_percent for t in x[1]) / len(x[1])),
            reverse=True
        )

        for aspect, trades in sorted_aspects[:10]:
            avg_profit = sum(t.profit_percent for t in trades) / len(trades)
            avg_score = sum(t.astrological_score for t in trades) / len(trades)

            prompt_parts.extend([
                f"### {aspect} ({len(trades)} occurrences)",
                f"- Average Profit: {avg_profit:.1f}%",
                f"- Average Astrological Score: {avg_score:.1f}/100",
                f"- Position Types: {len([t for t in trades if t.position_type == 'long'])} long, {len([t for t in trades if t.position_type == 'short'])} short",
                ""
            ])

        prompt_parts.extend([
            "## Specific Questions:",
            "",
            "1. **Which planetary aspects are most reliable for oil trading signals?**",
            "2. **Do Mars aspects correlate with oil price volatility?**",
            "3. **Are Jupiter aspects associated with oil price expansion?**",
            "4. **Do Saturn aspects indicate oil market restrictions?**",
            "5. **Which aspects favor long positions vs. short positions?**",
            "6. **Are there aspect patterns that signal optimal exit timing?**",
            "",
            "Provide specific guidance on using planetary aspects for oil futures trading decisions."
        ])

        return "\n".join(prompt_parts)