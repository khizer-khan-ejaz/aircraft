from flask import Blueprint, request, render_template, jsonify
from utils.wind_utils import calculate_ground_speed
from utils.geo_utils import calculate_etp
import math
import random

etp_bp = Blueprint('etp', __name__)

def calculate_etp(distance, gs_return, gs_outbound):
    """
    Calculate Equi-Time Point (ETP)
    Args:
        distance: Total distance in nautical miles
        gs_return: Ground speed returning (knots)
        gs_outbound: Ground speed outbound (knots)
    Returns:
        Tuple of (ETP distance in nm, time to ETP in minutes)
    """
    # Calculate ETP distance
    etp_distance = (distance * gs_return) / (gs_outbound + gs_return)
    
    # Calculate time to ETP (in hours, converted to minutes)
    time_to_etp = etp_distance / gs_outbound
    
    return round(etp_distance, 2), round(time_to_etp * 60, 2)

def generate_marks2_question():
    # Random parameters
    tas = random.randint(20, 50) * 5       # 100..250 step 5
    tas_single = random.randint(20, 50) * 5
    distance = random.randint(20, 50) * 10 # 200..500 step 10
    wind_speed = random.randint(2, 10) * 5 # 10..50 step 5
    wind_type = random.choice(['headwind', 'tailwind'])
    engine = random.choice(['single', 'normal'])
    wind_reverse = 'tailwind' if wind_type == 'headwind' else 'headwind'

    # Calculate ground speeds based on engine type and wind
    if engine == 'single':
        if wind_type == 'headwind':
            gs_outbound = tas - wind_speed
            gs_return = tas_single + wind_speed
            gs_outbound_wrong = tas - wind_speed
            gs_return_wrong = tas_single + wind_speed
            gs_return_fault = tas + wind_speed
        else:
            gs_outbound = tas + wind_speed
            gs_return = tas_single - wind_speed
            gs_outbound_wrong = tas_single + wind_speed
            gs_return_wrong = tas - wind_speed
            gs_return_fault = tas - wind_speed
    else:
        if wind_type == 'headwind':
            gs_outbound = tas - wind_speed
            gs_return = tas + wind_speed
            gs_outbound_wrong = tas_single - wind_speed
            gs_return_wrong = tas_single + wind_speed
            gs_return_fault = tas_single + wind_speed
        else:
            gs_outbound = tas + wind_speed
            gs_return = tas - wind_speed
            gs_outbound_wrong = tas_single - wind_speed
            gs_return_wrong = tas_single + wind_speed
            gs_return_fault = tas_single + wind_speed

    # Calculate ETP
    etp_distance, time_to_etp = calculate_etp(distance, gs_return, gs_outbound)
    etp_distance_wrong, time_to_etp_wrong = calculate_etp(distance, gs_return_fault, gs_outbound)
    etp_distance_wrong_1, time_to_etp_wrong_1 = calculate_etp(distance, gs_return_wrong, gs_outbound_wrong)
    etp_distance_wrong_2 = etp_distance_wrong_1 + 10
    time_to_etp_wrong_2 = time_to_etp_wrong_1 + 10

    options = {
        "A": f'The time of ETP {time_to_etp}min and the distance to the PNR is {etp_distance}nm',
        "B": f'The time of ETP {time_to_etp_wrong}min and the distance to the PNR is {etp_distance_wrong}nm',
        "C": f'The time of ETP {time_to_etp_wrong_1}min and the distance to the PNR is {etp_distance_wrong_1}nm',
        "D": f'The time of ETP {time_to_etp_wrong_2}min and the distance to the PNR is {etp_distance_wrong_2}nm',
    }

    # Format the question
    question = (
        f"From A to B is {distance} nm, Normal engine TAS: {tas} kts, "
        f"Single engine TAS: {tas_single} kts, Forecast {wind_type.capitalize()} outbound: {wind_speed} kts, "
        f"Normal operation TAS: {tas} kts. Find the ETP from A (NM), answer to the nearest whole NM for {engine} engine."
    )

    dgs = distance * gs_return
    add = gs_return + gs_outbound
    solution = {
        "formula": "ETP distance from A = (Total distance × GS_home) / (GS_home + GS_outbound)",
        "substitution": f"({distance} × {gs_return}) / ({gs_return} + {gs_outbound})",
        "calculation": f"{dgs} / {add} = {etp_distance} nm",
    }

    return {
        'question': question,
        'parameters': {
            'tas': tas,
            'distance': distance,
            'wind_speed': wind_speed,
            'wind_type': wind_type,
            'wind_reverse': wind_reverse,
            'options': options,
            'solution': solution,
            'time': time_to_etp
        },
        'answer': {
            'etp_distance': etp_distance,
            'units': {
                'distance': 'nautical miles',
                'time': time_to_etp
            }
        },
        'marks': 2
    }

def generate_marks3_question():
    tas = random.randrange(100, 251, 5)
    tas_single = random.randrange(100, 251, 5)
    distance = random.randrange(200, 501, 5)
    course_outbound = random.choice(list(range(90, 121)) + list(range(270, 361)))
    wind_speed = random.randrange(10, 51, 10)
    wind_dir = random.randint(0, 359)

    # Calculate ground speeds
    gs_outbound = calculate_ground_speed(course_outbound, tas, wind_dir, wind_speed)
    gs_outbound_wrong = calculate_ground_speed(course_outbound, tas_single, wind_dir, wind_speed)
    home_course = (course_outbound + 180) % 360
    gs_homebound = calculate_ground_speed(home_course, tas, wind_dir, wind_speed)
    gs_homebound_wrong = calculate_ground_speed(home_course, tas_single, wind_dir, wind_speed)

    # Calculate ETP
    etp_distance = (distance * gs_homebound) / (gs_outbound + gs_homebound)
    time_to_etp = (etp_distance / gs_outbound) * 60
    etp_distance_wrong = (distance * gs_homebound_wrong) / (gs_outbound_wrong + gs_homebound_wrong)
    time_to_etp_wrong = (etp_distance / gs_outbound_wrong) * 60

    question = (
        f"A to B {distance} nm eastbound, "
        f"Normal operation TAS: {tas} kts, "
        f"Asymmetric TAS: {tas_single} kts, "
        f"Outbound course: {course_outbound}°, "
        f"Wind {wind_dir}°M/{wind_speed} kts. "
        f"FIND (a) ETP from A (NM). (b) Time from A to the ETP (min). Nearest whole NM and minute."
    )

    options = {
        "A": f'The time of ETP {round(time_to_etp)}min and the distance to the ETP is {round(etp_distance)}nm',
        "B": f'The time of ETP {round(time_to_etp_wrong)}min and the distance to the ETP is {round(etp_distance_wrong)}nm',
        "C": f'The time of ETP {round(time_to_etp)}min and the distance to the ETP is {round(etp_distance_wrong)}nm',
        "D": f'The time of ETP {round(time_to_etp_wrong)}min and the distance to the ETP is {round(etp_distance)}nm',
    }

    return {
        'question': question,
        'parameters': {
            'tas': tas,
            'distance': distance,
            'course_outbound': course_outbound,
            'wind_speed': wind_speed,
            'wind_direction': wind_dir,
            'options': options
        },
        'answer': {
            'gs_outbound': round(gs_outbound, 2),
            'gs_homebound': round(gs_homebound, 2),
            'etp_distance': round(etp_distance, 2),
            'time_to_etp': round(time_to_etp, 2),
            'units': {
                'groundspeed': 'knots',
                'distance': 'nautical miles',
                'time': 'minutes'
            }
        },
        'marks': 3
    }

@etp_bp.route('/question')
def display_question():
    """
    Render the question selection page
    """
    return render_template('question1.html')

@etp_bp.route('/api/question', methods=['POST'])
def get_question():
    """
    POST endpoint that returns different question types based on marks parameter
    Expected JSON payload: {"marks": 2} or {"marks": 3}
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        # Validate that marks is provided
        if not data or 'marks' not in data:
            return jsonify({
                'error': 'Missing "marks" parameter in request body',
                'example': '{"marks": 2} or {"marks": 3}'
            }), 400
        
        marks = data['marks']
        
        # Generate question based on marks
        if marks == 2:
            question_data = generate_marks2_question()
            return jsonify({
                'status': 'success',
                'question_type': '2 marks',
                'data': question_data
            })
        elif marks == 3:
            question_data = generate_marks3_question()
            return jsonify({
                'status': 'success',
                'question_type': '3 marks',
                'data': question_data
            })
        else:
            return jsonify({
                'error': 'Invalid marks value. Only 2 and 3 marks questions are supported.',
                'valid_marks': [2, 3]
            }), 400
            
    except Exception as e:
        return jsonify({
            'error': 'Failed to process request',
            'message': str(e)
        }), 500

@etp_bp.route('/api/question/marks2', methods=['GET'])
def get_marks2_question():
    """
    GET endpoint for 2-mark question (backward compatibility)
    """
    question_data = generate_marks2_question()
    return jsonify(question_data)

@etp_bp.route('/api/question/marks3', methods=['GET'])
def get_marks3_question():
    """
    GET endpoint for 3-mark question (backward compatibility)
    """
    question_data = generate_marks3_question()
    return jsonify(question_data)
@etp_bp.route('/etpwitout')
def index():
    return render_template('question.html')
