"""
Lunar Transit Pattern Testing Framework

Tests the hypothesis: "When moon transits over a particular house/planet and market moves
in a direction, the same directional move should occur on the next similar transit,
unless there are material changes to the astrological environment."
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import psycopg2
import numpy as np
from scipy import stats
import swisseph as swe

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketDirection(Enum):
    UP = "up"
    DOWN = "down"
    SIDEWAYS = "sideways"

class LunarAspectType(Enum):
    CONJUNCTION = "conjunction"
    OPPOSITION = "opposition"
    TRINE = "trine"
    SQUARE = "square"
    SEXTILE = "sextile"

@dataclass
class LunarEvent:
    """Represents a lunar transit event"""
    date: datetime
    aspect_type: LunarAspectType
    target_planet: str
    target_position: float  # degrees
    orb: float
    moon_position: float

@dataclass
class MarketMove:
    """Represents a market movement following an event"""
    direction: MarketDirection
    magnitude: float  # percentage change
    duration_days: int
    start_price: float
    end_price: float

@dataclass
class LunarPattern:
    """A discovered lunar pattern with its track record"""
    description: str
    aspect_type: LunarAspectType
    target_planet: str
    events: List[Tuple[LunarEvent, MarketMove]]
    consistency_rate: float
    avg_magnitude: float
    avg_duration: float
    last_occurrence: datetime
    total_occurrences: int

@dataclass
class MaterialChange:
    """Represents a material change in astrological environment"""
    change_type: str
    planet: str
    description: str
    date: datetime
    significance: float

class LunarPatternTester:
    """Main class for testing lunar transit patterns"""

    def __init__(self, db_config: Dict[str, str], market_symbol: str = "CL"):
        self.db_config = db_config
        self.market_symbol = market_symbol
        self.conn = None

        # Configuration parameters
        self.config = {
            'market_move_window_days': [1, 2, 3, 5],  # Days to measure market impact
            'significance_threshold': 0.5,  # Minimum % move to be significant
            'pattern_consistency_threshold': 0.65,  # 65% consistency required
            'minimum_occurrences': 3,  # Need at least 3 occurrences to validate pattern
            'max_orb_degrees': 3.0,  # Maximum orb for lunar aspects
            'material_change_lookback_days': 90,  # How far back to check for material changes
        }

        # Initialize Swiss Ephemeris
        swe.set_ephe_path('/usr/share/swisseph:/usr/local/share/swisseph')

    async def connect_db(self):
        """Connect to the database"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            logger.info("Connected to database")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    async def get_market_data(self, start_date: datetime, end_date: datetime) -> Dict[datetime, float]:
        """Fetch market price data for the specified period"""
        cursor = self.conn.cursor()

        # For now, we'll create a placeholder - in reality you'd fetch from your price data table
        query = """
        SELECT trade_date,
               -- Placeholder: generate synthetic oil price data based on date
               50 + 20 * SIN(EXTRACT(DOY FROM trade_date) * 2 * PI() / 365) +
               RANDOM() * 10 - 5 as price
        FROM daily_astrological_conditions
        WHERE trade_date BETWEEN %s AND %s
        ORDER BY trade_date
        """

        cursor.execute(query, (start_date.date(), end_date.date()))
        results = cursor.fetchall()

        price_data = {}
        for date, price in results:
            price_data[datetime.combine(date, datetime.min.time())] = float(price)

        cursor.close()
        logger.info(f"Fetched {len(price_data)} price points")
        return price_data

    def calculate_lunar_position(self, date: datetime) -> float:
        """Calculate moon's position in degrees for given date"""
        julian_day = swe.julday(date.year, date.month, date.day, date.hour + date.minute/60.0)
        moon_pos, _ = swe.calc_ut(julian_day, swe.MOON)
        return moon_pos[0]  # Longitude in degrees

    def calculate_planet_position(self, planet_name: str, date: datetime) -> float:
        """Calculate planet position for given date"""
        planet_mapping = {
            'Sun': swe.SUN,
            'Mercury': swe.MERCURY,
            'Venus': swe.VENUS,
            'Mars': swe.MARS,
            'Jupiter': swe.JUPITER,
            'Saturn': swe.SATURN,
            'Uranus': swe.URANUS,
            'Neptune': swe.NEPTUNE,
            'Pluto': swe.PLUTO
        }

        if planet_name not in planet_mapping:
            raise ValueError(f"Unknown planet: {planet_name}")

        julian_day = swe.julday(date.year, date.month, date.day, date.hour + date.minute/60.0)
        planet_pos, _ = swe.calc_ut(julian_day, planet_mapping[planet_name])
        return planet_pos[0]

    def calculate_aspect_orb(self, pos1: float, pos2: float, aspect_degrees: float) -> float:
        """Calculate the orb (deviation) from exact aspect"""
        # Normalize positions to 0-360
        pos1 = pos1 % 360
        pos2 = pos2 % 360

        # Calculate the actual angle between positions
        angle_diff = abs(pos1 - pos2)
        if angle_diff > 180:
            angle_diff = 360 - angle_diff

        # Calculate orb from the target aspect
        orb = abs(angle_diff - aspect_degrees)
        if orb > 180:
            orb = 360 - orb

        return orb

    def find_lunar_aspects(self, start_date: datetime, end_date: datetime,
                          target_planet: str) -> List[LunarEvent]:
        """Find all lunar aspects to a target planet in the given period"""
        events = []
        current_date = start_date

        aspect_degrees = {
            LunarAspectType.CONJUNCTION: 0,
            LunarAspectType.OPPOSITION: 180,
            LunarAspectType.TRINE: 120,
            LunarAspectType.SQUARE: 90,
            LunarAspectType.SEXTILE: 60
        }

        while current_date <= end_date:
            moon_pos = self.calculate_lunar_position(current_date)
            planet_pos = self.calculate_planet_position(target_planet, current_date)

            # Check each aspect type
            for aspect_type, aspect_deg in aspect_degrees.items():
                orb = self.calculate_aspect_orb(moon_pos, planet_pos, aspect_deg)

                if orb <= self.config['max_orb_degrees']:
                    events.append(LunarEvent(
                        date=current_date,
                        aspect_type=aspect_type,
                        target_planet=target_planet,
                        target_position=planet_pos,
                        orb=orb,
                        moon_position=moon_pos
                    ))

            current_date += timedelta(days=1)

        logger.info(f"Found {len(events)} lunar aspects to {target_planet}")
        return events

    def calculate_market_move(self, event_date: datetime, price_data: Dict[datetime, float],
                             window_days: int = 3) -> Optional[MarketMove]:
        """Calculate market movement following a lunar event"""

        # Find the starting price (on or closest to event date)
        start_date = event_date
        while start_date not in price_data and start_date <= max(price_data.keys()):
            start_date += timedelta(days=1)

        if start_date not in price_data:
            return None

        start_price = price_data[start_date]

        # Find the ending price (window_days later)
        end_date = start_date + timedelta(days=window_days)
        while end_date not in price_data and end_date <= max(price_data.keys()):
            end_date += timedelta(days=1)

        if end_date not in price_data:
            return None

        end_price = price_data[end_date]

        # Calculate movement
        magnitude = ((end_price - start_price) / start_price) * 100

        # Determine direction
        if abs(magnitude) < self.config['significance_threshold']:
            direction = MarketDirection.SIDEWAYS
        elif magnitude > 0:
            direction = MarketDirection.UP
        else:
            direction = MarketDirection.DOWN

        return MarketMove(
            direction=direction,
            magnitude=magnitude,
            duration_days=window_days,
            start_price=start_price,
            end_price=end_price
        )

    def detect_material_changes(self, start_date: datetime, end_date: datetime) -> List[MaterialChange]:
        """Detect material changes in astrological environment between two dates"""
        changes = []

        # Check for sign changes of major planets
        major_planets = ['Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn']

        for planet in major_planets:
            start_pos = self.calculate_planet_position(planet, start_date)
            end_pos = self.calculate_planet_position(planet, end_date)

            start_sign = int(start_pos // 30)
            end_sign = int(end_pos // 30)

            if start_sign != end_sign:
                changes.append(MaterialChange(
                    change_type="sign_change",
                    planet=planet,
                    description=f"{planet} changed signs from {start_sign} to {end_sign}",
                    date=start_date,  # Approximate - could be more precise
                    significance=1.0
                ))

            # Check for significant position changes (more than 15 degrees)
            position_change = abs(end_pos - start_pos) % 360
            if position_change > 180:
                position_change = 360 - position_change

            if position_change > 15:  # Significant movement
                changes.append(MaterialChange(
                    change_type="major_movement",
                    planet=planet,
                    description=f"{planet} moved {position_change:.1f} degrees",
                    date=start_date,
                    significance=position_change / 30.0  # Normalize by sign width
                ))

        return changes

    def discover_patterns(self, lunar_events: List[LunarEvent],
                         price_data: Dict[datetime, float]) -> List[LunarPattern]:
        """Discover repeating lunar patterns"""
        patterns = {}

        # Group events by aspect type and target planet
        for event in lunar_events:
            key = (event.aspect_type, event.target_planet)
            if key not in patterns:
                patterns[key] = []

            # Calculate market move for this event
            for window in self.config['market_move_window_days']:
                market_move = self.calculate_market_move(event.date, price_data, window)
                if market_move and market_move.direction != MarketDirection.SIDEWAYS:
                    patterns[key].append((event, market_move))
                    break  # Use the first significant move found

        # Analyze each pattern group for consistency
        discovered_patterns = []

        for (aspect_type, planet), event_moves in patterns.items():
            if len(event_moves) < self.config['minimum_occurrences']:
                continue

            # Calculate consistency (same direction)
            directions = [move.direction for _, move in event_moves]
            most_common_direction = max(set(directions), key=directions.count)
            consistency_rate = directions.count(most_common_direction) / len(directions)

            if consistency_rate >= self.config['pattern_consistency_threshold']:
                # Calculate statistics
                magnitudes = [abs(move.magnitude) for _, move in event_moves]
                durations = [move.duration_days for _, move in event_moves]

                pattern = LunarPattern(
                    description=f"Moon {aspect_type.value} {planet} → {most_common_direction.value}",
                    aspect_type=aspect_type,
                    target_planet=planet,
                    events=event_moves,
                    consistency_rate=consistency_rate,
                    avg_magnitude=np.mean(magnitudes),
                    avg_duration=np.mean(durations),
                    last_occurrence=max(event.date for event, _ in event_moves),
                    total_occurrences=len(event_moves)
                )

                discovered_patterns.append(pattern)
                logger.info(f"Discovered pattern: {pattern.description} "
                           f"({consistency_rate:.1%} consistency, {len(event_moves)} occurrences)")

        return discovered_patterns

    async def backtest_patterns(self, start_date: datetime, end_date: datetime,
                               target_planets: List[str]) -> Dict[str, Any]:
        """Main backtesting function"""
        await self.connect_db()

        try:
            # Get market data
            price_data = await self.get_market_data(start_date, end_date)

            # Find all lunar events for each target planet
            all_events = []
            for planet in target_planets:
                events = self.find_lunar_aspects(start_date, end_date, planet)
                all_events.extend(events)

            # Discover patterns
            patterns = self.discover_patterns(all_events, price_data)

            # Test pattern stability over time
            results = await self.test_pattern_stability(patterns, price_data)

            return {
                'total_events': len(all_events),
                'discovered_patterns': len(patterns),
                'patterns': patterns,
                'stability_results': results,
                'market_symbol': self.market_symbol,
                'test_period': {'start': start_date, 'end': end_date}
            }

        finally:
            if self.conn:
                self.conn.close()

    async def test_pattern_stability(self, patterns: List[LunarPattern],
                                   price_data: Dict[datetime, float]) -> Dict[str, Any]:
        """Test if patterns remain stable over different time periods"""
        stability_results = {}

        for pattern in patterns:
            # Split events into early and late periods
            events_by_date = sorted(pattern.events, key=lambda x: x[0].date)
            mid_point = len(events_by_date) // 2

            early_events = events_by_date[:mid_point]
            late_events = events_by_date[mid_point:]

            if len(early_events) >= 2 and len(late_events) >= 2:
                # Calculate consistency for each period
                early_directions = [move.direction for _, move in early_events]
                late_directions = [move.direction for _, move in late_events]

                early_consistency = max(early_directions.count(d) for d in set(early_directions)) / len(early_directions)
                late_consistency = max(late_directions.count(d) for d in set(late_directions)) / len(late_directions)

                stability_results[pattern.description] = {
                    'early_consistency': early_consistency,
                    'late_consistency': late_consistency,
                    'stability_score': min(early_consistency, late_consistency),
                    'degradation': early_consistency - late_consistency
                }

        return stability_results

# Example usage function
async def run_oil_backtest():
    """Example function to test lunar patterns on oil market"""

    db_config = {
        'host': 'your_db_host',
        'user': 'your_db_user',
        'password': 'your_db_password',
        'database': 'your_db_name'
    }

    tester = LunarPatternTester(db_config, market_symbol="CL")

    # Test period: last 5 years
    end_date = datetime.now()
    start_date = end_date - timedelta(days=5*365)

    # Test lunar aspects to major planets
    target_planets = ['Jupiter', 'Saturn', 'Mars', 'Venus', 'Mercury']

    results = await tester.backtest_patterns(start_date, end_date, target_planets)

    # Print results
    print(f"\n=== Lunar Pattern Backtest Results ===")
    print(f"Market: {results['market_symbol']}")
    print(f"Period: {results['test_period']['start'].date()} to {results['test_period']['end'].date()}")
    print(f"Total lunar events analyzed: {results['total_events']}")
    print(f"Significant patterns discovered: {results['discovered_patterns']}")

    print(f"\n=== Discovered Patterns ===")
    for pattern in results['patterns']:
        print(f"\nPattern: {pattern.description}")
        print(f"  Consistency: {pattern.consistency_rate:.1%}")
        print(f"  Occurrences: {pattern.total_occurrences}")
        print(f"  Avg Magnitude: {pattern.avg_magnitude:.2f}%")
        print(f"  Last Seen: {pattern.last_occurrence.date()}")

    return results

if __name__ == "__main__":
    # Run the backtest
    results = asyncio.run(run_oil_backtest())