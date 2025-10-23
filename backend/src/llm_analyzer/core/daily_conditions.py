"""
Daily astrological conditions calculator using Swiss Ephemeris.
Calculates planetary positions and aspects for trading analysis.

Usage Examples:

1. LOCAL EXECUTION:
   # Set environment variables first
   export DB_HOST=your-db-host
   export DB_NAME=your-db-name
   export DB_USER=your-db-user
   export DB_PASSWORD=your-db-password

   # Run for today
   python3 scripts/llm_analysis/run_daily_conditions.py

   # Run for specific date
   python3 scripts/llm_analysis/run_daily_conditions.py --date 2024-01-15

   # Run for date range
   python3 scripts/llm_analysis/run_daily_conditions.py --start-date 2024-01-01 --end-date 2024-01-31

   # Display only (no database storage)
   python3 scripts/llm_analysis/run_daily_conditions.py --display-only

2. EKS/KUBERNETES EXECUTION:
   # Apply the daily conditions cron job
   kubectl apply -f deploy/k8s/shared/daily-conditions-job.yaml

   # Run one-time job manually
   kubectl create job manual-daily-conditions --from=cronjob/daily-conditions -n time-series-indexing

   # Check job status
   kubectl get jobs -n time-series-indexing

   # View logs
   kubectl logs job/manual-daily-conditions -n time-series-indexing

3. LOCAL TESTING (No Database):
   # Save to file for local testing
   python3 scripts/llm_analysis/run_daily_conditions.py --output-file /tmp/conditions.json

   # Test calculation only (display without storing)
   python3 scripts/llm_analysis/run_daily_conditions.py --display-only

   # Test database connection only
   python3 scripts/llm_analysis/run_daily_conditions.py --test-db

4. DEBUGGING:
   # Test with verbose output
   python3 scripts/llm_analysis/run_daily_conditions.py --verbose --display-only

   # Verbose with file output
   python3 scripts/llm_analysis/run_daily_conditions.py --verbose --output-file /tmp/debug_conditions.json

5. DIRECT USAGE IN CODE:
   ```python
   from llm_analyzer.core.daily_conditions import DailyAstrologyCalculator
   from datetime import date

   calc = DailyAstrologyCalculator()
   conditions = calc.calculate_daily_conditions(date.today())
   success = calc.store_daily_conditions(conditions)
   ```

Troubleshooting:
- If planetary_positions/major_aspects are NULL: Check JSON serialization and Swiss Ephemeris installation
- If connection fails: Verify DB_* environment variables
- If Swiss Ephemeris errors: Ensure pyswisseph is installed (pip install pyswisseph)
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

    def validate_calculated_data(self, conditions: Dict[str, Any]) -> bool:
        """Validate that calculated data is complete and serializable."""
        try:
            # Check required fields
            required_fields = ['trade_date', 'planetary_positions', 'major_aspects']
            for field in required_fields:
                if field not in conditions:
                    logger.error(f"❌ Missing required field: {field}")
                    return False

            # Check planetary positions
            positions = conditions['planetary_positions']
            if not isinstance(positions, dict) or len(positions) == 0:
                logger.error(f"❌ Invalid planetary_positions: {type(positions)}, length: {len(positions)}")
                return False

            # Count valid positions
            valid_positions = 0
            for planet, data in positions.items():
                if isinstance(data, dict) and 'error' not in data:
                    valid_positions += 1

            if valid_positions < 3:  # Should have at least Sun, Moon, Mercury
                logger.warning(f"⚠️ Only {valid_positions} valid planetary positions")
                return False

            # Check major aspects
            aspects = conditions['major_aspects']
            if not isinstance(aspects, list):
                logger.error(f"❌ Invalid major_aspects type: {type(aspects)}")
                return False

            # Test JSON serialization
            try:
                json.dumps(positions)
                json.dumps(aspects)
            except (TypeError, ValueError) as e:
                logger.error(f"❌ JSON serialization failed: {e}")
                return False

            logger.debug(f"✅ Validation passed: {valid_positions} planets, {len(aspects)} aspects")
            return True

        except Exception as e:
            logger.error(f"❌ Validation error: {e}")
            return False

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
        """Store daily conditions in normalized database schema."""
        try:
            # Validate data before storing
            if not self.validate_calculated_data(conditions):
                logger.error(f"❌ Data validation failed for {conditions.get('trade_date', 'unknown date')}")
                return False

            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            logger.debug(f"🔍 Storing normalized data for {conditions['trade_date']}")

            # Step 1: Insert/update main conditions record
            cursor.execute("""
                INSERT INTO daily_astrological_conditions (
                    trade_date, planetary_positions, lunar_phase_name,
                    lunar_phase_angle, significant_events, daily_score, market_outlook
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (trade_date) DO UPDATE SET
                    planetary_positions = EXCLUDED.planetary_positions,
                    lunar_phase_name = EXCLUDED.lunar_phase_name,
                    lunar_phase_angle = EXCLUDED.lunar_phase_angle,
                    significant_events = EXCLUDED.significant_events,
                    daily_score = EXCLUDED.daily_score,
                    market_outlook = EXCLUDED.market_outlook,
                    created_at = NOW()
                RETURNING id
            """, (
                conditions['trade_date'],
                json.dumps(conditions['planetary_positions']),  # Keep JSONB as backup
                conditions['lunar_phase_name'],
                conditions['lunar_phase_angle'],
                conditions['significant_events'],
                conditions['daily_score'],
                conditions['market_outlook']
            ))

            conditions_id = cursor.fetchone()[0]
            logger.debug(f"   Main record ID: {conditions_id}")

            # Step 2: Store normalized planetary positions
            positions_count = self._store_planetary_positions(cursor, conditions_id, conditions)

            # Step 3: Store normalized aspects
            aspects_count = self._store_planetary_aspects(cursor, conditions_id, conditions)

            # Step 4: Calculate and store harmonic analysis
            harmonic_success = self._store_harmonic_analysis(cursor, conditions_id, conditions)

            conn.commit()
            cursor.close()
            conn.close()

            logger.info(f"💾 Stored normalized data for {conditions['trade_date']}: {positions_count} positions, {aspects_count} aspects")
            return True

        except Exception as e:
            logger.error(f"❌ Error storing daily conditions: {e}")
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
            return False

    def _store_planetary_positions(self, cursor, conditions_id: int, conditions: Dict[str, Any]) -> int:
        """Store normalized planetary positions."""
        try:
            # Delete existing positions for this date
            cursor.execute("""
                DELETE FROM daily_planetary_positions
                WHERE conditions_id = %s
            """, (conditions_id,))

            positions_stored = 0
            for planet_name, position_data in conditions['planetary_positions'].items():
                if 'error' in position_data:
                    logger.warning(f"   Skipping {planet_name} due to calculation error")
                    continue

                cursor.execute("""
                    INSERT INTO daily_planetary_positions (
                        conditions_id, trade_date, planet, longitude, latitude,
                        zodiac_sign, degree_in_sign, is_retrograde
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    conditions_id,
                    conditions['trade_date'],
                    planet_name,
                    position_data['longitude'],
                    0.0,  # latitude - placeholder for now
                    position_data['sign'],
                    position_data['degree_in_sign'],
                    False  # is_retrograde - placeholder for now
                ))
                positions_stored += 1

            logger.debug(f"   Stored {positions_stored} planetary positions")
            return positions_stored

        except Exception as e:
            logger.error(f"❌ Error storing planetary positions: {e}")
            return 0

    def _store_planetary_aspects(self, cursor, conditions_id: int, conditions: Dict[str, Any]) -> int:
        """Store normalized planetary aspects."""
        try:
            # Delete existing aspects for this date
            cursor.execute("""
                DELETE FROM daily_planetary_aspects
                WHERE conditions_id = %s
            """, (conditions_id,))

            aspects_stored = 0
            for aspect in conditions['major_aspects']:
                # Ensure alphabetical planet ordering
                planet1 = min(aspect['planet1'], aspect['planet2'])
                planet2 = max(aspect['planet1'], aspect['planet2'])

                cursor.execute("""
                    INSERT INTO daily_planetary_aspects (
                        conditions_id, trade_date, planet1, planet2, aspect_type,
                        orb, separating_angle, is_exact, is_tight
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    conditions_id,
                    conditions['trade_date'],
                    planet1,
                    planet2,
                    aspect['aspect'],
                    aspect['orb'],
                    aspect['separating_angle'],
                    aspect.get('exact', False),
                    aspect['orb'] < 3.0  # is_tight if orb < 3 degrees
                ))
                aspects_stored += 1

            logger.debug(f"   Stored {aspects_stored} planetary aspects")
            return aspects_stored

        except Exception as e:
            logger.error(f"❌ Error storing planetary aspects: {e}")
            return 0

    def _store_harmonic_analysis(self, cursor, conditions_id: int, conditions: Dict[str, Any]) -> bool:
        """Calculate and store harmonic analysis."""
        try:
            # Delete existing harmonic analysis for this date
            cursor.execute("""
                DELETE FROM daily_harmonic_analysis
                WHERE conditions_id = %s
            """, (conditions_id,))

            # Calculate harmonic metrics
            aspects = conditions['major_aspects']
            positions = conditions['planetary_positions']

            # Count aspect types
            harmonious_aspects = len([a for a in aspects if a['aspect'] in ['trine', 'sextile']])
            challenging_aspects = len([a for a in aspects if a['aspect'] in ['square', 'opposition']])
            neutral_aspects = len([a for a in aspects if a['aspect'] == 'conjunction'])
            total_aspects = len(aspects)

            # Calculate ratios
            harmony_ratio = harmonious_aspects / total_aspects if total_aspects > 0 else 0
            tension_ratio = challenging_aspects / total_aspects if total_aspects > 0 else 0

            # Count elemental distribution
            element_counts = {'fire': 0, 'earth': 0, 'air': 0, 'water': 0}
            modal_counts = {'cardinal': 0, 'fixed': 0, 'mutable': 0}

            for planet_name, position_data in positions.items():
                if 'error' in position_data:
                    continue
                sign = position_data['sign']
                element = self._get_element_for_sign(sign)
                modality = self._get_modality_for_sign(sign)

                if element:
                    element_counts[element] += 1
                if modality:
                    modal_counts[modality] += 1

            # Calculate balance scores
            total_planets = sum(element_counts.values())
            elemental_balance = self._calculate_balance_score(element_counts.values())
            modal_balance = self._calculate_balance_score(modal_counts.values())

            # Calculate outer planet emphasis
            outer_planets = ['Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto']
            outer_planet_aspects = len([a for a in aspects if
                                     a['planet1'] in outer_planets or a['planet2'] in outer_planets])
            inner_planet_aspects = total_aspects - outer_planet_aspects

            # Store harmonic analysis
            cursor.execute("""
                INSERT INTO daily_harmonic_analysis (
                    conditions_id, trade_date, total_aspects, harmonious_aspects,
                    challenging_aspects, neutral_aspects, harmony_ratio, tension_ratio,
                    overall_harmony_score, fire_planets, earth_planets, air_planets,
                    water_planets, elemental_balance_score, cardinal_planets, fixed_planets,
                    mutable_planets, modal_balance_score, outer_planet_aspects,
                    inner_planet_aspects
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                conditions_id,
                conditions['trade_date'],
                total_aspects,
                harmonious_aspects,
                challenging_aspects,
                neutral_aspects,
                harmony_ratio,
                tension_ratio,
                int(conditions['daily_score']),  # Use existing daily score
                element_counts['fire'],
                element_counts['earth'],
                element_counts['air'],
                element_counts['water'],
                elemental_balance,
                modal_counts['cardinal'],
                modal_counts['fixed'],
                modal_counts['mutable'],
                modal_balance,
                outer_planet_aspects,
                inner_planet_aspects
            ))

            logger.debug(f"   Stored harmonic analysis: {harmony_ratio:.2f} harmony ratio, {elemental_balance:.2f} elemental balance")
            return True

        except Exception as e:
            logger.error(f"❌ Error storing harmonic analysis: {e}")
            return False

    def _get_element_for_sign(self, sign: str) -> str:
        """Get astrological element for zodiac sign."""
        element_map = {
            'Aries': 'fire', 'Leo': 'fire', 'Sagittarius': 'fire',
            'Taurus': 'earth', 'Virgo': 'earth', 'Capricorn': 'earth',
            'Gemini': 'air', 'Libra': 'air', 'Aquarius': 'air',
            'Cancer': 'water', 'Scorpio': 'water', 'Pisces': 'water'
        }
        return element_map.get(sign)

    def _get_modality_for_sign(self, sign: str) -> str:
        """Get astrological modality for zodiac sign."""
        modality_map = {
            'Aries': 'cardinal', 'Cancer': 'cardinal', 'Libra': 'cardinal', 'Capricorn': 'cardinal',
            'Taurus': 'fixed', 'Leo': 'fixed', 'Scorpio': 'fixed', 'Aquarius': 'fixed',
            'Gemini': 'mutable', 'Virgo': 'mutable', 'Sagittarius': 'mutable', 'Pisces': 'mutable'
        }
        return modality_map.get(sign)

    def _calculate_balance_score(self, counts) -> float:
        """Calculate balance score (0-1) for distribution."""
        counts_list = list(counts)
        total = sum(counts_list)
        if total == 0:
            return 0.0

        # Perfect balance would be equal distribution
        expected = total / len(counts_list)
        variance = sum((count - expected) ** 2 for count in counts_list) / len(counts_list)
        max_variance = expected ** 2 * (len(counts_list) - 1) / len(counts_list) + (total - expected) ** 2 / len(counts_list)

        if max_variance == 0:
            return 1.0

        return max(0.0, 1.0 - (variance / max_variance))

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

    def save_conditions_to_file(self, conditions: Dict[str, Any], file_path: str) -> bool:
        """Save daily conditions to a JSON file for local testing."""
        try:
            # Validate data first
            if not self.validate_calculated_data(conditions):
                logger.error(f"❌ Data validation failed for {conditions.get('trade_date', 'unknown date')}")
                return False

            # Convert date to string for JSON serialization
            conditions_copy = conditions.copy()
            conditions_copy['trade_date'] = str(conditions_copy['trade_date'])

            # Write to file
            with open(file_path, 'w') as f:
                json.dump(conditions_copy, f, indent=2, default=str)

            logger.info(f"💾 Saved conditions to file: {file_path}")
            return True

        except Exception as e:
            logger.error(f"❌ Error saving to file: {e}")
            return False

    def test_database_connection(self) -> bool:
        """Test database connection without storing data."""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            logger.info("✅ Database connection successful")
            return True

        except Exception as e:
            logger.warning(f"⚠️ Database connection failed: {e}")
            return False