"""
Main AstroEncoder class for astronomical data encoding.
"""

import swisseph as swe
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .data_models import AstronomicalData, PlanetaryPosition, Aspect, HouseData
from .utils import (
    degrees_to_sign, normalize_angle, calculate_angle_difference,
    is_within_orb, determine_applying_separating, calculate_lunar_phase, classify_lunar_phase
)


class AstroEncoder:
    """
    Encodes astronomical data for a given date, time, and location.
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

    # Default locations for house calculations
    DEFAULT_LOCATIONS = {
        'nyc': {'lat': 40.7128, 'lon': -74.0060, 'name': 'New York City'},
        'london': {'lat': 51.5074, 'lon': -0.1278, 'name': 'London'},
        'tokyo': {'lat': 35.6762, 'lon': 139.6503, 'name': 'Tokyo'},
        'utc': {'lat': 0.0, 'lon': 0.0, 'name': 'UTC (Greenwich)'}
    }

    def __init__(self, ephemeris_path: Optional[str] = None):
        """
        Initialize AstroEncoder.

        Args:
            ephemeris_path: Path to Swiss Ephemeris data files (optional)
        """
        if ephemeris_path:
            swe.set_ephe_path(ephemeris_path)

        # Set up Swiss Ephemeris (will use built-in data if no path specified)
        swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY)  # Default sidereal mode

    def encode_date(self,
                   date: datetime,
                   location: str = 'utc',
                   custom_location: Optional[Dict[str, float]] = None,
                   include_houses: bool = True,
                   custom_orbs: Optional[Dict[str, float]] = None) -> AstronomicalData:
        """
        Encode astronomical data for a specific date and location.

        Args:
            date: Date and time to encode (UTC)
            location: Location key from DEFAULT_LOCATIONS or 'custom'
            custom_location: Custom location dict with 'lat', 'lon', 'name' keys
            include_houses: Whether to calculate house positions
            custom_orbs: Custom orb values for aspects

        Returns:
            AstronomicalData object with complete astronomical information
        """
        # Ensure date is in UTC
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        elif date.tzinfo != timezone.utc:
            date = date.astimezone(timezone.utc)

        # Convert to Julian Day
        julian_day = swe.julday(date.year, date.month, date.day,
                               date.hour + date.minute/60.0 + date.second/3600.0)

        # Get location data
        if custom_location:
            location_data = custom_location
            location_name = custom_location.get('name', 'custom')
        else:
            location_data = self.DEFAULT_LOCATIONS.get(location, self.DEFAULT_LOCATIONS['utc'])
            location_name = location_data['name']

        # Calculate planetary positions
        positions = self._calculate_planetary_positions(julian_day)

        # Calculate aspects
        aspects = self._calculate_aspects(positions, custom_orbs)

        # Calculate houses if requested
        houses = None
        if include_houses:
            houses = self._calculate_houses(julian_day, location_data)
            # Add house information to planetary positions
            for planet_name, position in positions.items():
                position.house = houses.planetary_houses.get(planet_name)

        # Calculate lunar phase
        lunar_phase = calculate_lunar_phase(
            positions['sun'].longitude,
            positions['moon'].longitude
        )

        # Detect significant events
        significant_events = self._detect_significant_events(positions, aspects)

        return AstronomicalData(
            date=date,
            julian_day=julian_day,
            location=str(location_name),
            positions=positions,
            aspects=aspects,
            houses=houses,
            lunar_phase=lunar_phase,
            significant_events=significant_events
        )

    def _calculate_planetary_positions(self, julian_day: float) -> Dict[str, PlanetaryPosition]:
        """Calculate positions for all planets."""
        positions = {}

        for planet_name, planet_id in self.PLANETS.items():
            try:
                # Calculate planet position
                planet_data, ret_flag = swe.calc_ut(julian_day, planet_id, swe.FLG_SWIEPH)

                longitude = planet_data[0]
                latitude = planet_data[1]
                distance = planet_data[2]
                speed = planet_data[3]

                # Convert to zodiac sign
                sign, degree_in_sign, classification = degrees_to_sign(longitude)

                positions[planet_name] = PlanetaryPosition(
                    planet=planet_name,
                    longitude=longitude,
                    latitude=latitude,
                    distance=distance,
                    speed=speed,
                    sign=sign,
                    degree_in_sign=degree_in_sign,
                    degree_classification=classification
                )

            except Exception as e:
                print(f"Warning: Could not calculate position for {planet_name}: {e}")
                continue

        return positions

    def _calculate_aspects(self, positions: Dict[str, PlanetaryPosition],
                          custom_orbs: Optional[Dict[str, float]] = None) -> List[Aspect]:
        """Calculate aspects between all planet pairs."""
        aspects = []
        planet_names = list(positions.keys())

        # Use custom orbs if provided
        aspect_definitions = self.ASPECTS.copy()
        if custom_orbs:
            for aspect_name, orb in custom_orbs.items():
                if aspect_name in aspect_definitions:
                    aspect_definitions[aspect_name]['orb'] = float(orb)

        # Check all planet pairs
        for i, planet1 in enumerate(planet_names):
            for planet2 in planet_names[i+1:]:  # Avoid duplicates
                pos1 = positions[planet1]
                pos2 = positions[planet2]

                # Check each aspect type
                for aspect_name, definition in aspect_definitions.items():
                    target_angle = definition['angle']
                    max_orb = definition['orb']

                    within_orb, actual_orb = is_within_orb(
                        pos1.longitude, pos2.longitude, target_angle, max_orb
                    )

                    if within_orb:
                        # Calculate exactness (1.0 = exact, 0.0 = at orb limit)
                        exactness = 1.0 - (actual_orb / max_orb)

                        # Determine if applying or separating
                        applying_separating = determine_applying_separating(
                            pos1.longitude, pos1.speed,
                            pos2.longitude, pos2.speed,
                            target_angle
                        )

                        # Calculate actual angle between planets
                        actual_angle = calculate_angle_difference(pos1.longitude, pos2.longitude)

                        aspects.append(Aspect(
                            planet1=planet1,
                            planet2=planet2,
                            aspect_type=aspect_name,
                            orb=actual_orb,
                            exactness=exactness,
                            angle=actual_angle,
                            applying_separating=applying_separating
                        ))

        # Sort aspects by exactness (most exact first)
        aspects.sort(key=lambda a: a.exactness, reverse=True)

        return aspects

    def _calculate_houses(self, julian_day: float, location_data: Dict[str, float]) -> Optional[HouseData]:
        """Calculate house positions using Placidus system."""
        lat = location_data['lat']
        lon = location_data['lon']
        location_name = location_data['name']

        try:
            # Calculate houses using Placidus system
            houses, ascmc = swe.houses(julian_day, lat, lon, b'P')  # 'P' = Placidus

            house_cusps = houses.tolist()
            ascendant = ascmc[0]
            midheaven = ascmc[1]

            # Calculate which house each planet is in
            planetary_houses = {}
            for planet_name in self.PLANETS.keys():
                # This would be filled in after planetary positions are calculated
                planetary_houses[planet_name] = 1  # Placeholder

            return HouseData(
                system='placidus',
                location=str(location_name),
                latitude=lat,
                longitude=lon,
                house_cusps=house_cusps,
                ascendant=ascendant,
                midheaven=midheaven,
                planetary_houses=planetary_houses
            )

        except Exception as e:
            print(f"Warning: Could not calculate houses: {e}")
            return None

    def _determine_house_number(self, planet_longitude: float, house_cusps: List[float]) -> int:
        """Determine which house a planet longitude falls into."""
        planet_longitude = normalize_angle(planet_longitude)

        for i in range(12):
            current_cusp = house_cusps[i]
            next_cusp = house_cusps[(i + 1) % 12] if i < 11 else house_cusps[0]

            # Handle wrap-around at 0/360 degrees
            if current_cusp > next_cusp:  # Wraps around 0°
                if planet_longitude >= current_cusp or planet_longitude < next_cusp:
                    return i + 1
            else:
                if current_cusp <= planet_longitude < next_cusp:
                    return i + 1

        return 1  # Default to first house

    def _detect_significant_events(self, positions: Dict[str, PlanetaryPosition],
                                  aspects: List[Aspect]) -> List[str]:
        """Detect significant astronomical events."""
        events = []

        # Check for major conjunctions
        major_conjunctions = [
            ('saturn', 'neptune'),
            ('saturn', 'uranus'),
            ('jupiter', 'saturn'),
            ('saturn', 'pluto'),
            ('uranus', 'neptune')
        ]

        for planet1, planet2 in major_conjunctions:
            for aspect in aspects:
                planets_set = {aspect.planet1, aspect.planet2}
                if planets_set == {planet1, planet2} and aspect.aspect_type == 'conjunction':
                    if aspect.orb <= 5:  # Tight orb for significance
                        events.append(f"{planet1.title()}-{planet2.title()} conjunction (orb: {aspect.orb:.1f}°)")

        # Check for lunar phase extremes
        sun_pos = positions.get('sun')
        moon_pos = positions.get('moon')
        if sun_pos and moon_pos:
            lunar_phase = calculate_lunar_phase(sun_pos.longitude, moon_pos.longitude)
            phase_name = classify_lunar_phase(lunar_phase)

            if phase_name in ['new', 'full']:
                events.append(f"Lunar {phase_name} moon")

        # Check for planets at critical degrees (0°, 29°)
        for planet_name, position in positions.items():
            degree = position.degree_in_sign
            if degree <= 1 or degree >= 29:
                events.append(f"{planet_name.title()} at critical degree ({degree:.1f}° {position.sign.title()})")

        return events

    def get_current_positions(self, location: str = 'utc') -> AstronomicalData:
        """Get current astronomical positions."""
        return self.encode_date(datetime.now(timezone.utc), location)

    def batch_encode_dates(self, dates: List[datetime], location: str = 'utc') -> List[AstronomicalData]:
        """Encode multiple dates efficiently."""
        results = []
        for date in dates:
            try:
                result = self.encode_date(date, location)
                results.append(result)
            except Exception as e:
                print(f"Warning: Could not encode date {date}: {e}")
                continue
        return results