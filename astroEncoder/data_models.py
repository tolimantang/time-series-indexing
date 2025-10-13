"""
Data models for astronomical data representation.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class PlanetaryPosition:
    """Represents a planet's position at a specific time."""
    planet: str
    longitude: float  # 0-360 degrees
    latitude: float
    distance: float  # AU
    speed: float  # degrees per day
    sign: str  # zodiac sign name
    degree_in_sign: float  # 0-30 degrees within the sign
    degree_classification: str  # 'early', 'middle', 'late'
    house: Optional[int] = None  # 1-12, calculated separately


@dataclass
class Aspect:
    """Represents an aspect between two planets."""
    planet1: str
    planet2: str
    aspect_type: str  # 'conjunction', 'opposition', 'trine', etc.
    orb: float  # degrees from exact
    exactness: float  # 0-1, where 1 is exact
    angle: float  # actual angle between planets
    applying_separating: str  # 'applying', 'separating', 'unknown'


@dataclass
class HouseData:
    """Represents house system data."""
    system: str  # 'placidus', 'koch', etc.
    location: str  # location name
    latitude: float
    longitude: float
    house_cusps: List[float]  # 12 house cusps in degrees
    ascendant: float
    midheaven: float
    planetary_houses: Dict[str, int]  # planet -> house number


@dataclass
class AstronomicalData:
    """Complete astronomical data for a specific date/time/location."""
    date: datetime
    julian_day: float
    location: str
    positions: Dict[str, PlanetaryPosition]
    aspects: List[Aspect]
    houses: Optional[HouseData] = None
    lunar_phase: Optional[float] = None  # 0-360 degrees from new moon
    significant_events: List[str] = None  # Notable astronomical events

    def __post_init__(self):
        if self.significant_events is None:
            self.significant_events = []

    def get_planet_position(self, planet: str) -> Optional[PlanetaryPosition]:
        """Get position data for a specific planet."""
        return self.positions.get(planet.lower())

    def get_aspects_for_planet(self, planet: str) -> List[Aspect]:
        """Get all aspects involving a specific planet."""
        planet_lower = planet.lower()
        return [aspect for aspect in self.aspects
                if planet_lower in [aspect.planet1.lower(), aspect.planet2.lower()]]

    def get_aspect_between(self, planet1: str, planet2: str, aspect_type: str = None) -> List[Aspect]:
        """Get aspects between two specific planets."""
        p1, p2 = planet1.lower(), planet2.lower()
        aspects = []

        for aspect in self.aspects:
            planets_match = {aspect.planet1.lower(), aspect.planet2.lower()} == {p1, p2}
            type_match = aspect_type is None or aspect.aspect_type == aspect_type

            if planets_match and type_match:
                aspects.append(aspect)

        return aspects

    def has_conjunction(self, planet1: str, planet2: str, max_orb: float = 8.0) -> bool:
        """Check if two planets are in conjunction within specified orb."""
        conjunctions = self.get_aspect_between(planet1, planet2, "conjunction")
        return any(conj.orb <= max_orb for conj in conjunctions)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "date": self.date.isoformat(),
            "julian_day": self.julian_day,
            "location": self.location,
            "positions": {planet: {
                "planet": pos.planet,
                "longitude": pos.longitude,
                "latitude": pos.latitude,
                "distance": pos.distance,
                "speed": pos.speed,
                "sign": pos.sign,
                "degree_in_sign": pos.degree_in_sign,
                "degree_classification": pos.degree_classification,
                "house": pos.house
            } for planet, pos in self.positions.items()},
            "aspects": [{
                "planet1": aspect.planet1,
                "planet2": aspect.planet2,
                "aspect_type": aspect.aspect_type,
                "orb": aspect.orb,
                "exactness": aspect.exactness,
                "angle": aspect.angle,
                "applying_separating": aspect.applying_separating
            } for aspect in self.aspects],
            "houses": {
                "system": self.houses.system,
                "location": self.houses.location,
                "latitude": self.houses.latitude,
                "longitude": self.houses.longitude,
                "house_cusps": self.houses.house_cusps,
                "ascendant": self.houses.ascendant,
                "midheaven": self.houses.midheaven,
                "planetary_houses": self.houses.planetary_houses
            } if self.houses else None,
            "lunar_phase": self.lunar_phase,
            "significant_events": self.significant_events
        }