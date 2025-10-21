"""
Utility functions for astronomical calculations.
"""

import math
from typing import Tuple


def degrees_to_sign(longitude: float) -> Tuple[str, float, str]:
    """
    Convert longitude to zodiac sign, degree within sign, and classification.

    Args:
        longitude: Longitude in degrees (0-360)

    Returns:
        Tuple of (sign_name, degree_in_sign, classification)
    """
    zodiac_signs = [
        'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
        'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'
    ]

    # Normalize longitude to 0-360 range
    longitude = normalize_angle(longitude)

    # Calculate sign and degree within sign
    sign_index = int(longitude // 30)
    degree_in_sign = longitude % 30

    # Classify degree within sign
    if degree_in_sign < 10:
        classification = 'early'
    elif degree_in_sign < 20:
        classification = 'middle'
    else:
        classification = 'late'

    sign_name = zodiac_signs[sign_index]

    return sign_name, degree_in_sign, classification


def normalize_angle(angle: float) -> float:
    """
    Normalize angle to 0-360 degrees.

    Args:
        angle: Angle in degrees

    Returns:
        Normalized angle between 0 and 360
    """
    while angle < 0:
        angle += 360
    while angle >= 360:
        angle -= 360
    return angle


def calculate_angle_difference(angle1: float, angle2: float) -> float:
    """
    Calculate the shortest angular distance between two angles.

    Args:
        angle1: First angle in degrees
        angle2: Second angle in degrees

    Returns:
        Shortest angular distance (0-180 degrees)
    """
    diff = abs(normalize_angle(angle1) - normalize_angle(angle2))
    return min(diff, 360 - diff)


def is_within_orb(angle1: float, angle2: float, target_angle: float, orb: float) -> Tuple[bool, float]:
    """
    Check if two angles form a specific aspect within orb.

    Args:
        angle1: First angle in degrees
        angle2: Second angle in degrees
        target_angle: Target aspect angle (0, 60, 90, 120, 180, etc.)
        orb: Maximum allowed deviation from exact aspect

    Returns:
        Tuple of (is_within_orb, actual_orb_difference)
    """
    actual_angle = calculate_angle_difference(angle1, angle2)
    orb_diff = abs(actual_angle - target_angle)

    # Handle cases where aspect might be on either side (e.g., 178° vs 182° for opposition)
    if target_angle > 0:
        orb_diff_alt = abs(actual_angle - (360 - target_angle))
        orb_diff = min(orb_diff, orb_diff_alt)

    return orb_diff <= orb, orb_diff


def determine_applying_separating(planet1_longitude: float, planet1_speed: float,
                                 planet2_longitude: float, planet2_speed: float,
                                 aspect_angle: float) -> str:
    """
    Determine if an aspect is applying (getting closer) or separating (moving apart).

    Args:
        planet1_longitude: First planet's longitude
        planet1_speed: First planet's daily motion
        planet2_longitude: Second planet's longitude
        planet2_speed: Second planet's daily motion
        aspect_angle: The aspect angle being formed

    Returns:
        'applying', 'separating', or 'stationary'
    """
    # Calculate relative speed
    relative_speed = planet1_speed - planet2_speed

    # If relative speed is very small, consider it stationary
    if abs(relative_speed) < 0.01:
        return 'stationary'

    # Calculate current angular separation
    current_separation = calculate_angle_difference(planet1_longitude, planet2_longitude)

    # Predict separation after one day
    future_pos1 = planet1_longitude + planet1_speed
    future_pos2 = planet2_longitude + planet2_speed
    future_separation = calculate_angle_difference(future_pos1, future_pos2)

    # Calculate how close we are to the target aspect angle
    current_distance_to_aspect = abs(current_separation - aspect_angle)
    future_distance_to_aspect = abs(future_separation - aspect_angle)

    if future_distance_to_aspect < current_distance_to_aspect:
        return 'applying'
    elif future_distance_to_aspect > current_distance_to_aspect:
        return 'separating'
    else:
        return 'stationary'


def calculate_lunar_phase(sun_longitude: float, moon_longitude: float) -> float:
    """
    Calculate lunar phase angle.

    Args:
        sun_longitude: Sun's longitude in degrees
        moon_longitude: Moon's longitude in degrees

    Returns:
        Lunar phase angle (0-360°, where 0° = new moon, 180° = full moon)
    """
    phase_angle = normalize_angle(moon_longitude - sun_longitude)
    return phase_angle


def classify_lunar_phase(phase_angle: float) -> str:
    """
    Classify lunar phase based on angle.

    Args:
        phase_angle: Phase angle in degrees (0-360)

    Returns:
        Phase name: 'new', 'waxing_crescent', 'first_quarter', 'waxing_gibbous',
                   'full', 'waning_gibbous', 'last_quarter', 'waning_crescent'
    """
    phase_angle = normalize_angle(phase_angle)

    if phase_angle < 45:
        return 'new'
    elif phase_angle < 90:
        return 'waxing_crescent'
    elif phase_angle < 135:
        return 'first_quarter'
    elif phase_angle < 180:
        return 'waxing_gibbous'
    elif phase_angle < 225:
        return 'full'
    elif phase_angle < 270:
        return 'waning_gibbous'
    elif phase_angle < 315:
        return 'last_quarter'
    else:
        return 'waning_crescent'