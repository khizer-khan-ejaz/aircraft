from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils.geo_utils import calculate_geodesic
from utils.airport_utils import find_airport_by_name
from utils.data_loader import airports
import logging

# Configure logger (logging setup is in app.py)
logger = logging.getLogger(__name__)

map_bp = Blueprint('map', __name__)

@map_bp.route('/get_map_data', methods=['POST'])
@jwt_required()
def get_map_data_endpoint():
    """
    Endpoint to get map data for an existing question.
    Expected JSON payload:
    {
        "question_details": {
            "departure_name": str,
            "arrival_name": str,
            "land1_name": str,
            "land2_name": str,
            "tas": float,
            "wind": {"direction": float, "speed": float}
        },
        "reference": "L1"  // Chart reference (L1-L8)
    }
    """
    try:
        data = request.get_json(force=True) or {}
        if not data or 'question_details' not in data or 'reference' not in data:
            logger.error("Missing required parameters: question_details and reference")
            return jsonify({'error': 'Missing required parameters: question_details and reference'}), 400

        details = data['question_details']
        reference = data['reference']

        # Validate reference
        if not reference.startswith('L') or not reference[1:].isdigit() or int(reference[1:]) < 1 or int(reference[1:]) > 8:
            logger.error(f"Invalid reference format: {reference}")
            return jsonify({'error': 'Invalid reference format. Must be L1 through L8'}), 400

        # Extract and validate airport information
        required_keys = ['departure_name', 'arrival_name', 'land1_name', 'land2_name', 'tas', 'wind']
        if not all(key in details for key in required_keys):
            logger.error(f"Missing required question_details keys: {list(set(required_keys) - set(details.keys()))}")
            return jsonify({'error': 'Missing required question_details keys'}), 400

        dep_name = details['departure_name']
        arr_name = details['arrival_name']
        land1_name = details['land1_name']
        land2_name = details['land2_name']
        tas = details['tas']
        wind_speed = details['wind']['speed']
        wind_dir = details['wind']['direction']

        # Find airports on the chart
        dep1 = find_airport_by_name(dep_name, reference, airports)
        arr1 = find_airport_by_name(arr_name, reference, airports)
        land1_map = find_airport_by_name(land1_name, reference, airports)
        land2_map = find_airport_by_name(land2_name, reference, airports)

        if not all([dep1, arr1, land1_map, land2_map]):
            logger.error("Could not find all airports on the specified chart")
            return jsonify({'error': 'Could not find all airports on the specified chart'}), 400

        # Calculate geodesic for map
        P5 = (dep1.lat, dep1.long)
        P6 = (arr1.lat, arr1.long)
        P7 = (land1_map.lat, land1_map.long)
        P8 = (land2_map.lat, land2_map.long)

        geodesic_results_1 = calculate_geodesic(P5, P6, P7, P8, tas, wind_speed, wind_dir, chart_id=reference)
        if not geodesic_results_1:
            logger.error("Geodesic calculation failed")
            return jsonify({'error': 'Geodesic calculation failed'}), 500

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
        }), 200

    except KeyError as e:
        logger.error(f"KeyError: {str(e)}")
        return jsonify({'error': f'Missing key in request data: {str(e)}'}), 400
    except ValueError as ve:
        logger.error(f"ValueError: {str(ve)}")
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500