from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import random
import math
from typing import Dict, List, NamedTuple

from geographiclib.geodesic import Geodesic
import scipy.optimize as optimize
import logging

from allclass import *
from sample_airport import *
# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:5000"]}})

# Geodesic calculation function (modified for robustness)

# Airport and question generation classes (unchanged)

# Sample airport data (unchanged)

# Initialize generator
generator = AirportQuestionGenerator(sample_airports)

@app.route('/generate_question', methods=['POST'])
def generate_question_endpoint():
    try:
        data = request.get_json()
        if not data or 'reference' not in data:
            return jsonify({'error': 'Missing reference parameter'}), 400
        
        reference = data['reference']
        if not reference.startswith('L') or not reference[1:].isdigit() or int(reference[1:]) < 1 or int(reference[1:]) > 8:
            return jsonify({'error': 'Invalid reference format. Must be L1 through L8'}), 400
        
        num_airports = data.get('num_airports')
        if num_airports is None:
            return jsonify({'error': 'num_airports is required (3 or 4)'}), 400
        num_airports = int(num_airports)
        if num_airports not in [3, 4]:
            return jsonify({'error': 'Number of airports must be 3 or 4'}), 400
        
        question = generator.generate_question_with_reference(reference, num_airports)
        
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
        
        geodesic_results = calculate_geodesic(P1, P2, P3, P4, tas_normal, wind_speed, wind_dir)
        if not geodesic_results:
            logging.error("Geodesic calculation failed after retries")
            return jsonify({'error': 'Failed to generate valid geodesic configuration. Please try again.'}), 500
        
        return jsonify({
            'question': question.question,
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