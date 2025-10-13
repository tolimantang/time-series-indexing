# AstroEncoder

A Python package for encoding astronomical data using Swiss Ephemeris, designed for financial astrology and market correlation analysis.

## Features

- Calculate planetary positions for any date/time
- Compute aspects between planets with customizable orbs
- Calculate house positions using Placidus system
- Detect significant astronomical events
- Batch processing for multiple dates
- Lunar phase calculations
- Support for multiple locations

## Installation

1. **Install Swiss Ephemeris dependency:**
```bash
pip install pyswisseph
```

2. **Install additional dependencies:**
```bash
pip install pytest pytest-cov
```

3. **Navigate to the astroEncoder directory:**
```bash
cd /Users/yetang/Development/time-series-indexing/astroEncoder
```

## Quick Start

### Basic Usage

```python
from astroEncoder import AstroEncoder
from datetime import datetime, timezone

# Create encoder instance
encoder = AstroEncoder()

# Get current astronomical positions
current_data = encoder.get_current_positions(location='nyc')

# Print planetary positions
for planet_name, position in current_data.positions.items():
    print(f"{planet_name.upper()}: {position.degree_in_sign:.2f}° {position.sign.title()}")

# Check for Saturn-Neptune conjunction
has_conjunction = current_data.has_conjunction('saturn', 'neptune', max_orb=8.0)
print(f"Saturn-Neptune conjunction: {has_conjunction}")
```

### Analyze Specific Date

```python
# Analyze January 1, 2024
target_date = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
data = encoder.encode_date(target_date, location='nyc', include_houses=True)

# Get planetary aspects
aspects = data.get_aspect_between('saturn', 'neptune', 'conjunction')
if aspects:
    print(f"Saturn-Neptune conjunction: {aspects[0].orb:.2f}° orb")
```

## Running the Code

### 1. Run Basic Examples

```bash
# Run basic usage examples
python examples/basic_usage.py
```

### 2. Run Saturn-Neptune Conjunction Analysis

```bash
# Run specific conjunction analysis (answers your original query)
python examples/saturn_neptune_conjunction.py
```

### 3. Interactive Python Session

```bash
python3 -c "
from astroEncoder import AstroEncoder
encoder = AstroEncoder()
current = encoder.get_current_positions()
print('Current positions:')
for planet, pos in current.positions.items():
    print(f'{planet}: {pos.degree_in_sign:.1f}° {pos.sign.title()}')
"
```

## Running Tests

### Run All Tests
```bash
# Run all unit tests
pytest tests/ -v
```

### Run Specific Test Files
```bash
# Test the main encoder
pytest tests/test_encoder.py -v

# Test utility functions
pytest tests/test_utils.py -v
```

### Run Tests with Coverage
```bash
# Run tests with coverage report
pytest tests/ --cov=astroEncoder --cov-report=term-missing
```

### Test Individual Components
```bash
# Test planetary position calculations
pytest tests/test_encoder.py::TestAstroEncoder::test_planetary_positions -v

# Test aspect calculations
pytest tests/test_encoder.py::TestAstroEncoder::test_aspects_calculation -v

# Test conjunction detection
pytest tests/test_encoder.py::TestAstroEncoder::test_has_conjunction_method -v
```

## Verification Commands

### Quick Verification
```bash
# Verify the package imports correctly
python3 -c "from astroEncoder import AstroEncoder; print('✓ Package imports successfully')"

# Verify Swiss Ephemeris works
python3 -c "import swisseph as swe; print('✓ Swiss Ephemeris available')"

# Quick functionality test
python3 -c "
from astroEncoder import AstroEncoder
encoder = AstroEncoder()
data = encoder.get_current_positions()
print(f'✓ Current planetary positions calculated for {data.date}')
print(f'✓ Found {len(data.aspects)} aspects')
print(f'✓ Lunar phase: {data.lunar_phase:.1f}°')
"
```

### Validate Astronomical Accuracy
```bash
# Check today's planetary positions
python3 -c "
from astroEncoder import AstroEncoder
encoder = AstroEncoder()
data = encoder.get_current_positions()
sun = data.get_planet_position('sun')
moon = data.get_planet_position('moon')
print(f'Sun: {sun.degree_in_sign:.2f}° {sun.sign.title()}')
print(f'Moon: {moon.degree_in_sign:.2f}° {moon.sign.title()}')
print(f'Lunar phase: {data.lunar_phase:.1f}°')
"
```

## Example Output

When you run the examples, you should see output like:

```
CURRENT ASTRONOMICAL POSITIONS
==============================================================
Date: 2024-10-13 15:30:45.123456+00:00
Location: New York City

PLANETARY POSITIONS:
----------------------------------------
     SUN:  20.45° Libra        (House  4) [middle]
    MOON:  12.78° Gemini       (House 12) [middle]
 MERCURY:   5.23° Scorpio      (House  4) [early]
   VENUS:  28.91° Virgo        (House  3) [late]
    MARS:  15.67° Cancer       (House  1) [middle]
 JUPITER:   8.34° Gemini       (House 11) [early]
  SATURN:  14.23° Pisces       (House  8) [middle]
  URANUS:  22.56° Taurus       (House 10) [late]
 NEPTUNE:  27.12° Pisces       (House  8) [late]
   PLUTO:  29.45° Capricorn    (House  6) [late]

SATURN-NEPTUNE CONJUNCTION ANALYSIS
STATUS: IN CONJUNCTION
Orb: 2.89°
Exactness: 64.0%
Motion: applying
```

## Troubleshooting

### Common Issues

1. **Swiss Ephemeris not found:**
   ```bash
   pip install pyswisseph
   ```

2. **Import errors:**
   - Ensure you're in the correct directory
   - Check Python path includes the astroEncoder package

3. **Test failures:**
   - Make sure all dependencies are installed
   - Run `pip install pytest pytest-cov`

### Validation

The package calculates real astronomical positions using Swiss Ephemeris. You can verify accuracy by comparing with astronomical websites like:
- timeanddate.com/astronomy
- astro.com
- astrolabe.com

## API Reference

### Main Classes

- `AstroEncoder`: Main encoder class
- `AstronomicalData`: Container for all astronomical data
- `PlanetaryPosition`: Individual planet position data
- `Aspect`: Planetary aspect data
- `HouseData`: House system data

### Key Methods

- `encode_date()`: Calculate positions for specific date
- `get_current_positions()`: Get current astronomical data
- `batch_encode_dates()`: Process multiple dates
- `has_conjunction()`: Check for planetary conjunctions
- `get_aspect_between()`: Get aspects between specific planets