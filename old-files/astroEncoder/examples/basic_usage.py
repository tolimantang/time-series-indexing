#!/usr/bin/env python3
"""
Basic usage examples for AstroEncoder.

This script demonstrates how to use the AstroEncoder to get astronomical data
for specific dates and locations.
"""

import sys
import os
from datetime import datetime, timezone
from pathlib import Path

# Add the astroEncoder package to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from astroEncoder import AstroEncoder


def example_current_positions():
    """Example: Get current astronomical positions."""
    print("=" * 60)
    print("CURRENT ASTRONOMICAL POSITIONS")
    print("=" * 60)

    encoder = AstroEncoder()

    # Get current positions
    current_data = encoder.get_current_positions(location='nyc')

    print(f"Date: {current_data.date}")
    print(f"Location: {current_data.location}")
    print(f"Julian Day: {current_data.julian_day:.6f}")
    print()

    print("PLANETARY POSITIONS:")
    print("-" * 40)
    for planet_name, position in current_data.positions.items():
        print(f"{planet_name.upper():>8}: {position.degree_in_sign:6.2f}° {position.sign.title():>11} "
              f"(House {position.house or 'N/A':>2}) "
              f"[{position.degree_classification}]")

    print()
    print(f"LUNAR PHASE: {current_data.lunar_phase:.1f}° "
          f"({classify_lunar_phase_simple(current_data.lunar_phase)})")


def example_specific_date():
    """Example: Get positions for a specific date."""
    print("\n" + "=" * 60)
    print("SPECIFIC DATE ANALYSIS")
    print("=" * 60)

    encoder = AstroEncoder()

    # Analyze a specific date: January 1, 2024
    target_date = datetime(2025, 10, 13, 12, 0, 0, tzinfo=timezone.utc)
    data = encoder.encode_date(target_date, location='nyc', include_houses=True)

    print(f"Analysis for: {target_date.strftime('%B %d, %Y at %H:%M UTC')}")
    print(f"Location: {data.location}")
    print()

    # Show planetary positions
    print("PLANETARY POSITIONS:")
    print("-" * 60)
    print("Planet    | Longitude  | Sign & Degree        | House | Speed   ")
    print("-" * 60)

    for planet_name, position in data.positions.items():
        longitude_str = f"{position.longitude:6.2f}°"
        sign_degree_str = f"{position.degree_in_sign:5.2f}° {position.sign.title()}"
        house_str = f"{position.house or 'N/A':>2}"
        speed_str = f"{position.speed:+6.3f}°/day"

        print(f"{planet_name.title():>8}  | {longitude_str:>9} | {sign_degree_str:<18} | "
              f"{house_str:>4}  | {speed_str}")

    print()

    # Show significant aspects
    print("MAJOR ASPECTS:")
    print("-" * 50)
    major_aspects = [aspect for aspect in data.aspects if aspect.orb <= 5.0]
    major_aspects = sorted(major_aspects, key=lambda a: a.orb)

    if major_aspects:
        for aspect in major_aspects[:10]:  # Show top 10
            planet1 = aspect.planet1.title()
            planet2 = aspect.planet2.title()
            aspect_type = aspect.aspect_type.replace('_', ' ').title()
            orb_str = f"{aspect.orb:.2f}°"
            exactness_pct = f"{aspect.exactness * 100:.0f}%"

            print(f"{planet1:>8} {aspect_type:<12} {planet2:<8} "
                  f"(orb: {orb_str}, exactness: {exactness_pct}) "
                  f"[{aspect.applying_separating}]")
    else:
        print("No major aspects found within 5° orb.")

    # Show significant events
    if data.significant_events:
        print()
        print("SIGNIFICANT EVENTS:")
        print("-" * 30)
        for event in data.significant_events:
            print(f"• {event}")


def example_conjunction_search():
    """Example: Search for specific conjunctions."""
    print("\n" + "=" * 60)
    print("CONJUNCTION SEARCH")
    print("=" * 60)

    encoder = AstroEncoder()

    # Check for Saturn-Neptune conjunction around current time
    current_data = encoder.get_current_positions()

    print("Searching for planetary conjunctions...")
    print()

    # Major planetary pairs to check
    major_pairs = [
        ('saturn', 'neptune'),
        ('saturn', 'uranus'),
        ('jupiter', 'saturn'),
        ('jupiter', 'uranus'),
        ('saturn', 'pluto'),
        ('mars', 'jupiter')
    ]

    conjunctions_found = []

    for planet1, planet2 in major_pairs:
        has_conjunction = current_data.has_conjunction(planet1, planet2, max_orb=8.0)

        if has_conjunction:
            # Get the specific conjunction aspect
            aspects = current_data.get_aspect_between(planet1, planet2, 'conjunction')
            if aspects:
                aspect = aspects[0]  # Take the first one
                conjunctions_found.append((planet1, planet2, aspect.orb, aspect.exactness))

    if conjunctions_found:
        print("ACTIVE CONJUNCTIONS:")
        print("-" * 40)
        for planet1, planet2, orb, exactness in conjunctions_found:
            print(f"{planet1.title()}-{planet2.title()}: "
                  f"orb {orb:.2f}°, exactness {exactness*100:.0f}%")
    else:
        print("No major conjunctions found within 8° orb.")

    # Show all current aspects for reference
    print()
    print("ALL CURRENT ASPECTS (within 6° orb):")
    print("-" * 50)
    tight_aspects = [a for a in current_data.aspects if a.orb <= 6.0]

    for aspect in tight_aspects[:15]:  # Limit to top 15
        print(f"{aspect.planet1.title()} {aspect.aspect_type.replace('_', ' ')} "
              f"{aspect.planet2.title()}: {aspect.orb:.2f}° orb")


def example_batch_analysis():
    """Example: Analyze multiple dates."""
    print("\n" + "=" * 60)
    print("BATCH DATE ANALYSIS")
    print("=" * 60)

    encoder = AstroEncoder()

    # Analyze first day of each month in 2024
    dates = []
    for month in range(1, 13):
        dates.append(datetime(2024, month, 1, 12, 0, 0, tzinfo=timezone.utc))

    print("Analyzing first day of each month in 2024...")
    results = encoder.batch_encode_dates(dates, location='utc')

    print()
    print("SATURN-NEPTUNE CONJUNCTION TRACKING:")
    print("-" * 50)
    print("Month        | Saturn Pos  | Neptune Pos | Orb     | Status")
    print("-" * 50)

    for i, data in enumerate(results):
        month_name = data.date.strftime('%B')
        saturn_pos = data.get_planet_position('saturn')
        neptune_pos = data.get_planet_position('neptune')

        # Check for conjunction
        conjunctions = data.get_aspect_between('saturn', 'neptune', 'conjunction')

        saturn_str = f"{saturn_pos.degree_in_sign:4.1f}° {saturn_pos.sign.title()[:3]}"
        neptune_str = f"{neptune_pos.degree_in_sign:4.1f}° {neptune_pos.sign.title()[:3]}"

        if conjunctions:
            orb_str = f"{conjunctions[0].orb:5.2f}°"
            status = "CONJUNCT"
        else:
            # Calculate raw orb even if not officially in conjunction
            orb = abs(saturn_pos.longitude - neptune_pos.longitude)
            if orb > 180:
                orb = 360 - orb
            orb_str = f"{orb:5.2f}°"
            status = "apart"

        print(f"{month_name:>10}   | {saturn_str:>10} | {neptune_str:>10} | "
              f"{orb_str:>6} | {status}")


def classify_lunar_phase_simple(phase_angle):
    """Simple lunar phase classification."""
    if phase_angle < 45:
        return 'New'
    elif phase_angle < 135:
        return 'Waxing'
    elif phase_angle < 225:
        return 'Full'
    elif phase_angle < 315:
        return 'Waning'
    else:
        return 'New'


def main():
    """Run all examples."""
    print("AstroEncoder Examples")
    print("=" * 60)

    try:
        example_current_positions()
        example_specific_date()
        example_conjunction_search()
        example_batch_analysis()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError running examples: {e}")
        print("\nMake sure you have installed the required dependencies:")
        print("pip install pyswisseph")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())