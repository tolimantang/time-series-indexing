"""
Tests for the main AstroEncoder class.
"""

import pytest
from datetime import datetime, timezone
from astroEncoder import AstroEncoder
from astroEncoder.data_models import AstronomicalData, PlanetaryPosition, Aspect


class TestAstroEncoder:
    """Test the main AstroEncoder functionality."""

    @pytest.fixture
    def encoder(self):
        """Create an AstroEncoder instance for testing."""
        return AstroEncoder()

    @pytest.fixture
    def test_date(self):
        """A known date for testing: January 1, 2024, noon UTC."""
        return datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

    def test_encoder_initialization(self, encoder):
        """Test that encoder initializes correctly."""
        assert encoder is not None
        assert hasattr(encoder, 'PLANETS')
        assert hasattr(encoder, 'ASPECTS')
        assert len(encoder.PLANETS) == 10  # Sun through Pluto

    def test_encode_date_basic(self, encoder, test_date):
        """Test basic date encoding functionality."""
        result = encoder.encode_date(test_date)

        assert isinstance(result, AstronomicalData)
        assert result.date == test_date
        assert result.location == 'UTC (Greenwich)'
        assert len(result.positions) == 10  # All planets
        assert result.lunar_phase is not None

    def test_planetary_positions(self, encoder, test_date):
        """Test that planetary positions are calculated correctly."""
        result = encoder.encode_date(test_date)

        # Check that all planets have positions
        for planet_name in encoder.PLANETS.keys():
            assert planet_name in result.positions
            position = result.positions[planet_name]

            assert isinstance(position, PlanetaryPosition)
            assert position.planet == planet_name
            assert 0 <= position.longitude < 360
            assert position.sign in ['aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
                                   'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces']
            assert 0 <= position.degree_in_sign < 30
            assert position.degree_classification in ['early', 'middle', 'late']

    def test_aspects_calculation(self, encoder, test_date):
        """Test that aspects are calculated correctly."""
        result = encoder.encode_date(test_date)

        assert isinstance(result.aspects, list)
        assert len(result.aspects) > 0  # Should find some aspects

        for aspect in result.aspects:
            assert isinstance(aspect, Aspect)
            assert aspect.planet1 in encoder.PLANETS.keys()
            assert aspect.planet2 in encoder.PLANETS.keys()
            assert aspect.planet1 != aspect.planet2  # No self-aspects
            assert aspect.aspect_type in encoder.ASPECTS.keys()
            assert 0 <= aspect.orb <= 8  # Within maximum orb
            assert 0 <= aspect.exactness <= 1  # Exactness is normalized
            assert aspect.applying_separating in ['applying', 'separating', 'stationary']

    def test_houses_calculation(self, encoder, test_date):
        """Test house calculation."""
        result = encoder.encode_date(test_date, location='nyc', include_houses=True)

        assert result.houses is not None
        assert result.houses.system == 'placidus'
        assert result.houses.location == 'New York City'
        assert len(result.houses.house_cusps) == 12
        assert 0 <= result.houses.ascendant < 360
        assert 0 <= result.houses.midheaven < 360

        # Check that planets have house assignments
        for planet_name, position in result.positions.items():
            assert position.house is not None
            assert 1 <= position.house <= 12

    def test_custom_location(self, encoder, test_date):
        """Test encoding with custom location."""
        custom_loc = {'lat': 51.5074, 'lon': -0.1278, 'name': 'London Test'}
        result = encoder.encode_date(test_date, location='custom', custom_location=custom_loc)

        assert result.location == 'London Test'
        if result.houses:
            assert result.houses.latitude == 51.5074
            assert result.houses.longitude == -0.1278

    def test_significant_events_detection(self, encoder, test_date):
        """Test detection of significant astronomical events."""
        result = encoder.encode_date(test_date)

        assert isinstance(result.significant_events, list)
        # Note: We can't predict exactly what events will be detected,
        # but we can test the structure

    def test_lunar_phase_calculation(self, encoder, test_date):
        """Test lunar phase calculation."""
        result = encoder.encode_date(test_date)

        assert result.lunar_phase is not None
        assert 0 <= result.lunar_phase < 360

    def test_get_planet_position_method(self, encoder, test_date):
        """Test the get_planet_position method."""
        result = encoder.encode_date(test_date)

        sun_pos = result.get_planet_position('sun')
        assert sun_pos is not None
        assert sun_pos.planet == 'sun'

        # Test case insensitive
        sun_pos2 = result.get_planet_position('SUN')
        assert sun_pos2 is not None
        assert sun_pos2.planet == 'sun'

        # Test non-existent planet
        invalid_pos = result.get_planet_position('invalid')
        assert invalid_pos is None

    def test_get_aspects_for_planet_method(self, encoder, test_date):
        """Test getting aspects for a specific planet."""
        result = encoder.encode_date(test_date)

        sun_aspects = result.get_aspects_for_planet('sun')
        assert isinstance(sun_aspects, list)

        for aspect in sun_aspects:
            assert 'sun' in [aspect.planet1.lower(), aspect.planet2.lower()]

    def test_get_aspect_between_method(self, encoder, test_date):
        """Test getting aspects between two specific planets."""
        result = encoder.encode_date(test_date)

        # Try to find aspects between Sun and Moon
        sun_moon_aspects = result.get_aspect_between('sun', 'moon')
        assert isinstance(sun_moon_aspects, list)

        for aspect in sun_moon_aspects:
            planets = {aspect.planet1.lower(), aspect.planet2.lower()}
            assert planets == {'sun', 'moon'}

    def test_has_conjunction_method(self, encoder, test_date):
        """Test conjunction checking method."""
        result = encoder.encode_date(test_date)

        # Test with different orbs
        has_tight_conj = result.has_conjunction('saturn', 'neptune', max_orb=3.0)
        has_loose_conj = result.has_conjunction('saturn', 'neptune', max_orb=10.0)

        assert isinstance(has_tight_conj, bool)
        assert isinstance(has_loose_conj, bool)

        # Loose orb should be >= tight orb
        if has_tight_conj:
            assert has_loose_conj

    def test_custom_orbs(self, encoder, test_date):
        """Test encoding with custom orb values."""
        custom_orbs = {'conjunction': 10.0, 'opposition': 12.0}
        result = encoder.encode_date(test_date, custom_orbs=custom_orbs)

        # Should find more aspects with larger orbs
        conjunctions = [a for a in result.aspects if a.aspect_type == 'conjunction']
        for conj in conjunctions:
            assert conj.orb <= 10.0  # Within custom orb

    def test_batch_encode_dates(self, encoder):
        """Test batch encoding functionality."""
        dates = [
            datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
            datetime(2024, 2, 1, 12, 0, 0, tzinfo=timezone.utc)
        ]

        results = encoder.batch_encode_dates(dates)

        assert len(results) == 3
        for i, result in enumerate(results):
            assert isinstance(result, AstronomicalData)
            assert result.date == dates[i]

    def test_to_dict_method(self, encoder, test_date):
        """Test conversion to dictionary."""
        result = encoder.encode_date(test_date)
        data_dict = result.to_dict()

        assert isinstance(data_dict, dict)
        assert 'date' in data_dict
        assert 'positions' in data_dict
        assert 'aspects' in data_dict
        assert 'lunar_phase' in data_dict

        # Check that positions are properly serialized
        for planet_name, position_data in data_dict['positions'].items():
            assert 'planet' in position_data
            assert 'longitude' in position_data
            assert 'sign' in position_data

        # Check that aspects are properly serialized
        for aspect_data in data_dict['aspects']:
            assert 'planet1' in aspect_data
            assert 'planet2' in aspect_data
            assert 'aspect_type' in aspect_data
            assert 'orb' in aspect_data


class TestSpecificAstronomicalEvents:
    """Test specific known astronomical events for accuracy."""

    @pytest.fixture
    def encoder(self):
        return AstroEncoder()

    def test_known_conjunction(self, encoder):
        """
        Test a known astronomical event.

        Note: You would replace this with actual known conjunction dates
        and expected values for real validation.
        """
        # Example test date - you should replace with actual known event
        test_date = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = encoder.encode_date(test_date)

        # Verify the result structure is correct
        assert result is not None
        assert len(result.positions) > 0
        assert isinstance(result.aspects, list)

    def test_solstice_positions(self, encoder):
        """Test positions around solstices."""
        # Winter solstice 2023 (approximately)
        winter_solstice = datetime(2023, 12, 21, 12, 0, 0, tzinfo=timezone.utc)
        result = encoder.encode_date(winter_solstice)

        sun_position = result.get_planet_position('sun')
        assert sun_position is not None

        # Sun should be in Capricorn around winter solstice
        # Note: Exact degree would depend on year and precise calculation
        # This is a rough check
        expected_signs = ['sagittarius', 'capricorn']  # Allow some margin
        assert sun_position.sign in expected_signs

    def test_planetary_speeds(self, encoder):
        """Test that planetary speeds are reasonable."""
        test_date = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        result = encoder.encode_date(test_date)

        # Check that speeds are in reasonable ranges
        sun_pos = result.get_planet_position('sun')
        moon_pos = result.get_planet_position('moon')

        # Sun moves approximately 1 degree per day
        assert 0.5 < abs(sun_pos.speed) < 1.5

        # Moon moves approximately 12-15 degrees per day
        assert 10 < abs(moon_pos.speed) < 16