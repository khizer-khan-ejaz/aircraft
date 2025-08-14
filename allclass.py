import random
import math
from typing import Dict, List, NamedTuple
import logging
from sample_airport import *
from cal_func import calculate_geodesic1
from geographiclib.geodesic import Geodesic
import datetime
from pygeomag import GeoMag
import groq
from typing import Optional
from fuzzywuzzy import fuzz
geo = GeoMag()
class Airport:
    def __init__(self, code, name, lat, long, reference):
        self.code = code
        self.name = name
        self.lat = lat
        self.long = long
        self.reference = reference
    def __repr__(self):
        return f"{self.code} - {self.name}"
        
def decimal_year(date: datetime.datetime) -> float:
    """Convert a datetime to decimal year."""
    year_start = datetime.datetime(date.year, 1, 1)
    year_end = datetime.datetime(date.year + 1, 1, 1)
    year_length = (year_end - year_start).total_seconds()
    elapsed = (date - year_start).total_seconds()
    return date.year + elapsed / year_length

class Point:
    def __init__(self, lat, long):
        self.lat = lat
        self.long = long
class Navigation:
    def get_track_angle(self, dep, arr, magnetic=True, date=None):
        # Validate inputs
        if not (-90 <= dep.lat <= 90 and -180 <= dep.long <= 180 and 
                -90 <= arr.lat <= 90 and -180 <= arr.long <= 180):
            raise ValueError("Invalid latitude or longitude")
        if (dep.lat, dep.long) == (arr.lat, arr.long):
            return 0.0

        # Calculate true bearing using great-circle formula
        lat1 = math.radians(dep.lat)
        lon1 = math.radians(dep.long)
        lat2 = math.radians(arr.lat)
        lon2 = math.radians(arr.long)
        
        dlon = lon2 - lon1
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        true_bearing = math.degrees(math.atan2(y, x))
        true_bearing = (true_bearing + 360) % 360
        
        if not magnetic:
            return round(true_bearing, 2)
        
        # Convert to magnetic bearing
        magnetic_variation = self.get_magnetic_variation(dep.lat, dep.long, date)
        magnetic_bearing = (true_bearing - magnetic_variation + 360) % 360
        
        return round(magnetic_bearing, 2)

    def get_magnetic_variation(self, lat, lon, date=None):
        if geo is None:
            print("GeoMag unavailable. Using fallback magnetic variation (-12.0 for New York).")
            return -12.0  # Fallback for New York, 2023
        try:
            date = date or datetime.datetime.utcnow()
            dec_year = self.decimal_year(date)
            result = geo.calculate(glat=lat, glon=lon, alt=0, time=dec_year)
            return float(result.dec)
        except Exception as e:
            print(f"Error calculating magnetic variation: {e}")
            return -12.0  # Fallback for New York

    def decimal_year(self, date):
        """Convert a datetime object to decimal year."""
        year_start = datetime.datetime(date.year, 1, 1)
        year_end = datetime.datetime(date.year + 1, 1, 1)
        year_length = (year_end - year_start).total_seconds()
        seconds_into_year = (date - year_start).total_seconds()
        return date.year + seconds_into_year / year_length

    def get_midpoint(self, dep, arr):
        """Calculate the geographic midpoint between two points."""
        # Convert to radians
        lat1 = math.radians(dep.lat)
        lon1 = math.radians(dep.long)
        lat2 = math.radians(arr.lat)
        lon2 = math.radians(arr.long)
        
        # Convert to Cartesian coordinates
        x1 = math.cos(lat1) * math.cos(lon1)
        y1 = math.cos(lat1) * math.sin(lon1)
        z1 = math.sin(lat1)
        x2 = math.cos(lat2) * math.cos(lon2)
        y2 = math.cos(lat2) * math.sin(lon2)
        z2 = math.sin(lat2)
        
        # Average coordinates
        x = (x1 + x2) / 2
        y = (y1 + y2) / 2
        z = (z1 + z2) / 2
        
        # Convert back to lat/long
        lon = math.atan2(y, x)
        hyp = math.sqrt(x * x + y * y)
        lat = math.atan2(z, hyp)
        
        # Convert to degrees
        mid_lat = math.degrees(lat)
        mid_lon = math.degrees(lon)
        
        return Point(round(mid_lat, 4), round(mid_lon, 4))

    def get_route_magnitude(self, dep, arr, unit='km'):
        """Calculate great-circle distance between two points."""
        # Earth's radius (km)
        R = 6371.0  # Use 3440.1 for nautical miles, 3958.8 for statute miles
        
        lat1 = math.radians(dep.lat)
        lon1 = math.radians(dep.long)
        lat2 = math.radians(arr.lat)
        lon2 = math.radians(arr.long)
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        
        if unit == 'nm':
            distance *= 0.539957  # Convert km to nautical miles
        elif unit == 'mi':
            distance *= 0.621371  # Convert km to statute miles
            
        return round(distance, 2)

class QuestionDetails(NamedTuple):
    departure: Airport
    arrival: Airport
    land1: Airport
    land2: Airport
    cruise_level: int
    tas_normal: float
    tas_single_engine: float
    wind_normal: Dict
    wind_single_engine: Dict
    shape_type: str
    reference: str
    rondom_choice:str

class CurrentQuestion(NamedTuple):
    question: str
    details: QuestionDetails

class AirportQuestionGenerator:
    def __init__(self, airports: List[Airport]):
        self.airports = airports
    
    def calculate_distance(self, lat1, lon1, lat2, lon2):
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        return distance
    
    def calculate_angle(self, a, b, c):
        try:
            cos_C = (a*a + b*b - c*c) / (2*a*b)
            cos_C = max(-1, min(1, cos_C))
            angle_C = math.degrees(math.acos(cos_C))
            return angle_C
        except:
            return 0
    
    def calculate_angle_between_lines(self, p1, p2, p3, p4):
        vector1_x = p2.long - p1.long
        vector1_y = p2.lat - p1.lat
        vector2_x = p4.long - p3.long
        vector2_y = p4.lat - p3.lat
        
        dot_product = vector1_x * vector2_x + vector1_y * vector2_y
        
        mag1 = math.sqrt(vector1_x * vector1_x + vector1_y * vector1_y)
        mag2 = math.sqrt(vector2_x * vector2_x + vector2_y * vector2_y)
        
        if mag1 < 1e-6 or mag2 < 1e-6:
            return 0
        
        cos_angle = dot_product / (mag1 * mag2)
        cos_angle = max(-1, min(1, cos_angle))
        angle = math.degrees(math.acos(cos_angle))
        
        return angle
    
    def get_track_angle(self, dep, arr, magnetic=True):
    # Calculate true bearing using great-circle formula
        lat1 = math.radians(dep.lat)
        lon1 = math.radians(dep.long)
        lat2 = math.radians(arr.lat)
        lon2 = math.radians(arr.long)
        
        dlon = lon2 - lon1
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        true_bearing = math.degrees(math.atan2(y, x))
        true_bearing = (true_bearing + 360) % 360
        
        if not magnetic:
            return true_bearing
        
        # Convert true bearing to magnetic bearing using your existing function
        magnetic_variation = self.get_magnetic_variation(dep.lat, dep.long)
        magnetic_bearing = (true_bearing + magnetic_variation) % 360
        
        return magnetic_bearing

    def get_magnetic_variation(self, lat, lon, date=None):
        try:
            date = date or datetime.datetime.utcnow()
            dec_year = decimal_year(date)
            result = geo.calculate(glat=lat, glon=lon, alt=0, time=dec_year)
            return float(result.dec)  # Ensure numeric return
        except Exception as e:
            print(f"Error calculating magnetic variation: {e}")
            return 0.0  # Default value on failure
            
    def determine_triangle_type(self, a, b, c):
        sides = sorted([a, b, c])
        
        if sides[0] + sides[1] <= sides[2]:
            return "Degenerate Triangle"
        
        if abs(sides[0]**2 + sides[1]**2 - sides[2]**2) < 1e-6:
            return "Right Triangle"
        
        if abs(sides[0] - sides[2]) < 1e-6:
            return "Equilateral Triangle"
        
        if abs(sides[0] - sides[1]) < 1e-6 or abs(sides[1] - sides[2]) < 1e-6:
            return "Isosceles Triangle"
        
        return "Scalene Triangle"
    
    def is_valid_parallelogram(self, p1, p2, p3, p4):
        # Calculate distances for opposite sides
        side1 = self.calculate_distance(p1.lat, p1.long, p2.lat, p2.long)
        side2 = self.calculate_distance(p3.lat, p3.long, p4.lat, p4.long)
        side3 = self.calculate_distance(p1.lat, p1.long, p3.lat, p3.long)
        side4 = self.calculate_distance(p2.lat, p2.long, p4.lat, p4.long)
        
        # Check if opposite sides are approximately equal
        if abs(side1 - side2) / max(side1, side2, 1) > 0.2 or abs(side3 - side4) / max(side3, side4, 1) > 0.2:
            return False
        
        # Check if the points are not collinear
        angle1 = self.calculate_angle_between_lines(p1, p2, p3, p4)
        angle2 = self.calculate_angle_between_lines(p1, p3, p2, p4)
        if abs(angle1) < 5 or abs(angle1 - 180) < 5 or abs(angle2) < 5 or abs(angle2 - 180) < 5:
            return False
        
        return True
    
    def calculate_critical_point(self, question):
        dep = question.details.departure
        arr = question.details.arrival
        land1 = question.details.land1
        
        distance_dep_arr = self.calculate_distance(dep.lat, dep.long, arr.lat, arr.long)
        distance_dep_land = self.calculate_distance(dep.lat, dep.long, land1.lat, land1.long)
        distance_arr_land = self.calculate_distance(arr.lat, arr.long, land1.lat, land1.long)
        
        tas = question.details.tas_single_engine
        wind_speed = question.details.wind_single_engine['speed']
        
        if distance_dep_arr < 1e-6:
            return None
            
        cp_distance = distance_dep_arr * (distance_arr_land / (distance_dep_land + distance_arr_land))
        
        wind_factor = 1.0
        if wind_speed > 0:
            wind_factor = 1.0 + (wind_speed / tas) * 0.2
        
        return cp_distance * wind_factor
   
    def select_airports_for_shape_with_reference(self, specified_reference, num_airports):
        attempts = 0
        max_attempts = 1000
        excluded_codes = {"YMNG", "MBW", "HLT", "MQL", "MGB", "WYA", "MEL", "HBA"}
        airports_dep_arr = [a for a in self.airports if a.reference == specified_reference and a.code not in excluded_codes]
        airports_full = [a for a in self.airports if a.reference == specified_reference]
        
        if len(airports_dep_arr) < 2:
            raise ValueError(f"Not enough airports for reference {specified_reference}")
        
        while attempts < max_attempts:
            attempts += 1
            if num_airports == 3:
                dep = random.choice(airports_dep_arr)
                arr = random.choice(airports_dep_arr)
                while arr == dep:
                    arr = random.choice(airports_dep_arr)
                eland2 = random.choice(airports_full)
                while eland2 == dep or eland2 == arr:
                    eland2 = random.choice(airports_full)
                
                d1 = self.calculate_distance(dep.lat, dep.long, arr.lat, arr.long)
                d2 = self.calculate_distance(dep.lat, dep.long, eland2.lat, eland2.long)
                d3 = self.calculate_distance(arr.lat, arr.long, eland2.lat, eland2.long)
                
                if d1 + d2 <= d3 or d1 + d3 <= d2 or d2 + d3 <= d1:
                    continue
                
                angle_dep = self.calculate_angle(d2, d1, d3)
                angle_arr = self.calculate_angle(d1, d3, d2)
                angle_eland2 = self.calculate_angle(d2, d3, d1)
                
                if (85 < angle_dep < 95) or (85 < angle_arr < 95) or (85 < angle_eland2 < 95):
                    continue
                
                if min(angle_dep, angle_arr, angle_eland2) < 5:
                    continue
                
                eland = dep
                shape_type = "triangle"
                
                return {
                    "dep": dep,
                    "arr": arr,
                    "eland": eland,
                    "eland2": eland2,
                    "shapeType": shape_type,
                    "reference": specified_reference
                }
            elif num_airports == 4:
                dep = random.choice(airports_dep_arr)
                arr = random.choice(airports_dep_arr)
                while arr == dep:
                    arr = random.choice(airports_dep_arr)
                eland = random.choice(airports_full)
                while eland == dep or eland == arr:
                    eland = random.choice(airports_full)
                eland2 = random.choice(airports_full)
                while eland2 == dep or eland2 == arr or eland2 == eland:
                    eland2 = random.choice(airports_full)
                
                main_distance = self.calculate_distance(dep.lat, dep.long, arr.lat, arr.long)
                if main_distance < 300:
                    continue
                
                # Ensure valid parallelogram
                if not self.is_valid_parallelogram(dep, arr, eland, eland2):
                    continue
                
                # Additional distance checks to avoid degenerate cases
                d1 = self.calculate_distance(dep.lat, dep.long, eland.lat, eland.long)
                d2 = self.calculate_distance(arr.lat, arr.long, eland2.lat, eland2.long)
                d3 = self.calculate_distance(eland.lat, eland.long, eland2.lat, eland2.long)
                if min(d1, d2, d3) < 50:  # Ensure reasonable separation
                    continue
                
                shape_type = "parallelogram"
                
                return {
                    "dep": dep,
                    "arr": arr,
                    "eland": eland,
                    "eland2": eland2,
                    "shapeType": shape_type,
                    "reference": specified_reference
                }
            else:
                raise ValueError("num_airports must be 3 or 4")
    
        raise ValueError(f"Could not find valid airport configuration for reference {specified_reference} after {max_attempts} attempts")
    def generate_question_with_reference(self, specified_reference, num_airports):
        max_attempts = 22200
        attempts = 0

        if num_airports not in [3, 4]:
            raise ValueError("num_airports must be 3 or 4")

        max_distances = {
            'L1': 226.415095,
            'L2': 220.858896,
            'L3': 187.5,
            'L4': 327.27272700000003,
            'L5': 346.153846,
            'L6': 500,
            'L7': 486.4844869999999,
            'L8': 473.68423
        }

        max_distance = max_distances.get(specified_reference)
        if max_distance is None:
            raise ValueError(f"Invalid reference level: {specified_reference}")

        while attempts < max_attempts:
            attempts += 1
            try:
                selected = self.select_airports_for_shape_with_reference(specified_reference, num_airports)
                
                dep = selected["dep"]
                arr = selected["arr"]
                eland = selected["eland"]
                eland2 = selected["eland2"]
                
                if num_airports == 3:
                    dep = selected["dep"]
                    arr = selected["arr"]
                    eland = arr 
                    eland2 = selected["eland2"]
                
                # Calculate distances using geodesic
                geod = Geodesic.WGS84
                P1 = (dep.lat, dep.long)
                P2 = (arr.lat, arr.long)
                P3 = (eland.lat, eland.long)
                P4 = (eland2.lat, eland2.long)
                def find_airport_by_name(name, reference, airports):
                    if not name or not airports:
                        # Using print for direct feedback, but logging is better
                        print("Invalid input: name or airports list is empty")
                        return None
                    name_lower, name_upper = name.lower().strip(), name.upper().strip()
                    reference_list = []
                    if isinstance(reference, list):
                        reference_list = [ref.upper().strip() for ref in reference if isinstance(ref, str) and ref.strip()]
                    elif isinstance(reference, str) and reference.strip():
                        reference_list = [reference.upper().strip()]
                    
                    candidates = []
                    for airport in airports:
                        score = 0
                        airport_name_clean = airport.name.lower().strip()
                        airport_code_lower = airport.code.lower().strip()
                        airport_reference = airport.reference.upper().strip() if airport.reference else ""
                        
                        if name_lower == airport_name_clean: score += 100
                        if name_upper == airport.code: score += 95
                        if reference_list and airport_reference in reference_list: score += 90
                        if airport_name_clean.startswith(name_lower): score += 85
                        fuzzy_score = fuzz.ratio(name_lower, airport_name_clean)
                        if fuzzy_score >= 80: score += fuzzy_score * 0.75
                        if name_lower in airport_name_clean: score += 65
                        
                        if score > 0:
                            candidates.append({"airport": airport, "score": score})
                    
                    if candidates:
                        return max(candidates, key=lambda x: x["score"])["airport"]
                    
                    print(f"No match found for '{name}'")
                    return None
                dep1 = find_airport_by_name(dep.name, specified_reference, airports)
                arr1 = find_airport_by_name(arr.name, specified_reference, airports)
                land1_map = find_airport_by_name(eland.name, specified_reference, airports)
                land2_map = find_airport_by_name(eland2.name, specified_reference, airports)
                P5 = (dep1.lat, dep1.long)
                P6 = (arr1.lat, arr1.long)
                P7 = (land1_map.lat, land1_map.long)
                P8 = (land2_map.lat, land2_map.long)
                


                p1p2 = geod.Inverse(P1[0], P1[1], P2[0], P2[1])
                p1p2_dist = p1p2['s12'] / 1852.0
                p3p4 = geod.Inverse(P3[0], P3[1], P4[0], P4[1])
                p3p4_dist = p3p4['s12'] / 1852.0
                
                mp_p1p2 = geod.InverseLine(P1[0], P1[1], P2[0], P2[1]).Position(0.5)
                mp_p1p2_point = (mp_p1p2['lat2'], mp_p1p2['lon2'])
                mp_p3p4 = geod.InverseLine(P3[0], P3[1], P4[0], P4[1]).Position(0.5)
                mp_p3p4_point = (mp_p3p4['lat2'], mp_p3p4['lon2'])
                
                mid_dist = geod.Inverse(mp_p1p2_point[0], mp_p1p2_point[1], 
                                      mp_p3p4_point[0], mp_p3p4_point[1])
                mid_dist_nm = mid_dist['s12'] / 1852.0
                if p1p2_dist <= 100:
                    logging.debug(f"P1P2 distance {p1p2_dist:.1f}nm is less than or equal to 100nm")
                    continue
                    
                if p3p4_dist >= (p1p2_dist * 0.95):
                    logging.debug(f"P3P4 distance {p3p4_dist:.1f} not less than 85% of P1P2 {p1p2_dist:.1f}")
                    continue
                
                if (p1p2_dist > max_distance or 
                    p3p4_dist > max_distance or 
                    mid_dist_nm > max_distance):
                    logging.debug(f"Distance constraints not met for {specified_reference}: "
                                f"P1-P2={p1p2_dist:.2f}nm, P3-P4={p3p4_dist:.2f}nm, "
                                f"Midpoints={mid_dist_nm:.2f}nm (max={max_distance}nm)")
                    continue
                
                # Generate question parameters
                cruise_level = random.choice([150, 170, 190, 210, 230])
                normal_min, normal_max = 240, 250
                single_min, single_max = 180, 200
                normal_choices = list(range(normal_min, normal_max + 1, 5))
                single_choices = list(range(single_min, single_max + 1, 5))
                tas_normal = random.choice(normal_choices)
                tas_single_engine = random.choice(single_choices)
                
                # Define valid wind direction ranges (035–075, 105–165, 195–255, 285–345, multiples of 5)
                wind_direction_ranges = [
                    list(range(35, 76, 5)),
                    list(range(105, 166, 5)),
                    list(range(195, 256, 5)),
                    list(range(285, 346, 5))
                ]
                valid_wind_directions = [direction for sublist in wind_direction_ranges for direction in sublist]

                # Select wind_dir_normal
                wind_dir_normal = random.choice(valid_wind_directions)

                # Select wind_dir_single (within ±20° of wind_dir_normal)
                possible_single_directions = [
                    d for d in valid_wind_directions
                    if abs((d - wind_dir_normal + 180) % 360 - 180) <= 20
                ]
                wind_dir_single = random.choice(possible_single_directions if possible_single_directions else valid_wind_directions)
                
                # Wind speed logic
                min_speed = 40
                max_speed = 70
                possible_values = list(range(min_speed, max_speed + 1, 5))
                wind_speed_normal = random.choice(possible_values)
                
                raw_speed = wind_speed_normal * (0.8 + random.random() * 0.4)
                rounded_speed = round(raw_speed / 5) * 5
                if rounded_speed >= 90:
                    rounded_speed = 85
                wind_speed_single = int(rounded_speed)
                reference_point = random.choice([dep.name, arr.name])
                cp_sentence_options = [
                (f"Your calculation of the location of the single engine CP (Critical Point) ", False),  # Use single engine
                (f"Your calculated CP location for  ", True)              # Use normal ops
            ]
                cp_phrase, use_normal_data = random.choice(cp_sentence_options)
                if use_normal_data:
                    tas_used = tas_normal
                    wind_dir_used = wind_dir_normal
                    wind_speed_used = wind_speed_normal
                else:
                    tas_used = tas_single_engine
                    wind_dir_used = wind_dir_single
                    wind_speed_used = wind_speed_single
                dep_lat = round(dep.lat)
                dep_long = round(dep.long)
                arr_lat = round(arr.lat)
                arr_long = round(arr.long)
                eland_lat = round(eland.lat)
                eland_long = round(eland.long)
                eland2_lat = round(eland2.lat)
                eland2_long = round(eland2.long)

                # Format coordinates with N/S, E/W, and degree symbol
                dep_coords = f"{abs(dep_lat)}°{'S' if dep_lat < 0 else 'N'}, {abs(dep_long)}°{'E' if dep_long >= 0 else 'W'}"
                arr_coords = f"{abs(arr_lat)}°{'S' if arr_lat < 0 else 'N'}, {abs(arr_long)}°{'E' if arr_long >= 0 else 'W'}"
                eland_coords = f"{abs(eland_lat)}°{'S' if eland_lat < 0 else 'N'}, {abs(eland_long)}°{'E' if eland_long >= 0 else 'W'}"
                eland2_coords = f"{abs(eland2_lat)}°{'S' if eland2_lat < 0 else 'N'}, {abs(eland2_long)}°{'E' if eland2_long >= 0 else 'W'}"

                # Output the formatted coordinates
                      
                def get_random_question_template():
                    question_text_1 = (
                        f"Refer ERC {selected['reference']}. You are planning a flight from {dep.name}({dep.code})({dep_coords}) to {arr.name}({arr.code})({arr_coords}) "
                        f"direct at FL{cruise_level} with a TAS of {tas_normal} kt for normal operations "
                        f"and single engine TAS of {tas_single_engine} kt. WV {wind_dir_normal}M / {wind_speed_normal} kt "
                        f"at FL{cruise_level} (normal ops crz), WV {wind_dir_single}M / {wind_speed_single} kt for single "
                        f"engine cruise level. {cp_phrase} "
                        f"for {eland.name}({eland_coords}) and {eland2.name}({eland2_coords}), on the {dep.code} - {arr.code} track, measured as a distance "
                        f"from {reference_point} is -"
                    )
                    question_text_2 = (
                        f"Refer ERC {selected['reference']}.\n You are en route from {dep.name}({dep.code})({dep_coords}) to {arr.name}({arr.code})({arr_coords}) "
                        f"The in-flight details include a with a TAS of {tas_used} knots "
                        f" a wind velocity obtained from the FMS of {wind_dir_used}°(M)/{wind_speed_used}KT"
                        f" Due to a possible technical issue you decide to calculate the position of the ETP"
                        f"between {eland.name}({eland_coords}) and {eland2.name}({eland2_coords}), on the {dep.code} - {arr.code} track, ETP  "
                        f"from {reference_point} is -"
                    )
                    question_text_3 = (
                        f"Refer ERC {selected['reference']} from {dep.name}({dep.code}) ({dep_coords}) to {arr.name}({arr.code})({arr_coords}) "
                        f"The in-flight details include a TAS  {tas_used} knots  and "
                        f"and a wind velocity obtained from the FMS of  {wind_dir_used}M / {wind_speed_used} kt  "
                        f"technical issue you decide to calculate the position of the ETP between"
                        f"for {eland.name}({eland_coords}) and {eland2.name} ({eland2_coords}), on the {dep.code} - {arr.code} track, measured as a distance "
                        f"from {reference_point} is -"
                    )

                    templates = [question_text_1, question_text_2, question_text_3]
                    return random.choice(templates)

                question_text=get_random_question_template()
                
                
                def refine_question_with_groq(question_text: str, api_key: Optional[str] = None) -> str:
                        """
                        Refine the aviation question text using Groq API to make it more clear and professional.
                        
                        Args:
                            question_text: The original question text to be refined
                            api_key: Optional Groq API key. If not provided, will use GROQ_API_KEY environment variable
                            
                        Returns:
                            Refined question text
                            
                        Raises:
                            ValueError: If API key is not available or API call fails
                        """
                        # Get API key
                        api_key = "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"
                        if not api_key:
                            raise ValueError("Groq API key not provided and GROQ_API_KEY environment variable not set")
                        
                        # Initialize Groq client
                        client = groq.Client(api_key=api_key)
                        
                        # Create the prompt
                        prompt = f"""
                       **Role**: You are a senior flight operations examiner responsible for drafting and refining commercial pilot navigation exam questions. Your task is to rephrase the following navigation scenario into a precise, professionally formatted test question.

**Guidelines**:
1. Preserve all technical data exactly as provided (TAS, altitudes, waypoints, wind data)
2. Use proper ICAO standard phraseology and terminology throughout
3. Ensure measurement instructions are unambiguous and exam-appropriate
4. Use proper aviation grammar and sentence structure

**Input Question**:
{question_text}

**Output Requirements**:
- Begin with proper ERC chart reference format
- State departure and destination airports with ICAO codes
- Specify flight level clearly
- Group performance data logically (normal operations first, then single-engine)


**Expected Output Format**:


Please refine the input question following these guidelines.
    
                        """

                        
                        try:
                            # Make the API call
                            chat_completion = client.chat.completions.create(
                                messages=[
                                    {
                                        "role": "system",
                                        "content": "You are an aviation expert who specializes in refining technical flight planning questions."
                                    },
                                    {
                                        "role": "user",
                                        "content": prompt
                                    }
                                ],
                                model="llama-3.3-70b-versatile",
                                temperature=0,  # Keep it precise
                                max_tokens=500
                            )
                            
                            # Extract and return the refined text
                            refined_text = chat_completion.choices[0].message.content
                            
                            # Clean up any extra quotes or formatting
                            refined_text = refined_text.strip('"').strip()
                            
                            return refined_text
                            
                        except Exception as e:
                            raise ValueError(f"Failed to refine question with Groq API: {str(e)}") from e

                #print(question_text)
               
                
                
                details = QuestionDetails(
                    departure=dep,
                    arrival=arr,
                    land1=eland,
                    land2=eland2,
                    cruise_level=cruise_level,
                    tas_normal=tas_normal,
                    tas_single_engine=tas_used,
                    wind_normal={"direction": wind_dir_used, "speed": wind_speed_normal},
                    wind_single_engine={"direction": wind_dir_used, "speed": wind_speed_used},
                    shape_type=selected["shapeType"],
                    reference=selected["reference"],
                    rondom_choice=reference_point
               
                )
                
                question = CurrentQuestion(question=question_text, details=details)
                
                tas_single = tas_single_engine
                wind_speed_single = wind_speed_single
                wind_dir_single = wind_dir_single % 360
                
                if P1 == P2 or P3 == P4 or tas_single <= 0 or wind_speed_single < 0:
                    logging.debug(f"Invalid parameters: P1={P1}, P2={P2}, P3={P3}, P4={P4}, tas={tas_single}, wind_speed={wind_speed_single}")
                    continue
                
                geodesic_results = calculate_geodesic1(P1, P2, P3, P4, tas_single, wind_speed_single, wind_dir_single)
                geodesic_results_1=calculate_geodesic1(P5,P6,P7,P8,tas_single,wind_speed_single,wind_dir_single)
                
                if geodesic_results and geodesic_results_1 is None:
                    logging.warning(f"Geodesic calculation failed for: {dep.code}-{arr.code}-{eland.code}-{eland2.code}")
                    continue
                
                distance_p3 = geodesic_results['distance_to_P3_nm_1']
                distance_p4 = geodesic_results['distance_to_P4_nm']
                critical_point_data = geodesic_results.get('critical_point')
                if isinstance(critical_point_data, (list, tuple)) and len(critical_point_data) == 2:
                    critical_point_obj = Point(critical_point_data[0], critical_point_data[1])
                elif hasattr(critical_point_data, 'lat') and hasattr(critical_point_data, 'long'):
                    critical_point_obj = critical_point_data
                else:
                    logging.error(f"Invalid critical_point type: {type(critical_point_data)}")
                    continue
                
                nav = Navigation()
                mid_house = nav.get_midpoint(critical_point_obj, eland)
                mid_land1 = nav.get_midpoint(critical_point_obj, eland2) 
                course_from_home = nav.get_track_angle(mid_house, eland)
                course_from_land1 = nav.get_track_angle(mid_land1, eland2)
                
                def calculate_ground_speed(true_course, tas, wind_dir, wind_speed):
                    """
                    Calculate ground speed given true course, true airspeed, wind direction, and wind speed.
                    
                    Args:
                        true_course (float): Intended flight path in degrees (clockwise from north).
                        tas (float): True airspeed in knots.
                        wind_dir (float): Direction wind is coming from in degrees (clockwise from north).
                        wind_speed (float): Wind speed in knots.
                    
                    Returns:
                        float: Ground speed in knots.
                    """
                    tc_rad = math.radians(true_course)
                    wd_rad = math.radians(wind_dir)
                    wca_rad = math.asin((wind_speed / tas) * math.sin(wd_rad - tc_rad))
                    gs = tas * math.cos(wca_rad) - wind_speed * math.cos(wd_rad - tc_rad)
                    return gs
                
                gs = calculate_ground_speed(course_from_home, tas_single, wind_dir_single, wind_speed_single)
                cs = calculate_ground_speed(course_from_land1, tas_single, wind_dir_single, wind_speed_single)
                
                time_p3 = distance_p3 / gs
                time_p4 = distance_p4 / cs
                time = time_p3 - time_p4
                
                if abs(time) > 0.008333333:
                    logging.debug(f"Time difference {time*60:.2f} minutes exceeds 2 minutes")
                    continue
                
                # Ensure question is a CurrentQuestion object before calculating critical point
                if not isinstance(question, CurrentQuestion):
                    logging.error(f"Invalid question type: {type(question)}, value: {question}")
                    continue
                
                try:
                    logging.debug(f"Before calculate_critical_point: type(question)={type(question)}, question={question}")
                    critical_point = self.calculate_critical_point(question)
                    if critical_point is not None:
                        return question
                    else:
                        logging.debug(f"Critical point calculation returned None")
                except Exception as e:
                    logging.debug(f"Critical point calculation failed: {str(e)}")
                    continue
                    
            except Exception as e:
                logging.debug(f"Attempt {attempts} failed: {str(e)}")
                continue
        
        raise ValueError(f"Could not generate valid question for reference")