from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import random
import math
from math import cos, sin, atan2, sqrt, radians, degrees, asin
import datetime
import logging
from typing import Dict, List, NamedTuple

from geographiclib.geodesic import Geodesic
import scipy.optimize as optimize

# Import these libraries if available in your environment
try:
    from pygeomag import GeoMag
    geo = GeoMag()
    has_pygeomag = True
except ImportError:
    has_pygeomag = False
    logging.warning("pygeomag library not found. Magnetic variation calculations will be disabled.")

from allclass import *
from sample_airport import *

# Configure logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000", "http://127.0.0.1:5000"]}})

# ---- Adding wind effect and ground speed calculation functions from first code ----

def decimal_year(date: datetime.datetime) -> float:
    """Calculate decimal year from datetime object."""
    year_start = datetime.datetime(date.year, 1, 1)
    next_year_start = datetime.datetime(date.year + 1, 1, 1)
    year_length = (next_year_start - year_start).total_seconds()
    elapsed = (date - year_start).total_seconds()
    return date.year + elapsed / year_length

def vincenty_inverse(lat1, lon1, lat2, lon2, max_iter=200, tol=1e-12):
    """Calculate distance, initial and final bearing between two points using the Vincenty formula."""
    a = 6378137.0
    f = 1 / 298.257223563
    b = (1 - f) * a

    phi1, phi2 = radians(lat1), radians(lat2)
    L = radians(lon2 - lon1)
    U1 = math.atan((1 - f) * math.tan(phi1))
    U2 = math.atan((1 - f) * math.tan(phi2))
    sinU1, cosU1 = sin(U1), cos(U1)
    sinU2, cosU2 = sin(U2), cos(U2)

    lamb = L
    for _ in range(max_iter):
        sin_lambda, cos_lambda = sin(lamb), cos(lamb)
        sin_sigma = sqrt((cosU2 * sin_lambda) ** 2 +
                        (cosU1 * sinU2 - sinU1 * cosU2 * cos_lambda) ** 2)
        if sin_sigma == 0:
            return 0.0, 0.0, 0.0
        cos_sigma = sinU1 * sinU2 + cosU1 * cosU2 * cos_lambda
        sigma = atan2(sin_sigma, cos_sigma)
        sin_alpha = cosU1 * cosU2 * sin_lambda / sin_sigma
        cos2_alpha = 1 - sin_alpha ** 2
        cos2_sigma_m = (cos_sigma - 2 * sinU1 * sinU2 / cos2_alpha) if cos2_alpha != 0 else 0
        C = f / 16 * cos2_alpha * (4 + f * (4 - 3 * cos2_alpha))
        prev_lamb = lamb
        lamb = L + (1 - C) * f * sin_alpha * (
            sigma + C * sin_sigma * (cos2_sigma_m + C * cos_sigma *
            (-1 + 2 * cos2_sigma_m ** 2)))
        if abs(lamb - prev_lamb) < tol:
            break
    else:
        raise ValueError("Vincenty algorithm failed to converge")

    u_sq = cos2_alpha * (a ** 2 - b ** 2) / (b ** 2)
    A = 1 + u_sq / 16384 * (4096 + u_sq * (-768 + u_sq * (320 - 175 * u_sq)))
    B = u_sq / 1024 * (256 + u_sq * (-128 + u_sq * (74 - 47 * u_sq)))
    delta_sigma = B * sin_sigma * (cos2_sigma_m + B / 4 * (
        cos_sigma * (-1 + 2 * cos2_sigma_m ** 2) -
        B / 6 * cos2_sigma_m * (-3 + 4 * sin_sigma ** 2) * (-3 + 4 * cos2_sigma_m ** 2)))

    distance = b * A * (sigma - delta_sigma)

    alpha1 = atan2(cosU2 * sin(lamb),
                cosU1 * sinU2 - sinU1 * cosU2 * cos(lamb))
    alpha2 = atan2(cosU1 * sin(lamb),
                -sinU1 * cosU2 + cosU1 * sinU2 * cos(lamb))

    return (degrees(alpha1) + 360) % 360, (degrees(alpha2) + 360) % 360, distance

def get_magnetic_variation(lat, lon, date=None):
    """Get magnetic variation for a given position and date."""
    if not has_pygeomag:
        return 0.0  # Return zero if pygeomag is not available
        
    date = date or datetime.datetime.utcnow()
    dec_year = decimal_year(date)
    result = geo.calculate(glat=lat, glon=lon, alt=0, time=dec_year)
    return result.d

def calculate_course_and_distance(departure, arrival, current_pos=None, date=None):
    """Calculate true and magnetic course, distance, and magnetic variation."""
    t1, _, d_m = vincenty_inverse(departure['lat'], departure['lon'],
                                arrival['lat'], arrival['lon'])
    if current_pos:
        t1, _, _ = vincenty_inverse(current_pos['lat'], current_pos['lon'],
                                    arrival['lat'], arrival['lon'])
        var = get_magnetic_variation(current_pos['lat'], current_pos['lon'], date)
        is_dyn = True
    else:
        var = get_magnetic_variation(departure['lat'], departure['lon'], date)
        is_dyn = False

    mag_course = (t1 - var + 360) % 360
    return {
        'true_course': round(t1, 1),
        'magnetic_course': round(mag_course, 1),
        'distance_nm': round(d_m / 1852, 1),
        'variation': round(var, 1),
        'dynamic': is_dyn
    }

def geographic_midpoint(lat1, lon1, lat2, lon2):
    """Calculate the geographic midpoint between two points."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    bx = cos(lat2) * cos(lon2 - lon1)
    by = cos(lat2) * sin(lon2 - lon1)
    lat3 = atan2(
        sin(lat1) + sin(lat2),
        sqrt((cos(lat1) + bx) ** 2 + by ** 2)
    )
    lon3 = lon1 + atan2(by, cos(lat1) + bx)
    return degrees(lat3), degrees(lon3)

def calculate_wind_effects(true_course, tas, wind_dir, wind_speed):
    """
    Calculate wind correction angle, true heading, and groundspeed.
    Wind direction should be given in degrees true (from which wind blows).
    
    Parameters:
    - true_course: true course in degrees
    - tas: true airspeed in knots
    - wind_dir: wind direction in degrees true (from)
    - wind_speed: wind speed in knots
    
    Returns:
    Dictionary with wind correction angle, true heading, and groundspeed
    """
    tc_rad = radians(true_course)
    wd_rad = radians(wind_dir)

    wca_rad = asin((wind_speed / tas) * sin(wd_rad - tc_rad))
    wca_deg = degrees(wca_rad)

    gs = tas * cos(wca_rad) + wind_speed * cos(wd_rad - tc_rad)
    true_heading = (true_course + wca_deg + 360) % 360

    return {
        'wind_correction_angle': round(wca_deg, 1),
        'true_heading': round(true_heading, 1),
        'groundspeed': round(gs, 1)
    }

# ---- End of added functions ----

# Initialize generator
generator = AirportQuestionGenerator(sample_airports)

# Modify calculate_geodesic function to include ground speed calculations

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
        geodesic_results = calculate_geodesic(P1, P2, P3, P4, tas_normal, wind_speed, wind_dir)
        distance_p3 = geodesic_results['distance_to_P3_nm_1']
        distance_p4 = geodesic_results['distance_to_P4_nm']
        cousefromhome=vincenty_inverse(dep.lat, dep.long, arr.lat, arr.long)[1]
        
        cousefromland1=vincenty_inverse(arr.lat,arr.long, dep.lat, dep.long)[0]
        gs=calculate_wind_effects(cousefromhome, tas_normal, wind_dir, wind_speed)['groundspeed']
        cs=calculate_wind_effects(cousefromland1, tas_normal, wind_dir, wind_speed)['groundspeed']
        time_p3=distance_p3/gs
        time_p4=distance_p4/cs        # Calculate geodesic results, which include the ground speed calculations
        time=time_p3-time_p4
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
                'geodesic': geodesic_results,
                'gs':gs,
                'cs':cs,
                'time1' : time_p3,
                'distance_p4':distance_p4,
                'time2' : time_p4,
                'time':time
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

# Add a new endpoint to calculate wind effects and ground speed
@app.route('/calculate_wind_effects', methods=['POST'])
def wind_effects_endpoint():
    try:
        data = request.get_json()
        if not data or 'true_course' not in data or 'tas' not in data or 'wind_dir' not in data or 'wind_speed' not in data:
            return jsonify({'error': 'Missing required parameters: true_course, tas, wind_dir, and wind_speed are required'}), 400
        
        true_course = float(data['true_course'])
        tas = float(data['tas'])
        wind_dir = float(data['wind_dir'])
        wind_speed = float(data['wind_speed'])
        
        # Calculate wind effects including ground speed
        results = calculate_wind_effects(true_course, tas, wind_dir, wind_speed)
        
        return jsonify(results)
    except ValueError as ve:
        logging.error(f"ValueError: {str(ve)}")
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500

# Error handlers
@app.errorhandler(400)
def bad_request(e):
    return jsonify({'error': str(e.description)}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Resource not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)