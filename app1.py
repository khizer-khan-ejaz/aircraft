from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import random
import math
from typing import Dict, List, NamedTuple
import folium
from geographiclib.geodesic import Geodesic
import scipy.optimize as optimize
import logging
from folium.plugins import MousePosition
# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:5000"]}})

# Geodesic calculation function (modified for robustness)
def calculate_geodesic(P1, P2, P3, P4, TAS, wind_speed, degree):
    geod = Geodesic.WGS84
    g_P3_P4 = geod.Inverse(P3[0], P3[1], P4[0], P4[1])
    distance_P3_P4_nm = g_P3_P4['s12'] / 1852  
    def geodesic_intersection(line1_start, line1_end, line2_start, line2_end):
        def distance_between_lines(params):
            s1, s2 = params
            line1 = geod.InverseLine(line1_start[0], line1_start[1], line1_end[0], line1_end[1])
            line2 = geod.InverseLine(line2_start[0], line2_start[1], line2_end[0], line2_end[1])
            
            if line1.s13 == 0 or line2.s13 == 0:
                return float('inf')
                
            point1 = line1.Position(s1 * line1.s13, Geodesic.STANDARD | Geodesic.LONG_UNROLL)
            point2 = line2.Position(s2 * line2.s13, Geodesic.STANDARD | Geodesic.LONG_UNROLL)
            g = geod.Inverse(point1['lat2'], point1['lon2'], point2['lat2'], point2['lon2'])
            return g['s12']
        
        line1_check = geod.Inverse(line1_start[0], line1_start[1], line1_end[0], line1_end[1])
        line2_check = geod.Inverse(line2_start[0], line2_start[1], line2_end[0], line2_end[1])
        
        if line1_check['s12'] < 1000 or line2_check['s12'] < 1000:  # Ensure lines are long enough
            return None, None
        
        initial_guess = [0.5, 0.5]
        try:
            result = optimize.minimize(distance_between_lines, initial_guess, method='Nelder-Mead', bounds=[(0, 1), (0, 1)])
            if not result.success or result.fun > 1000:  # Allow small intersection errors
                logging.warning("Optimization failed or intersection too far")
                return None, None
            line1 = geod.InverseLine(line1_start[0], line1_start[1], line1_end[0], line1_end[1])
            line2 = geod.InverseLine(line2_start[0], line2_start[1], line2_end[0], line2_end[1])
            
            point1 = line1.Position(result.x[0] * line1.s13, Geodesic.STANDARD | Geodesic.LONG_UNROLL)
            point2 = line2.Position(result.x[1] * line2.s13, Geodesic.STANDARD | Geodesic.LONG_UNROLL)
            intersection = ((point1['lat2'] + point2['lat2']) / 2, (point1['lon2'] + point2['lon2']) / 2)
            g = geod.Inverse(point1['lat2'], point1['lon2'], point2['lat2'], point2['lon2'])
            
            dist_p1_to_inter = geod.Inverse(P1[0], P1[1], intersection[0], intersection[1])['s12']
            dist_p2_to_inter = geod.Inverse(P2[0], P2[1], intersection[0], intersection[1])['s12']
            dist_p1_to_p2 = geod.Inverse(P1[0], P1[1], P2[0], P2[1])['s12']
            
            if dist_p1_to_p2 < 1000:  # Ensure reasonable distance
                return None, None
                
            if dist_p1_to_inter + dist_p2_to_inter > dist_p1_to_p2 * 1.1:  # Relaxed tolerance
                return None, None
            
            return intersection, g['s12']
        except Exception as e:
            logging.error(f"Optimization error: {str(e)}")
            return None, None

    def generate_geodesic_points(start, end, num_points=100):
        line = geod.InverseLine(start[0], start[1], end[0], end[1])
        
        if line.s13 < 1000 or num_points <= 1:
            return [(start[0], start[1])], line
            
        ds = line.s13 / (num_points - 1)
        points = []
        for i in range(num_points):
            s = ds * i
            g = line.Position(s, Geodesic.STANDARD | Geodesic.LONG_UNROLL)
            points.append((g['lat2'], g['lon2']))
        return points, line

    # Input validation
    if any(coord is None for coord in [P1, P2, P3, P4]) or P1 == P2 or P3 == P4 or TAS <= 0 or wind_speed < 0:
        logging.warning(f"Invalid input: P1={P1}, P2={P2}, P3={P3}, P4={P4}, TAS={TAS}, wind_speed={wind_speed}")
        return None
    
    mid_C_D = ((P3[0] + P4[0]) / 2, (P3[1] + P4[1]) / 2)
    
    g_CD = geod.Inverse(P3[0], P3[1], P4[0], P4[1])
    bearing_CD = g_CD['azi1']
    perp_bearing = (bearing_CD + 90) % 360

    if g_CD['s12'] < 1000:  # Ensure reasonable distance
        return None

    p1_p2_geodesic, _ = generate_geodesic_points(P1, P2)
    p3_p4_geodesic, _ = generate_geodesic_points(P3, P4)

    perp_distance = 1000000
    perp_point1 = geod.Direct(mid_C_D[0], mid_C_D[1], perp_bearing, perp_distance)
    perp_point1 = (perp_point1['lat2'], perp_point1['lon2'])
    perp_point2 = geod.Direct(mid_C_D[0], mid_C_D[1], (perp_bearing + 180) % 360, perp_distance)
    perp_point2 = (perp_point2['lat2'], perp_point2['lon2'])
    perp_geodesic, _ = generate_geodesic_points(perp_point1, perp_point2)

    p1p2_perp_intersection, p1p2_dist = geodesic_intersection(P1, P2, perp_point1, perp_point2)
    if p1p2_perp_intersection is None:
        logging.warning("No intersection between P1-P2 and perpendicular line")
        return None
        
    distance_to_P3_nm = (geod.Inverse(p1p2_perp_intersection[0], p1p2_perp_intersection[1], P3[0], P3[1])['s12'] / 1000) * 0.539957
    if distance_to_P3_nm < 0.1:  # Avoid division by zero
        return None
    
    distance_to_degree = (distance_to_P3_nm / TAS) * wind_speed
    
    line_distance = distance_to_degree * 1852
    nm_line_point = geod.Direct(p1p2_perp_intersection[0], p1p2_perp_intersection[1], degree, line_distance)
    nm_line_end_point = (nm_line_point['lat2'], nm_line_point['lon2'])
    nm_geodesic, _ = generate_geodesic_points(p1p2_perp_intersection, nm_line_end_point)

    g_p1p2 = geod.Inverse(P1[0], P1[1], P2[0], P2[1])
    p1p2_bearing = g_p1p2['azi1']
    perp_to_p1p2_bearing = (p1p2_bearing + 90) % 360

    perp_nm_distance = 1000000
    perp_nm_point1 = geod.Direct(nm_line_end_point[0], nm_line_end_point[1], perp_to_p1p2_bearing, perp_nm_distance)
    perp_nm_point1 = (perp_nm_point1['lat2'], perp_nm_point1['lon2'])
    perp_nm_point2 = geod.Direct(nm_line_end_point[0], nm_line_end_point[1], (perp_to_p1p2_bearing + 180) % 360, perp_nm_distance)
    perp_nm_point2 = (perp_nm_point2['lat2'], perp_nm_point2['lon2'])
    perp_nm_geodesic, _ = generate_geodesic_points(perp_nm_point1, perp_nm_point2)

    perp_nm_p1p2_intersection, p1p2_nm_dist = geodesic_intersection(P1, P2, perp_nm_point1, perp_nm_point2)
    if perp_nm_p1p2_intersection is None:
        logging.warning("No perpendicular intersection with P1-P2")
        return None
    
    distance_to_P1 = geod.Inverse(perp_nm_p1p2_intersection[0], perp_nm_p1p2_intersection[1], P1[0], P1[1])['s12'] / 1000

    # Create base map with OpenSky Network tiles
    my_map = folium.Map(
        location=p1p2_perp_intersection,
        zoom_start=6,
      
        attr='OpenSky Network',
        name='OpenSky',
        control_scale=True
    )
    
    # Add IFR Low chart as an additional tile layer
    folium.TileLayer(
    tiles='https://tileservice.charts.noaa.gov/tiles/50k_enrl/{z}/{x}/{y}.png',
    attr='FAA - IFR Low Enroute Charts',
    name='IFR Low Altitude',
    overlay=False,
    min_zoom=0,
    max_zoom=10  # Adjust based on server support   
    ).add_to(my_map)
    # Add layer control to toggle between tile layers
    folium.LayerControl().add_to(my_map)
    
    # Add mouse position for coordinate reference
    MousePosition().add_to(my_map)

    # Add all the original visualization elements
    folium.PolyLine(p1_p2_geodesic, color='purple', weight=3, tooltip='P1 to P2').add_to(my_map)
    folium.PolyLine(p3_p4_geodesic, color='orange', weight=3, tooltip='P3 to P4').add_to(my_map)
    folium.PolyLine(perp_geodesic, color='red', weight=3, tooltip='Perpendicular Line').add_to(my_map)
    folium.PolyLine(nm_geodesic, color='blue', weight=3, tooltip=f'{degree}-Degree Line').add_to(my_map)
    folium.PolyLine(perp_nm_geodesic, color='green', weight=3, tooltip='Perpendicular to P1-P2').add_to(my_map)

    folium.Marker(location=p1p2_perp_intersection, popup=f'Initial Intersection\nLat: {p1p2_perp_intersection[0]:.6f}\nLon: {p1p2_perp_intersection[1]:.6f}', icon=folium.Icon(color='black', icon='info-sign')).add_to(my_map)
    folium.Marker(location=nm_line_end_point, popup=f'{degree}-Degree Line End\nLat: {nm_line_end_point[0]:.6f}\nLon: {nm_line_end_point[1]:.6f}', icon=folium.Icon(color='blue', icon='arrow-up')).add_to(my_map)
    folium.Marker(location=perp_nm_p1p2_intersection, popup=f'Perpendicular Intersection\nLat: {perp_nm_p1p2_intersection[0]:.6f}\nLon: {perp_nm_p1p2_intersection[1]:.6f}', icon=folium.Icon(color='green', icon='crosshair')).add_to(my_map)

    points = {'P1': P1, 'P2': P2, 'C (P3)': P3, 'D (P4)': P4}
    colors = {'P1': 'blue', 'P2': 'blue', 'C (P3)': 'green', 'D (P4)': 'green'}
    for label, coords in points.items():
        folium.Marker(location=coords, popup=f"{label}\nLat: {coords[0]:.6f}\nLon: {coords[1]:.6f}", icon=folium.Icon(color=colors[label])).add_to(my_map)

    map_html = my_map._repr_html_()

    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {"name": "P1 to P2", "color": "purple"}, "geometry": {"type": "LineString", "coordinates": [[p[1], p[0]] for p in p1_p2_geodesic]}},
            {"type": "Feature", "properties": {"name": "P3 to P4", "color": "orange"}, "geometry": {"type": "LineString", "coordinates": [[p[1], p[0]] for p in p3_p4_geodesic]}},
            {"type": "Feature", "properties": {"name": "Perpendicular Line", "color": "red"}, "geometry": {"type": "LineString", "coordinates": [[p[1], p[0]] for p in perp_geodesic]}},
            {"type": "Feature", "properties": {"name": f"{degree}-Degree Line", "color": "blue"}, "geometry": {"type": "LineString", "coordinates": [[p[1], p[0]] for p in nm_geodesic]}},
            {"type": "Feature", "properties": {"name": "Perpendicular to P1-P2", "color": "green"}, "geometry": {"type": "LineString", "coordinates": [[p[1], p[0]] for p in perp_nm_geodesic]}}
        ]
    }
    
    for label, coords in points.items():
        geojson_data["features"].append({"type": "Feature", "properties": {"name": label, "color": colors[label]}, "geometry": {"type": "Point", "coordinates": [coords[1], coords[0]]}})

    key_points = {"Initial Intersection": p1p2_perp_intersection, f"{degree}-Degree Line End": nm_line_end_point, "Perpendicular Intersection": perp_nm_p1p2_intersection}
    for label, coords in key_points.items():
        geojson_data["features"].append({"type": "Feature", "properties": {"name": label}, "geometry": {"type": "Point", "coordinates": [coords[1], coords[0]]}})
        
    steps = [
            {
                "step_number": 1,
                "title": "Calculate Critical Point Distance",
                "description": f"Calculate Distance Between Critical Landing Airports: Compute the straight-line distance between {P3} to {P4} using their geographic coordinates.",
                "calculation": f"Distance from {P3} to {P4}",
                "result": " nautical miles"
            },
            {
                "step_number": 2,
                "title": f"Determine Midpoint of {P3} to {P4}",
                "description": "Identify the midpoint along the line connecting the two critical landing airports by averaging their coordinates."
            },
            {
                "step_number": 3,
                "title": f"Draw {P1} to {P2} and Find Intersection",
                "description": "Construct a straight line from the source airport to the destination airport. "
                            "From the midpoint (Step 2), draw a perpendicular line intersecting the source-to-destination line. "
                            "Record the coordinates of this intersection point."
            },
            {
                "step_number": 4,
                "title": f"Calculate Distance from Critical Airports to Intersection",
                "description": "Compute the distance from one of the critical landing airports to the intersection point identified in Step 3.",
                "result": f"{distance_to_P3_nm} nautical miles from departure"
            },
            {
                "step_number": 5,
                "title": "Compute Distance Length Influenced by Wind",
                "description": "This calculates a length adjusted for wind impact based on the provided TAS and wind speed.",
                "formula": f"(distance from intersection to critical airports) / {TAS}) × {wind_speed}",
                "result": f"{degree} nm"
            },
            {
                "step_number": 6,
                "title": "Construct Wind-Adjusted Line",
                "description": f"From the intersection point (Step 3), create a line segment with a length equal to the wind-adjusted distance (Step 5). "
                            f"Orient this line in the direction of {degree} degrees."
            },
            {
                "step_number": 7,
                "title": "Draw Perpendicular Line to Source-Destination Line",
                "description": "From the endpoint of the wind-adjusted line (Step 6), draw a perpendicular line intersecting the source-to-destination line. "
                            "Record the coordinates of this new intersection point."
            },
            {
                "step_number": 8,
                "title": "Calculate Distance from Source to Final Intersection",
                "description": "Using the intersection point from Step 7 on the source-to-destination line, compute the distance from this point to the departure airport.",
                "result": f"{distance_to_P1 * 0.539957} nm"
            }
        ]
        
    results = {
        'p1p2_perp_intersection': {'lat': p1p2_perp_intersection[0], 'lon': p1p2_perp_intersection[1]},
        'nm_line_end_point': {'lat': nm_line_end_point[0], 'lon': nm_line_end_point[1]},
        'perp_nm_p1p2_intersection': {'lat': perp_nm_p1p2_intersection[0], 'lon': perp_nm_p1p2_intersection[1]},
        'p1p2_nm_dist_km': p1p2_nm_dist / 1000,
        'distance_to_P1_nm': distance_to_P1 * 0.539957,
        'distance_to_P3_nm': distance_to_P3_nm,
        'distance_to_degree': distance_to_degree,
        'geojson': geojson_data,
        'map_html': map_html,
        "steps": steps,
        "OPTION-A": distance_to_P1 * 0.539957,
        "OPTION-B": (distance_to_P1 * 0.539957)+190,
        "OPTION-C": (distance_to_P1 * 0.539957)-190,
        "OPTION-D": (distance_to_P1 * 0.539957)-100,
        'distance_p3_p4': distance_P3_P4_nm,
    }
    
    return results

# Airport and question generation classes (unchanged)
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
                normal_min, normal_max = 240, 250
                single_min, single_max = 180, 200

                # Convert to possible multiples of 5
                normal_choices = list(range(normal_min, normal_max + 1, 5))
                single_choices = list(range(single_min, single_max + 1, 5))

                # Randomly select from these choices
                tas_normal = random.choice(normal_choices)
                tas_single_engine = random.choice(single_choices)
                
                track = 270
                wind_dir_raw = (track + 180 + (random.random() - 0.5) * 60) % 360

# Round to nearest multiple of 10
                wind_dir_rounded = round(wind_dir_raw / 10) * 10

                # Ensure it's a 3-digit number (100-359)
                if wind_dir_rounded < 100:
                    wind_dir_rounded += 100
                    
                # Make sure it doesn't exceed 359
                wind_dir_rounded = min(wind_dir_rounded, 350)

                wind_dir_normal = int(wind_dir_rounded)
                min_speed = 40
                max_speed = 70
                possible_values = list(range(min_speed, max_speed + 1, 5))  # [40, 45, 50, 55, 60, 65, 70]

                # Randomly select from these values
                wind_speed_normal = random.choice(possible_values)
                wind_dir_raw = (wind_dir_normal + (random.random() - 0.5) * 20) % 360

# Round to nearest multiple of 10
                wind_dir_rounded = round(wind_dir_raw / 10) * 10

                # Ensure it's a 3-digit number (100-359)
                if wind_dir_rounded < 100:
                    wind_dir_rounded += 100
                    
                # Make sure it doesn't exceed 359
                wind_dir_rounded = min(wind_dir_rounded, 350)

                wind_dir_single = int(wind_dir_rounded)
                raw_speed = wind_speed_normal * (0.8 + random.random() * 0.4)

# Round to nearest multiple of 5
                rounded_speed = round(raw_speed / 5) * 5

                # Ensure it's less than 90
                if rounded_speed >= 90:
                    rounded_speed = 85  # Next multiple of 5 below 90

                wind_speed_single = int(rounded_speed)
                
                question_text = (
                    f"Refer ERC {selected['reference']}. You are planning a flight from {dep.name} to {arr.name} "
                    f"direct (draw the track) at FL{cruise_level} with a TAS of {tas_normal} kt for normal operations "
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

# Sample airport data (unchanged)
sample_airports = [
    Airport("HLT", "Hamilton Airport", -37.64997, 142.06181, "L1"),
    Airport("MGB", "Mount Gambier Airport", -37.824429, 140.783783, "L1"),
    Airport("MEL", "Melbourne Airport", -37.663712, 144.844788, "L1"),
    Airport("MBW", "Moorabbin Airport", -37.976654, 145.097290, "L1"),
    Airport("AVV", "Avalon Airport", -38.044249, 144.472564, "L1"),
    Airport("KNS", "King Island Airport", -39.878548, 143.882933, "L1"),
    Airport("SXE", "East Sale Airport", -38.098889, 147.149444, "L1"),
    Airport("TGN", "Latrobe Valley Airport", -38.204332516, 146.468831458, "L1"),
    Airport("BWT", "Wynyard Airport", -40.9989014, 145.7310028, "L1"),
    Airport("HBA", "Hobart Airport", -42.8361015, 147.5099945, "L1"),
    Airport("LST", "Launceston Airport", -41.5452995, 147.2140045, "L1"),
    Airport("WYA", "Whyalla Airport", -33.0588989, 137.5140076, "L2"),
    Airport("YPED", "RAAF Base Edinburgh", -34.7024994, 138.6210022, "L2"),
    Airport("YPPF", "Parafield Airport", -34.789330176, 138.626497494, "L2"),
    Airport("ADL", "Adelaide Airport", -34.940329572, 138.5249979, "L2"),
    Airport("MQL", "Mildura Airport", -34.22416577, 142.084666328, "L2"),
    Airport("SWH", "Swan Hill Airport", -35.372165178, 143.526331228, "L2"),
    Airport("SHT", "Shepparton Airport", -36.423998304, 145.388831778, "L2"),
    Airport("YMNG", "Mangalore Airport", -36.886329788, 145.183832598, "L2"),
    Airport("MEL", "Melbourne Airport", -37.68583059, 144.837663316, "L2"),
    Airport("SXE", "East Sale Airport", -26.4390917, 133.281323, "L2"),
    Airport("TGN", "Latrobe Valley Airport", -38.204332516, 146.468831458, "L2"),
    Airport("MBW", "Moorabbin Airport", -37.972662776, 145.100999596, "L2"),
    Airport("WGA", "Wagga Wagga Airport", -35.15916603, 147.459831494, "L2"),
    Airport("CWW", "Corowa Airport", -35.989829374, 146.353598586, "L2"),
    Airport("ABX", "Albury Airport", -36.067333064, 146.954829514, "L2"),
    Airport("PKE", "Parkes Airport", -33.1348094608, 148.234092397, "L2"),
    Airport("GFF", "Griffith Airport", -34.252165658, 146.055166446, "L2"),
    Airport("CWT", "Cowra Airport", -33.839329976, 148.641247435, "L2"),
    Airport("BHS", "Bathurst Airport", -33.405665044, 149.651164062, "L2"),
    Airport("XRH", "RAAF Base Richmond", -33.5999976, 150.774663568, "L2"),
    Airport("SYD", "Sydney Kingsford Smith Airport", -33.947346, 151.179428, "L2"),
    Airport("GUL", "Goulburn Airport", -34.800996796, 149.717663796, "L2"),
    Airport("WOL", "Shellharbour Airport", -34.583332, 150.866669, "L2"),
    Airport("CBR", "Canberra Airport", -35.30416545, 149.190332572, "L2"),
    Airport("NOA", "HMAS Albatross (Nowra) Airport", -34.948889, 150.536944, "L2"),
    Airport("OOM", "Cooma–Snowy Mountains Airport", -36.2999988, 148.9833294, "L2"),
    Airport("MIM", "Merimbula Airport", -36.905163046, 149.900163066, "L2"),
    Airport("XMC", "Mallacoota Airport", -37.5999976, 149.7166638, "L2"),
    Airport("RMA", "Roma Airport", -26.569444, 148.783611, "L3"),
    Airport("SGO", "St George Airport", -28.043166494, 148.590497638, "L3"),
    Airport("WGE", "Walgett Airport", -30.032778, 148.125833, "L3"),
    Airport("DBO", "Dubbo City Regional Airport", -32.218165794, 148.571331048, "L3"),
    Airport("PKE", "Parkes Airport", -33.1348094608, 148.234092397, "L3"),
    Airport("CWT", "Cowra Airport", -33.839329976, 148.641247435, "L3"),
    Airport("YTOG", "Togo Station Airport", -30.0821991, 149.5319977, "L3"),
    Airport("NAA", "Narrabri Airport", -30.326111, 149.776111, "L3"),
    Airport("MRZ", "Moree Airport", -29.464411, 149.845108, "L3"),
    Airport("DGE", "Mudgee Airport", -32.599167, 149.586944, "L3"),
    Airport("BHS", "Bathurst Airport", -33.411111, 149.578611, "L3"),
    Airport("XRH", "RAAF Base Richmond", -33.599561, 150.751419, "L3"),
    Airport("MTL", "Maitland Airport", -32.7048, 151.4890, "L3"),
    Airport("TMW", "Tamworth Airport", -31.091944, 150.934167, "L3"),
    Airport("IVR", "Inverell Airport", -29.782000, 151.118000, "L3"),
    Airport("YAMB", "RAAF Base Amberley", -27.633333, 152.716667, "L3"),
    Airport("MCY", "Sunshine Coast Airport", -26.650000, 153.066666, "L3"),
    Airport("BNE", "Brisbane Airport", -27.4673, 153.0233, "L3"),
    Airport("SHQ", "Southport Airport", -27.966667, 153.4, "L3"),
    Airport("OOL", "Gold Coast Airport", -28.016666, 153.399994, "L3"),
    Airport("BNK", "Ballina Byron Gateway Airport", -28.8333, 153.5333, "L3"),
    Airport("GFN", "Grafton Airport", -29.6901, 152.9333, "L3"),
    Airport("CFS", "Coffs Harbour Airport", -30.2963, 153.1135, "L3"),
    Airport("PQQ", "Port Macquarie Airport", -31.4333, 152.9000, "L3"),
    Airport("NTL", "Newcastle Airport", -32.8090, 151.8390, "L3"),
    Airport("SYD", "Sydney Kingsford Smith Airport", -33.865143, 151.209900, "L3"),
    Airport("BWU", "Bankstown Airport", -33.917290, 151.035889, "L3"),
    Airport("WOL", "Illawarra Regional Airport", -34.425072, 150.893143, "L3"),
    Airport("OKY", "Oakey Army Aviation Centre", -27.4331, 151.7167, "L3"),
    Airport("CNS", "Cairns Airport", -16.8858, 145.7553, "L4"),
    Airport("TSV", "Townsville Airport", -19.2525, 146.7647, "L4"),
    Airport("KCE", "Collinsville Airport", -20.5967, 147.8600, "L4"),
    Airport("PPP", "Whitsunday Coast Airport", -20.4950, 148.5517, "L4"),
    Airport("MKY", "Mackay Airport", -21.1692, 149.1763, "L4"),
    Airport("ROK", "Rockhampton Airport", -23.3819, 150.4750, "L4"),
    Airport("GLT", "Gladstone Airport", -23.8697, 151.2229, "L4"),
    Airport("BDB", "Bundaberg Airport", -24.9039, 152.3190, "L4"),
    Airport("MCY", "Sunshine Coast Airport", -26.6020, 153.0880, "L4"),
    Airport("BNE", "Brisbane Airport", -27.3833, 153.1183, "L4"),
    Airport("OOL", "Gold Coast Airport", -28.1590, 153.5030, "L4"),
    Airport("IVR", "Inverell Airport", -29.8883, 151.1440, "L4"),
    Airport("OKY", "Oakey Army Aviation Centre", -27.4070, 151.7343, "L4"),
    Airport("RMA", "Roma Airport", -26.5450, 148.7740, "L4"),
    Airport("EMD", "Emerald Airport", -23.5687, 148.1734, "L4"),
    Airport("HGD", "Hughenden Airport", -20.8150, 144.2250, "L4"),
    Airport("LRE", "Longreach Airport", -23.4340, 144.2800, "L4"),
    Airport("CTL", "Charleville Airport", -26.4133, 146.2610, "L4"),
    Airport("SGO", "St George Airport", -28.0497, 148.5950, "L4"),
    Airport("WGE", "Walgett Airport", -30.0328, 148.1220, "L4"),
    Airport("MRZ", "Moree Airport", -29.4989, 149.8450, "L4"),
    Airport("NAA", "Narrabri Airport", -30.3192, 149.8270, "L4"),
    Airport("CMA", "Cunnamulla Airport", -28.0300, 145.6220, "L4"),
    Airport("WNR", "Windorah Airport", -25.4131, 142.6670, "L4"),
    Airport("ISA", "Mount Isa Airport", -20.6639, 139.4890, "L4"),
    Airport("PKE", "Parkes Airport", -33.1314, 148.2388, "L5"),
    Airport("DBO", "Dubbo City Regional Airport", -32.2167, 148.575, "L5"),
    Airport("WGE", "Walgett Airport", -30.0328, 148.126, "L5"),
    Airport("SGO", "St George Airport", -28.0497, 148.595, "L5"),
    Airport("CTL", "Charleville Airport", -26.4133, 146.261, "L5"),
    Airport("HGD", "Hughenden Airport", -20.815, 144.225, "L5"),
    Airport("GFF", "Griffith Airport", -34.2508, 146.067, "L5"),
    Airport("CAZ", "Cobar Airport", -31.5383, 145.796, "L5"),
    Airport("BRK", "Bourke Airport", -30.0392, 145.952, "L5"),
    Airport("CMA", "Cunnamulla Airport", -28.03, 145.621, "L5"),
    Airport("LRE", "Longreach Airport", -23.4342, 144.281, "L5"),
    Airport("WDH", "Windorah Airport", -25.4131, 142.667, "L5"),
    Airport("BHQ", "Broken Hill Airport", -32.0014, 141.472, "L5"),
    Airport("MQL", "Mildura Airport", -34.2292, 142.085, "L5"),
    Airport("MOO", "Moomba Airport", -28.0992, 140.195, "L5"),
    Airport("BVI", "Birdsville Airport", -25.8975, 139.348, "L5"),
    Airport("BQL", "Boulia Airport", -22.9133, 139.9, "L5"),
    Airport("ISA", "Mount Isa Airport", -20.6639, 139.4890, "L5"),
    Airport("CNJ", "Cloncurry Airport", -20.6683, 140.504, "L5"),
    Airport("PHD", "Port Hedland International Airport", -20.4389, 118.6733, "L6"),
    Airport("TNC", "Tennant Creek Airport", -19.6489, 134.2440, "L6"),
    Airport("ISA", "Mount Isa Airport", -20.6633, 139.4880, "L6"),
    Airport("CNJ", "Cloncurry Airport", -20.6683, 140.5040, "L6"),
    Airport("HUD", "Hughenden Airport", -20.6230, 144.1820, "L6"),
    Airport("BME", "Broome International Airport", -17.9481, 122.2350, "L6"),
    Airport("DRB", "Derby Airport", -17.3170, 123.9130, "L6"),
    Airport("CRU", "Curtin Springs Airport", -23.6680, 133.8670, "L6"),
    Airport("ARG", "Argyle Airport", -15.0330, 127.6330, "L6"),
    Airport("HLS", "Halls Creek Airport", -18.2390, 127.6660, "L6"),
    Airport("SWE", "Sweers Airport", -21.5000, 123.5000, "L6"),
    Airport("NTN", "Normanton Airport", -17.9550, 141.5400, "L6"),
    Airport("BKT", "Burketown Airport", -18.2160, 139.9950, "L6"),
    Airport("CNS", "Cairns Airport", -16.9180, 145.7550, "L6"),
    Airport("KNU", "Kununurra Airport", -15.7780, 128.7540, "L6"),
    Airport("TID", "Tindal Airport", -14.5700, 132.3700, "L6"),
    Airport("GTE", "Groote Eylandt Airport", -13.6470, 136.9100, "L6"),
    Airport("COE", "Coen Airport", -15.6000, 143.8910, "L6"),
    Airport("LKR", "Lockhart River Airport", -14.7870, 144.2730, "L6"),
    Airport("WEI", "Weipa Airport", -12.6810, 141.9250, "L6"),
    Airport("GOV", "Gove Airport", -12.6670, 136.8450, "L6"),
    Airport("MNG", "Maningrida Airport", -12.4170, 134.6520, "L6"),
    Airport("DRW", "Darwin International Airport", -12.4140, 130.8810, "L6"),
    Airport("HKC", "Hooker Creek Airport", -26.3850, 133.9780, "L6"),
    Airport("HID", "Horn Island Airport", -10.5860, 142.2190, "L6"),
    Airport("HKC", "Halls Creek", -18.2331, 127.6724, "L7"),
    Airport("WBT", "Warburton", -26.1287, 126.5797, "L7"),
    Airport("FOR", "Forrest", -30.8549, 128.0994, "L7"),
    Airport("HOK", "Hooker Creek", -18.3282, 130.6372, "L7"),
    Airport("AYQ", "Ayers Rock", -25.1721, 130.9748, "L7"),
    Airport("CBP", "Coober Pedy", -29.0318, 134.7238, "L7"),
    Airport("CED", "Ceduna", -32.1265, 133.7270, "L7"),
    Airport("PLO", "Port Lincoln", -34.6044, 135.8733, "L7"),
    Airport("WMA", "Woomera", -31.1435, 136.8083, "L7"),
    Airport("ASP", "Alice Springs", -23.7929, 133.8782, "L7"),
    Airport("TCA", "Tennant Creek", -19.6347, 134.1819, "L7"),
    Airport("MRR", "Marree", -30.5987, 138.4423, "L7"),
    Airport("LEC", "Leigh Creek", -30.5987, 138.4423, "L7"),
    Airport("EDH", "Edinburgh", -34.7770, 138.6000, "L7"),
    Airport("WYA", "Whyalla", -33.0581, 137.5242, "L7"),
    Airport("EPR", "Esperance Airport", -33.6844, 121.8220, "L8"),
    Airport("WCD", "Carosue Dam Airport", -30.1742, 122.3225, "L8"),
    Airport("KGI", "Kalgoorlie-Boulder Airport", -30.7894, 121.4620, "L8"),
    Airport("DCN", "RAAF Base Curtin", -17.5817, 123.8283, "L8"),
    Airport("DRB", "Derby Airport", -17.3700, 123.6609, "L8"),
    Airport("ALH", "Albany Airport", -34.9433, 117.8083, "L8"),
    Airport("LNO", "Leonora Airport", -28.8781, 121.3150, "L8"),
    Airport("LER", "Leinster Airport", -27.8433, 120.7033, "L8"),
    Airport("YLAW", "Lawlers Airport", -28.0919, 120.5408, "L8"),
    Airport("WUN", "Wiluna Airport", -26.6292, 120.2206, "L8"),
    Airport("YJUN", "Jundee Airport", -26.4217, 120.5770, "L8"),
    Airport("ZNE", "Newman Airport", -23.4178, 119.8030, "L8"),
    Airport("BME", "Broome International Airport", -17.9497, 122.2278, "L8"),
    Airport("PHE", "Port Hedland International Airport", -20.3733, 118.6225, "L8"),
    Airport("PBO", "Paraburdoo Airport", -23.1711, 117.7450, "L8"),
    Airport("MKR", "Meekatharra Airport", -26.6117, 118.5472, "L8"),
    Airport("MMG", "Mount Magnet Airport", -28.1161, 117.8428, "L8"),
    Airport("YLG", "Yalgoo Airport", -28.3450, 116.6819, "L8"),
    Airport("CXD", "Cunderdin Airport", -31.6228, 117.2200, "L8"),
    Airport("PER", "Perth Airport", -31.9403, 115.9669, "L8"),
    Airport("BQB", "Busselton Margaret River Airport", -33.6872, 115.4017, "L8"),
    Airport("JAD", "Jandakot Airport", -32.0975, 115.8819, "L8"),
    Airport("PEA", "RAAF Base Pearce", -31.6678, 116.0147, "L8"),
    Airport("YGIN", "Gingin Airport", -31.6367, 115.6783, "L8"),
    Airport("YBRM", "Beermullah Airport", -31.2317, 115.7133, "L8"),
    Airport("GET", "Geraldton Airport", -28.7961, 114.7075, "L8"),
    Airport("CVQ", "Carnarvon Airport", -24.8800, 113.6719, "L8"),
    Airport("LEA", "Learmonth Airport", -22.2356, 114.0886, "L8"),
    Airport("KTA", "Karratha Airport", -20.7122, 116.7733, "L8"),
]

# Initialize generator
generator = AirportQuestionGenerator(sample_airports)

@app.route('/generate_question', methods=['POST'])
def generate_question_endpoint():
    try:
        # Parse the JSON request data
        data = request.get_json()
        if not data or 'reference' not in data or 'num_airports' not in data or 'marks' not in data:
            return jsonify({'error': 'Missing required parameters: reference, num_airports, and marks are required'}), 400
        
        # Extract parameters
        reference = data['reference']
        num_airports = int(data['num_airports'])
        marks = int(data['marks'])

        # Validate reference
        if not reference.startswith('L') or not reference[1:].isdigit() or int(reference[1:]) < 1 or int(reference[1:]) > 8:
            return jsonify({'error': 'Invalid reference format. Must be L1 through L8'}), 400
        
        # Validate num_airports
        if num_airports not in [3, 4]:
            return jsonify({'error': 'Number of airports must be 3 or 4'}), 400
        
        # Validate marks
        if marks not in [2, 3]:
            return jsonify({'error': 'Marks must be 2 or 3'}), 400

        # Generate the base question
        question = generator.generate_question_with_reference(reference, num_airports)
        
        # Extract details for geodesic calculation
        dep = question.details.departure
        arr = question.details.arrival
        land1 = question.details.land1
        land2 = question.details.land2
        tas_normal = question.details.tas_single_engine
        wind_speed = question.details.wind_single_engine['speed']
        wind_dir = question.details.wind_single_engine['direction'] % 360
        
        P1 = (dep.lat, dep.long)
        P2 = (arr.lat, arr.long)
        P3 = (land1.lat, land1.long)
        P4 = (land2.lat, land2.long)
        
        # Calculate geodesic results, which include the P3-P4 distance
        geodesic_results = calculate_geodesic(P1, P2, P3, P4, tas_normal, wind_speed, wind_dir)
        if not geodesic_results:
            logging.error("Geodesic calculation failed after retries")
            return jsonify({'error': 'Failed to generate valid geodesic configuration. Please try again.'}), 500
        
        # Base question text from the generator
        base_question = question.question
        
        # Modify question text based on marks
        if marks == 2:
            # For 2-mark questions, include the P3-P4 distance
            distance_p3_p4 = geodesic_results['distance_p3_p4']
            additional_text = f" Given that the distance between {land1.name} and {land2.name} is {distance_p3_p4:.1f} nm,"
            # Insert the additional text before "is -"
            parts = base_question.split("is -")
            if len(parts) == 2:
                full_question = parts[0] + additional_text + " is -"
            else:
                full_question = base_question  # Fallback if "is -" is not found
        else:
            # For 3-mark questions, use the base question without the distance
            full_question = base_question

        # Prepare the response
        return jsonify({
            'question': full_question,
            'details': {
                'departure': dep.code,
                'departure_name': dep.name,
                'arrival': arr.code,
                'arrival_name': arr.name,
                'land1': land1.code,
                'land1_name': land1.name,
                'land2': land2.code,
                'land2_name': land2.name,
                'cruise_level': question.details.cruise_level,
                'tas_normal': question.details.tas_normal,
                'tas_single_engine': question.details.tas_single_engine,
                'wind_normal': question.details.wind_normal,
                'wind_single_engine': question.details.wind_single_engine,
                'shape_type': question.details.shape_type,
                'reference': question.details.reference,
                'geodesic': geodesic_results
            }
        })
    except ValueError as ve:
        logging.error(f"ValueError: {str(ve)}")
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'online',
        'endpoints': {
            '/generate_question': 'POST - Generate questions for specific reference and num_airports',
            '/question': 'GET - Display question and map interface'
        }
    })

@app.route('/question')
def display_question():
    return render_template('question.html')

# Error handlers
@app.errorhandler(400)
def bad_request(e):
    return jsonify({'error': str(e.description)}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Resource not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)