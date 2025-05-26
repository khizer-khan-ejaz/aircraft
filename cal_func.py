import scipy.optimize as optimize
import logging
from PIL import Image
from io import BytesIO
import base64
from folium.plugins import MousePosition
from geographiclib.geodesic import Geodesic
import folium
from geographiclib.geodesic import Geodesic

class Point:
    def __init__(self, lat, long):
        self.lat = lat
        self.long = long
# Configure logging

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
        
        if line1_check['s12'] < 1000 or line2_check['s12'] < 1000:
            return None, None
        
        initial_guess = [0.5, 0.5]
        try:
            result = optimize.minimize(distance_between_lines, initial_guess, method='Nelder-Mead', bounds=[(0, 1), (0, 1)])
            if not result.success or result.fun > 1000:
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
            
            if dist_p1_to_p2 < 1000:
                return None, None
                
            if dist_p1_to_inter + dist_p2_to_inter > dist_p1_to_p2 * 1.1:
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

    if g_CD['s12'] < 1000:
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
    variation = get_magnetic_variation(p1p2_perp_intersection[0], p1p2_perp_intersection[1])   
    distance_to_P3_nm = (geod.Inverse(p1p2_perp_intersection[0], p1p2_perp_intersection[1], P3[0], P3[1])['s12'] / 1000) * 0.539957
    if distance_to_P3_nm < 0.1:
        return None
    
    distance_to_degree = (distance_to_P3_nm / TAS) * wind_speed
    
    line_distance = distance_to_degree * 1852
    degree = degree + variation
    
    nm_line_point = geod.Direct(p1p2_perp_intersection[0], p1p2_perp_intersection[1], degree, line_distance)
    nm_line_end_point = (nm_line_point['lat2'], nm_line_point['lon2'])
    nm_geodesic, _ = generate_geodesic_points(p1p2_perp_intersection, nm_line_end_point)

    # Use fixed north (0°) bearing for perpendicular line
    perp_nm_distance = 1000000
    perp_nm_point1 = geod.Direct(nm_line_end_point[0], nm_line_end_point[1], perp_bearing, perp_nm_distance)
    perp_nm_point1 = (perp_nm_point1['lat2'], perp_nm_point1['lon2'])
    perp_nm_point2 = geod.Direct(nm_line_end_point[0], nm_line_end_point[1], (perp_bearing + 180) % 360, perp_nm_distance)
    perp_nm_point2 = (perp_nm_point2['lat2'], perp_nm_point2['lon2'])
    perp_nm_geodesic, _ = generate_geodesic_points(perp_nm_point1, perp_nm_point2)
    
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
from pygeomag import GeoMag
import datetime
# Initialize pygeomag
geo = GeoMag()
# Configure loggi
def decimal_year(date: datetime.datetime) -> float:
    year_start = datetime.datetime(date.year, 1, 1)
    next_year_start = datetime.datetime(date.year + 1, 1, 1)
    year_length = (next_year_start - year_start).total_seconds()
    elapsed = (date - year_start).total_seconds()
    return date.year + elapsed / year_length

def get_magnetic_variation(lat, lon, date=None):
    date = date or datetime.datetime.utcnow()
    dec_year = decimal_year(date)
    result = geo.calculate(glat=lat, glon=lon, alt=0, time=dec_year)
    return result.d

# Example: Single point


# Calculate magnetic variation

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
        
        if line1_check['s12'] < 1000 or line2_check['s12'] < 1000:
            return None, None
        
        initial_guess = [0.5, 0.5]
        try:
            result = optimize.minimize(distance_between_lines, initial_guess, method='Nelder-Mead', bounds=[(0, 1), (0, 1)])
            if not result.success or result.fun > 1000:
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
            
            if dist_p1_to_p2 < 1000:
                return None, None
                
            if dist_p1_to_inter + dist_p2_to_inter > dist_p1_to_p2 * 1.1:
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

    if g_CD['s12'] < 1000:
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
    variation = get_magnetic_variation(p1p2_perp_intersection[0], p1p2_perp_intersection[1])   
    distance_to_P3_nm = (geod.Inverse(p1p2_perp_intersection[0], p1p2_perp_intersection[1], P3[0], P3[1])['s12'] / 1000) * 0.539957
    if distance_to_P3_nm < 0.1:
        return None
    
    distance_to_degree = (distance_to_P3_nm / TAS) * wind_speed
    
    line_distance = distance_to_degree * 1852
    degree = degree + variation
    
    nm_line_point = geod.Direct(p1p2_perp_intersection[0], p1p2_perp_intersection[1], degree, line_distance)
    nm_line_end_point = (nm_line_point['lat2'], nm_line_point['lon2'])
    nm_geodesic, _ = generate_geodesic_points(p1p2_perp_intersection, nm_line_end_point)

    # Use fixed north (0°) bearing for perpendicular line
    perp_nm_distance = 1000000
    perp_nm_point1 = geod.Direct(nm_line_end_point[0], nm_line_end_point[1], perp_bearing, perp_nm_distance)
    perp_nm_point1 = (perp_nm_point1['lat2'], perp_nm_point1['lon2'])
    perp_nm_point2 = geod.Direct(nm_line_end_point[0], nm_line_end_point[1], (perp_bearing + 180) % 360, perp_nm_distance)
    perp_nm_point2 = (perp_nm_point2['lat2'], perp_nm_point2['lon2'])
    perp_nm_geodesic, _ = generate_geodesic_points(perp_nm_point1, perp_nm_point2)  
    
    perp_nm_geodesic, _ = generate_geodesic_points(perp_nm_point1, perp_nm_point2)

    perp_nm_p1p2_intersection, p1p2_nm_dist = geodesic_intersection(P1, P2, perp_nm_point1, perp_nm_point2)

    if perp_nm_p1p2_intersection is None:
        logging.warning("No perpendicular intersection with P1-P2")
        return None
    critical_point = (perp_nm_p1p2_intersection[0], perp_nm_p1p2_intersection[1])
    distance_to_P1 = geod.Inverse(perp_nm_p1p2_intersection[0], perp_nm_p1p2_intersection[1], P1[0], P1[1])['s12'] / 1000
    distance_to_P3 = int(geod.Inverse(perp_nm_p1p2_intersection[0], perp_nm_p1p2_intersection[1], P3[0], P3[1])['s12'] / 1000)
    distance_to_P4 = int(geod.Inverse(perp_nm_p1p2_intersection[0], perp_nm_p1p2_intersection[1], P4[0], P4[1])['s12'] / 1000)

    # Create base map with OpenStreetMap tiles
    my_map = folium.Map(
        location=p1p2_perp_intersection,
        zoom_start=6,
        tiles='OpenStreetMap',
        attr='OpenStreetMap',
        name='OpenStreetMap',
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
    folium.LayerControl().add_to(my_map)
    
    MousePosition().add_to(my_map)

    folium.PolyLine(p1_p2_geodesic, color='purple', weight=3, tooltip='P1 to P2').add_to(my_map)
    folium.PolyLine(p3_p4_geodesic, color='orange', weight=3, tooltip='P3 to P4').add_to(my_map)
    folium.PolyLine(perp_geodesic, color='red', weight=3, tooltip='Perpendicular Line').add_to(my_map)
    folium.PolyLine(nm_geodesic, color='blue', weight=3, tooltip=f'{degree}-Degree Line').add_to(my_map)
    folium.PolyLine(perp_nm_geodesic, color='green', weight=3, tooltip='Perpendicular to P1-P2 (North-South)').add_to(my_map)

    folium.Marker(location=p1p2_perp_intersection, popup=f'Initial Intersection\nLat: {p1p2_perp_intersection[0]:.6f}\nLon: {p1p2_perp_intersection[1]:.6f}', icon=folium.Icon(color='black', icon='info-sign')).add_to(my_map)
    folium.Marker(location=nm_line_end_point, popup=f'{degree}-Degree Line End\nLat: {nm_line_end_point[0]:.6f}\nLon: {nm_line_end_point[1]:.6f}', icon=folium.Icon(color='blue', icon='arrow-up')).add_to(my_map)
    folium.Marker(location=perp_nm_p1p2_intersection, popup=f'Perpendicular Intersection\nLat: {perp_nm_p1p2_intersection[0]:.6f}\nLon: {perp_nm_p1p2_intersection[1]:.6f}', icon=folium.Icon(color='green', icon='crosshair')).add_to(my_map)
    folium.Marker(location=perp_nm_point1, popup=f'Perp NM Point 1 (North)\nLat: {perp_nm_point1[0]:.6f}\nLon: {perp_nm_point1[1]:.6f}', icon=folium.Icon(color='red', icon='star')).add_to(my_map)
    folium.Marker(location=perp_nm_point2, popup=f'Perp NM Point 2 (South)\nLat: {perp_nm_point2[0]:.6f}\nLon: {perp_nm_point2[1]:.6f}', icon=folium.Icon(color='red', icon='star')).add_to(my_map)

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
            {"type": "Feature", "properties": {"name": "Perpendicular to P1-P2 (North-South)", "color": "green"}, "geometry": {"type": "LineString", "coordinates": [[p[1], p[0]] for p in perp_nm_geodesic]}}
        ]
    }
    
    for label, coords in points.items():
        geojson_data["features"].append({"type": "Feature", "properties": {"name": label, "color": colors[label]}, "geometry": {"type": "Point", "coordinates": [coords[1], coords[0]]}})
    
    key_points = {
        "Initial Intersection": p1p2_perp_intersection,
        f"{degree}-Degree Line End": nm_line_end_point,
        "Perpendicular Intersection": perp_nm_p1p2_intersection,
        "Perp NM Point 1 (North)": perp_nm_point1,
        "Perp NM Point 2 (South)": perp_nm_point2
    }
    for label, coords in key_points.items():
        geojson_data["features"].append({"type": "Feature", "properties": {"name": label}, "geometry": {"type": "Point", "coordinates": [coords[1], coords[0]]}})
    
    results = {
        'p1p2_perp_intersection': {'lat': p1p2_perp_intersection[0], 'lon': p1p2_perp_intersection[1]},
        'nm_line_end_point': {'lat': nm_line_end_point[0], 'lon': nm_line_end_point[1]},
        'perp_nm_p1p2_intersection': {'lat': perp_nm_p1p2_intersection[0], 'lon': perp_nm_p1p2_intersection[1]},
        'perp_nm_point1': {'lat': perp_nm_point1[0], 'lon': perp_nm_point1[1]},
        'perp_nm_point2': {'lat': perp_nm_point2[0], 'lon': perp_nm_point2[1]},
        'p1p2_nm_dist_km': p1p2_nm_dist / 1000,
        'distance_to_P1_nm': int(distance_to_P1 * 0.539957),
        'distance_to_P3_nm': distance_to_P3_nm,
        'distance_to_degree': distance_to_degree,
        'geojson': geojson_data,
        'map_html': map_html,
        "OPTION-A": distance_to_P1 * 0.539957,
        "OPTION-B": (distance_to_P1 * 0.539957) + 190,
        "OPTION-C": (distance_to_P1 * 0.539957) - 190,
        "OPTION-D": (distance_to_P1 * 0.539957) - 100,
        'distance_p3_p4': distance_P3_P4_nm,
        'distance_to_P3_nm_1': (distance_to_P3 * 0.539957),
        'distance_to_P4_nm': (distance_to_P4 * 0.539957),
        'critical_point': critical_point,
    }
    
    return results
