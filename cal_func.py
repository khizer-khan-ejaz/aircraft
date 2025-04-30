import folium
from geographiclib.geodesic import Geodesic
import scipy.optimize as optimize
import logging
from allclass import *
from sample_airport import *
from folium.plugins import MousePosition
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
    distance_to_P3= int(geod.Inverse(perp_nm_p1p2_intersection[0], perp_nm_p1p2_intersection[1], P3[0], P3[1])['s12'] / 1000)
    distance_to_P4=int(geod.Inverse(perp_nm_p1p2_intersection[0], perp_nm_p1p2_intersection[1], P4[0], P4[1])['s12'] / 1000)
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
        'distance_to_P3_nm_1': (distance_to_P3 * 0.539957),
        'distance_to_P4_nm': (distance_to_P4 * 0.539957),
    }
    
    return results