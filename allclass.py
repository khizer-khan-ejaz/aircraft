import random
import math
from typing import Dict, List, NamedTuple
import logging
from sample_airport import *
from cal_func import calculate_geodesic
from geographiclib.geodesic import Geodesic
class Point:
    def __init__(self, lat, long):
        self.lat = lat
        self.long = long
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
    
    def get_track_angle(self, dep, arr):
        lat1 = math.radians(dep.lat)
        lon1 = math.radians(dep.long)
        lat2 = math.radians(arr.lat)
        lon2 = math.radians(arr.long)
        
        dlon = lon2 - lon1
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        bearing = math.degrees(math.atan2(y, x))
        bearing = (bearing + 360) % 360
        
        return bearing
    
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

            # Define maximum distances for each reference level
            max_distances = {
                'L1': 226.415095,
                'L2': 220.858896,
                'L3': 187.5,
                'L4':327.27272700000003,
                'L5':346.153846,
                'L6':  500 ,
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
                    
                    # Calculate all required distances
                    P1 = (dep.lat, dep.long)
                    P2 = (arr.lat, arr.long)
                    P3 = (eland.lat, eland.long)
                    P4 = (eland2.lat, eland2.long)
                    
                    # Calculate distances using geodesic
                    geod = Geodesic.WGS84
                    
                    # P1-P2 distance
                    p1p2 = geod.Inverse(P1[0], P1[1], P2[0], P2[1])
                    p1p2_dist = p1p2['s12'] / 1852.0  # Convert meters to nautical miles
                    
                    # P3-P4 distance
                    p3p4 = geod.Inverse(P3[0], P3[1], P4[0], P4[1])
                    p3p4_dist = p3p4['s12'] / 1852.0
                    
                    # Midpoint of P1-P2
                    mp_p1p2 = geod.InverseLine(P1[0], P1[1], P2[0], P2[1]).Position(0.5)
                    mp_p1p2_point = (mp_p1p2['lat2'], mp_p1p2['lon2'])
                    
                    # Midpoint of P3-P4
                    mp_p3p4 = geod.InverseLine(P3[0], P3[1], P4[0], P4[1]).Position(0.5)
                    mp_p3p4_point = (mp_p3p4['lat2'], mp_p3p4['lon2'])
                    
                    # Distance between midpoints
                    mid_dist = geod.Inverse(mp_p1p2_point[0], mp_p1p2_point[1], 
                                        mp_p3p4_point[0], mp_p3p4_point[1])
                    mid_dist_nm = mid_dist['s12'] / 1852.0
                    
                    # Check all distance constraints
                    if (p1p2_dist > max_distance or 
                        p3p4_dist > max_distance or 
                        mid_dist_nm > max_distance):
                        logging.debug(f"Distance constraints not met for {specified_reference}: "
                                    f"P1-P2={p1p2_dist:.2f}nm, P3-P4={p3p4_dist:.2f}nm, "
                                    f"Midpoints={mid_dist_nm:.2f}nm (max={max_distance}nm)")
                        continue
                    
                    # Rest of your existing code for question generation...
                    cruise_level = random.choice([150, 170, 190, 210, 230])
                    normal_min, normal_max = 240, 250
                    single_min, single_max = 180, 200

                    normal_choices = list(range(normal_min, normal_max + 1, 5))
                    single_choices = list(range(single_min, single_max + 1, 5))

                    tas_normal = random.choice(normal_choices)
                    tas_single_engine = random.choice(single_choices)
                    
                    track = 270
                    wind_dir_raw = (track + 180 + (random.random() - 0.5) * 60) % 360
                    wind_dir_rounded = round(wind_dir_raw / 10) * 10
                    if wind_dir_rounded < 100:
                        wind_dir_rounded += 100
                    wind_dir_rounded = min(wind_dir_rounded, 350)
                    wind_dir_normal = int(wind_dir_rounded)
                    min_speed = 40
                    max_speed = 70
                    possible_values = list(range(min_speed, max_speed + 1, 5))
                    wind_speed_normal = random.choice(possible_values)
                    
                    wind_dir_raw = (wind_dir_normal + (random.random() - 0.5) * 20) % 360
                    wind_dir_rounded = round(wind_dir_raw / 10) * 10
                    if wind_dir_rounded < 100:
                        wind_dir_rounded += 100
                    wind_dir_rounded = min(wind_dir_rounded, 350)
                    wind_dir_single = int(wind_dir_rounded)
                    raw_speed = wind_speed_normal * (0.8 + random.random() * 0.4)
                    rounded_speed = round(raw_speed / 5) * 5
                    if rounded_speed >= 90:
                        rounded_speed = 85
                    wind_speed_single = int(rounded_speed)
                    
                    question_text = (
                        f"Refer ERC {selected['reference']}. You are planning a flight from {dep.name} to {arr.name} "
                        f"direct  at FL{cruise_level} with a TAS of {tas_normal} kt for normal operations "
                        f"and single engine TAS of {tas_single_engine} kt. WV {wind_dir_normal}M / {wind_speed_normal} kt "
                        f"at FL{cruise_level} (normal ops crz), WV {wind_dir_single}M / {wind_speed_single} kt for single "
                        f"engine cruise level. Your calculation of the location of the single engine CP (Critical Point) "
                        f"for {eland.name} and {eland2.name}, on the {dep.code} - {arr.code} track, measured as a distance "
                        f"from {dep.name} is -"
                    )
                    
                    details = QuestionDetails(
                        departure=dep,
                        arrival=arr,
                        land1=eland,
                        land2=eland2,
                        cruise_level=cruise_level,
                        tas_normal=tas_normal,
                        tas_single_engine=tas_single_engine,
                        wind_normal={"direction": wind_dir_normal, "speed": wind_speed_normal},
                        wind_single_engine={"direction": wind_dir_single, "speed": wind_speed_single},
                        shape_type=selected["shapeType"],
                        reference=selected["reference"]
                    )
                    
                    question = CurrentQuestion(question=question_text, details=details)
                    
                    tas_single = tas_single_engine
                    wind_speed_single = wind_speed_single
                    wind_dir_single = wind_dir_single % 360
                    
                    if P1 == P2 or P3 == P4 or tas_single <= 0 or wind_speed_single < 0:
                        logging.debug(f"Invalid parameters: P1={P1}, P2={P2}, P3={P3}, P4={P4}, tas={tas_single}, wind_speed={wind_speed_single}")
                        continue
                    
                    # Compute geodesic results
                    geodesic_results = calculate_geodesic(P1, P2, P3, P4, tas_single, wind_speed_single, wind_dir_single)
                    
                    if geodesic_results is None:
                        logging.warning(f"Geodesic calculation failed for: {dep.code}-{arr.code}-{eland.code}-{eland2.code}")
                        continue
                    
                    # Calculate time difference
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
                    course_from_home = self.get_track_angle(eland, critical_point_obj)
                    course_from_land1 = self.get_track_angle(critical_point_obj, eland2)
                    
                    # Calculate groundspeeds using wind effects (from Flask code's calculate_wind_effects)
                    def calculate_wind_effects(true_course, tas, wind_dir, wind_speed):
                        tc_rad = math.radians(true_course)
                        wd_rad = math.radians(wind_dir)
                        wca_rad = math.asin((wind_speed / tas) * math.sin(wd_rad - tc_rad))
                        gs = tas * math.cos(wca_rad) + wind_speed * math.cos(wd_rad - tc_rad)
                        return gs
                    
                    gs = calculate_wind_effects(course_from_home, tas_single, wind_dir_single, wind_speed_single)
                    cs = calculate_wind_effects(course_from_land1, tas_single, wind_dir_single, wind_speed_single)
                    
                    time_p3 = distance_p3 / gs
                    time_p4 = distance_p4 / cs
                    time = time_p3 - time_p4
                    
                    # Check if time difference is within 2 minutes (0.03333 hours)
                    if abs(time) > 0.033333333333:
                        logging.debug(f"Time difference {time*60:.2f} minutes exceeds 2 minutes")
                        continue
                    
                    # Try to calculate critical point
                    try:
                        critical_point = self.calculate_critical_point(question)
                        if critical_point is not None:
                            return question
                        else:
                            logging.debug(f"Critical point calculation returned None")
                    except Exception as e:
                        logging.debug(f"Critical point calculation failed: {str(e)}")
                        
                except Exception as e:
                    logging.debug(f"Attempt {attempts} failed: {str(e)}")
                    continue
                    
            raise ValueError(f"Could not generate valid question for reference {specified_reference} after {max_attempts} attempts")