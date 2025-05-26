from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import random
import math
from typing import Dict, List, NamedTuple
import folium
from geographiclib.geodesic import Geodesic
import scipy.optimize as optimize
import logging
from PIL import Image
from io import BytesIO
import base64
from folium.plugins import MousePosition
class Point:
    def __init__(self, lat, long):
        self.lat = lat
        self.long = long
# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:5000", "http://localhost:5173", "null"]}})

# Define chart configuration with bounds and rotation angles
CHART_CONFIGS = {
    'L1': {
        'bounds': [[-37.2272322, 140.180078], [-43.4776, 151.4275]],
        'rotation': -90,
        'path': 'L1.jpg'
    },
    'L2': {
        'bounds' : [[ -32.9641,  137.2906], [ -38.2339,  151.8275]],
        'rotation': -90,
        'path': 'L2-new1.jpg'
    },
    'L3': {
        'bounds': [[-25.2248, 145.1294], [-35.4676, 156.8039]],
        'rotation': -370,
        'path': 'L32.jpg'
    },
    'L4': {
        'bounds': [[-13.4399, 138.1804], [-32.4676, 155.4039]],
        'rotation': 40,
        'path': 'L4.jpg'
    },
    'L5': {
        'bounds': [[-20.0167,137.2716], [  -34.7597,    150.2039]],
        'rotation': 3,
        'path': 'L5.jpg'
    },
    'L6': {
        'bounds': [[-2.6577,117.5537], [-24.9870,   147.0850]],
        'rotation': 84,
        'path': 'L6.jpg'
    },
    'L7': {
        'bounds': [[   -18.0258,    124.5537], [     -38.9870,   140.0850]],
        'rotation': 0,
        'path': 'L7.jpg'
    },
    'L8': {
        'bounds': [[-16.0258,113.3568], [-36.0870,125.0850]],
        'rotation': 0,
        'path': 'L8.jpg'
    }    
}

# Populate default configurations for L1-L8 if not already present
default_chart_bounds = [[-45, 110], [-10, 155]]
default_chart_rotation = 0
for i in range(1, 9):
    chart_key = f'L{i}'
    if chart_key not in CHART_CONFIGS:
        logging.info(f"Chart '{chart_key}' not in CHART_CONFIGS, adding default placeholder using '{chart_key}.jpg'.")
        CHART_CONFIGS[chart_key] = {
            'bounds': default_chart_bounds,
            'rotation': default_chart_rotation,
            'path': f'{chart_key}.jpg'
        }

def create_map_with_chart(chart_id='L1', geodesic_results=None, airports_list_param=None):
    target_chart_id_for_config = chart_id
    if chart_id not in CHART_CONFIGS:
        logging.warning(f"Chart ID '{chart_id}' not found in CHART_CONFIGS. Attempting to use 'L1' as fallback.")
        if 'L1' in CHART_CONFIGS:
            target_chart_id_for_config = 'L1'
        elif CHART_CONFIGS:
            target_chart_id_for_config = list(CHART_CONFIGS.keys())[0]
            logging.warning(f"Default 'L1' not in configs, using first available: '{target_chart_id_for_config}'.")
        else:
            logging.error("No chart configurations available. Creating a basic map without any chart overlay.")
            m = folium.Map(location=[-25, 135], zoom_start=4, tiles="OpenStreetMap")
            if geodesic_results and 'geojson' in geodesic_results and geodesic_results['geojson']:
                folium.GeoJson(geodesic_results['geojson'], name="Geodesic Data").add_to(m)
            folium.LayerControl().add_to(m)
            return m

    chart_config = CHART_CONFIGS[target_chart_id_for_config]

    center_lat = (chart_config['bounds'][0][0] + chart_config['bounds'][1][0]) / 2
    center_lon = (chart_config['bounds'][0][1] + chart_config['bounds'][1][1]) / 2
    m = folium.Map(location=[center_lat, center_lon], zoom_start=6, min_zoom=4)

    folium.TileLayer('openstreetmap', name="OpenStreetMap (Base)", zindex=0, control=True).add_to(m)

    chart_overlay_added = False
    try:
        image_path = chart_config['path']
        logging.info(f"Attempting to load chart image for '{target_chart_id_for_config}' from: {image_path}")
        image = Image.open(chart_config['path']).convert("RGBA")  # Resize to reduce memory
        bg = Image.new("RGBA", image.size, (255, 255, 255, 0))
        composed_image = Image.alpha_composite(bg, image)
        
        try:
            rotated_image = composed_image.rotate(chart_config['rotation'], expand=True, fillcolor=(255,255,255,0))
        except Exception as e:
            logging.error(f"Failed to rotate image for {target_chart_id_for_config}: {e}", exc_info=True)
            rotated_image = composed_image  # Fallback to unrotated image

        buffered = BytesIO()
        rotated_image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

        folium.raster_layers.ImageOverlay(
            name=f'IFR Chart: {target_chart_id_for_config}',
            image=f"data:image/png;base64,{img_str}",
            bounds=chart_config['bounds'],
            opacity=1,
            interactive=True,
            cross_origin=False,
            zindex=1,
            show=True
        ).add_to(m)
        logging.info(f"Successfully added chart overlay for {target_chart_id_for_config} from {image_path}")
        chart_overlay_added = True
    except FileNotFoundError:
        logging.error(f"Chart image file NOT FOUND for {target_chart_id_for_config} at {chart_config['path']}. No chart overlay will be added.")
    except Exception as e:
        logging.error(f"Error processing chart image {chart_config.get('path', 'N/A')} for {target_chart_id_for_config}: {e}", exc_info=True)

    folium.TileLayer(
        tiles='https://tiles.openaip.net/geowebcache/service/tms/1.0.0/ifrlow@EPSG:900913@png/{z}/{x}/{y}.png',
        attr='OpenAIP IFR Low Chart (Tiles © OpenAIP contributors)',
        name='OpenAIP IFR Low (Tiles)',
        overlay=True, control=True, show=False, zindex=0
    ).add_to(m)

    folium.TileLayer(
        tiles='https://tileservice.charts.noaa.gov/tiles/50k_enrl/{z}/{x}/{y}.png',
        attr='FAA - IFR Low Enroute Charts (Tiles)',
        name='FAA IFR Low (Tiles)',
        overlay=True, control=True, show=False, zindex=0
    ).add_to(m)

    if geodesic_results and 'geojson' in geodesic_results and \
       isinstance(geodesic_results['geojson'], dict) and 'features' in geodesic_results['geojson'] and isinstance(geodesic_results['geojson']['features'], list):
        logging.info("Adding geodesic features from geojson_data.")
        fg_geodesic = folium.FeatureGroup(name="Geodesic Calculations", show=True, control=True)
        for feature in geodesic_results['geojson']['features']:
            props = feature.get('properties', {})
            name = props.get('name', 'Unnamed Feature')
            geom_type = feature.get('geometry', {}).get('type')
            coordinates = feature.get('geometry', {}).get('coordinates')

            if not geom_type or not coordinates:
                logging.warning(f"Skipping feature '{name}' due to missing geometry type or coordinates.")
                continue

            if geom_type == 'LineString':
                color = props.get('color', 'blue')
                line_coords = [[pt[1], pt[0]] for pt in coordinates if isinstance(pt, (list, tuple)) and len(pt) == 2]
                if line_coords:
                    folium.PolyLine(
                        locations=line_coords, color=color,
                        weight=props.get('weight', 3), opacity=props.get('opacity', 0.9),
                        tooltip=name
                    ).add_to(fg_geodesic)
            elif geom_type == 'Point':
                color = props.get('color', 'red')
                icon_name = props.get('icon_name', 'info-sign')
                icon_prefix = props.get('icon_prefix', 'glyphicon')
                lon, lat = coordinates
                folium.Marker(
                    location=[lat, lon],
                    popup=folium.Popup(f"<b>{name}</b><br>Lat: {lat:.5f}<br>Lon: {lon:.5f}", max_width=300),
                    tooltip=name,
                    icon=folium.Icon(color=color, icon=icon_name, prefix=icon_prefix)
                ).add_to(fg_geodesic)
        fg_geodesic.add_to(m)
    else:
        logging.warning("Geodesic results or GeoJSON data is missing/malformed. No geodesic features added.")

    if airports_list_param:
        logging.info(f"Adding {len(airports_list_param)} airports from 'airports_list_param'.")
        fg_airports = folium.FeatureGroup(name="Key Airports (from param)", show=True, control=True)
        airport_coords_for_line = []
        for ap_obj in airports_list_param:
            if hasattr(ap_obj, 'lat') and hasattr(ap_obj, 'long'):
                airport_coords_for_line.append([ap_obj.lat, ap_obj.long])
                folium.Marker(
                    location=[ap_obj.lat, ap_obj.long],
                    popup=f"<b>{getattr(ap_obj, 'code', 'N/A')}: {getattr(ap_obj, 'name', 'N/A')}</b><br>Lat: {ap_obj.lat:.5f}<br>Long: {ap_obj.long:.5f}",
                    tooltip=f"Airport: {getattr(ap_obj, 'code', 'N/A')}",
                    icon=folium.Icon(color='darkblue', icon='plane', prefix='fa')
                ).add_to(fg_airports)
        if len(airport_coords_for_line) > 1:
            folium.PolyLine(
                locations=airport_coords_for_line, color='darkred', weight=1, opacity=0.6, dash_array='5, 5',
                tooltip='Connection between Key Airports (from param)'
            ).add_to(fg_airports)
        fg_airports.add_to(m)

    m.add_child(folium.LatLngPopup())
    MousePosition(position='topright', separator=' | Lng: ', empty_string='NaN', prefix="Lat:").add_to(m)
    folium.LayerControl(collapsed=False, zindex=10).add_to(m)
    return m

def calculate_geodesic(P1, P2, P3, P4, TAS, wind_speed, degree,chart_id):
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

    perp_distance = 100000
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

    perp_nm_distance = 100000
    perp_nm_point1 = geod.Direct(nm_line_end_point[0], nm_line_end_point[1], perp_to_p1p2_bearing, perp_nm_distance)
    perp_nm_point1 = (perp_nm_point1['lat2'], perp_nm_point1['lon2'])
    perp_nm_point2 = geod.Direct(nm_line_end_point[0], nm_line_end_point[1], (perp_to_p1p2_bearing + 180) % 360, perp_nm_distance)
    perp_nm_point2 = (perp_nm_point2['lat2'], perp_nm_point2['lon2'])
    perp_nm_geodesic, _ = generate_geodesic_points(perp_nm_point1, perp_nm_point2)

    perp_nm_p1p2_intersection, p1p2_nm_dist = geodesic_intersection(P1, P2, perp_nm_point1, perp_nm_point2)
    if perp_nm_p1p2_intersection is None:
        logging.warning("No perpendicular intersection with P1-P2")
        return None
    critical_point=(perp_nm_p1p2_intersection[0], perp_nm_p1p2_intersection[1])
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
        tiles='https://tiles.openaip.net/geowebcache/service/tms/1.0.0/ifrlow@EPSG:900913@png/{z}/{x}/{y}.png',
        attr='OpenAIP IFR Low Chart',
        name='IFR Low Chart',
        overlay=True,
        control=True
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

   
    

    geojson_data = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "name": "Track (P1 to P2)",
                "color": "purple",
                "weight": 3
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [[p[1], p[0]] for p in p1_p2_geodesic]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "name": "Critical Airports Line (P3 to P4)",
                "color": "orange",
                "weight": 3
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [[p[1], p[0]] for p in p3_p4_geodesic]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "name": "Perp. to P3-P4 Midline",
                "color": "magenta",
                "weight": 2,
                "opacity": 0.7
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [[p[1], p[0]] for p in perp_geodesic]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "name": f"{degree}-Degree Offset Line",
                "color": "blue",
                "weight": 3
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [[p[1], p[0]] for p in nm_geodesic]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "name": "Perp. from Offset to Track (defines CP)",
                "color": "green",
                "weight": 3
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [[p[1], p[0]] for p in perp_nm_geodesic]
            }
        }
    ]
}
    points_definitions = {
        'P1 (Departure)': {'coords': P1, 'color': 'cadetblue', 'icon_name': 'plane', 'icon_prefix': 'fa'},
        'P2 (Arrival)': {'coords': P2, 'color': 'cadetblue', 'icon_name': 'flag-checkered', 'icon_prefix': 'fa'},
        'P3 (Critical Airport 1)': {'coords': P3, 'color': 'darkred', 'icon_name': 'hospital-o', 'icon_prefix': 'fa'},
        'P4 (Critical Airport 2)': {'coords': P4, 'color': 'darkred', 'icon_name': 'hospital-o', 'icon_prefix': 'fa'},
        'Initial Intersection': {'coords': p1p2_perp_intersection, 'color': 'black', 'icon_name': 'circle-o', 'icon_prefix': 'fa'},
        f'Offset Line End ({degree}°)': {'coords': nm_line_end_point, 'color': 'darkblue', 'icon_name': 'arrow-right', 'icon_prefix': 'fa'},
        'Critical Point (CP)': {'coords': perp_nm_p1p2_intersection, 'color': 'red', 'icon_name': 'crosshairs', 'icon_prefix': 'fa'}
    }
    for name, p_info in points_definitions.items():
        if p_info['coords']:
            geojson_data["features"].append({
                "type": "Feature",
                "properties": {"name": name, "color": p_info['color'], "icon_name": p_info['icon_name'], "icon_prefix": p_info['icon_prefix']},
                "geometry": {"type": "Point", "coordinates": [p_info['coords'][1], p_info['coords'][0]]}
            })
    map_obj = create_map_with_chart(chart_id=chart_id, geodesic_results={'geojson': geojson_data}, airports_list_param=None)
    map_html_output = map_obj._repr_html_()
    for label, coords in points.items():
        geojson_data["features"].append({"type": "Feature", "properties": {"name": label, "color": colors[label]}, "geometry": {"type": "Point", "coordinates": [coords[1], coords[0]]}})

    key_points = {"Initial Intersection": p1p2_perp_intersection, f"{degree}-Degree Line End": nm_line_end_point, "Perpendicular Intersection": perp_nm_p1p2_intersection}
    for label, coords in key_points.items():
        geojson_data["features"].append({"type": "Feature", "properties": {"name": label}, "geometry": {"type": "Point", "coordinates": [coords[1], coords[0]]}})
        
    
    results = {
        'p1p2_perp_intersection': {'lat': p1p2_perp_intersection[0], 'lon': p1p2_perp_intersection[1]},
        'nm_line_end_point': {'lat': nm_line_end_point[0], 'lon': nm_line_end_point[1]},
        'perp_nm_p1p2_intersection': {'lat': perp_nm_p1p2_intersection[0], 'lon': perp_nm_p1p2_intersection[1]},
        'p1p2_nm_dist_km': p1p2_nm_dist / 1000,
        'distance_to_P1_nm': int(distance_to_P1 * 0.539957),
        'distance_to_P3_nm': distance_to_P3_nm,
        'distance_to_degree': distance_to_degree,
        'geojson': geojson_data,
        'map_html': map_html_output,
        
        "OPTION-A": distance_to_P1 * 0.539957,
        "OPTION-B": (distance_to_P1 * 0.539957)+190,
        "OPTION-C": (distance_to_P1 * 0.539957)-190,
        "OPTION-D": (distance_to_P1 * 0.539957)-100,
        'distance_p3_p4': distance_P3_P4_nm,
        'distance_to_P3_nm_1': (distance_to_P3 * 0.539957),
        'distance_to_P4_nm': (distance_to_P4 * 0.539957),
        'critical_point':critical_point,
    }
    
    return results
def calculate_geodesic1(P1, P2, P3, P4, TAS, wind_speed, degree):
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
    critical_point=(perp_nm_p1p2_intersection[0], perp_nm_p1p2_intersection[1])
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
        tiles='https://tiles.openaip.net/geowebcache/service/tms/1.0.0/ifrlow@EPSG:900913@png/{z}/{x}/{y}.png',
        attr='OpenAIP IFR Low Chart',
        name='IFR Low Chart',
        overlay=True,
        control=True
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
        
    
    results = {
        'p1p2_perp_intersection': {'lat': p1p2_perp_intersection[0], 'lon': p1p2_perp_intersection[1]},
        'nm_line_end_point': {'lat': nm_line_end_point[0], 'lon': nm_line_end_point[1]},
        'perp_nm_p1p2_intersection': {'lat': perp_nm_p1p2_intersection[0], 'lon': perp_nm_p1p2_intersection[1]},
        'p1p2_nm_dist_km': p1p2_nm_dist / 1000,
        'distance_to_P1_nm': int(distance_to_P1 * 0.539957),
        'distance_to_P3_nm': distance_to_P3_nm,
        'distance_to_degree': distance_to_degree,
        'geojson': geojson_data,
        'map_html': map_html,
        
        "OPTION-A": distance_to_P1 * 0.539957,
        "OPTION-B": (distance_to_P1 * 0.539957)+190,
        "OPTION-C": (distance_to_P1 * 0.539957)-190,
        "OPTION-D": (distance_to_P1 * 0.539957)-100,
        'distance_p3_p4': distance_P3_P4_nm,
        'distance_to_P3_nm_1': (distance_to_P3 * 0.539957),
        'distance_to_P4_nm': (distance_to_P4 * 0.539957),
        'critical_point':critical_point,
    }
    
    return results
class Airport:
    def __init__(self, code, name, lat, long, reference ):
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
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = math.sin(dLat/2) * math.sin(dLat/2) + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(dLon/2) * math.sin(dLon/2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance_km = R * c
        return distance_km

    def calculate_angle(self, side_a, side_b, side_c_opposite_angle):
        try:
            if not (side_a > 0 and side_b > 0 and side_c_opposite_angle > 0):
                return 0
            if side_a + side_b <= side_c_opposite_angle or \
               side_a + side_c_opposite_angle <= side_b or \
               side_b + side_c_opposite_angle <= side_a:
                return 0
            cos_C_val = (side_a**2 + side_b**2 - side_c_opposite_angle**2) / (2 * side_a * side_b)
            cos_C_val = max(-1.0, min(1.0, cos_C_val))
            angle_C_rad = math.acos(cos_C_val)
            return math.degrees(angle_C_rad)
        except (ZeroDivisionError, ValueError):
            return 0

    def get_track_angle(self, dep: Airport, arr: Airport):
        geod = Geodesic.WGS84
        g = geod.Inverse(dep.lat, dep.long, arr.lat, arr.long)
        bearing = g['azi1']
        return (bearing + 360) % 360

    def is_valid_parallelogram(self, p1, p2, p3, p4):
        geod = Geodesic.WGS84
        dist_p1p2 = geod.Inverse(p1.lat, p1.long, p2.lat, p2.long)['s12']
        dist_p3p4 = geod.Inverse(p3.lat, p3.long, p4.lat, p4.long)['s12']
        dist_p1p3 = geod.Inverse(p1.lat, p1.long, p3.lat, p3.long)['s12']
        dist_p2p4 = geod.Inverse(p2.lat, p2.long, p4.lat, p4.long)['s12']

        tolerance_m = 100000  # Increased from 50000
        if not (abs(dist_p1p2 - dist_p3p4) < tolerance_m and abs(dist_p1p3 - dist_p2p4) < tolerance_m):
            return False

        mid14_lat = (p1.lat + p4.lat) / 2
        mid14_lon = (p1.long + p4.long) / 2
        mid23_lat = (p2.lat + p3.lat) / 2
        mid23_lon = (p2.long + p3.long) / 2

        dist_midpoints = geod.Inverse(mid14_lat, mid14_lon, mid23_lat, mid23_lon)['s12']
        if dist_midpoints > tolerance_m / 2:
            return False

        if dist_p1p2 < 100000 or dist_p1p3 < 100000:
            return False
        return True

    def select_airports_for_shape_with_reference(self, specified_reference, num_airports):
        attempts = 0
        max_attempts = 5000  # Increased from 2000
        excluded_codes = {"YMNG", "MBW", "HLT", "MQL", "MGB", "WYA", "MEL", "HBA"}

        airports_for_ref = [a for a in self.airports if a.reference == specified_reference]
        logging.info(f"Found {len(airports_for_ref)} airports for reference {specified_reference}")
        if not airports_for_ref:
            raise ValueError(f"No airports found for reference {specified_reference}")

        potential_dep_arr = [a for a in airports_for_ref if a.code not in excluded_codes]
        if len(potential_dep_arr) < 2:
            potential_dep_arr = list(airports_for_ref)
        if len(potential_dep_arr) < 2:
            raise ValueError(f"Not enough airports for dep/arr for reference {specified_reference}")
        if len(airports_for_ref) < num_airports:
            raise ValueError(f"Not enough total airports for shape for reference {specified_reference}")

        while attempts < max_attempts:
            attempts += 1
            dep, arr = random.sample(potential_dep_arr, 2)
            remaining_for_elands = [a for a in airports_for_ref if a not in [dep, arr] and a.code not in excluded_codes]
            if not remaining_for_elands and num_airports > 2:
                remaining_for_elands = [a for a in airports_for_ref if a not in [dep, arr]]

            if num_airports == 3:
                if not remaining_for_elands:
                    continue
                eland2 = random.choice(remaining_for_elands)
                eland = dep

                d_dep_arr_km = self.calculate_distance(dep.lat, dep.long, arr.lat, arr.long)
                d_dep_eland2_km = self.calculate_distance(dep.lat, dep.long, eland2.lat, eland2.long)
                d_arr_eland2_km = self.calculate_distance(arr.lat, arr.long, eland2.lat, eland2.long)

                if not (d_dep_arr_km > 50 and d_dep_eland2_km > 50 and d_arr_eland2_km > 50):
                    continue

                sides_sorted = sorted([d_dep_arr_km, d_dep_eland2_km, d_arr_eland2_km])
                if sides_sorted[0] + sides_sorted[1] <= sides_sorted[2] + 1e-2:
                    continue

                angle_at_dep = self.calculate_angle(d_dep_arr_km, d_dep_eland2_km, d_arr_eland2_km)
                angle_at_arr = self.calculate_angle(d_dep_arr_km, d_arr_eland2_km, d_dep_eland2_km)
                angle_at_eland2 = self.calculate_angle(d_dep_eland2_km, d_arr_eland2_km, d_dep_arr_km)
                min_angle_deg = 20
                max_angle_deg = 160
                if not (min_angle_deg < angle_at_dep < max_angle_deg and \
                        min_angle_deg < angle_at_arr < max_angle_deg and \
                        min_angle_deg < angle_at_eland2 < max_angle_deg):
                    continue

                logging.debug(f"Selected triangle: {dep.code}-{arr.code} land1={eland.code} land2={eland2.code} for {specified_reference}")
                return {"dep": dep, "arr": arr, "eland": eland, "eland2": eland2,
                        "shapeType": "triangle", "reference": specified_reference}

            elif num_airports == 4:
                if len(remaining_for_elands) < 2:
                    continue
                eland, eland2 = random.sample(remaining_for_elands, 2)

                if self.calculate_distance(dep.lat, dep.long, arr.lat, arr.long) < 150:
                    continue

                if not self.is_valid_parallelogram(dep, arr, eland, eland2):
                    continue

                logging.debug(f"Selected parallelogram: {dep.code}-{arr.code} land1={eland.code} land2={eland2.code} for {specified_reference}")
                return {"dep": dep, "arr": arr, "eland": eland, "eland2": eland2,
                        "shapeType": "parallelogram", "reference": specified_reference}
        raise ValueError(f"Could not find valid airport configuration for ref {specified_reference}, {num_airports} airports after {max_attempts} attempts")

    def generate_question_with_reference(self, specified_reference, num_airports):
        max_gen_attempts = 2440  # Increased from 10
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
        for attempt in range(max_gen_attempts):
            try:
                selected_airports_info = self.select_airports_for_shape_with_reference(specified_reference, num_airports)
                dep, arr, eland, eland2 = selected_airports_info["dep"], selected_airports_info["arr"], \
                                         selected_airports_info["eland"], selected_airports_info["eland2"]
                P1 = (dep.lat, dep.long)
                P2 = (arr.lat, arr.long)
                P3 = (eland.lat, eland.long)
                P4 = (eland2.lat, eland2.long)
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

                cruise_level = random.choice([150, 170, 190, 210, 230, 250, 270])
                tas_normal = random.choice(list(range(220, 281, 5)))
                tas_single_engine = random.choice(list(range(160, 221, 5)))

                avg_track_deg = self.get_track_angle(dep, arr)
                wind_dir_offset = random.uniform(-60, 60)
                base_wind_dir = (avg_track_deg + 180 + wind_dir_offset) % 360

                wind_dir_normal = round(base_wind_dir / 10.0) * 10
                if wind_dir_normal == 0:
                    wind_dir_normal = 360
                wind_dir_normal = max(10, wind_dir_normal)
                wind_speed_normal = random.choice(list(range(20, 71, 5)))

                wind_dir_single_raw = (wind_dir_normal + random.uniform(-20, 20)) % 360
                wind_dir_single = round(wind_dir_single_raw / 10.0) * 10
                if wind_dir_single == 0:
                    wind_dir_single = 360
                wind_dir_single = max(10, wind_dir_single)
                wind_speed_single = round((wind_speed_normal * random.uniform(0.8, 1.2))/5.0)*5
                wind_speed_single = max(15, min(80, wind_speed_single))

                question_text = (
                    f"Refer ERC {selected_airports_info['reference']}. You are planning a flight from {dep.name} ({dep.code}) to {arr.name} ({arr.code}) "
                    f"direct at FL{cruise_level}. Normal ops: TAS {tas_normal} kt, WV {wind_dir_normal:03.0f}T / {wind_speed_normal} kt. "
                    f"Single engine: TAS {tas_single_engine} kt, WV {wind_dir_single:03.0f}T / {wind_speed_single} kt (at SE cruise level). "
                    f"Calculate the single engine CP between alternates {eland.name} ({eland.code}) and {eland2.name} ({eland2.code}), "
                    f"measured as a distance from {dep.name} ({dep.code}) along the flight planned track. The CP is -"
                )

                q_details = QuestionDetails(
                    departure=dep, arrival=arr, land1=eland, land2=eland2,
                    cruise_level=cruise_level, tas_normal=tas_normal, tas_single_engine=tas_single_engine,
                    wind_normal={"direction": wind_dir_normal, "speed": wind_speed_normal},
                    wind_single_engine={"direction": wind_dir_single, "speed": wind_speed_single},
                    shape_type=selected_airports_info["shapeType"], reference=selected_airports_info["reference"]
                )
                current_q = CurrentQuestion(question=question_text, details=q_details)
                tas_single = tas_single_engine
                wind_speed_single = wind_speed_single
                wind_dir_single = wind_dir_single % 360
                    
                if P1 == P2 or P3 == P4 or tas_single <= 0 or wind_speed_single < 0:
                    logging.debug(f"Invalid parameters: P1={P1}, P2={P2}, P3={P3}, P4={P4}, tas={tas_single}, wind_speed={wind_speed_single}")
                    continue

                geodesic_results = calculate_geodesic1(P1, P2, P3, P4, tas_single, wind_speed_single, wind_dir_single)
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
                course_from_home = self.get_track_angle(critical_point_obj,eland)
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
                    
                if (dep.lat, dep.long) == (arr.lat, arr.long) or \
                   (eland.lat, eland.long) == (eland2.lat, eland2.long):
                    logging.warning(f"Duplicate points selected in attempt {attempt+1}. Retrying.")
                    continue

                logging.info(f"Successfully generated question scenario for {specified_reference} on attempt {attempt+1}.")
                return current_q

            except ValueError as e:
                logging.warning(f"Error during question scenario generation attempt {attempt+1} for {specified_reference}: {str(e)}. Retrying.")
            except Exception as e:
                logging.error(f"Unexpected error during question generation attempt {attempt+1}: {str(e)}", exc_info=True)
        raise ValueError(f"Could not generate valid question scenario for ref {specified_reference} after {max_gen_attempts} attempts.")

sample_airports = [
        Airport("YHMT", "Hamilton ", -37.648008228685455, 142.0591476608094, "L1"),
        Airport("YMTG", "Mount Gambier ", -37.74413175688362, 140.7827877824896, "L1"),
        Airport("YMML", "Melbourne ",-37.66915019557909, 144.8402520816833, "L1"),
        Airport("YMMB", "Moorabbin ", -37.97567474904334, 145.09471550908984, "L1"),
        Airport("YMAV", "Avalon ", -38.03888072296835, 144.4684221536711, "L1"),
        Airport("YKII", "King Island ", -39.87954610649811, 143.88176246542253, "L1"),
        Airport("YMES", "East Sale ", -38.1054117999142, 147.12861918065798, "L1"),
        Airport("YLTV", "Latrobe Valley ", -38.204332516, 146.468831458, "L1"),
        Airport("YWYY", "Wynyard ", -40.9989014, 145.7310028, "L1"),
        Airport("YMHB", "Hobart ", -42.8361015, 147.51067, "L1"),
        Airport("YMLT", "Launceston ", -41.5452995, 147.2140045, "L1"),
        Airport("YWHA", "Whyalla ", -33.0524 ,137.5218, "L2"),
        Airport("YPED", "RAAF Base Edinburgh", -34.701997192, 138.618664192, "L2"),
        Airport("YPPF", "Parafield ",-34.789330176 ,138.626497494, "L2"),
        Airport("YPAD", "Adelaide ", -34.940329572, 138.5249979, "L2"),
        Airport("YMIA", "Mildura ", -34.22416577, 142.084666328, "L2"),
        Airport("YSWH", "Swan Hill ", -35.372165178 ,143.526331228, "L2"),
        Airport("YSHT", "Shepparton ", -36.423998304, 145.388831778, "L2"),
        Airport("YMNG", "Mangalore ", -36.886329788 ,145.183832598, "L2"),
        Airport("YMML", "Melbourne ", -37.660139, 144.842000, "L2"),
        Airport("YMES", "East Sale ",-38.092332964 ,147.1499994, "L2"),
        Airport("YLTV", "Latrobe Valley ", -38.204332516, 146.468831458, "L2"),
        Airport("YMMB", "Moorabbin ", -37.972662776 ,145.100999596, "L2"),
        Airport("YSWG", "Wagga Wagga ", -35.15916603 ,147.459831494, "L2"),
        Airport("YCOR", "Corowa ", -35.989829374 ,146.353598586, "L2"),
        Airport("YMAY", "Albury ", -36.067333064 ,146.954829514, "L2"),
        Airport("YSNW", "Nowra ", -34.9512 ,150.5298, "L2"),
        Airport("YPKS", "Parkes ", -33.1348094608 ,148.234092397, "L2"),
        Airport("YGTH", "Griffith ",-34.252165658 ,146.055166446, "L2"),
        Airport("YHMT", "Hamilton ", -37.648008228685455, 142.0591476608094, "L2"),
        Airport("YMTG", "Mount Gambier ", -37.74413175688362, 140.7827877824896, "L2"),
        Airport("YCWR", "Cowra ", -33.839329976 ,148.641247435, "L2"),
        Airport("YBTH", "Bathurst ", -33.405665044, 149.651164062, "L2"),
        Airport("YSRI", "RAAF Base Richmond", -33.5999976, 150.774663568, "L2"),
        Airport("YSSY", "Sydney Kingsford Smith ", -33.9498935, 151.18196819346, "L2"),
        Airport("YGLB", "Goulburn ", -34.800996796, 149.717663796, "L2"),
        Airport("YSHL", "Wollongong ", -34.56017242708677, 150.7904543381237, "L2"),
        Airport("YSCB", "Canberra ", -35.30514547116734, 149.19345679954466, "L2"),
        Airport("YSNW", "HMAS Albatross (Nowra) ", -34.93806564501446, 150.55627795348977, "L2"),
        Airport("YCOM", "Cooma ", -36.29269167547091, 148.97072575171424, "L2"),
        Airport("YMER", "Merimbula ", -36.909703221940006, 149.902112538259, "L2"),
        Airport("YMCO", "Mallacoota ", -37.59891651521126, 149.72290368535934, "L2"),
        Airport("YMNG", "Mangalore ", -36.8859, 145.1942, "L2"),
        Airport("YPED", "Edinburgh ", -34.7048,138.6124, "L2"),
        Airport("YSCB", "Canberra ", -34.7048,138.6124, "L2"),
        Airport("YSHT", "Shepparton ", -36.4284,145.3960, "L2"),
        Airport("YROM", "Roma ", -26.543959398766567, 148.77921118040965, "L3"),
        Airport("YSGE", "St George ", -28.04673506725657, 148.5944931242954, "L3"),
        Airport("YWLG", "Walgett ", -30.03066532344572, 148.12298012411094, "L3"),
        Airport("YSDU", "Dubbo  ", -32.21857118595852, 148.5696900091599, "L3"),
        Airport("YPKS", "Parkes ", -33.138144677695585, 148.23350662270056, "L3"),
        Airport("YCWR", "Cowra ", -33.84498913866449, 148.65060402459252, "L3"),
        Airport("YTOG", "Togo Station ",-30.320833333333333, 149.8311111111111, "L3"),
        Airport("YWLM", "Williamtown ",-32.80336, 151.82878, "L3"),
        Airport("YBBN", "Narrabri ", -30.318446060832635, 149.82894659742354, "L3"),
        Airport("YMOR", "Moree ", -29.495875265330454, 149.85006048203778, "L3"),
        Airport("YMDG", "Mudgee ", -32.56413099558059, 149.61622278063064, "L3"),
        Airport("YBTH", "Bathurst ", -33.413613818021254, 149.65514451293063, "L3"),
        Airport("YSRI", " Richmond(NSW)", -33.59477130243219, 150.78238889294994, "L3"),
        Airport("YMND", "West Maitland ", -32.7046471425939, 151.48902143987516, "L3"),
        Airport("YSTW", "Tamworth ", -31.084160049880005, 150.8484596262986, "L3"),
        Airport("YIVR", "Inverell ",-29.883617181885416, 151.1410462632321, "L3"),
        Airport("YAMB", "RAAF Base Amberley", -27.628788073120827, 152.7029330224224, "L3"),
        Airport("YBSU", "Sunshine Coast ", -26.59995408512291, 153.08864992608162, "L3"),
        Airport("YWOL", "Wollongong ",-34.55794, 150.79100 , "L3"),
        Airport("YBBE", "Brisbane ", -27.39324306291285, 153.12406685874217, "L3"),
        Airport("YARM", "Armidale ", -30.528055555555557, 151.61722222222224, "L3"),
        Airport("YSPT", "Southport ", -27.92435982604407, 153.37122363963428, "L3"),
        Airport("YBCG", "Gold Coast ",-28.1630074423367, 153.50701287399133, "L3"),
        Airport("YBNA", "Ballina  ", -28.837105046709222, 153.55619760713515, "L3"),
        Airport("YGFN", "Grafton ", -29.704399600459375, 152.93058872305537, "L3"),
        Airport("YCFS", "Coffs Harbour ", -30.322915611953626, 153.11582331011377, "L3"),
        Airport("YPMQ", "Port Macquarie ", -31.43110401026344, 152.86718934588652, "L3"),
        Airport("YWLM", "Newcastle ", -32.79334435639444, 151.8366783515182, "L3"),
        Airport("YSSY", "Sydney Kingsford Smith ", -33.94932813503329, 151.1819145437487, "L3"),
        Airport("YSBK", "Bankstown ", -33.91955471293055, 150.99115188412213, "L3"),
        Airport("YSHL ", "Wollongong ",-34.560207769190235, 150.79046506695988, "L3"),
        Airport("YBOK", "Oakey ", -27.415750741124253, 151.74392381319225, "L3"),
        Airport("YBCS", "Cairns ", -16.87752644953846, 145.74998883920173, "L4"),
        Airport("YBTL", "Townsville ", -19.246840852122897, 146.76682568650855, "L4"),
        Airport("YCSV", "Collinsville ", -20.599265880624966, 147.8521379663104, "L4"),
        Airport("YBPN", "Whitsunday Coast ", -20.491973383459936, 148.55828725096177, "L4"),
        Airport("YBMK", "Mackay ", -21.171591896527246, 149.18062063749537, "L4"),
        Airport("YBRK", "Rockhampton ",-23.37793176941593, 150.4783475952538, "L4"),
        Airport("YGLT", "Gladstone ", -23.87162197857864, 151.2245102087655, "L4"),
        Airport("YBUD", "Bundaberg ", -24.89863384536775, 152.32132629531728, "L4"),
        Airport("YBSU", "Sunshine Coast ", -26.59986774594939, 153.08853190888362, "L4"),
        Airport("YBBN", "Brisbane ", -27.392938236645, 153.12380936667384, "L4"),
        Airport("YBCG", "Gold Coast ", -28.163045713821376, 153.5069266261541, "L4"),
        Airport("YIVR", "Inverell ", -29.883615024123316, 151.14098228205688, "L4"),
        Airport("YBOK", "Oakey ", -27.415750741124253, 151.74392381319225, "L4"),
        Airport("YROM", "Roma ", -26.543752775259573, 148.7792246017792, "L4"),
        Airport("YEML", "Emerald ", -23.568666579908516, 148.17434131060628, "L4"),
        Airport("YHUG", "Hughenden ", -20.816364268412023, 144.22723079700768, "L4"),
        Airport("YLRE", "Longreach ", -23.4374929570087, 144.2742633817648, "L4"),
        Airport("YBCV", "Charleville ", -26.41316605598972, 146.25905545305622, "L4"),
        Airport("YSGE", "St George ", -28.04673506725657, 148.5944931242954, "L4"),
        Airport("YWLG", "Walgett ", -30.030605500621483, 148.12301648021102, "L4"),
        Airport("YMOR", "Moree ", -29.49595930984892, 149.84997465134833, "L4"),
        Airport("YBBN", "Narrabri ", -30.31855719860127, 149.82893586858734, "L4"),
        Airport("YCMU", "Cunnamulla ", -28.03120047104545, -28.03120047104545, "L4"),
        Airport("YWDH", "Windorah ", -25.411794188157597, 142.6636005530118, "L4"),
        Airport("YBMA", "Mount Isa ", -20.667685043869323, 139.49166869514892, "L4"),
        Airport("YBPN", "Proserpine ", -20.496944, 148.552972, "L4"),
        Airport("YPKS", "Parkes ", -33.13822553225391, 148.23365682640707, "L5"),
        Airport("YSDU", "Dubbo City Regional ", -32.21870733806678, 148.56973292450465, "L5"),
        Airport("YWLG", "Walgett ",-30.030605500621483, 148.12301648021102, "L5"),
        Airport("YSGE", "St George ", -28.04673506725657, 148.5944931242954, "L5"),
        Airport("YBCV", "Charleville ", -26.413271753269207, 146.2590661818924, "L5"),
        Airport("YHUG", "Hughenden ", -20.816364268412023, 144.22723079700768, "L5"),
        Airport("YGTH", "Griffith ", -34.25522372865909, 146.0626175210129, "L5"),
        Airport("YCBA", "Cobar ", -31.537227058015578, 145.79755423981362, "L5"),
        Airport("YBKE", "Bourke ", -30.041573486449646, 145.94973438021168, "L5"),
        Airport("YCMU", "Cunnamulla ", -28.03120047104545, 145.6259367684755, "L5"),
        Airport("YBCV", "Longreach ",  -23.4374929570087, 144.2742633817648, "L5"),
        Airport("YWDH", "Windorah ", -25.41170697102898, 142.66355763766708, "L5"),
        Airport("YBHI", "Broken Hill ", -31.99867489621589, 141.47023649565682, "L5"),
        Airport("YMIA", "Mildura ", -34.23039132038609, 142.08446387857967, "L5"),
        Airport("YOOM", "Moomba ", -28.101358583730516, 140.19808333778928, "L5"),
        Airport("YBDV", "Birdsville ", -25.897106711417525, 139.351143197214, "L5"),
        Airport("YBOU", "Boulia ", -22.90834638302379, 139.8995042087263, "L5"),
        Airport("YBMA", "Mount Isa ", -20.667624813680774, 139.49159359329565, "L5"),
        Airport("YCCY", "Cloncurry ", -20.66864543621559, 140.5083835895894, "L5"),
        Airport("PHD", "Port Hedland International ", -20.37787257449251, 118.63185182582794, "L6"),
        Airport("YTNK", "Tennant Creek ", -19.640798157313885, 134.1844341625696, "L6"),
        Airport("YBMA", "Mount Isa ", -20.667624813680774, 139.49159359329565, "L6"),
        Airport("YCCY", "Cloncurry ", -20.66864543621559, 140.5083835895894, "L6"),
        Airport("YHUD", "Hughenden ", -20.816364268412023, 144.22723079700768, "L6"),
        Airport("YBRM", "Broome International ", -17.952401185890363, 122.23371785087417, "L6"),
        Airport("YDBY", "Derby ", -17.36972335026861, 123.66248420667453, "L6"),
        Airport("YCSP", "Curtin Springs ",-17.58548933837214, 123.8245984477583, "L6"),
        Airport("YARG", "Argyle ", -16.639052571456034, 128.4514390151139, "L6"),
        Airport("YHLC", "Halls Creek ", -18.231473416922547, 127.66873929506419, "L6"),
        Airport("YNTN", "Normanton ", -17.68494544312939, 141.07301298738244, "L6"),
        Airport("YBKT", "Burketown ", -17.745444369391826, 139.53845429319512, "L6"),
        Airport("YBCS", "Cairns ", -16.877444315773054, 145.75001029687408, "L6"),
        Airport("YPKU", "Kununurra ", -15.783906423112267, 128.7126632953204, "L6"),
        Airport("YPTN", "Tindal ", -14.512605418014585, 132.36509902193492, "L6"),
        Airport("YGTE", "Groote Eylandt ", -13.973602547006935, 136.45752754017758, "L6"),
        Airport("YCOE", "Coen ", -15.6000, 143.8910, "L6"),
        Airport("YLHR", "Lockhart River ", -12.784999910474962, 143.30665252189007, "L6"),
        Airport("YBWP", "Weipa ", -12.680623980440746, 141.92431769490454, "L6"),
        Airport("YPGV", "Gove ", -12.269593696361744, 136.82246982373096, "L6"),
        Airport("YMGD", "Maningrida ", -12.054725912229845, 134.23225989488955, "L6"),
        Airport("YPDN", "Darwin International ", -12.414729505016107, 130.8830950255878, "L6"),
        Airport("YHOD", "Hooker Creek ", -26.3850, 133.9780, "L6"),
        Airport("YHID", "Horn Island ", -10.59090634465989, 142.2945386660208, "L6"),
        Airport("YHLC", "Halls Creek ", -18.231534558423313, 127.66869637971945, "L7"),
        Airport("YWBR", "Warburton", -26.12553254030709, 126.58333327469452, "L7"),
        Airport("YFRT", "Forrest", -30.846640806823697, 128.11451796676081, "L7"),
        Airport("YHOD", "Hooker Creek", -18.33464482501615, 130.6359552778695, "L7"),
        Airport("YAYE", "Ayers Rock", -25.190406584190825, 130.97623950882132, "L7"),
        Airport("YCBP", "Coober Pedy", -29.040703636406697, 134.7218267801622, "L7"),
        Airport("YCDU", "Ceduna", -32.12382103886972, 133.70176823984437, "L7"),
        Airport("YPLC", "Port Lincoln", -34.603691371294325, 135.8745396939452, "L7"),
        Airport("YPWR", "Woomera", -31.145940604521503, 136.81253898026756, "L7"),
        Airport("YBAS", "Alice Springs", -23.80163262127604, 133.9032980262685, "L7"),
        Airport("YTNK", "Tennant Creek", -19.640858784989415, 134.1846058239485, "L7"),
        Airport("YMRE", "Marree", -29.65795232295386, 138.06973323971806, "L7"),
        Airport("YLEC", "Leigh Creek", -30.597383429597876, 138.4223243820929, "L7"),
        Airport("YPED", "Edinburgh", -33.48349259204509, 138.64399790517135, "L7"),
        Airport("YWHA", "Whyalla", -33.05223565469144, 137.52165546687692, "L7"),
        Airport("YESP", "Esperance ", -33.68257177466934, 121.830466482256, "L8"),
        Airport("YSCD", "Carosue Dam ", -30.17030549576343, 122.32510108021805, "L8"),
        Airport("YPKG", "Kalgoorlie-Boulder ", -30.785139331177707, 121.45790479374061, "L8"),
        Airport("ICAO", "RAAF Base Curtin",-17.587647073508073, 123.8259232527156, "L8"),
        Airport("YDBY", "Derby ", -17.36967215235245, 123.66243056249363, "L8"),
        Airport("YABA", "Albany ", -34.902410813326156, 117.7641616093025, "L8"),
        Airport("YLEO", "Leonora ", -28.87913293370292, 121.31673801770397, "L8"),
        Airport("YLST", "Leinster ", -27.838544610330164, 120.7038471954494, "L8"),
        Airport("YLAW", "Lawlers ", -28.09175408298124, 120.53984736847843, "L8"),
        Airport("YWLU", "Wiluna ", -26.62757506775238, 120.22050036841051, "L8"),
        Airport("YJUN", "Jundee ", -26.627728522383826, 120.22043599539343, "L8"),
        Airport("YNWN", "Newman ", -23.41595857165631, 119.80229608176387, "L8"),
        Airport("YBRM", "Broome International ", -17.952309327546406, 122.23366420669328, "L8"),
        Airport("YPPD", "Port Hedland International ", -20.37782228754356, 118.63178745281085, "L8"),
        Airport("YPBO", "Paraburdoo ", -23.17364023120617, 117.74798698360733, "L8"),
        Airport("YMEK", "Meekatharra ", -26.610831522776493, 118.5459620395738, "L8"),
        Airport("YMOG", "Mount Magnet ", -28.11586768299786, 117.84324360895394, "L8"),
        Airport("YYAL", "Yalgoo ", -28.234863271728607, 116.3581560613759, "L8"),
        Airport("YCUN", "Cunderdin ", -31.622529714565214, 117.21752970727533, "L8"),
        Airport("YPPH", "Perth ", -31.939040273024595, 115.97542962834727, "L8"),
        Airport("YBLN", "Busselton Margaret River ", -33.685759999551664, 115.39871589389442, "L8"),
        Airport("YPJT", "Jandakot ", -32.09388995699968, 115.8790784379896, "L8"),
        Airport("YPEA", "RAAF Base Pearce", -31.667446803024184, 116.02927508214805, "L8"),
        Airport("YGIN", "Gingin ", -31.462585287347537, 115.85886949022037, "L8"),
        Airport("YBRM", "Beermullah ", -31.267708764732273, 115.83883021096337, "L8"),
        Airport("YGEL", "Geraldton ", -28.79601686502884, 114.70237792433117, "L8"),
        Airport("YCAR", "Carnarvon ",-24.88277379172996, 113.66397954928247, "L8"),
        Airport("YPLM", "Learmonth ", -22.239796342113156, 114.09415311055321, "L8"),
        Airport("YPKA", "Karratha ", -20.708488939017283, 116.7702464970038, "L8"),
        Airport("YBMA", "Cloncurry ", -20.665694, 140.500889, "L4"),
        Airport("YWBR", "Warburton",   -26.128166666666668,  126.57969444444445, "L7"),
        Airport("YHOD", "Hooker Creek ",  -18.330944444444444,  130.63719444444445, "L6"),
        Airport("YPAD", "Adelaide",   -34.94697,  138.52453, "L7"),
]
import random

airports = [
        Airport("YHMT", "Hamilton ",  -37.5075, 142.0972, "L1"),
        Airport("YMTG", "Mount Gambier ", -37.6827, 140.7719, "L1"),
        Airport("YMML", "Melbourne ", -37.4269 , 144.9811, "L1"),
        Airport("YMMB", "Moorabbin ",  -37.7751 ,  145.2365, "L1"),
        Airport("YMAV", "Avalon ", -37.8662 , 144.5883, "L1"),
        Airport("YKII", "King Island ", -39.8634,  144.0967, "L1"),
        Airport("YMES", "East Sale ", -37.8944, 147.3706, "L1"),
        Airport("YLTV", "Latrobe Valley ",-38.0027,  146.6949, "L1"),
        Airport("YWYY", "Wynyard ", -40.9592,145.9369, "L1"),
        Airport("YMHB", "Hobart ",  -42.8357, 147.7441, "L1"),
        Airport("YMLT", "Launceston ", -41.5302, 147.4352, "L1"),
        Airport("YWHA", "Whyalla ", -33.0524 ,137.5218, "L2"),
        Airport("YPED", "RAAF Base Edinburgh", -34.701997192, 138.618664192, "L2"),
        Airport("YPPF", "Parafield ",-34.6055 ,138.7951, "L2"),
        Airport("YPAD", "Adelaide ",  -34.7506,  138.7065, "L2"),
        Airport("YMIA", "Mildura ", -33.9723, 142.2687, "L2"),
        Airport("YSWH", "Swan Hill ", -35.0174 ,143.7503, "L2"),
        Airport("YSHL", "Wollongong ", -34.4103, 151.0922, "L2"),
        Airport("YMAV", "Avalon ",  -37.4149,  144.6954, "L2"),
        Airport("YMNG", "Mangalore ", -36.886329788 ,145.183832598, "L2"),
        Airport("YMML", "Melbourne ",   -37.0672,  145.0511, "L2"),
        Airport("YMES", "East Sale ",-37.4836 , 147.2964, "L2"),
        Airport("YLTV", "Latrobe Valley ",  -37.5576, 146.6345, "L2"),
        Airport("YMMB", "Moorabbin ",  -37.3461,  145.2859, "L2"),
        Airport("YSWG", "Wagga Wagga ", -35.15916603 ,147.459831494, "L2"),
        Airport("YCOR", "Corowa ", -35.5769 ,146.5714, "L2"),
        Airport("YMAY", "Albury ", -35.6573 ,147.1701, "L2"),
        Airport("YSNW", "Nowra ", -34.7597 , 150.8093 , "L2"),
        Airport("YPKS", "Parkes ", -32.9902 ,148.5873, "L2"),
        Airport("YGTH", "Griffith ",-33.9803 ,146.3144, "L2"),
        Airport("YMTG", "Mount Gambier ", -37.1931,  141.1221, "L2"),
        Airport("YCWR", "Cowra ",  -33.6718 ,148.9911, "L2"),
        Airport("YBTH", "Bathurst ", -33.3087, 150.0375, "L2"),
        Airport("YSRI", "RAAF Base Richmond",  -33.5460,  151.1664, "L2"),
        Airport("YSSY", "Sydney Kingsford Smith ", -33.8716, 151.5564, "L2"),
        Airport("YGLB", "Goulburn ", -34.5925   , 150.0073, "L2"),
        Airport("YSHL", "Shellharbour ",  -35.9558,145.5963, "L2"),
        Airport("YSCB", "Canberra ", -35.0030,149.4360, "L2"),
        Airport("YCOM", "Cooma ",  -35.9702, 149.1367, "L2"),
        Airport("YMER", "Merimbula ", -36.4920,  150.0293, "L2"),
        Airport("YMCO", "Mallacoota ",  -37.1187, 149.8178, "L2"),
        Airport("YMNG", "Mangalore ", -36.3754,145.3982, "L2"),
        Airport("YPED", "Edinburgh ", -34.5020, 138.7738, "L2"),
        Airport("YHMT", "Hamilton ",  -37.0837, 142.3224, "L2"),
        Airport("YSHT", "Shepparton ", -36.4284,145.3960, "L2"),
        Airport("YROM", "Roma ",  -26.0469,148.0133, "L3"),
        Airport("YSGE", "St George ", -27.7516,  147.6837, "L3"),
        Airport("YWLG", "Walgett ",  -29.9454, 146.9202, "L3"),
        Airport("YSDU", "Dubbo  ", -32.3196, 147.6178, "L3"),
        Airport("YPKS", "Parkes ", -33.3122, 147.0905, "L3"),
        Airport("YCWR", "Cowra ",  -34.0663, 147.7112, "L3"),
        Airport("YTOG", "Togo Station ",-30.320833333333333, 149.8311111111111, "L3"),
        Airport("YWLM", "Williamtown ", -33.0052, 152.7196, "L3"),
        Airport("YBBN", "Narrabri ", -30.2828, 149.716, "L3"),
        Airport("YMOR", "Moree ", -29.3774, 149.7052, "L3"),
        Airport("YMDG", "Mudgee ", -32.6717, 149.1998, "L3"),
        Airport("YBTH", "Bathurst ", -33.6055, 149.2712, "L3"),
        Airport("YSRI", " Richmond(NSW)", -33.59477130243219, 150.78238889294994, "L3"),
        Airport("YMND", "West Maitland ", -32.7046471425939, 151.48902143987516, "L3"),
        Airport("YSTW", "Tamworth ", -31.084160049880005, 150.8484596262986, "L3"),
        Airport("YIVR", "Inverell ", -29.8359, 151.8091, "L3"),
        Airport("YAMB", " Amberley", -27.3937,  154.5035, "L3"),
        Airport("YBSU", "Sunshine Coast ", -26.2244, 155.2341, "L3"),
        Airport("YWOL", "Wollongong ",-34.55794, 150.79100 , "L3"),
        Airport("YBBE", "Brisbane ",  -27.1025, 155.2416, "L3"),
        Airport("YARM", "Armidale ", -30.528055555555557, 151.61722222222224, "L3"),
        Airport("YSPT", "Southport ", -27.92435982604407, 153.37122363963428, "L3"),
        Airport("YBCG", "Gold Coast ",-28.0138, 155.7669, "L3"),
        Airport("YBNA", "Ballina  ", -28.7556, 155.7944, "L3"),
        Airport("YGFN", "Grafton ",  -29.7477, 154.8358, "L3"),
        Airport("YCFS", "Coffs Harbour ", -30.3800, 154.951, "L3"),
        Airport("YPMQ", "Port Macquarie ",-31.5657, 154.4554, "L3"),
        Airport("YWLM", "Newcastle ", -32.79334435639444, 151.8366783515182, "L3"),
        Airport("YSSY", "Sydney Kingsford Smith ",  -34.1857, 151.6470, "L3"),
        Airport("YSBK", "Bankstown ", -34.1573,  151.3586, "L3"),
        Airport("YSHL ", "Wollongong ", -34.8285, 151.0085, "L3"),
        Airport("YBOK", "Oakey ", -27.0891,  152.9012, "L3"),
         Airport("YBCS", "Cairns ",  -15.9244,145.2173, "L4"),
        Airport("YBTL", "Townsville ",  -18.5629, 146.4093, "L4"),
        Airport("YCSV", "Collinsville ", -19.9863, 147.6151, "L4"),
        Airport("YBPN", "Proserpine ", -19.8313, 148.2605, "L4"),
        Airport("YBMK", "Mackay ",  -20.5454, 148.9417, "L4"),
        Airport("YBRK", "Rockhampton ", -22.9217, 150.3067, "L4"),
        Airport("YGLT", "Gladstone ",  -23.4078, 151.0455, "L4"),
        Airport("YBUD", "Bundaberg ",  -24.4821,  152.1332, "L4"),
        Airport("YBSU", "Sunshine Coast ",  -26.2922, 152.9242, "L4"),
        Airport("YBBN", "Brisbane ", -27.0983, 153.0011, "L4"),
        Airport("YBCG", "Gold Coast ",  -27.9532, 153.3774, "L4"),
        Airport("YIVR", "Inverell ", -29.8466, 151.2762, "L4"),
        Airport("YBOK", "Oakey ",  -27.2107,151.7088, "L4"),
        Airport("YROM", "Roma ", -26.4460, 148.9005, "L4"),
        Airport("YEML", "Emerald ", -23.2742, 148.1314, "L4"),
        Airport("YHUG", "Hughenden ", -20.5531, 144.0953, "L4"),
        Airport("YLRE", "Longreach ", -23.4280, 144.4070, "L4"),
        Airport("YBCV", "Charleville ",  -26.4853, 146.5796, "L4"),
        Airport("YSGE", "St George ", -28.0526, 148.8455, "L4"),
        Airport("YWLG", "Walgett ",  -30.1499,148.5406, "L4"),
        Airport("YMOR", "Moree ", -29.5113, 150.0870, "L4"),
        Airport("YBBN", "Narrabri ", -30.3539, 150.1117, "L4"),
        Airport("YCMU", "Cunnamulla ",  -28.2342, 146.0934, "L4"),
        Airport("YWDH", "Windorah ", -25.7084,  143.0859, "L4"),
        Airport("YBMA", "Mount Isa ", -20.9204, 139.4769, "L4"),
        Airport("YBMA", "Cloncurry ", -20.8126, 140.4657, "L4"),
        Airport("YPKS", "Parkes ",  -33.1697, 148.3594, "L5"),
        Airport("YSDU", "Dubbo  ", -32.4217, 148.8757, "L5"),
        Airport("YWLG", "Walgett ",-30.4250, 148.7109, "L5"),
        Airport("YSGE", "St George ", -28.6327, 149.6008, "L5"),
        Airport("YBCV", "Charleville ", -26.9319, 147.0630, "L5"),
        Airport("YHUG", "Hughenden ",  -21.3968, 145.3931, "L5"),
        Airport("YGTH", "Griffith ", -33.9935, 145.7913, "L5"),
        Airport("YCBA", "Cobar ",  -31.5832,  145.8600, "L5"),
        Airport("YBKE", "Bourke ",  -30.2543, 146.2390, "L5"),
        Airport("YCMU", "Cunnamulla ",  -28.3624, 146.1484, "L5"),
        Airport("YBCV", "Longreach ",   -23.9461, 145.1514, "L5"),
        Airport("YWDH", "Windorah ",  -25.6935, 142.9431, "L5"),
        Airport("YBHI", "Broken Hill ",  -31.7095,  140.9354, "L5"),
        Airport("YMIA", "Mildura ",  -33.7289, 141.4105, "L5"),
        Airport("YOOM", "Moomba ", -28.0914, 139.7900, "L5"),
        Airport("YBDV", "Birdsville ",  -25.9778, 138.9441, "L5"),
        Airport("YBOU", "Boulia ",  -23.1479,  139.8257, "L5"),
        Airport("YBMA", "Mount Isa ",  -20.9358, 139.4714, "L5"),
        Airport("YCCY", "Cloncurry ",  -20.9666 , 140.7486, "L5"),
         Airport("PHD", "Port Hedland  ",  -18.1876, 117.8174, "L6"),
        Airport("YTNK", "Tennant Creek ",  -19.7564, 133.3411, "L6"),
        Airport("YBMA", "Mount Isa ", -22.2789,  138.4167, "L6"),
        Airport("YCCY", "Cloncurry ", -22.5633, 139.3726, "L6"),
        Airport("YHUD", "Hughenden ",  -23.7250, 143.0310, "L6"),
        Airport("YBRM", "Broome ",  -15.2630,  121.5417, "L6"),
        Airport("YDBY", "Derby ", -14.6314, 123.1348, "L6"),
        Airport("YCSP", "Curtin  ",-15.0350, 123.2721, "L6"),
        Airport("YARG", "Argyle ", -14.4347,  128.0347, "L6"),
        Airport("YHLC", "Halls Creek ",  -16.5678,  127.0514, "L6"),
        Airport("YNTN", "Normanton ", -18.6775, 140.5371, "L6"),
        Airport("YBCS", "Cairns ",  -18.7815, 145.3931, "L6"),
        Airport("YPKU", "Kununurra ",  -13.2827, 128.4521, "L6"),
        Airport("YPTN", "Tindal ", -12.2649, 132.3853, "L6"),
        Airport("YGTE", "Groote Eylandt ", -12.4151, 136.6095, "L6"),
        Airport("YCOE", "Coen ",  -13.8487, 143.4045, "L6"),
        Airport("YLHR", "Lockhart River ", -12.5117, 143.8550, "L6"),
        Airport("YBWP", "Weipa ", -11.9748, 142.4707, "L6"),
        Airport("YPGV", "Gove ",  -10.0446, 137.2852, "L6"),
        Airport("YMGD", "Maningrida ", -9.1889, 134.6924, "L6"),
        Airport("YPDN", "Darwin International ", -8.9570, 131.1877, "L6"),
        Airport("YHOD", "Hooker Creek ",  -17.2676,  130.0152, "L6"),
        Airport("YHID", "Horn Island ",  -9.0912, 143.2617, "L6"),
        Airport("YHLC", "Halls Creek ", -18.1563,  127.2986, "L7"),
        Airport("YWBR", "Warburton",  -31.6534, 137.2412, "L7"),
        Airport("YFRT", "Forrest",  -31.0414, 127.5718, "L7"),
        Airport("YHOD", "Hooker Creek",  -18.3441,  130.9680, "L7"),
        Airport("YAYE", "Ayers Rock",  -25.4532, 131.0449, "L7"),
        Airport("YCBP", "Coober Pedy", -29.040703636406697, 134.7218267801622, "L7"),
        Airport("YCDU", "Ceduna",  -32.3846, 133.7421, "L7"),
        Airport("YPLC", "Port Lincoln",  -34.7867, 135.9119, "L7"),
        Airport("YPWR", "Woomera", -31.6347,  137.2302, "L7"),
        Airport("YBAS", "Alice Springs", -24.2670,  134.5935, "L7"),
        Airport("YTNK", "Tennant Creek",  -19.9114,135.3186, "L7"),
        Airport("YMRE", "Marree", -29.65795232295386, 138.06973323971806, "L7"),
        Airport("YLEC", "Leigh Creek", -31.2316,  139.1473, "L7"),
        Airport("YPED", "Edinburgh", -35.0997, 138.8287, "L7"),
        Airport("YWHA", "Whyalla",  -33.4956,  137.8290, "L7"),
        Airport("YPAD", "Adelaide",   -35.3174,  138.6584, "L7"),
        Airport("YWBR", "Warburton",   -26.3500,  125.8813, "L7"),
        Airport("YESP", "Esperance ", -33.5105, 121.8274, "L8"),
        Airport("YPKG", "Kalgoorlie ", -30.9493,  121.4209, "L8"),
        Airport("ICAO", "Curtin",-18.4119, 123.2446, "L8"),
        Airport("YDBY", "Derby ", -18.1459,  123.0579, "L8"),
        Airport("YABA", "Albany ", -34.7642, 118.5370, "L8"),
        Airport("YLEO", "Leonora ", -29.2329, 121.2076, "L8"),
        Airport("YLST", "Leinster ", -28.2802, 120.6244, "L8"),
        
        Airport("YWLU", "Wiluna ", -26.62757506775238, 120.22050036841051, "L8"),
        
        Airport("YNWN", "Newman ",  -24.1919, 119.6136, "L8"),
        Airport("YBRM", "Broome International ", -18.8179, 121.6846, "L8"),
        Airport("YPPD", "Port Hedland International ",  -21.3457, 118.4052, "L8"),
        Airport("YPBO", "Paraburdoo ",  -24.0715,  117.7295, "L8"),
        Airport("YMEK", "Meekatharra ", -27.2351,  118.6523, "L8"),
        Airport("YMOG", "Mount Magnet ", -28.11586768299786, 117.84324360895394, "L8"),
        Airport("YYAL", "Yalgoo ", -28.234863271728607, 116.3581560613759, "L8"),
        Airport("YCUN", "Cunderdin ", -31.8706, 117.8284, "L8"),
        
        Airport("YBLN", "Busselton Margaret River ", -33.7719, 116.4308, "L8"),
        Airport("YPJT", "Jandakot ", -32.3707,   116.7078, "L8"),
        Airport("YPEA", "Pearce",  -31.9568,  116.7709, "L8"),
        Airport("YGIN", "Gingin ", -31.8052, 116.6391, "L8"),
        Airport("YBRM", "Beermullah ", -31.6358,  116.6034, "L8"),
        Airport("YGEL", "Geraldton ", -29.4635,  115.4169, "L8"),
        Airport("YCAR", "Carnarvon ",-25.9482, 114.1699, "L8"),
        Airport("YPLM", "Learmonth ",  -23.4078, 114.2688, "L8"),
        Airport("YPKA", "Karratha ", -21.7748,116.6748, "L8"),
]

# Clean up duplicate airport entries
unique_airports = {}
for airport in sample_airports:
    if airport.code not in unique_airports:
        unique_airports[airport.code] = airport
cleaned_sample_airports = list(unique_airports.values())

generator = AirportQuestionGenerator(cleaned_sample_airports)

def find_airport_by_name(name,airports):
    """Find airport in airports_list by name (case insensitive partial match)"""
    name_lower = name.lower()
    for airport in airports:
        if name_lower in airport.name.lower():
            return airport  # Return the Airport object directly
    return None

@app.route('/generate_question', methods=['POST'])
def generate_question_endpoint():
    try:
        data = request.get_json()
        if not data or not isinstance(data, dict):
            return jsonify({'error': 'Invalid or missing JSON payload'}), 400
        if 'reference' not in data or 'num_airports' not in data or 'marks' not in data:
            return jsonify({'error': 'Missing required parameters: reference, num_airports, and marks are required'}), 400

        logging.info(f"Processing /generate_question with payload: {data}")
        reference_chart_id = data['reference'].upper()
        try:
            num_airports = int(data['num_airports'])
            marks = int(data['marks'])
        except (ValueError, TypeError):
            return jsonify({'error': 'num_airports and marks must be integers'}), 400

        if reference_chart_id not in CHART_CONFIGS:
            return jsonify({'error': f'Invalid reference chart ID. Config not found for: {reference_chart_id}. Available: {list(CHART_CONFIGS.keys())}'}), 400
        if num_airports not in [3, 4]:
            return jsonify({'error': 'Number of airports must be 3 or 4'}), 400
        if marks not in [2, 3]:
            return jsonify({'error': 'Marks must be 2 or 3'}), 400

        question_obj = generator.generate_question_with_reference(reference_chart_id, num_airports)
        q_details = question_obj.details
        dep, arr, land1, land2 = q_details.departure, q_details.arrival, q_details.land1, q_details.land2
        P1, P2 = (dep.lat, dep.long), (arr.lat, arr.long)
        P3, P4 = (land1.lat, land1.long), (land2.lat, land2.long)

        # Find corresponding airports in the 'airports' list for map calculations
        dep1 = find_airport_by_name(dep.name, airports)
        arr1 = find_airport_by_name(arr.name, airports)
        land1_map = find_airport_by_name(land1.name, airports)
        land2_map = find_airport_by_name(land2.name, airports)

        # Check if all airports were found in the 'airports' list
        if not all([dep1, arr1, land1_map, land2_map]):
            missing = [name for name, obj in [
                (dep.name, dep1), (arr.name, arr1), (land1.name, land1_map), (land2.name, land2_map)
            ] if obj is None]
            logging.error(f"Could not find airports in 'airports' list: {missing}")
            return jsonify({'error': f"Could not find airports for map: {missing}"}), 400

        P5, P6 = (dep1.lat, dep1.long), (arr1.lat, arr1.long)
        P7, P8 = (land1_map.lat, land1_map.long), (land2_map.lat, land2_map.long)

        tas_for_calc = q_details.tas_single_engine
        wind_speed_for_calc = q_details.wind_single_engine['speed']
        degree_param_for_calc = q_details.wind_single_engine['direction'] % 360
        if degree_param_for_calc == 0:
            degree_param_for_calc = 360
        geodesic_output_1 = calculate_geodesic1(P1, P2, P3, P4, tas_for_calc, wind_speed_for_calc, degree_param_for_calc)
        # Geodesic calculation for answers (using sample_airports coordinates)
        geodesic_output = calculate_geodesic(P5, P6, P7, P8, tas_for_calc, wind_speed_for_calc, degree_param_for_calc, chart_id=reference_chart_id)
        # Geodesic calculation for map (using airports coordinates)
       

        if not geodesic_output or not geodesic_output_1:
            logging.error(f"Geodesic calculation failed. Ref: {reference_chart_id}, Args: P1={P1}, P2={P2}, P3={P3}, P4={P4}, P5={P5}, P6={P6}, P7={P7}, P8={P8}, TAS={tas_for_calc}, Wind={wind_speed_for_calc}@{degree_param_for_calc}")
            return jsonify({'error': 'Failed to compute geodesic data due to invalid airport configuration or intersection not found.'}), 400

        base_question_text = question_obj.question
        full_question_text = base_question_text
        if marks == 2:
            dist_p3_p4_val_nm = geodesic_output.get('distance_p3_p4_nm', 0.0)
            # Use Airport objects directly for name and code
            additional_text = f" Given that the distance between {land1.name} ({land1.code}) and {land2.name} ({land2.code}) is {dist_p3_p4_val_nm:.1f} nm,"
            cp_marker = "The CP is -"
            if cp_marker in base_question_text:
                parts = base_question_text.split(cp_marker)
                full_question_text = parts[0].strip() + additional_text + " " + cp_marker
            else:
                full_question_text = base_question_text.strip() + additional_text

        response_payload = {
            'question_text': full_question_text,
            'question_details_raw': {
                'departure_code': dep.code, 'departure_name': dep.name, 'dep_lat': dep.lat, 'dep_lon': dep.long,
                'arrival_code': arr.code, 'arrival_name': arr.name, 'arr_lat': arr.lat, 'arr_lon': arr.long,
                'land1_code': land1.code, 'land1_name': land1.name, 'land1_lat': land1.lat, 'land1_lon': land1.long,
                'land2_code': land2.code, 'land2_name': land2.name, 'land2_lat': land2.lat, 'land2_lon': land2.long,
                'cruise_level': q_details.cruise_level,
                'tas_normal': q_details.tas_normal, 'tas_single_engine': q_details.tas_single_engine,
                'wind_normal': q_details.wind_normal, 'wind_single_engine': q_details.wind_single_engine,
                'shape_type': q_details.shape_type, 'reference_chart_id': q_details.reference,
            },
            'geodesic_calculations_and_map': geodesic_output,
            'geodesic_calculations_and_map_1': geodesic_output_1
        }
        return jsonify(response_payload)

    except ValueError as ve:
        logging.error(f"ValueError in /generate_question: {str(ve)}", exc_info=True)
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        logging.error(f"Unexpected error in /generate_question: {str(e)}", exc_info=True)
        return jsonify({'error': f'An unexpected server error occurred: {str(e)}'}), 500
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'online',
        'message': 'Aviation Geodesic Calculation Service',
        'endpoints': {
            '/generate_question': 'POST - Body: {"reference": "L1", "num_airports": 3_or_4, "marks": 2_or_3}',
            '/question': 'GET - Renders question.html template for testing.'
        },
        'configured_charts': list(CHART_CONFIGS.keys())
    })

@app.route('/question')
def display_question_page():
    try:
        return render_template('question.html')
    except Exception as e:
        logging.error(f"Error rendering question.html: {e}", exc_info=True)
        return "Error: Could not load question page. Ensure 'question.html' exists in 'templates' folder.", 500

@app.route('/.well-known/appspecific/com.chrome.devtools.json', methods=['GET'])
def well_known_devtools():
    return jsonify({}), 200

@app.errorhandler(400)
def handle_bad_request(e):
    description = getattr(e, 'description', "Bad Request")
    logging.warning(f"Bad Request (400): {description}")
    return jsonify(error=str(description)), 400

@app.errorhandler(404)
def handle_not_found(e):
    logging.warning(f"Not Found (404): Resource {request.path} was not found.")
    return jsonify(error="Resource not found"), 404

@app.errorhandler(500)
def handle_internal_error(e):
    original_exception = getattr(e, "original_exception", e)
    logging.error(f"Internal Server Error (500): {original_exception}", exc_info=True)
    return jsonify(error=f"An internal server error occurred: {str(original_exception)}"), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)