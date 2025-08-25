#!/usr/bin/env python3
"""Debug ESPN data population."""

import logging
import os
logging.basicConfig(level=logging.DEBUG)

from populate_espn import populate_from_espn

# Check for ESPN credentials
espn_s2 = os.getenv("ESPN_S2")
swid = os.getenv("SWID")

if espn_s2 and swid:
    print("Found ESPN credentials in environment")
    test_league_id = '1004124703'  # Your private league
    year = 2024  # Use current year
else:
    print("No ESPN credentials found, using public league for testing")
    # Using ESPN's public mock league for testing
    test_league_id = '30660'  # This is a commonly used public test league
    year = 2024

print(f"Testing with league ID: {test_league_id}, year: {year}")

try:
    print("Testing ESPN data population...")
    populate_from_espn(test_league_id, year=year)
    print("ESPN population completed successfully!")
except Exception as e:
    print(f"ESPN population failed: {e}")
    import traceback
    traceback.print_exc()
    
    if "does not exist" in str(e):
        print("\nTip: For private leagues, you need to set ESPN_S2 and SWID in your .env file")
        print("You can find these values in your browser cookies when logged into ESPN")
