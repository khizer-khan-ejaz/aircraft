import datetime
import math
from allclass import *
from sample_airport import *
generator = AirportQuestionGenerator(sample_airports)
def calculate_ground_speed(true_course, tas, wind_dir, wind_speed):
                        tc_rad = math.radians(true_course)
                        wd_rad = math.radians(wind_dir)
                        wca_rad = math.asin((wind_speed / tas) * math.sin(wd_rad - tc_rad))
                        gs = tas * math.cos(wca_rad) - wind_speed * math.cos(wd_rad - tc_rad)
                        return gs
def decimal_year(date: datetime.datetime) -> float:
    """Calculate decimal year from datetime object."""
    year_start = datetime.datetime(date.year, 1, 1)
    next_year_start = datetime.datetime(date.year + 1, 1, 1)
    year_length = (next_year_start - year_start).total_seconds()
    elapsed = (date - year_start).total_seconds()
    return date.year + elapsed / year_length
def calculate_groundspeed(tas, course_deg, wind_speed, wind_dir_deg):
    """
    Calculate groundspeed given TAS, course, wind speed, and wind direction.
    Uses vector triangle method.
    """
    # Convert angles to radians
    course_rad = math.radians(course_deg)
    wind_dir_rad = math.radians(wind_dir_deg)
    
    # Wind direction relative to course
    theta = wind_dir_rad - course_rad
    
    # Ground speed formula
    gs = math.sqrt(tas**2 + wind_speed**2 - 2 * tas * wind_speed * math.cos(theta))
    return round(gs, 2)
def find(name,airports):
    """Find airport in airports_list by name (case insensitive partial match)"""
    name_lower = name.lower()
    for airport in airports:
        if name_lower in airport.name.lower():
            return airport  # Return the Airport object directly
    return None
