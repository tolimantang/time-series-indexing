#!/usr/bin/env python3
"""
Saturn-Neptune Conjunction Analysis Example

This script specifically analyzes the Saturn-Neptune conjunction,
which is relevant for your original query about when Saturn and Neptune
are almost conjunct.
"""

import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add the astroEncoder package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from astroEncoder import AstroEncoder


def analyze_saturn_neptune_conjunction():
    """Analyze the current Saturn-Neptune conjunction."""
    print("SATURN-NEPTUNE CONJUNCTION ANALYSIS")
    print("=" * 50)

    encoder = AstroEncoder()

    # Get current positions
    current_data = encoder.get_current_positions()

    saturn_pos = current_data.get_planet_position('saturn')
    neptune_pos = current_data.get_planet_position('neptune')

    print(f"Analysis Date: {current_data.date.strftime('%B %d, %Y %H:%M UTC')}")
    print()

    print("CURRENT POSITIONS:")
    print("-" * 30)
    print(f"Saturn:  {saturn_pos.degree_in_sign:6.2f}° {saturn_pos.sign.title()}")
    print(f"Neptune: {neptune_pos.degree_in_sign:6.2f}° {neptune_pos.sign.title()}")
    print()

    # Calculate exact orb
    saturn_lon = saturn_pos.longitude
    neptune_lon = neptune_pos.longitude

    orb = abs(saturn_lon - neptune_lon)
    if orb > 180:
        orb = 360 - orb

    print(f"SEPARATION: {orb:.4f}°")

    # Check if in conjunction
    conjunctions = current_data.get_aspect_between('saturn', 'neptune', 'conjunction')

    if conjunctions:
        conjunction = conjunctions[0]
        print(f"STATUS: IN CONJUNCTION")
        print(f"Orb: {conjunction.orb:.4f}°")
        print(f"Exactness: {conjunction.exactness * 100:.1f}%")
        print(f"Motion: {conjunction.applying_separating}")
    else:
        print(f"STATUS: Not in conjunction (orb > 8°)")

    print()

    # Show speeds to understand motion
    print("PLANETARY MOTION:")
    print("-" * 25)
    print(f"Saturn speed:  {saturn_pos.speed:+.6f}°/day")
    print(f"Neptune speed: {neptune_pos.speed:+.6f}°/day")

    relative_speed = saturn_pos.speed - neptune_pos.speed
    print(f"Relative speed: {relative_speed:+.6f}°/day")

    if relative_speed > 0:
        print("Saturn is moving faster (catching up or separating)")
    else:
        print("Neptune is moving faster (rare)")

    # Estimate when exact conjunction occurs
    if conjunctions and conjunctions[0].applying_separating == 'applying':
        days_to_exact = conjunctions[0].orb / abs(relative_speed)
        exact_date = current_data.date + timedelta(days=days_to_exact)
        print(f"\nEstimated exact conjunction: {exact_date.strftime('%B %d, %Y')}")
        print(f"Days from now: {days_to_exact:.1f}")


def track_conjunction_over_time():
    """Track the conjunction over several months."""
    print("\n" + "=" * 50)
    print("CONJUNCTION TRACKING OVER TIME")
    print("=" * 50)

    encoder = AstroEncoder()

    # Look at monthly snapshots
    base_date = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    dates = []

    for month_offset in range(-6, 7):  # 6 months before and after
        date = base_date.replace(month=max(1, min(12, base_date.month + month_offset)))
        if month_offset < 0:
            date = date.replace(year=date.year - 1)
        elif month_offset >= 12 - base_date.month:
            date = date.replace(year=date.year + 1)
        dates.append(date)

    print("Date         | Saturn      | Neptune     | Orb      | Status    | Motion")
    print("-" * 75)

    closest_orb = float('inf')
    closest_date = None

    for date in dates:
        try:
            data = encoder.encode_date(date)
            saturn_pos = data.get_planet_position('saturn')
            neptune_pos = data.get_planet_position('neptune')

            # Calculate orb
            orb = abs(saturn_pos.longitude - neptune_pos.longitude)
            if orb > 180:
                orb = 360 - orb

            if orb < closest_orb:
                closest_orb = orb
                closest_date = date

            # Check conjunction status
            conjunctions = data.get_aspect_between('saturn', 'neptune', 'conjunction')
            status = "CONJUNCT" if conjunctions else "apart"
            motion = conjunctions[0].applying_separating if conjunctions else "N/A"

            date_str = date.strftime('%b %Y')
            saturn_str = f"{saturn_pos.degree_in_sign:4.1f}° {saturn_pos.sign.title()[:3]}"
            neptune_str = f"{neptune_pos.degree_in_sign:4.1f}° {neptune_pos.sign.title()[:3]}"

            print(f"{date_str:>12} | {saturn_str:>10} | {neptune_str:>10} | "
                  f"{orb:6.2f}° | {status:>8} | {motion:>8}")

        except Exception as e:
            print(f"{date.strftime('%b %Y'):>12} | ERROR: {e}")

    print()
    print(f"Closest approach found: {closest_date.strftime('%B %Y')} "
          f"with {closest_orb:.3f}° orb")


def check_jupiter_position():
    """Check Jupiter's position as mentioned in the original query."""
    print("\n" + "=" * 50)
    print("JUPITER POSITION ANALYSIS")
    print("=" * 50)

    encoder = AstroEncoder()
    current_data = encoder.get_current_positions()

    jupiter_pos = current_data.get_planet_position('jupiter')

    print(f"Jupiter Position: {jupiter_pos.degree_in_sign:.2f}° {jupiter_pos.sign.title()}")
    print(f"Degree Classification: {jupiter_pos.degree_classification}")

    # Check if Jupiter is in Cancer
    if jupiter_pos.sign.lower() == 'cancer':
        print("✓ Jupiter IS currently in Cancer")
        if jupiter_pos.degree_classification == 'late':
            print("✓ Jupiter is in LATE Cancer")
        else:
            print(f"• Jupiter is in {jupiter_pos.degree_classification} Cancer")
    else:
        print(f"✗ Jupiter is currently in {jupiter_pos.sign.title()}, not Cancer")

    # Show Jupiter's upcoming sign changes
    print()
    print("Jupiter's movement (approximate):")
    print(f"Current speed: {jupiter_pos.speed:.4f}°/day")

    # Estimate when Jupiter changes signs
    degrees_to_next_sign = 30 - jupiter_pos.degree_in_sign
    days_to_next_sign = degrees_to_next_sign / abs(jupiter_pos.speed)

    next_sign_index = (['aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
                       'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces']
                      .index(jupiter_pos.sign.lower()) + 1) % 12
    next_sign = ['aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
                 'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'][next_sign_index]

    next_sign_date = current_data.date + timedelta(days=days_to_next_sign)
    print(f"Estimated entry to {next_sign.title()}: {next_sign_date.strftime('%B %d, %Y')}")


def check_moon_position():
    """Check Moon's position and upcoming sign change."""
    print("\n" + "=" * 50)
    print("MOON POSITION ANALYSIS")
    print("=" * 50)

    encoder = AstroEncoder()
    current_data = encoder.get_current_positions()

    moon_pos = current_data.get_planet_position('moon')

    print(f"Moon Position: {moon_pos.degree_in_sign:.2f}° {moon_pos.sign.title()}")
    print(f"Moon Speed: {moon_pos.speed:.2f}°/day")

    # Calculate when Moon enters next sign
    degrees_to_next_sign = 30 - moon_pos.degree_in_sign
    hours_to_next_sign = (degrees_to_next_sign / abs(moon_pos.speed)) * 24

    signs = ['aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
             'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces']
    current_sign_index = signs.index(moon_pos.sign.lower())
    next_sign = signs[(current_sign_index + 1) % 12]

    next_sign_time = current_data.date + timedelta(hours=hours_to_next_sign)

    print(f"Next sign change: {next_sign.title()}")
    print(f"Estimated time: {next_sign_time.strftime('%B %d, %Y at %H:%M UTC')}")
    print(f"Hours from now: {hours_to_next_sign:.1f}")

    # Check if Moon is about to go to Gemini
    if next_sign.lower() == 'gemini':
        if hours_to_next_sign <= 48:  # Within 2 days
            print("✓ Moon IS about to enter Gemini (within 2 days)")
        else:
            print(f"• Moon will enter Gemini in {hours_to_next_sign/24:.1f} days")
    else:
        print(f"✗ Moon is about to enter {next_sign.title()}, not Gemini")


def main():
    """Run the Saturn-Neptune conjunction analysis."""
    try:
        analyze_saturn_neptune_conjunction()
        track_conjunction_over_time()
        check_jupiter_position()
        check_moon_position()

        print("\n" + "=" * 50)
        print("Analysis completed!")
        print("=" * 50)

    except Exception as e:
        print(f"Error during analysis: {e}")
        print("\nMake sure you have installed pyswisseph:")
        print("pip install pyswisseph")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())