#!/usr/bin/env python3
"""
Real Backtesting Service

A FastAPI service that accepts backtesting requests and runs real lunar pattern analysis
using the EnhancedDailyLunarTester.

Features:
- Real data validation before analysis
- Integration with EnhancedDailyLunarTester
- Support for same_day, next_day, and all timing types
- Proper error handling and status reporting
"""

import os
import sys
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException, BackgroundTasks
import psycopg2
import pandas as pd

# Add the analyzer to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'llm_analyzer'))
from enhanced_daily_lunar_tester import EnhancedDailyLunarTester

# Swiss Ephemeris for planetary calculations
import swisseph as swe
import yfinance as yf
from datetime import timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Real Backtesting Service",
    description="Lunar pattern backtesting with real market data validation and analysis",
    version="2.0.0"
)

class BacktestRequest(BaseModel):
    # Common fields for all backtest types
    symbol: str = Field(..., description="Market symbol (e.g., PLATINUM_FUTURES, PL=F)")
    market_name: str = Field(..., description="Market name (e.g., PLATINUM)")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")

    # Backtest type discriminator
    backtest_type: str = Field(..., description="Type of backtest: 'lunar', 'planetary', or 'ingress'")

    # Lunar-specific fields (only used when backtest_type='lunar')
    timing_type: Optional[str] = Field("next_day", description="Lunar timing type: same_day, next_day, or all")
    accuracy_threshold: Optional[float] = Field(0.65, description="Minimum accuracy threshold for lunar patterns")
    min_occurrences: Optional[int] = Field(5, description="Minimum pattern occurrences for lunar patterns")

    # Planetary-specific fields (only used when backtest_type='planetary')
    planet1: Optional[str] = Field(None, description="First planet (e.g., jupiter)")
    planet2: Optional[str] = Field(None, description="Second planet (e.g., mars)")
    aspect_types: Optional[List[str]] = Field(None, description="Aspect types (e.g., ['trine']). If None, uses all major aspects")
    orb_size: Optional[float] = Field(8.0, description="Orb size in degrees for planetary aspects")

    # Ingress-specific fields (only used when backtest_type='ingress')
    planet: Optional[str] = Field(None, description="Planet for ingress (e.g., jupiter) or 'all' for all major planets")
    zodiac_signs: Optional[List[str]] = Field(None, description="Zodiac signs for ingress (e.g., ['cancer']) or ['all'] for all signs")

class BacktestResponse(BaseModel):
    request_id: str
    status: str
    message: str
    patterns_found: Optional[int] = None
    best_pattern: Optional[Dict[str, Any]] = None
    execution_time_seconds: Optional[float] = None
    data_summary: Optional[Dict[str, Any]] = None

class PatternSummary(BaseModel):
    symbol: str
    market_name: str
    timing_type: str
    total_patterns: int
    best_accuracy: float
    best_pattern_name: str
    analysis_date: str

class PlanetaryBacktestRequest(BaseModel):
    symbol: str = Field(..., description="Trading symbol (e.g., PL=F)")
    market_name: str = Field(..., description="Market name (e.g., PLATINUM)")
    planet1: str = Field(..., description="First planet (e.g., Jupiter)")
    planet2: str = Field(..., description="Second planet (e.g., Mars)")
    aspect_types: Optional[List[str]] = Field(None, description="Aspect types (e.g., ['trine']). If None, uses all major aspects")
    orb_size: float = Field(8.0, description="Orb size in degrees")
    start_date: str = Field(..., description="Start date for backtest (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date for backtest (YYYY-MM-DD)")

class PlanetaryBacktestResult(BaseModel):
    phase: str  # "approaching" or "separating"
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    return_pct: float
    holding_days: int
    aspect_info: Dict[str, Any]

class PlanetaryBacktestResponse(BaseModel):
    request_id: str
    status: str
    message: str
    symbol: str
    planet1: str
    planet2: str
    aspect_types: List[str]
    orb_size: float
    total_aspects_found: int
    approaching_phase_results: List[PlanetaryBacktestResult]
    separating_phase_results: List[PlanetaryBacktestResult]
    summary_stats: Dict[str, Any]
    execution_time_seconds: float
    insights_saved: bool  # Whether results were saved to planetary_patterns table

class PlanetaryBacktester:
    """Planetary aspect backtesting with two-phase strategy (approaching vs separating)"""

    def __init__(self):
        # Swiss Ephemeris planet constants
        self.planet_constants = {
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

        # Major aspects in degrees
        self.aspects = {
            'conjunction': 0,
            'sextile': 60,
            'square': 90,
            'trine': 120,
            'opposition': 180
        }

    def run_backtest(self, symbol: str, market_name: str, planet1: str, planet2: str,
                    aspect_types: List[str], orb_size: float, start_date: str, end_date: str):
        """Run complete planetary backtest with two-phase strategy"""

        logger.info(f"🪐 Starting planetary backtest: {planet1}-{planet2} for {symbol}")

        # Get market data
        market_data = self._get_market_data(symbol, start_date, end_date)
        if market_data.empty:
            raise ValueError(f"No market data found for {symbol} in the date range")

        # Use all major aspects if none specified
        if not aspect_types:
            aspect_types = list(self.aspects.keys())

        results = {}

        # Run backtest for each aspect type
        for aspect_type in aspect_types:
            logger.info(f"📐 Testing {aspect_type} aspect ({self.aspects[aspect_type]}°)")

            # Find aspect periods
            aspect_periods = self._find_aspect_periods(
                planet1, planet2, aspect_type, orb_size, start_date, end_date
            )

            if not aspect_periods:
                logger.warning(f"No {aspect_type} aspects found for {planet1}-{planet2}")
                continue

            # Run two-phase backtesting
            approaching_results = self._backtest_phase(
                market_data, aspect_periods, "approaching"
            )
            separating_results = self._backtest_phase(
                market_data, aspect_periods, "separating"
            )

            results[aspect_type] = {
                'approaching_phase': approaching_results,
                'separating_phase': separating_results,
                'total_aspects': len(aspect_periods)
            }

            # Store results in planetary_patterns table
            self._store_results(
                symbol, market_name, planet1, planet2, aspect_type, orb_size,
                start_date, end_date, approaching_results, separating_results
            )

        return results

    def _get_market_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Get market data from database or yfinance"""
        try:
            # First try database
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT trade_date, open_price, high_price, low_price, close_price, volume
                FROM market_data
                WHERE symbol = %s AND trade_date BETWEEN %s AND %s
                ORDER BY trade_date
            """, (symbol, start_date, end_date))

            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            if rows:
                df = pd.DataFrame(rows, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
                return df

        except Exception as e:
            logger.warning(f"Database lookup failed: {e}, trying yfinance")

        # Fallback to yfinance
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            return df
        except Exception as e:
            logger.error(f"Failed to get market data: {e}")
            return pd.DataFrame()

    def _find_aspect_periods(self, planet1: str, planet2: str, aspect_type: str,
                           orb_size: float, start_date: str, end_date: str) -> List[Dict]:
        """Find periods when planets are within orb of specific aspect"""

        aspect_angle = self.aspects[aspect_type]
        planet1_id = self.planet_constants[planet1.lower()]
        planet2_id = self.planet_constants[planet2.lower()]

        periods = []
        current_period = None

        # Check each day for aspect within orb
        current_date = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)

        while current_date <= end_dt:
            try:
                # Calculate Julian day
                jd = swe.julday(current_date.year, current_date.month, current_date.day, 12.0)

                # Get planetary positions
                pos1, _ = swe.calc_ut(jd, planet1_id)
                pos2, _ = swe.calc_ut(jd, planet2_id)

                # Calculate angular difference
                angle_diff = abs(pos1[0] - pos2[0])
                if angle_diff > 180:
                    angle_diff = 360 - angle_diff

                # Check if within orb of aspect
                orb_distance = abs(angle_diff - aspect_angle)
                if orb_distance > 180:
                    orb_distance = 360 - orb_distance

                if orb_distance <= orb_size:
                    if current_period is None:
                        # Start new period
                        current_period = {
                            'start_date': current_date,
                            'orb_entry': current_date,
                            'exact_date': None,
                            'orb_exit': None,
                            'min_orb_distance': orb_distance
                        }
                    else:
                        # Update existing period
                        if orb_distance < current_period['min_orb_distance']:
                            current_period['min_orb_distance'] = orb_distance
                            current_period['exact_date'] = current_date
                else:
                    if current_period is not None:
                        # End current period
                        current_period['orb_exit'] = current_date - timedelta(days=1)
                        current_period['end_date'] = current_period['orb_exit']
                        periods.append(current_period)
                        current_period = None

            except Exception as e:
                logger.warning(f"Swiss Ephemeris calculation failed for {current_date}: {e}")

            current_date += timedelta(days=1)

        # Close final period if still open
        if current_period is not None:
            current_period['orb_exit'] = current_date - timedelta(days=1)
            current_period['end_date'] = current_period['orb_exit']
            periods.append(current_period)

        logger.info(f"Found {len(periods)} {aspect_type} aspect periods")
        return periods

    def _backtest_phase(self, market_data: pd.DataFrame, aspect_periods: List[Dict], phase: str) -> Dict:
        """Backtest specific phase (approaching or separating)"""

        trades = []

        for period in aspect_periods:
            if phase == "approaching":
                # Entry at orb start, exit at exact aspect
                entry_date = period['orb_entry']
                exit_date = period['exact_date'] or period['end_date']
            else:  # separating
                # Entry at exact aspect, exit at orb end
                entry_date = period['exact_date'] or period['start_date']
                exit_date = period['orb_exit'] or period['end_date']

            # Find closest market data dates
            entry_price, exit_price = self._get_trade_prices(market_data, entry_date, exit_date)

            if entry_price and exit_price:
                return_pct = ((exit_price - entry_price) / entry_price) * 100
                holding_days = (exit_date - entry_date).days

                trades.append({
                    'entry_date': entry_date,
                    'exit_date': exit_date,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'return_pct': return_pct,
                    'holding_days': holding_days,
                    'aspect_info': period
                })

        # Calculate statistics
        if not trades:
            return {
                'total_trades': 0,
                'avg_return_pct': 0,
                'win_rate': 0,
                'avg_holding_days': 0,
                'best_return_pct': 0,
                'worst_return_pct': 0,
                'trades': []
            }

        returns = [t['return_pct'] for t in trades]
        holding_days = [t['holding_days'] for t in trades]

        return {
            'total_trades': len(trades),
            'avg_return_pct': float(sum(returns) / len(returns)),
            'win_rate': float(len([r for r in returns if r > 0]) / len(returns)),
            'avg_holding_days': float(sum(holding_days) / len(holding_days)),
            'best_return_pct': float(max(returns)),
            'worst_return_pct': float(min(returns)),
            'trades': trades
        }

    def _get_trade_prices(self, market_data: pd.DataFrame, entry_date, exit_date):
        """Get entry and exit prices from market data"""
        try:
            # Find closest available dates
            entry_price = None
            exit_price = None

            # Look for entry price (within 3 days)
            for days_offset in range(4):
                check_date = entry_date + timedelta(days=days_offset)
                if check_date.date() in market_data.index.date:
                    entry_price = market_data.loc[market_data.index.date == check_date.date(), 'Close'].iloc[0]
                    break

            # Look for exit price (within 3 days)
            for days_offset in range(4):
                check_date = exit_date + timedelta(days=days_offset)
                if check_date.date() in market_data.index.date:
                    exit_price = market_data.loc[market_data.index.date == check_date.date(), 'Close'].iloc[0]
                    break

            return entry_price, exit_price

        except Exception as e:
            logger.warning(f"Price lookup failed: {e}")
            return None, None

    def _store_results(self, symbol: str, market_name: str, planet1: str, planet2: str,
                      aspect_type: str, orb_size: float, start_date: str, end_date: str,
                      approaching_results: Dict, separating_results: Dict):
        """Store results in planetary_patterns table"""

        conn = get_db_connection()
        cursor = conn.cursor()

        # Store approaching phase results
        self._insert_phase_results(
            cursor, symbol, market_name, planet1, planet2, aspect_type, orb_size,
            start_date, end_date, "approaching", approaching_results
        )

        # Store separating phase results
        self._insert_phase_results(
            cursor, symbol, market_name, planet1, planet2, aspect_type, orb_size,
            start_date, end_date, "separating", separating_results
        )

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"✅ Stored {aspect_type} results for {planet1}-{planet2}")

    def _insert_phase_results(self, cursor, symbol: str, market_name: str, planet1: str, planet2: str,
                             aspect_type: str, orb_size: float, start_date: str, end_date: str,
                             phase: str, results: Dict):
        """Insert phase-specific results into planetary_patterns table"""

        pattern_name = f"{planet1.title()}-{planet2.title()} {aspect_type.title()} {phase.title()} Phase"

        cursor.execute("""
            INSERT INTO planetary_patterns (
                market_symbol, symbol, planet1, planet2, aspect_type, orb_size,
                start_date, end_date, phase, total_trades, avg_return_pct, win_rate,
                avg_holding_days, best_return_pct, worst_return_pct, accuracy_rate,
                pattern_name, total_aspects_found, backtest_version
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (market_symbol, planet1, planet2, aspect_type, phase, orb_size, start_date, end_date)
            DO UPDATE SET
                total_trades = EXCLUDED.total_trades,
                avg_return_pct = EXCLUDED.avg_return_pct,
                win_rate = EXCLUDED.win_rate,
                avg_holding_days = EXCLUDED.avg_holding_days,
                best_return_pct = EXCLUDED.best_return_pct,
                worst_return_pct = EXCLUDED.worst_return_pct,
                accuracy_rate = EXCLUDED.accuracy_rate,
                updated_at = CURRENT_TIMESTAMP
        """, (
            f"{market_name}_DAILY", symbol, planet1.lower(), planet2.lower(), aspect_type,
            float(orb_size), start_date, end_date, phase, int(results['total_trades']),
            float(results['avg_return_pct']), float(results['win_rate']), float(results['avg_holding_days']),
            float(results['best_return_pct']), float(results['worst_return_pct']), float(results['win_rate']),
            pattern_name, int(len(results.get('trades', []))), 'v1.0'
        ))

class PlanetaryIngressBacktester:
    """Planetary ingress backtesting with simple next-day price comparison strategy"""

    def __init__(self):
        # Swiss Ephemeris planet constants (excluding moon as requested)
        self.planet_constants = {
            'sun': swe.SUN,
            'mercury': swe.MERCURY,
            'venus': swe.VENUS,
            'mars': swe.MARS,
            'jupiter': swe.JUPITER,
            'saturn': swe.SATURN,
            'uranus': swe.URANUS,
            'neptune': swe.NEPTUNE,
            'pluto': swe.PLUTO
        }

        # All zodiac signs with their degree ranges
        self.zodiac_signs = {
            'aries': 0,
            'taurus': 30,
            'gemini': 60,
            'cancer': 90,
            'leo': 120,
            'virgo': 150,
            'libra': 180,
            'scorpio': 210,
            'sagittarius': 240,
            'capricorn': 270,
            'aquarius': 300,
            'pisces': 330
        }

    def run_ingress_backtest(self, symbol: str, market_name: str, planet: str,
                           zodiac_signs: List[str], start_date: str, end_date: str):
        """Run complete planetary ingress backtest"""

        logger.info(f"🌟 Starting ingress backtest: {planet} into {zodiac_signs} for {symbol}")

        # Get market data
        market_data = self._get_market_data(symbol, start_date, end_date)
        if market_data.empty:
            raise ValueError(f"No market data found for {symbol} in the date range")

        # Expand "all" parameters
        planets_to_test = self._expand_planets([planet])
        signs_to_test = self._expand_zodiac_signs(zodiac_signs)

        results = {}

        # Run backtest for each planet/sign combination
        for test_planet in planets_to_test:
            for sign in signs_to_test:
                logger.info(f"⭐ Testing {test_planet} ingress into {sign}")

                # Find ingress dates
                ingress_dates = self._find_ingress_dates(
                    test_planet, sign, start_date, end_date
                )

                if not ingress_dates:
                    logger.warning(f"No {test_planet} ingresses into {sign} found")
                    continue

                # Run simple next-day price comparison backtest
                ingress_results = self._backtest_ingress_events(
                    market_data, ingress_dates, test_planet, sign
                )

                pattern_key = f"{test_planet}_{sign}"
                results[pattern_key] = {
                    'planet': test_planet,
                    'zodiac_sign': sign,
                    'ingress_events': len(ingress_dates),
                    'results': ingress_results
                }

                # Store results in planetary_patterns table
                self._store_ingress_results(
                    symbol, market_name, test_planet, sign,
                    start_date, end_date, ingress_results, ingress_dates
                )

        return results

    def _expand_planets(self, planets: List[str]) -> List[str]:
        """Expand 'all' to all major planets"""
        if 'all' in planets:
            return list(self.planet_constants.keys())
        return [p.lower() for p in planets]

    def _expand_zodiac_signs(self, signs: List[str]) -> List[str]:
        """Expand 'all' to all zodiac signs"""
        if 'all' in signs:
            return list(self.zodiac_signs.keys())
        return [s.lower() for s in signs]

    def _get_market_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Get market data from database or yfinance (reuse logic from PlanetaryBacktester)"""
        try:
            # First try database
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT trade_date, open_price, high_price, low_price, close_price, volume
                FROM market_data
                WHERE symbol = %s AND trade_date BETWEEN %s AND %s
                ORDER BY trade_date
            """, (symbol, start_date, end_date))

            rows = cursor.fetchall()
            cursor.close()
            conn.close()

            if rows:
                df = pd.DataFrame(rows, columns=['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
                return df

        except Exception as e:
            logger.warning(f"Database lookup failed: {e}, trying yfinance")

        # Fallback to yfinance
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            return df
        except Exception as e:
            logger.error(f"Failed to get market data: {e}")
            return pd.DataFrame()

    def _find_ingress_dates(self, planet: str, sign: str, start_date: str, end_date: str) -> List[Dict]:
        """Find dates when planet ingresses into specified zodiac sign"""

        planet_id = self.planet_constants[planet.lower()]
        sign_start_degree = self.zodiac_signs[sign.lower()]
        sign_end_degree = (sign_start_degree + 30) % 360

        ingress_dates = []
        current_date = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        previous_position = None

        while current_date <= end_dt:
            try:
                # Calculate Julian day
                jd = swe.julday(current_date.year, current_date.month, current_date.day, 12.0)

                # Get planetary position
                pos, _ = swe.calc_ut(jd, planet_id)
                current_longitude = pos[0] % 360

                if previous_position is not None:
                    # Check if planet crossed into the sign
                    if self._crossed_into_sign(previous_position, current_longitude, sign_start_degree):
                        ingress_dates.append({
                            'ingress_date': current_date,
                            'planet': planet,
                            'zodiac_sign': sign,
                            'longitude_at_ingress': current_longitude
                        })
                        logger.info(f"🌟 Found {planet} ingress into {sign} on {current_date.date()}")

                previous_position = current_longitude

            except Exception as e:
                logger.warning(f"Swiss Ephemeris calculation failed for {current_date}: {e}")

            current_date += timedelta(days=1)

        logger.info(f"Found {len(ingress_dates)} {planet} ingresses into {sign}")
        return ingress_dates

    def _crossed_into_sign(self, prev_longitude: float, curr_longitude: float, sign_start: float) -> bool:
        """Check if planet crossed from outside sign to inside sign"""
        # Handle wraparound at 360/0 degrees
        if sign_start == 0:  # Aries
            # Check if crossed from Pisces (330-360) to Aries (0-30)
            return (prev_longitude >= 330 and curr_longitude <= 30) or \
                   (prev_longitude > curr_longitude and curr_longitude <= 30)
        else:
            # Normal case: check if crossed the sign boundary
            return prev_longitude < sign_start <= curr_longitude

    def _backtest_ingress_events(self, market_data: pd.DataFrame, ingress_dates: List[Dict],
                                planet: str, sign: str) -> Dict:
        """Simple next-day price comparison strategy for ingress events"""

        trades = []

        for ingress in ingress_dates:
            ingress_date = ingress['ingress_date']

            # Find prices on ingress day and next day
            ingress_price, next_day_price = self._get_ingress_trade_prices(
                market_data, ingress_date
            )

            if ingress_price and next_day_price:
                return_pct = ((next_day_price - ingress_price) / ingress_price) * 100

                trades.append({
                    'ingress_date': ingress_date,
                    'next_day_date': ingress_date + timedelta(days=1),
                    'ingress_price': ingress_price,
                    'next_day_price': next_day_price,
                    'return_pct': return_pct,
                    'ingress_info': ingress
                })

        # Calculate statistics
        if not trades:
            return {
                'total_trades': 0,
                'avg_return_pct': 0,
                'win_rate': 0,
                'best_return_pct': 0,
                'worst_return_pct': 0,
                'trades': []
            }

        returns = [t['return_pct'] for t in trades]

        return {
            'total_trades': len(trades),
            'avg_return_pct': float(sum(returns) / len(returns)),
            'win_rate': float(len([r for r in returns if r > 0]) / len(returns)),
            'best_return_pct': float(max(returns)),
            'worst_return_pct': float(min(returns)),
            'trades': trades
        }

    def _get_ingress_trade_prices(self, market_data: pd.DataFrame, ingress_date):
        """Get ingress day price and next day price from market data"""
        try:
            ingress_price = None
            next_day_price = None

            # Look for ingress day price (within 3 days)
            for days_offset in range(4):
                check_date = ingress_date + timedelta(days=days_offset)
                if check_date.date() in market_data.index.date:
                    ingress_price = market_data.loc[market_data.index.date == check_date.date(), 'Close'].iloc[0]
                    break

            # Look for next trading day price (within 7 days to account for weekends)
            for days_offset in range(1, 8):
                check_date = ingress_date + timedelta(days=days_offset)
                if check_date.date() in market_data.index.date:
                    next_day_price = market_data.loc[market_data.index.date == check_date.date(), 'Close'].iloc[0]
                    break

            return ingress_price, next_day_price

        except Exception as e:
            logger.warning(f"Price lookup failed: {e}")
            return None, None

    def _store_ingress_results(self, symbol: str, market_name: str, planet: str, sign: str,
                              start_date: str, end_date: str, results: Dict, ingress_dates: List):
        """Store ingress results in planetary_patterns table"""

        conn = get_db_connection()
        cursor = conn.cursor()

        pattern_name = f"{planet.title()} Ingress into {sign.title()}"

        # Store with ingress-specific fields
        cursor.execute("""
            INSERT INTO planetary_patterns (
                market_symbol, symbol, planet1, planet2, aspect_type, orb_size,
                start_date, end_date, phase, zodiac_sign, ingress_date,
                total_trades, avg_return_pct, win_rate, best_return_pct, worst_return_pct,
                accuracy_rate, pattern_name, total_aspects_found, backtest_version
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (market_symbol, planet1, planet2, aspect_type, phase, zodiac_sign, orb_size, start_date, end_date)
            DO UPDATE SET
                total_trades = EXCLUDED.total_trades,
                avg_return_pct = EXCLUDED.avg_return_pct,
                win_rate = EXCLUDED.win_rate,
                best_return_pct = EXCLUDED.best_return_pct,
                worst_return_pct = EXCLUDED.worst_return_pct,
                accuracy_rate = EXCLUDED.accuracy_rate,
                updated_at = CURRENT_TIMESTAMP
        """, (
            f"{market_name}_DAILY", symbol, planet.lower(), None, 'ingress', None,
            start_date, end_date, sign.lower(), sign.lower(),
            ingress_dates[0]['ingress_date'].date() if ingress_dates else None,
            int(results['total_trades']), float(results['avg_return_pct']),
            float(results['win_rate']), float(results['best_return_pct']),
            float(results['worst_return_pct']), float(results['win_rate']),
            pattern_name, int(len(ingress_dates)), 'v1.0'
        ))

        conn.commit()
        cursor.close()
        conn.close()

        logger.info(f"✅ Stored ingress results for {planet} into {sign}")

# In-memory storage for request tracking (in production, use Redis/DB)
active_requests: Dict[str, Dict] = {}

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'financial_postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', '')
    )

def validate_market_data(symbol: str, market_name: str, start_date: str = None, end_date: str = None):
    """Check if market data exists for the given symbol"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check multiple possible symbol formats
    possible_symbols = [
        symbol,
        f"{market_name}_DAILY",
        f"{market_name}_FUTURES",
        f"{symbol}_DAILY",
        market_name
    ]

    data_found = {}
    for sym in possible_symbols:
        # Check market_data table
        cursor.execute("""
            SELECT COUNT(*), MIN(trade_date), MAX(trade_date)
            FROM market_data
            WHERE symbol = %s
        """, (sym,))
        result = cursor.fetchone()

        if result and result[0] > 0:
            data_found[sym] = {
                'table': 'market_data',
                'count': result[0],
                'start_date': result[1],
                'end_date': result[2]
            }


    cursor.close()
    conn.close()

    return data_found

def validate_astrological_data(start_date: str = None, end_date: str = None):
    """Check if astrological data exists for the date range"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check planetary positions
    cursor.execute("""
        SELECT COUNT(*), MIN(trade_date), MAX(trade_date)
        FROM daily_planetary_positions
    """)
    positions_result = cursor.fetchone()

    # Check planetary aspects
    cursor.execute("""
        SELECT COUNT(*), MIN(trade_date), MAX(trade_date)
        FROM daily_planetary_aspects
    """)
    aspects_result = cursor.fetchone()

    cursor.close()
    conn.close()

    return {
        'planetary_positions': {
            'count': positions_result[0] if positions_result else 0,
            'start_date': positions_result[1] if positions_result else None,
            'end_date': positions_result[2] if positions_result else None
        },
        'planetary_aspects': {
            'count': aspects_result[0] if aspects_result else 0,
            'start_date': aspects_result[1] if aspects_result else None,
            'end_date': aspects_result[2] if aspects_result else None
        }
    }

@app.get("/")
async def root():
    return {
        "service": "Real Backtesting Service",
        "status": "running",
        "version": "2.0.0",
        "active_requests": len(active_requests),
        "features": ["real_analysis", "data_validation", "all_timing_type", "enhanced_daily_lunar_tester"]
    }

@app.get("/health")
async def health_check():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {e}")

@app.post("/backtest", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    """Run backtesting analysis - handles both lunar and planetary backtests"""

    # Validate backtest_type
    if request.backtest_type not in ['lunar', 'planetary', 'ingress']:
        raise HTTPException(
            status_code=400,
            detail="backtest_type must be 'lunar', 'planetary', or 'ingress'"
        )

    # Validate type-specific required fields
    if request.backtest_type == 'lunar':
        if request.timing_type not in ['same_day', 'next_day', 'all']:
            raise HTTPException(
                status_code=400,
                detail="timing_type must be 'same_day', 'next_day', or 'all' for lunar backtests"
            )
    elif request.backtest_type == 'planetary':
        if not request.planet1 or not request.planet2:
            raise HTTPException(
                status_code=400,
                detail="planet1 and planet2 are required for planetary backtests"
            )
        if not request.start_date or not request.end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date and end_date are required for planetary backtests"
            )
    elif request.backtest_type == 'ingress':
        if not request.planet:
            raise HTTPException(
                status_code=400,
                detail="planet is required for ingress backtests"
            )
        if not request.zodiac_signs:
            raise HTTPException(
                status_code=400,
                detail="zodiac_signs are required for ingress backtests"
            )
        if not request.start_date or not request.end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date and end_date are required for ingress backtests"
            )

    # Generate request ID
    if request.backtest_type == 'lunar':
        request_id = f"{request.symbol}_{request.timing_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    elif request.backtest_type == 'planetary':
        request_id = f"{request.symbol}_{request.planet1}_{request.planet2}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    else:  # ingress
        request_id = f"{request.symbol}_{request.planet}_ingress_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Pre-validate data availability
    try:
        market_data = validate_market_data(request.symbol, request.market_name, request.start_date, request.end_date)
        astro_data = validate_astrological_data(request.start_date, request.end_date)

        if not market_data:
            return BacktestResponse(
                request_id=request_id,
                status="failed",
                message=f"No market data found for {request.market_name} ({request.symbol}). Available symbols can be checked via /data/summary endpoint.",
                data_summary={
                    "market_data_found": False,
                    "searched_symbols": [request.symbol, f"{request.market_name}_DAILY", f"{request.market_name}_FUTURES"],
                    "astrological_data": astro_data
                }
            )

        # Track request
        active_requests[request_id] = {
            "status": "starting",
            "request": request.dict(),
            "start_time": datetime.now(),
            "data_summary": {
                "market_data": market_data,
                "astrological_data": astro_data
            }
        }

    except Exception as e:
        logger.error(f"Data validation failed: {e}")
        return BacktestResponse(
            request_id=request_id,
            status="failed",
            message=f"Data validation failed: {str(e)}"
        )

    # Route to appropriate backtest handler
    if request.backtest_type == 'lunar':
        background_tasks.add_task(execute_lunar_backtest, request_id, request)
        message = f"Lunar backtesting started for {request.market_name} ({request.timing_type}) with EnhancedDailyLunarTester"
    elif request.backtest_type == 'planetary':
        background_tasks.add_task(execute_planetary_backtest, request_id, request)
        message = f"Planetary backtesting started for {request.market_name} ({request.planet1}-{request.planet2}) with PlanetaryBacktester"
    else:  # ingress
        background_tasks.add_task(execute_ingress_backtest, request_id, request)
        message = f"Ingress backtesting started for {request.market_name} ({request.planet} into {request.zodiac_signs}) with PlanetaryIngressBacktester"

    return BacktestResponse(
        request_id=request_id,
        status="accepted",
        message=message,
        data_summary=active_requests[request_id]["data_summary"]
    )

@app.get("/backtest/{request_id}", response_model=BacktestResponse)
async def get_backtest_status(request_id: str):
    """Get status of a backtesting request"""

    if request_id not in active_requests:
        raise HTTPException(status_code=404, detail="Request not found")

    request_info = active_requests[request_id]
    return BacktestResponse(
        request_id=request_id,
        status=request_info["status"],
        message=request_info.get("message", ""),
        patterns_found=request_info.get("patterns_found"),
        best_pattern=request_info.get("best_pattern"),
        execution_time_seconds=request_info.get("execution_time"),
        data_summary=request_info.get("data_summary")
    )

@app.get("/requests")
async def list_active_requests():
    """List all active/recent requests"""
    return {
        "active_requests": len(active_requests),
        "requests": [
            {
                "request_id": req_id,
                "status": info["status"],
                "symbol": info["request"]["symbol"],
                "timing_type": info["request"]["timing_type"],
                "start_time": info["start_time"].isoformat(),
                "has_data": bool(info.get("data_summary", {}).get("market_data"))
            }
            for req_id, info in active_requests.items()
        ]
    }

@app.get("/data/summary")
async def get_data_summary():
    """Get summary of available market and astrological data"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Get available market symbols
        cursor.execute("""
            SELECT symbol, COUNT(*), MIN(trade_date), MAX(trade_date)
            FROM market_data
            GROUP BY symbol
            ORDER BY symbol
        """)
        market_symbols = [
            {
                "symbol": row[0],
                "count": row[1],
                "start_date": row[2].isoformat() if row[2] else None,
                "end_date": row[3].isoformat() if row[3] else None
            }
            for row in cursor.fetchall()
        ]

        # Get intraday symbols
        cursor.execute("""
            SELECT symbol, COUNT(*), MIN(datetime::date), MAX(datetime::date)
            FROM market_data_intraday
            GROUP BY symbol
            ORDER BY symbol
        """)
        intraday_symbols = [
            {
                "symbol": row[0],
                "count": row[1],
                "start_date": row[2].isoformat() if row[2] else None,
                "end_date": row[3].isoformat() if row[3] else None
            }
            for row in cursor.fetchall()
        ]

        # Get astrological data summary
        astro_data = validate_astrological_data()

        cursor.close()
        conn.close()

        return {
            "market_data": market_symbols,
            "intraday_data": intraday_symbols,
            "astrological_data": astro_data,
            "total_market_symbols": len(market_symbols),
            "total_intraday_symbols": len(intraday_symbols)
        }

    except Exception as e:
        logger.error(f"Failed to get data summary: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.get("/patterns/summary")
async def get_patterns_summary():
    """Get summary of all stored patterns"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                market_symbol,
                timing_type,
                COUNT(*) as total_patterns,
                MAX(accuracy_rate) as best_accuracy,
                (SELECT pattern_name FROM lunar_patterns lp2
                 WHERE lp2.market_symbol = lp.market_symbol
                 AND lp2.timing_type = lp.timing_type
                 ORDER BY accuracy_rate DESC LIMIT 1) as best_pattern_name
            FROM lunar_patterns lp
            GROUP BY market_symbol, timing_type
            ORDER BY market_symbol, timing_type
        """)

        results = cursor.fetchall()
        cursor.close()
        conn.close()

        summaries = []
        for market_symbol, timing_type, total_patterns, best_accuracy, best_pattern_name in results:
            summaries.append(PatternSummary(
                symbol=market_symbol,
                market_name=market_symbol.replace('_DAILY', '').replace('_FUTURES', ''),
                timing_type=timing_type,
                total_patterns=total_patterns,
                best_accuracy=float(best_accuracy) if best_accuracy else 0.0,
                best_pattern_name=best_pattern_name or "None",
                analysis_date=datetime.now().date().isoformat()
            ))

        return {"summaries": summaries}

    except Exception as e:
        logger.error(f"Failed to get pattern summary: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

async def execute_lunar_backtest(request_id: str, request: BacktestRequest):
    """Execute real backtesting analysis using EnhancedDailyLunarTester"""
    try:
        active_requests[request_id]["status"] = "running"
        active_requests[request_id]["message"] = "Running real lunar pattern analysis with EnhancedDailyLunarTester..."

        logger.info(f"🚀 Starting REAL backtest {request_id}: {request.symbol} ({request.timing_type})")

        start_time = datetime.now()

        # Validate market data exists
        market_data = validate_market_data(request.symbol, request.market_name)
        if not market_data:
            active_requests[request_id].update({
                "status": "failed",
                "message": f"No market data found for {request.market_name} ({request.symbol}). Cannot perform lunar pattern analysis."
            })
            return

        # Run analysis for each timing type
        timing_types = []
        if request.timing_type == "all":
            timing_types = ["same_day", "next_day"]
        else:
            timing_types = [request.timing_type]

        total_patterns_found = 0
        best_pattern = None
        best_accuracy = 0.0

        for timing_type in timing_types:
            logger.info(f"🌙 Running {timing_type} analysis for {request.market_name}")

            # Create tester with custom parameters
            tester = EnhancedDailyLunarTester(timing_type=timing_type)

            # Override thresholds if provided
            if request.accuracy_threshold:
                tester.ACCURACY_THRESHOLD = request.accuracy_threshold
            if request.min_occurrences:
                tester.MIN_OCCURRENCES = request.min_occurrences

            # Get patterns count before analysis (use separate connection)
            conn_before = get_db_connection()
            cursor_before = conn_before.cursor()
            cursor_before.execute("""
                SELECT COUNT(*) FROM lunar_patterns
                WHERE market_symbol = %s AND timing_type = %s
            """, (f"{request.market_name}_DAILY", timing_type))
            patterns_before = cursor_before.fetchone()[0]
            cursor_before.close()
            conn_before.close()

            # Run the REAL analysis
            tester.run_analysis(request.symbol, request.market_name)

            # Get patterns count after analysis (use separate connection)
            conn_after = get_db_connection()
            cursor_after = conn_after.cursor()
            cursor_after.execute("""
                SELECT COUNT(*) FROM lunar_patterns
                WHERE market_symbol = %s AND timing_type = %s
            """, (f"{request.market_name}_DAILY", timing_type))
            patterns_after = cursor_after.fetchone()[0]
            new_patterns = patterns_after - patterns_before

            total_patterns_found += new_patterns

            # Get best pattern for this timing type
            cursor_after.execute("""
                SELECT pattern_name, accuracy_rate
                FROM lunar_patterns
                WHERE market_symbol = %s AND timing_type = %s
                ORDER BY accuracy_rate DESC LIMIT 1
            """, (f"{request.market_name}_DAILY", timing_type))
            result = cursor_after.fetchone()

            if result and result[1] > best_accuracy:
                best_accuracy = result[1]
                best_pattern = {
                    "name": result[0],
                    "accuracy": float(result[1]),
                    "timing_type": timing_type
                }
            cursor_after.close()
            conn_after.close()


            logger.info(f"✅ Completed {timing_type} analysis: {new_patterns} new patterns found")

        execution_time = (datetime.now() - start_time).total_seconds()

        # Update final status
        active_requests[request_id].update({
            "status": "completed",
            "message": f"Real analysis completed using EnhancedDailyLunarTester. Found {total_patterns_found} new patterns.",
            "patterns_found": total_patterns_found,
            "best_pattern": best_pattern,
            "execution_time": execution_time
        })

        logger.info(f"✅ Completed REAL backtest {request_id}: {total_patterns_found} patterns found")

    except Exception as e:
        logger.error(f"❌ Real backtest {request_id} failed: {e}", exc_info=True)
        active_requests[request_id].update({
            "status": "failed",
            "message": f"Real analysis failed: {str(e)}"
        })

async def execute_planetary_backtest(request_id: str, request: BacktestRequest):
    """Execute planetary backtesting analysis and store results in planetary_patterns table"""
    try:
        active_requests[request_id]["status"] = "running"
        active_requests[request_id]["message"] = f"Running planetary backtest for {request.planet1}-{request.planet2}..."

        logger.info(f"🪐 Starting planetary backtest {request_id}: {request.symbol} ({request.planet1}-{request.planet2})")

        start_time = datetime.now()

        # Create PlanetaryBacktester instance
        backtester = PlanetaryBacktester()

        # Run the backtest
        results = backtester.run_backtest(
            symbol=request.symbol,
            market_name=request.market_name,
            planet1=request.planet1,
            planet2=request.planet2,
            aspect_types=request.aspect_types,
            orb_size=request.orb_size,
            start_date=request.start_date,
            end_date=request.end_date
        )

        execution_time = (datetime.now() - start_time).total_seconds()

        # Calculate summary statistics
        total_aspects_found = sum(r.get('total_aspects', 0) for r in results.values())
        total_trades = sum(r['approaching_phase']['total_trades'] + r['separating_phase']['total_trades']
                          for r in results.values())

        # Find best performing aspect/phase combination
        best_performance = {'avg_return': -float('inf'), 'aspect': None, 'phase': None}
        for aspect, data in results.items():
            for phase in ['approaching_phase', 'separating_phase']:
                phase_data = data[phase]
                if phase_data['total_trades'] > 0 and phase_data['avg_return_pct'] > best_performance['avg_return']:
                    best_performance.update({
                        'avg_return': phase_data['avg_return_pct'],
                        'aspect': aspect,
                        'phase': phase.replace('_phase', ''),
                        'win_rate': phase_data['win_rate'],
                        'trades': phase_data['total_trades']
                    })

        # Update final status
        active_requests[request_id].update({
            "status": "completed",
            "message": f"Planetary backtest completed. Found {total_aspects_found} aspect periods, {total_trades} total trades.",
            "patterns_found": total_aspects_found,
            "best_pattern": {
                "name": f"{request.planet1.title()}-{request.planet2.title()} {best_performance['aspect'].title()} ({best_performance['phase'].title()})",
                "avg_return": best_performance['avg_return'],
                "win_rate": best_performance['win_rate'],
                "trades": best_performance['trades']
            } if best_performance['aspect'] else None,
            "execution_time": execution_time,
            "total_aspects": total_aspects_found,
            "total_trades": total_trades,
            "insights_saved": True
        })

        logger.info(f"✅ Completed planetary backtest {request_id}: {total_aspects_found} aspects, {total_trades} trades")

    except Exception as e:
        logger.error(f"❌ Planetary backtest {request_id} failed: {e}", exc_info=True)
        active_requests[request_id].update({
            "status": "failed",
            "message": f"Planetary analysis failed: {str(e)}"
        })

async def execute_ingress_backtest(request_id: str, request: BacktestRequest):
    """Execute planetary ingress backtesting analysis and store results in planetary_patterns table"""
    try:
        active_requests[request_id]["status"] = "running"
        active_requests[request_id]["message"] = f"Running ingress backtest for {request.planet} into {request.zodiac_signs}..."

        logger.info(f"🌟 Starting ingress backtest {request_id}: {request.symbol} ({request.planet} into {request.zodiac_signs})")

        start_time = datetime.now()

        # Create PlanetaryIngressBacktester instance
        backtester = PlanetaryIngressBacktester()

        # Run the ingress backtest
        results = backtester.run_ingress_backtest(
            symbol=request.symbol,
            market_name=request.market_name,
            planet=request.planet,
            zodiac_signs=request.zodiac_signs,
            start_date=request.start_date,
            end_date=request.end_date
        )

        execution_time = (datetime.now() - start_time).total_seconds()

        # Calculate summary statistics
        total_ingress_events = sum(r.get('ingress_events', 0) for r in results.values())
        total_trades = sum(r['results']['total_trades'] for r in results.values())

        # Find best performing planet/sign combination
        best_performance = {'avg_return': -float('inf'), 'planet': None, 'sign': None}
        for pattern_key, data in results.items():
            if data['results']['total_trades'] > 0 and data['results']['avg_return_pct'] > best_performance['avg_return']:
                best_performance.update({
                    'avg_return': data['results']['avg_return_pct'],
                    'planet': data['planet'],
                    'sign': data['zodiac_sign'],
                    'win_rate': data['results']['win_rate'],
                    'trades': data['results']['total_trades']
                })

        # Update final status
        active_requests[request_id].update({
            "status": "completed",
            "message": f"Ingress backtest completed. Found {total_ingress_events} ingress events, {total_trades} total trades.",
            "patterns_found": total_ingress_events,
            "best_pattern": {
                "name": f"{best_performance['planet'].title()} Ingress into {best_performance['sign'].title()}",
                "avg_return": best_performance['avg_return'],
                "win_rate": best_performance['win_rate'],
                "trades": best_performance['trades']
            } if best_performance['planet'] else None,
            "execution_time": execution_time,
            "total_ingress_events": total_ingress_events,
            "total_trades": total_trades,
            "insights_saved": True
        })

        logger.info(f"✅ Completed ingress backtest {request_id}: {total_ingress_events} events, {total_trades} trades")

    except Exception as e:
        logger.error(f"❌ Ingress backtest {request_id} failed: {e}", exc_info=True)
        active_requests[request_id].update({
            "status": "failed",
            "message": f"Ingress analysis failed: {str(e)}"
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backtesting_service:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )