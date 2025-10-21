"""
Astrological Data Verbalizer
Converts astrological data into natural language descriptions for LLM analysis.
"""

from typing import List, Dict, Optional
from datetime import datetime
import logging

from ..models.data_models import AstronomicalData, PlanetaryPosition, Aspect

logger = logging.getLogger(__name__)


class AstroVerbalizer:
    """
    Converts astrological data into human-readable descriptions
    optimized for LLM-based pattern analysis.
    """

    # Planet characteristics for interpretation
    PLANET_KEYWORDS = {
        'sun': ['leadership', 'vitality', 'authority', 'confidence', 'ego'],
        'moon': ['emotions', 'intuition', 'cycles', 'public mood', 'instincts'],
        'mercury': ['communication', 'intellect', 'commerce', 'quick changes', 'analysis'],
        'venus': ['harmony', 'values', 'attraction', 'cooperation', 'beauty'],
        'mars': ['action', 'aggression', 'energy', 'conflict', 'initiative'],
        'jupiter': ['expansion', 'optimism', 'growth', 'speculation', 'excess'],
        'saturn': ['restriction', 'discipline', 'structure', 'limits', 'patience'],
        'uranus': ['innovation', 'disruption', 'sudden changes', 'revolution', 'technology'],
        'neptune': ['illusion', 'confusion', 'spirituality', 'dissolution', 'dreams'],
        'pluto': ['transformation', 'power', 'depth', 'destruction', 'rebirth']
    }

    # Zodiac sign characteristics
    SIGN_KEYWORDS = {
        'aries': ['initiative', 'pioneering', 'impulsive', 'competitive', 'direct'],
        'taurus': ['stability', 'material', 'persistent', 'conservative', 'practical'],
        'gemini': ['communication', 'versatile', 'curious', 'changeable', 'intellectual'],
        'cancer': ['protective', 'emotional', 'cyclical', 'nurturing', 'cautious'],
        'leo': ['dramatic', 'confident', 'generous', 'proud', 'creative'],
        'virgo': ['analytical', 'practical', 'methodical', 'critical', 'perfectionist'],
        'libra': ['balanced', 'diplomatic', 'harmonious', 'indecisive', 'cooperative'],
        'scorpio': ['intense', 'transformative', 'secretive', 'powerful', 'investigative'],
        'sagittarius': ['expansive', 'optimistic', 'philosophical', 'adventurous', 'excessive'],
        'capricorn': ['structured', 'ambitious', 'practical', 'conservative', 'disciplined'],
        'aquarius': ['innovative', 'humanitarian', 'detached', 'revolutionary', 'unpredictable'],
        'pisces': ['intuitive', 'compassionate', 'dreamy', 'confused', 'spiritual']
    }

    # Aspect interpretations
    ASPECT_KEYWORDS = {
        'conjunction': ['fusion', 'intensification', 'new beginnings', 'unity'],
        'opposition': ['tension', 'polarity', 'awareness', 'culmination'],
        'trine': ['harmony', 'flow', 'ease', 'natural talent'],
        'square': ['challenge', 'friction', 'dynamic tension', 'crisis'],
        'sextile': ['opportunity', 'cooperation', 'gentle stimulation'],
        'quincunx': ['adjustment', 'awkwardness', 'need for adaptation'],
        'semi_square': ['minor friction', 'irritation', 'small challenges'],
        'sesqui_square': ['stress', 'pressure', 'forcing change']
    }

    def verbalize_daily_data(self, astro_data: AstronomicalData) -> str:
        """
        Create a comprehensive daily astrological description.

        Args:
            astro_data: Astronomical data for the day

        Returns:
            Natural language description of the astrological conditions
        """
        descriptions = []

        # Date and basic info
        date_str = astro_data.date.strftime('%Y-%m-%d')
        descriptions.append(f"Astrological conditions for {date_str}:")

        # Planetary positions
        planet_desc = self._describe_planetary_positions(astro_data.positions)
        if planet_desc:
            descriptions.append(f"Planetary positions: {planet_desc}")

        # Major aspects
        aspect_desc = self._describe_major_aspects(astro_data.aspects)
        if aspect_desc:
            descriptions.append(f"Key aspects: {aspect_desc}")

        # Lunar phase
        if astro_data.lunar_phase is not None:
            lunar_desc = self._describe_lunar_phase(astro_data.lunar_phase)
            descriptions.append(f"Lunar phase: {lunar_desc}")

        # Significant events
        if astro_data.significant_events:
            events_desc = "; ".join(astro_data.significant_events)
            descriptions.append(f"Notable events: {events_desc}")

        # Overall interpretation
        interpretation = self._create_market_interpretation(astro_data)
        if interpretation:
            descriptions.append(f"Market implications: {interpretation}")

        return " ".join(descriptions)

    def _describe_planetary_positions(self, positions: Dict[str, PlanetaryPosition]) -> str:
        """Describe planetary positions in signs."""
        descriptions = []

        # Focus on major planets for market analysis
        major_planets = ['sun', 'moon', 'mercury', 'venus', 'mars', 'jupiter', 'saturn']

        for planet in major_planets:
            if planet in positions:
                pos = positions[planet]
                degree_desc = self._degree_description(pos.degree_in_sign)

                # Add speed information for inner planets
                speed_desc = ""
                if planet in ['mercury', 'venus', 'mars'] and pos.speed < 0:
                    speed_desc = " (retrograde)"

                descriptions.append(f"{planet.title()} in {degree_desc} {pos.sign.title()}{speed_desc}")

        return "; ".join(descriptions)

    def _describe_major_aspects(self, aspects: List[Aspect]) -> str:
        """Describe the most significant aspects."""
        # Filter for major aspects and high exactness
        major_aspects = [
            a for a in aspects
            if a.aspect_type in ['conjunction', 'opposition', 'trine', 'square']
            and a.exactness > 0.7
        ]

        # Sort by exactness
        major_aspects.sort(key=lambda x: x.exactness, reverse=True)

        descriptions = []
        for aspect in major_aspects[:5]:  # Top 5 most exact aspects
            exactness_desc = "exact" if aspect.exactness > 0.95 else "close"
            applying_desc = f" ({aspect.applying_separating})" if aspect.applying_separating != 'unknown' else ""

            descriptions.append(
                f"{exactness_desc} {aspect.aspect_type} between {aspect.planet1.title()} and {aspect.planet2.title()}{applying_desc}"
            )

        return "; ".join(descriptions)

    def _describe_lunar_phase(self, lunar_phase: float) -> str:
        """Describe the lunar phase."""
        # Normalize to 0-360 degrees
        phase = lunar_phase % 360

        if 0 <= phase < 45 or 315 <= phase < 360:
            return "New Moon phase (new beginnings, fresh starts)"
        elif 45 <= phase < 135:
            return "Waxing Moon phase (building energy, growth)"
        elif 135 <= phase < 225:
            return "Full Moon phase (culmination, high energy, volatility)"
        elif 225 <= phase < 315:
            return "Waning Moon phase (release, decline, consolidation)"
        else:
            return f"Moon phase at {phase:.1f} degrees"

    def _degree_description(self, degree: float) -> str:
        """Describe the degree within a sign."""
        if degree < 10:
            return "early"
        elif degree < 20:
            return "middle"
        else:
            return "late"

    def _create_market_interpretation(self, astro_data: AstronomicalData) -> str:
        """Create market-focused interpretation."""
        interpretations = []

        # Check for volatile configurations
        if self._has_mars_aspects(astro_data.aspects):
            interpretations.append("heightened volatility and sudden price movements")

        # Check for stability indicators
        if self._has_earth_sign_emphasis(astro_data.positions):
            interpretations.append("stabilizing influences and practical considerations")

        # Check for expansion/contraction cycles
        jupiter_aspects = self._get_planet_aspects(astro_data.aspects, 'jupiter')
        saturn_aspects = self._get_planet_aspects(astro_data.aspects, 'saturn')

        if jupiter_aspects:
            interpretations.append("expansionary pressures and optimistic sentiment")
        if saturn_aspects:
            interpretations.append("restrictive forces and cautious sentiment")

        # Check for communication/news impacts
        mercury_aspects = self._get_planet_aspects(astro_data.aspects, 'mercury')
        if mercury_aspects:
            interpretations.append("significant news or communication impacts")

        return "; ".join(interpretations) if interpretations else "mixed astrological influences"

    def _has_mars_aspects(self, aspects: List[Aspect]) -> bool:
        """Check for Mars aspects indicating volatility."""
        return any(
            'mars' in [a.planet1, a.planet2] and a.aspect_type in ['square', 'opposition', 'conjunction']
            for a in aspects if a.exactness > 0.7
        )

    def _has_earth_sign_emphasis(self, positions: Dict[str, PlanetaryPosition]) -> bool:
        """Check for emphasis on earth signs (stability)."""
        earth_signs = ['taurus', 'virgo', 'capricorn']
        earth_count = sum(1 for pos in positions.values() if pos.sign in earth_signs)
        return earth_count >= 4  # At least 4 planets in earth signs

    def _get_planet_aspects(self, aspects: List[Aspect], planet: str) -> List[Aspect]:
        """Get aspects involving a specific planet."""
        return [a for a in aspects if planet in [a.planet1, a.planet2] and a.exactness > 0.7]

    def verbalize_date_range(self, astro_data_list: List[AstronomicalData]) -> List[str]:
        """
        Verbalize multiple days of astrological data.

        Args:
            astro_data_list: List of astronomical data

        Returns:
            List of daily descriptions
        """
        return [self.verbalize_daily_data(data) for data in astro_data_list]

    def create_trading_window_summary(
        self,
        entry_date: datetime,
        exit_date: datetime,
        astro_data_list: List[AstronomicalData]
    ) -> str:
        """
        Create a summary of astrological conditions during a trading window.

        Args:
            entry_date: Trade entry date
            exit_date: Trade exit date
            astro_data_list: Astrological data for the period

        Returns:
            Summary description for LLM analysis
        """
        if not astro_data_list:
            return "No astrological data available for this trading period."

        summary_parts = []

        # Period overview
        duration = (exit_date - entry_date).days
        summary_parts.append(
            f"Trading period from {entry_date.strftime('%Y-%m-%d')} to {exit_date.strftime('%Y-%m-%d')} "
            f"({duration} days)"
        )

        # Entry conditions
        entry_data = astro_data_list[0]
        entry_desc = self.verbalize_daily_data(entry_data)
        summary_parts.append(f"Entry conditions: {entry_desc}")

        # Exit conditions
        if len(astro_data_list) > 1:
            exit_data = astro_data_list[-1]
            exit_desc = self.verbalize_daily_data(exit_data)
            summary_parts.append(f"Exit conditions: {exit_desc}")

        # Period highlights
        if len(astro_data_list) > 2:
            highlights = self._identify_period_highlights(astro_data_list)
            if highlights:
                summary_parts.append(f"Key period events: {highlights}")

        return " | ".join(summary_parts)

    def _identify_period_highlights(self, astro_data_list: List[AstronomicalData]) -> str:
        """Identify significant events during the trading period."""
        all_events = []
        for data in astro_data_list:
            all_events.extend(data.significant_events)

        # Remove duplicates and limit to most significant
        unique_events = list(set(all_events))
        return "; ".join(unique_events[:3]) if unique_events else ""