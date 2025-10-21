"""
Astrological Data Encoder
Calculates planetary positions and aspects for financial market correlation analysis.
"""

from .core.encoder import AstroEncoder
from .core.data_access import AstroDataAccess
from .models.data_models import AstronomicalData, PlanetaryPosition, Aspect
from .core.verbalizer import AstroVerbalizer

__version__ = "1.0.0"
__all__ = ["AstroEncoder", "AstroDataAccess", "AstronomicalData", "PlanetaryPosition", "Aspect", "AstroVerbalizer"]