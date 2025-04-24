import random
import math
from typing import Dict, List, NamedTuple
import logging
from sample_airport import *
from cal_func import calculate_geodesic
class Airport:
    def __init__(self, code, name, lat, long, reference):
        self.code = code
        self.name = name
        self.lat = lat
        self.long = long
        self.reference = reference

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
        max_attempts = 200
        attempts = 0
        
        if num_airports not in [3, 4]:
            raise ValueError("num_airports must be 3 or 4")

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
                    eland = dep
                    eland2 = selected["eland2"]
                
                cruise_level = random.choice([150, 170, 190, 210, 230])
                tas_normal = random.randint(40, 60) * 5
                tas_single_engine = int(random.randint(30, 60) * 5)
                
                track = self.get_track_angle(dep, arr)
                wind_dir_normal = random.randint(20, 36) * 10
                wind_speed_normal = int(40 + random.random() * 30)*5
                wind_dir_single = random.randint(20, 36) * 10
                raw_speed = wind_speed_normal * (0.8 + random.random() * 0.4)
                wind_speed_single = min(int(round(raw_speed / 5) * 5), 95)
                P1 = (dep.lat, dep.long)
                P2 = (arr.lat, arr.long)
                P3 = (eland.lat, eland.long)
                P4 = (eland2.lat, eland2.long)
                def format_latitude(lat):
                    degrees = abs(int(lat))  # Get absolute value of degrees (integer part)
                    direction = 'N' if lat >= 0 else 'S'  # Determine direction
                    return f"{degrees:02d} {direction}"  # Format as two digits and direction

                # Function to format longitude
                def format_longitude(lon):
                    degrees = abs(int(lon))  # Get absolute value of degrees (integer part)
                    direction = 'E' if lon >= 0 else 'W'  # Determine direction
                    return f"{degrees:02d} {direction}"  # Format as two digits and direction

# Format coordinates for each point
                formatted_lat = format_latitude(P1[0])
                formatted_long = format_longitude(P1[1])

                formatted_lat_1 = format_latitude(P2[0])
                formatted_long_1 = format_longitude(P2[1])

                formatted_lat_3 = format_latitude(P3[0])
                formatted_long_3 = format_longitude(P3[1])

                formatted_lat_4 = format_latitude(P4[0])
                formatted_long_4 = format_longitude(P4[1])
                question_text = (
                    f"Refer ERC {selected['reference']}. You are planning a flight from {dep.name}{formatted_lat,formatted_long}{dep.code} to {arr.name} {formatted_lat_1,formatted_long_1}{arr.code}"
                    f"   with a TAS of {tas_normal} kt for normal operations "
                    f"and single engine TAS of {tas_single_engine} kt. WV {wind_dir_normal}M / {wind_speed_normal} kt "
                    f"at FL{cruise_level} (normal ops crz), WV {wind_dir_single}M / {wind_speed_single} kt for single "
                    f"engine cruise level. Your calculation of the location of the single engine CP (Critical Point) "
                    f"for {eland.name}{formatted_lat_3,formatted_long_3} and {eland2.name}{formatted_lat_4,formatted_long_4}, on the {dep.code} - {arr.code} track, measured as a distance "
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
                
                P1 = (dep.lat, dep.long)
                P2 = (arr.lat, arr.long)
                P3 = (eland.lat, eland.long)
                P4 = (eland2.lat, eland2.long)
                tas_single = tas_single_engine
                wind_speed_single = wind_speed_single
                wind_dir_single = wind_dir_single % 360
                
                if P1 == P2 or P3 == P4 or tas_single <= 0 or wind_speed_single < 0:
                    logging.debug(f"Invalid parameters: P1={P1}, P2={P2}, P3={P3}, P4={P4}, tas={tas_single}, wind_speed={wind_speed_single}")
                    continue
                
                geodesic_results = calculate_geodesic(P1, P2, P3, P4, tas_single, wind_speed_single, wind_dir_single)
                
                if geodesic_results is None:
                    logging.warning(f"Geodesic calculation failed for: {dep.code}-{arr.code}-{eland.code}-{eland2.code}")
                    if selected["shapeType"] == "triangle":
                        P4_mod = (P4[0] + 0.0001, P4[1] + 0.0001)
                        geodesic_results = calculate_geodesic(P1, P2, P3, P4_mod, tas_single, wind_speed_single, wind_dir_single)
                        if geodesic_results is None:
                            continue
                    else:
                        # For parallelogram, try perturbing P3 and P4 slightly
                        P3_mod = (P3[0] + random.uniform(-0.001, 0.001), P3[1] + random.uniform(-0.001, 0.001))
                        P4_mod = (P4[0] + random.uniform(-0.001, 0.001), P4[1] + random.uniform(-0.001, 0.001))
                        geodesic_results = calculate_geodesic(P1, P2, P3_mod, P4_mod, tas_single, wind_speed_single, wind_dir_single)
                        if geodesic_results is None:
                            continue
                
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
