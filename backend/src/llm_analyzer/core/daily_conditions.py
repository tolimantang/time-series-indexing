"""
Daily astrological conditions calculator using Swiss Ephemeris.
Calculates planetary positions and aspects for trading analysis.
"""

import os
import json
import logging
import psycopg2
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
import swisseph as swe

logger = logging.getLogger(__name__)


class DailyAstrologyCalculator:
    """Calculate daily astrological conditions for trading analysis."""

    def __init__(self, db_config: Optional[Dict[str, str]] = None):
        """Initialize with database configuration."""
        self.db_config = db_config or {
            'host': os.getenv('DB_HOST'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
        }

        # Planetary constants
        self.planets = {
            'Sun': swe.SUN,
            'Moon': swe.MOON,
            'Mercury': swe.MERCURY,
            'Venus': swe.VENUS,
            'Mars': swe.MARS,
            'Jupiter': swe.JUPITER,
            'Saturn': swe.SATURN,
            'Uranus': swe.URANUS,
            'Neptune': swe.NEPTUNE,
            'Pluto': swe.PLUTO
        }

        # Zodiac signs
        self.zodiac_signs = [
            'Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
            'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'
        ]

        # Set ephemeris path if available
        ephemeris_path = os.getenv('EPHEMERIS_PATH', '/opt/ephemeris')
        if os.path.exists(ephemeris_path):
            swe.set_ephe_path(ephemeris_path)

        logger.info("✅ Daily Astrology Calculator initialized")

    def calculate_planetary_positions(self, target_date: date) -> Dict[str, Any]:
        """Calculate planetary positions for a given date."""
        try:
            # Convert date to Julian Day
            jd = swe.julday(target_date.year, target_date.month, target_date.day, 12.0)  # Noon UTC

            positions = {}

            for planet_name, planet_id in self.planets.items():
                try:
                    # Calculate position
                    position_data = swe.calc_ut(jd, planet_id)
                    longitude = position_data[0][0]  # Longitude in degrees

                    # Convert to zodiac sign and degree
                    sign_index = int(longitude // 30)
                    degree_in_sign = longitude % 30

                    positions[planet_name] = {
                        'longitude': longitude,
                        'sign': self.zodiac_signs[sign_index],
                        'degree_in_sign': degree_in_sign,
                        'formatted': f"{degree_in_sign:.1f}° {self.zodiac_signs[sign_index]}"
                    }

                except Exception as e:
                    logger.warning(f"⚠️ Error calculating {planet_name} position: {e}")
                    positions[planet_name] = {'error': str(e)}

            logger.info(f"📊 Calculated positions for {len(positions)} planets on {target_date}")
            return positions

        except Exception as e:
            logger.error(f"❌ Error calculating planetary positions: {e}")
            return {}

    def calculate_lunar_phase(self, target_date: date) -> Dict[str, Any]:
        """Calculate lunar phase information."""
        try:
            jd = swe.julday(target_date.year, target_date.month, target_date.day, 12.0)

            # Get Sun and Moon positions
            sun_pos = swe.calc_ut(jd, swe.SUN)[0][0]
            moon_pos = swe.calc_ut(jd, swe.MOON)[0][0]

            # Calculate phase angle
            phase_angle = (moon_pos - sun_pos) % 360

            # Determine phase name
            if phase_angle < 45:
                phase_name = "New Moon"
            elif phase_angle < 135:
                phase_name = "Waxing Moon"
            elif phase_angle < 225:
                phase_name = "Full Moon"
            else:
                phase_name = "Waning Moon"

            # Calculate illumination percentage
            illumination = (1 - abs(180 - phase_angle) / 180) * 100

            return {
                'phase_angle': phase_angle,
                'phase_name': phase_name,
                'illumination_percent': illumination,
                'is_new_moon': abs(phase_angle) < 15,
                'is_full_moon': abs(phase_angle - 180) < 15
            }

        except Exception as e:
            logger.error(f"❌ Error calculating lunar phase: {e}")
            return {}

    def calculate_major_aspects(self, positions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculate major planetary aspects."""
        aspects = []
        major_aspect_orbs = {
            'conjunction': 8,    # 0 degrees
            'opposition': 8,     # 180 degrees
            'trine': 6,          # 120 degrees
            'square': 6,         # 90 degrees
            'sextile': 4         # 60 degrees
        }

        planet_names = list(positions.keys())

        for i, planet1 in enumerate(planet_names):
            for planet2 in planet_names[i+1:]:
                if 'error' in positions[planet1] or 'error' in positions[planet2]:
                    continue

                pos1 = positions[planet1]['longitude']
                pos2 = positions[planet2]['longitude']

                # Calculate angular separation
                separation = abs(pos2 - pos1)
                if separation > 180:
                    separation = 360 - separation

                # Check for major aspects
                for aspect_name, target_angle in [
                    ('conjunction', 0), ('opposition', 180), ('trine', 120),
                    ('square', 90), ('sextile', 60)
                ]:
                    orb = major_aspect_orbs[aspect_name]
                    target = target_angle if target_angle == 0 or separation <= 180 else 180

                    if abs(separation - target) <= orb:
                        aspects.append({
                            'planet1': planet1,
                            'planet2': planet2,
                            'aspect': aspect_name,
                            'orb': abs(separation - target),
                            'exact': abs(separation - target) < 1,
                            'separating_angle': separation
                        })

        logger.info(f"🌟 Found {len(aspects)} major aspects")
        return aspects

    def calculate_daily_score(self, positions: Dict[str, Any], aspects: List[Dict[str, Any]],
                            lunar_phase: Dict[str, Any]) -> float:
        """Calculate overall daily astrological favorability score (0-100)."""
        score = 50.0  # Base score

        try:
            # Lunar phase scoring
            if lunar_phase.get('phase_name') == 'Waxing Moon':
                score += 10  # Generally favorable for growth
            elif lunar_phase.get('phase_name') == 'Full Moon':
                score += 5   # Peak energy but volatile
            elif lunar_phase.get('is_new_moon'):
                score += 8   # New beginnings

            # Mars aspects (volatility indicator)
            mars_aspects = [a for a in aspects if 'Mars' in [a['planet1'], a['planet2']]]
            for aspect in mars_aspects:
                if aspect['aspect'] in ['trine', 'sextile']:
                    score += 8  # Harmonious Mars energy
                elif aspect['aspect'] in ['square', 'opposition']:
                    score -= 5  # Challenging Mars energy

            # Jupiter aspects (expansion/optimism)
            jupiter_aspects = [a for a in aspects if 'Jupiter' in [a['planet1'], a['planet2']]]
            for aspect in jupiter_aspects:
                if aspect['aspect'] in ['trine', 'sextile', 'conjunction']:
                    score += 6  # Generally positive

            # Saturn aspects (restriction/discipline)
            saturn_aspects = [a for a in aspects if 'Saturn' in [a['planet1'], a['planet2']]]
            for aspect in saturn_aspects:
                if aspect['aspect'] in ['square', 'opposition']:
                    score -= 4  # Restrictive energy
                elif aspect['aspect'] in ['trine', 'sextile']:
                    score += 3  # Disciplined energy

            # Venus aspects (market sentiment)
            venus_aspects = [a for a in aspects if 'Venus' in [a['planet1'], a['planet2']]]
            for aspect in venus_aspects:
                if aspect['aspect'] in ['trine', 'sextile']:
                    score += 4  # Harmonious market sentiment

            # Exact aspects get bonus
            exact_aspects = [a for a in aspects if a.get('exact', False)]
            score += len(exact_aspects) * 2

            # Clamp score between 0 and 100
            score = max(0, min(100, score))

        except Exception as e:
            logger.warning(f"⚠️ Error calculating daily score: {e}")
            score = 50.0

        return round(score, 1)

    def determine_market_outlook(self, positions: Dict[str, Any], aspects: List[Dict[str, Any]],
                               daily_score: float) -> str:
        """Determine overall market outlook based on astrological conditions."""
        try:
            # Count challenging vs harmonious aspects
            challenging = len([a for a in aspects if a['aspect'] in ['square', 'opposition']])
            harmonious = len([a for a in aspects if a['aspect'] in ['trine', 'sextile']])

            # Check for Mars activity (volatility)
            mars_activity = len([a for a in aspects if 'Mars' in [a['planet1'], a['planet2']]])

            if daily_score >= 70:
                return 'bullish'
            elif daily_score <= 30:
                return 'bearish'
            elif mars_activity >= 3 or challenging > harmonious + 2:
                return 'volatile'
            else:
                return 'neutral'

        except Exception as e:
            logger.warning(f"⚠️ Error determining market outlook: {e}")
            return 'neutral'

    def get_significant_events(self, aspects: List[Dict[str, Any]],
                             lunar_phase: Dict[str, Any]) -> List[str]:
        """Identify significant astrological events for the day."""
        events = []

        try:
            # Exact aspects
            exact_aspects = [a for a in aspects if a.get('exact', False)]
            for aspect in exact_aspects:
                events.append(f"Exact {aspect['aspect']} between {aspect['planet1']} and {aspect['planet2']}")

            # Lunar phase events
            if lunar_phase.get('is_new_moon'):
                events.append("New Moon - New beginnings favored")
            elif lunar_phase.get('is_full_moon'):
                events.append("Full Moon - Peak energy, increased volatility")

            # Major outer planet aspects
            outer_planets = ['Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
            major_aspects = [a for a in aspects if
                           a['planet1'] in outer_planets and a['planet2'] in outer_planets and
                           a['orb'] < 2]
            for aspect in major_aspects:
                events.append(f"Close {aspect['aspect']} between {aspect['planet1']} and {aspect['planet2']}")

        except Exception as e:
            logger.warning(f"⚠️ Error getting significant events: {e}")

        return events

    def calculate_daily_conditions(self, target_date: date) -> Dict[str, Any]:
        """Calculate complete daily astrological conditions."""
        logger.info(f"🌟 Calculating daily conditions for {target_date}")

        # Calculate planetary positions
        positions = self.calculate_planetary_positions(target_date)
        if not positions:
            return {'error': 'Failed to calculate planetary positions'}

        # Calculate lunar phase
        lunar_phase = self.calculate_lunar_phase(target_date)

        # Calculate major aspects
        aspects = self.calculate_major_aspects(positions)

        # Calculate daily score
        daily_score = self.calculate_daily_score(positions, aspects, lunar_phase)

        # Determine market outlook
        market_outlook = self.determine_market_outlook(positions, aspects, daily_score)

        # Get significant events
        significant_events = self.get_significant_events(aspects, lunar_phase)

        conditions = {
            'trade_date': target_date,
            'planetary_positions': positions,
            'major_aspects': aspects,
            'lunar_phase_name': lunar_phase.get('phase_name'),
            'lunar_phase_angle': lunar_phase.get('phase_angle'),
            'significant_events': significant_events,
            'daily_score': daily_score,
            'market_outlook': market_outlook
        }

        logger.info(f"✅ Daily conditions calculated: {daily_score}/100 score, {market_outlook} outlook")
        return conditions

    def store_daily_conditions(self, conditions: Dict[str, Any]) -> bool:
        """Store daily conditions in database."""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO daily_astrological_conditions (
                    trade_date, planetary_positions, major_aspects, lunar_phase_name,
                    lunar_phase_angle, significant_events, daily_score, market_outlook
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (trade_date) DO UPDATE SET
                    planetary_positions = EXCLUDED.planetary_positions,
                    major_aspects = EXCLUDED.major_aspects,
                    lunar_phase_name = EXCLUDED.lunar_phase_name,
                    lunar_phase_angle = EXCLUDED.lunar_phase_angle,
                    significant_events = EXCLUDED.significant_events,
                    daily_score = EXCLUDED.daily_score,
                    market_outlook = EXCLUDED.market_outlook,
                    created_at = NOW()
            """, (
                conditions['trade_date'],
                json.dumps(conditions['planetary_positions']),
                json.dumps(conditions['major_aspects']),
                conditions['lunar_phase_name'],
                conditions['lunar_phase_angle'],
                conditions['significant_events'],
                conditions['daily_score'],
                conditions['market_outlook']
            ))

            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"💾 Stored daily conditions for {conditions['trade_date']}")
            return True

        except Exception as e:
            logger.error(f"❌ Error storing daily conditions: {e}")
            return False

    def calculate_and_store_date_range(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Calculate and store conditions for a range of dates."""
        logger.info(f"📅 Calculating conditions from {start_date} to {end_date}")

        current_date = start_date
        processed_count = 0
        error_count = 0

        while current_date <= end_date:
            try:
                conditions = self.calculate_daily_conditions(current_date)
                if 'error' not in conditions:
                    success = self.store_daily_conditions(conditions)
                    if success:
                        processed_count += 1
                    else:
                        error_count += 1
                else:
                    error_count += 1

                current_date += timedelta(days=1)

            except Exception as e:
                logger.error(f"❌ Error processing {current_date}: {e}")
                error_count += 1
                current_date += timedelta(days=1)

        summary = {
            'start_date': start_date,
            'end_date': end_date,
            'total_days': (end_date - start_date).days + 1,
            'processed_successfully': processed_count,
            'errors': error_count,
            'success_rate': processed_count / ((end_date - start_date).days + 1) * 100
        }

        logger.info(f"✅ Date range processing completed: {processed_count}/{summary['total_days']} days processed")
        return summary