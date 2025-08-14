from flask import Blueprint, request, jsonify,Flask
from utils.geo_utils import calculate_geodesic, create_map_with_chart
from utils.airport_utils import find_airport_by_name
from utils.data_loader import airports
import logging
map_bp = Blueprint('map', __name__)
app = Flask(__name__)
@app.route('/get_map_data', methods=['POST'])
def get_map_data_endpoint():
    """
    Endpoint to get map data for an existing question
    Expected JSON payload:
    {
        "question_details": {...}, // The details object from a previous question
        "reference": "L1"  // Chart reference
    }
    """
    try:
        data = request.get_json()
        if not data or 'question_details' not in data or 'reference' not in data:
            return jsonify({'error': 'Missing required parameters: question_details and reference'}), 400
        
        details = data['question_details']
        reference = data['reference']
        
        # Extract airport information
        dep_name = details['departure_name']
        arr_name = details['arrival_name']
        land1_name = details['land1_name']
        land2_name = details['land2_name']
        
        # Find airports on the chart
        dep1 = find_airport_by_name(dep_name, reference, airports)
        arr1 = find_airport_by_name(arr_name, reference, airports)
        land1_map = find_airport_by_name(land1_name, reference, airports)
        land2_map = find_airport_by_name(land2_name, reference, airports)
        
        if not all([dep1, arr1, land1_map, land2_map]):
            return jsonify({'error': 'Could not find all airports on the specified chart'}), 400
        
        # Calculate geodesic for map
        P5 = (dep1.lat, dep1.long)
        P6 = (arr1.lat, arr1.long)
        P7 = (land1_map.lat, land1_map.long)
        P8 = (land2_map.lat, land2_map.long)
        
        tas = details.get('tas_single_engine', details.get('tas_normal', 200))
        wind_speed = details['wind_single_engine']['speed']
        wind_dir = details['wind_single_engine']['direction']
        
        geodesic_results_1 = calculate_geodesic(P5, P6, P7, P8, tas, wind_speed, wind_dir, chart_id=reference)
        
        return jsonify({
            'geodesic_1': geodesic_results_1,
            'map_data': {
                'chart_reference': reference,
                'airports': {
                    'departure': {'code': dep1.code, 'name': dep1.name, 'lat': dep1.lat, 'long': dep1.long},
                    'arrival': {'code': arr1.code, 'name': arr1.name, 'lat': arr1.lat, 'long': arr1.long},
                    'land1': {'code': land1_map.code, 'name': land1_map.name, 'lat': land1_map.lat, 'long': land1_map.long},
                    'land2': {'code': land2_map.code, 'name': land2_map.name, 'lat': land2_map.lat, 'long': land2_map.long}
                }
            }
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        logging.error(f"Error getting map data: {str(e)}")
        return jsonify({'error': 'Failed to generate map data'}), 500
