"""
Tests for utility functions.
"""

import pytest
import math
from astroEncoder.utils import (
    degrees_to_sign, normalize_angle, calculate_angle_difference,
    is_within_orb, determine_applying_separating, calculate_lunar_phase,
    classify_lunar_phase
)


class TestDegreesToSign:
    """Test zodiac sign conversion."""

    def test_aries_early(self):
        sign, degree, classification = degrees_to_sign(5.0)
        assert sign == 'aries'
        assert degree == 5.0
        assert classification == 'early'

    def test_taurus_middle(self):
        sign, degree, classification = degrees_to_sign(45.0)  # 15° Taurus
        assert sign == 'taurus'
        assert degree == 15.0
        assert classification == 'middle'

    def test_gemini_late(self):
        sign, degree, classification = degrees_to_sign(85.0)  # 25° Gemini
        assert sign == 'gemini'
        assert degree == 25.0
        assert classification == 'late'

    def test_pisces_end_of_zodiac(self):
        sign, degree, classification = degrees_to_sign(359.0)  # 29° Pisces
        assert sign == 'pisces'
        assert degree == 29.0
        assert classification == 'late'

    def test_zero_degrees(self):
        sign, degree, classification = degrees_to_sign(0.0)
        assert sign == 'aries'
        assert degree == 0.0
        assert classification == 'early'

    def test_negative_degrees(self):
        sign, degree, classification = degrees_to_sign(-30.0)  # Should wrap to 330° (0° Pisces)
        assert sign == 'pisces'
        assert degree == 0.0
        assert classification == 'early'


class TestNormalizeAngle:
    """Test angle normalization."""

    def test_positive_angle(self):
        assert normalize_angle(45.0) == 45.0

    def test_negative_angle(self):
        assert normalize_angle(-30.0) == 330.0

    def test_over_360(self):
        assert normalize_angle(450.0) == 90.0

    def test_multiple_revolutions(self):
        assert normalize_angle(720.0) == 0.0
        assert normalize_angle(-720.0) == 0.0

    def test_exactly_360(self):
        assert normalize_angle(360.0) == 0.0


class TestCalculateAngleDifference:
    """Test angle difference calculation."""

    def test_simple_difference(self):
        assert calculate_angle_difference(90.0, 120.0) == 30.0

    def test_wrap_around(self):
        assert calculate_angle_difference(350.0, 10.0) == 20.0

    def test_opposite_sides(self):
        assert calculate_angle_difference(0.0, 180.0) == 180.0

    def test_same_angle(self):
        assert calculate_angle_difference(45.0, 45.0) == 0.0

    def test_maximum_difference(self):
        # Maximum difference should be 180°
        assert calculate_angle_difference(0.0, 180.0) == 180.0
        assert calculate_angle_difference(90.0, 270.0) == 180.0


class TestIsWithinOrb:
    """Test aspect orb checking."""

    def test_exact_conjunction(self):
        within_orb, orb_diff = is_within_orb(45.0, 45.0, 0.0, 8.0)
        assert within_orb is True
        assert orb_diff == 0.0

    def test_conjunction_within_orb(self):
        within_orb, orb_diff = is_within_orb(45.0, 50.0, 0.0, 8.0)
        assert within_orb is True
        assert orb_diff == 5.0

    def test_conjunction_outside_orb(self):
        within_orb, orb_diff = is_within_orb(45.0, 55.0, 0.0, 8.0)
        assert within_orb is False
        assert orb_diff == 10.0

    def test_exact_opposition(self):
        within_orb, orb_diff = is_within_orb(0.0, 180.0, 180.0, 8.0)
        assert within_orb is True
        assert orb_diff == 0.0

    def test_opposition_within_orb(self):
        within_orb, orb_diff = is_within_orb(5.0, 180.0, 180.0, 8.0)
        assert within_orb is True
        assert orb_diff == 5.0

    def test_trine_exact(self):
        within_orb, orb_diff = is_within_orb(0.0, 120.0, 120.0, 8.0)
        assert within_orb is True
        assert orb_diff == 0.0


class TestDetermineApplyingSeparating:
    """Test applying/separating calculation."""

    def test_applying_conjunction(self):
        # Faster planet (Moon) catching up to slower planet (Sun)
        result = determine_applying_separating(10.0, 13.0, 15.0, 1.0, 0.0)
        assert result == 'applying'

    def test_separating_conjunction(self):
        # Faster planet moving away from slower planet
        result = determine_applying_separating(15.0, 13.0, 10.0, 1.0, 0.0)
        assert result == 'separating'

    def test_stationary_aspect(self):
        # Very similar speeds
        result = determine_applying_separating(10.0, 1.001, 15.0, 1.0, 0.0)
        assert result == 'stationary'


class TestLunarPhase:
    """Test lunar phase calculations."""

    def test_new_moon(self):
        # Sun and Moon at same longitude
        phase = calculate_lunar_phase(45.0, 45.0)
        assert phase == 0.0

    def test_full_moon(self):
        # Moon opposite Sun
        phase = calculate_lunar_phase(45.0, 225.0)
        assert phase == 180.0

    def test_first_quarter(self):
        # Moon 90° ahead of Sun
        phase = calculate_lunar_phase(0.0, 90.0)
        assert phase == 90.0

    def test_lunar_phase_classification(self):
        assert classify_lunar_phase(0.0) == 'new'
        assert classify_lunar_phase(45.0) == 'waxing_crescent'
        assert classify_lunar_phase(90.0) == 'first_quarter'
        assert classify_lunar_phase(135.0) == 'waxing_gibbous'
        assert classify_lunar_phase(180.0) == 'full'
        assert classify_lunar_phase(225.0) == 'waning_gibbous'
        assert classify_lunar_phase(270.0) == 'last_quarter'
        assert classify_lunar_phase(315.0) == 'waning_crescent'