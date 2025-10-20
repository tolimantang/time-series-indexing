"""
AstroEncoder - Astronomical data encoding for financial correlation analysis.

A package for encoding astronomical data (planetary positions, aspects, houses)
into structured formats suitable for financial market correlation analysis.
"""

from .encoder import AstroEncoder
from .data_models import AstronomicalData, PlanetaryPosition, Aspect
from .utils import degrees_to_sign, normalize_angle

__version__ = "0.1.0"
__all__ = ["AstroEncoder", "AstronomicalData", "PlanetaryPosition", "Aspect", "degrees_to_sign", "normalize_angle"]