"""
Main AstroEncoder class for astronomical data encoding.
Adapted for financial market correlation analysis.
"""

import swisseph as swe
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import logging

from ..models.data_models import AstronomicalData, PlanetaryPosition, Aspect, HouseData
from ..utils.utils import (
    degrees_to_sign, normalize_angle, calculate_angle_difference,
    is_within_orb, determine_applying_separating, calculate_lunar_phase, classify_lunar_phase
)

logger = logging.getLogger(__name__)


class AstroEncoder:
    """
    Encodes astronomical data for financial market analysis.
    Calculates planetary positions, aspects, and lunar phases.
    """

    # Planet constants from Swiss Ephemeris
    PLANETS = {
        'sun': swe.SUN,
        'moon': swe.MOON,
        'mercury': swe.MERCURY,
        'venus': swe.VENUS,
        'mars': swe.MARS,
        'jupiter': swe.JUPITER,
        'saturn': swe.SATURN,
        'uranus': swe.URANUS,
        'neptune': swe.NEPTUNE,
        'pluto': swe.PLUTO
    }

    # Standard aspects with their angles and default orbs
    ASPECTS = {
        'conjunction': {'angle': 0, 'orb': 8},
        'opposition': {'angle': 180, 'orb': 8},
        'trine': {'angle': 120, 'orb': 8},
        'square': {'angle': 90, 'orb': 8},
        'sextile': {'angle': 60, 'orb': 6},
        'quincunx': {'angle': 150, 'orb': 3},
        'semi_square': {'angle': 45, 'orb': 3},
        'sesqui_square': {'angle': 135, 'orb': 3}
    }

    # Default locations for financial markets
    DEFAULT_LOCATIONS = {
        'nyc': {'lat': 40.7128, 'lon': -74.0060, 'name': 'New York City'},  # NYSE/NYMEX
        'london': {'lat': 51.5074, 'lon': -0.1278, 'name': 'London'},       # ICE Brent
        'chicago': {'lat': 41.8781, 'lon': -87.6298, 'name': 'Chicago'},   # CME
        'universal': {'lat': 0.0, 'lon': 0.0, 'name': 'Universal'}         # No location
    }

    def __init__(self, ephemeris_path: Optional[str] = None):
        """
        Initialize the AstroEncoder.

        Args:
            ephemeris_path: Path to Swiss Ephemeris data files
        """
        if ephemeris_path:
            swe.set_ephe_path(ephemeris_path)

        logger.info("AstroEncoder initialized")

    def encode_date(
        self,
        date: datetime,
        location: str = 'universal',
        include_houses: bool = False
    ) -> AstronomicalData:
        """
        Encode astronomical data for a specific date.

        Args:
            date: Date to encode
            location: Location key for house calculations
            include_houses: Whether to calculate house positions

        Returns:
            Complete astronomical data for the date
        """
        try:
            # Convert to Julian day
            julian_day = swe.julday(date.year, date.month, date.day, date.hour + date.minute/60.0)

            # Calculate planetary positions
            positions = self._calculate_planetary_positions(julian_day)

            # Calculate aspects
            aspects = self._calculate_aspects(positions)

            # Calculate lunar phase
            lunar_phase = self._calculate_lunar_phase(positions)

            # Calculate houses if requested
            houses = None
            if include_houses and location in self.DEFAULT_LOCATIONS:
                houses = self._calculate_houses(julian_day, location, positions)

            # Create astronomical data object
            astro_data = AstronomicalData(
                date=date,
                julian_day=julian_day,
                location=location,
                positions=positions,
                aspects=aspects,
                houses=houses,
                lunar_phase=lunar_phase,
                significant_events=self._identify_significant_events(positions, aspects)
            )

            return astro_data

        except Exception as e:
            logger.error(f"Error encoding date {date}: {e}")
            raise

    def _calculate_planetary_positions(self, julian_day: float) -> Dict[str, PlanetaryPosition]:
        """Calculate positions for all planets."""
        positions = {}

        for planet_name, planet_id in self.PLANETS.items():
            try:
                # Calculate position
                result, ret = swe.calc_ut(julian_day, planet_id)

                if ret >= 0:  # Success
                    longitude, latitude, distance, speed_lon = result[:4]

                    # Convert to zodiac sign
                    sign, degree_in_sign, classification = degrees_to_sign(longitude)

                    positions[planet_name] = PlanetaryPosition(
                        planet=planet_name,
                        longitude=longitude,
                        latitude=latitude,
                        distance=distance,
                        speed=speed_lon,
                        sign=sign,
                        degree_in_sign=degree_in_sign,
                        degree_classification=classification
                    )
                else:
                    logger.warning(f"Failed to calculate position for {planet_name}")

            except Exception as e:
                logger.error(f"Error calculating {planet_name}: {e}")

        return positions

    def _calculate_aspects(self, positions: Dict[str, PlanetaryPosition]) -> List[Aspect]:
        """Calculate aspects between planets."""
        aspects = []
        planet_names = list(positions.keys())

        for i, planet1_name in enumerate(planet_names):
            for planet2_name in planet_names[i+1:]:
                planet1 = positions[planet1_name]
                planet2 = positions[planet2_name]

                # Calculate angle between planets
                angle = calculate_angle_difference(planet1.longitude, planet2.longitude)

                # Check each aspect type
                for aspect_name, aspect_data in self.ASPECTS.items():
                    target_angle = aspect_data['angle']
                    orb_limit = aspect_data['orb']

                    # Calculate orb (difference from exact aspect)
                    orb = min(
                        abs(angle - target_angle),
                        abs(angle - (target_angle + 360)),
                        abs(angle - (target_angle - 360))
                    )

                    if orb <= orb_limit:
                        # Calculate exactness (1.0 = exact, 0.0 = at orb limit)
                        exactness = 1.0 - (orb / orb_limit)

                        # Determine if applying or separating
                        applying_separating = determine_applying_separating(
                            planet1.longitude, planet1.speed,
                            planet2.longitude, planet2.speed,
                            target_angle
                        )

                        aspects.append(Aspect(
                            planet1=planet1_name,
                            planet2=planet2_name,
                            aspect_type=aspect_name,
                            orb=orb,
                            exactness=exactness,
                            angle=angle,
                            applying_separating=applying_separating
                        ))

        return aspects

    def _calculate_lunar_phase(self, positions: Dict[str, PlanetaryPosition]) -> Optional[float]:
        """Calculate lunar phase."""
        if 'sun' in positions and 'moon' in positions:
            sun_lon = positions['sun'].longitude
            moon_lon = positions['moon'].longitude
            return calculate_lunar_phase(sun_lon, moon_lon)
        return None

    def _calculate_houses(
        self,
        julian_day: float,
        location: str,
        positions: Dict[str, PlanetaryPosition]
    ) -> Optional[HouseData]:
        """Calculate house positions."""
        if location not in self.DEFAULT_LOCATIONS:
            return None

        try:
            loc_data = self.DEFAULT_LOCATIONS[location]
            lat, lon = loc_data['lat'], loc_data['lon']

            # Calculate houses using Placidus system
            houses, ascmc = swe.houses(julian_day, lat, lon, b'P')

            # Map planets to houses
            planetary_houses = {}
            for planet_name, position in positions.items():
                house_num = self._find_house_for_planet(position.longitude, houses)
                planetary_houses[planet_name] = house_num

            return HouseData(
                system='placidus',
                location=loc_data['name'],
                latitude=lat,
                longitude=lon,
                house_cusps=list(houses),
                ascendant=ascmc[0],
                midheaven=ascmc[1],
                planetary_houses=planetary_houses
            )

        except Exception as e:
            logger.error(f"Error calculating houses: {e}")
            return None

    def _find_house_for_planet(self, planet_longitude: float, house_cusps: List[float]) -> int:
        """Find which house a planet is in."""
        # Normalize planet longitude
        planet_lon = normalize_angle(planet_longitude)

        for i in range(12):
            cusp_current = normalize_angle(house_cusps[i])
            cusp_next = normalize_angle(house_cusps[(i + 1) % 12])

            # Handle cases where house crosses 0 degrees
            if cusp_current <= cusp_next:
                if cusp_current <= planet_lon < cusp_next:
                    return i + 1
            else:  # Crosses 0 degrees
                if planet_lon >= cusp_current or planet_lon < cusp_next:
                    return i + 1

        return 1  # Default to first house

    def _identify_significant_events(
        self,
        positions: Dict[str, PlanetaryPosition],
        aspects: List[Aspect]
    ) -> List[str]:
        """Identify significant astrological events."""
        events = []

        # Check for strong aspects (exact within 1 degree)
        exact_aspects = [a for a in aspects if a.orb <= 1.0]
        if exact_aspects:
            for aspect in exact_aspects:
                events.append(f"Exact {aspect.aspect_type} between {aspect.planet1} and {aspect.planet2}")

        # Check for planetary sign changes (within 1 degree of sign boundary)
        for planet_name, position in positions.items():
            if position.degree_in_sign <= 1.0:
                events.append(f"{planet_name.title()} entering {position.sign}")
            elif position.degree_in_sign >= 29.0:
                events.append(f"{planet_name.title()} leaving {position.sign}")

        # Check for retrograde motion
        for planet_name, position in positions.items():
            if position.speed < 0:
                events.append(f"{planet_name.title()} retrograde")

        return events

    def encode_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        location: str = 'universal'
    ) -> List[AstronomicalData]:
        """
        Encode astronomical data for a date range.

        Args:
            start_date: Start date
            end_date: End date
            location: Location for calculations

        Returns:
            List of astronomical data for each day in range
        """
        results = []
        current_date = start_date

        while current_date <= end_date:
            try:
                astro_data = self.encode_date(current_date, location)
                results.append(astro_data)
            except Exception as e:
                logger.error(f"Error encoding {current_date}: {e}")

            # Move to next day
            current_date = current_date.replace(
                day=current_date.day + 1
            ) if current_date.day < 28 else current_date.replace(
                month=current_date.month + 1 if current_date.month < 12 else 1,
                year=current_date.year + (1 if current_date.month == 12 else 0),
                day=1
            )

        return results