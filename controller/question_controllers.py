from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models.question import AirportQuestionGenerator, CurrentQuestion
from utils.data_loader import PREDEFINED_2_MARK_QUESTIONS, sample_airports, airports
from utils.airport_utils import find_airport_by_name, find
from utils.geo_utils import calculate_geodesic1, haversine_distance
from utils.wind_utils import calculate_ground_speed
from models.airport import Navigation, Point
from utils.allclass import *
from data.sample_data import *
from cal_func import *
import logging
import random
import math

# Configure logger (logging setup is in app.py)
logger = logging.getLogger(__name__)

question_bp = Blueprint('question', __name__)

generator = AirportQuestionGenerator(sample_airports)

@question_bp.route('/generate_question', methods=['POST'])
@jwt_required()
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
        show_map = data.get('show_map', False)  # New parameter for map display

        # Validate reference
        if not reference.startswith('L') or not reference[1:].isdigit() or int(reference[1:]) < 1 or int(reference[1:]) > 8:
            return jsonify({'error': 'Invalid reference format. Must be L1 through L8'}), 400

        # Validate num_airports
        if num_airports not in [3, 4]:
            return jsonify({'error': 'Number of airports must be 3 or 4'}), 400

        # Validate marks
        if marks not in [2, 3]:
            return jsonify({'error': 'Marks must be 2 or 3'}), 400

        # For 2-mark questions, use predefined questions with retry logic
        if marks == 2:
            # Filter predefined questions by the provided reference
            filtered_questions = [q for q in PREDEFINED_2_MARK_QUESTIONS if q['reference'] == reference]

            if not filtered_questions:
                return jsonify({'error': f'No 2-mark questions found for the reference: {reference}'}), 400

            max_question_attempts = 100000  # Number of times to retry the entire question
            for question_attempt in range(max_question_attempts):

                # Select a random predefined question from the filtered list
                predefined_question = random.choice(filtered_questions)

                # Find airports in sample_airports
                dep = find(predefined_question['dep_name_text'], sample_airports)
                arr = find(predefined_question['arr_name_text'], sample_airports)
                land1 = find(predefined_question['etp_dest1_name_text'], sample_airports)
                land2 = find(predefined_question['etp_dest2_name_text'], sample_airports)

                if not all([dep, arr, land1, land2]):
                    return jsonify({'error': 'Could not find all airports in sample data'}), 400

                def generate_three_digit_multiple_of_10():
                    base_number = random.randint(10, 35)
                    return base_number * 10

                def generate_wind_strength():
                    num_multiples = 90 // 5
                    random_index = random.randint(0, num_multiples - 1)
                    return (random_index + 1) * 5

                def random_multiple_of_5(min_value, max_value):
                    lower_bound = min_value if min_value % 5 == 0 else min_value + (5 - min_value % 5)
                    upper_bound = max_value if max_value % 5 == 0 else max_value - (max_value % 5)
                    num_multiples = (upper_bound - lower_bound) // 5 + 1
                    random_index = random.randint(0, num_multiples - 1)
                    return lower_bound + random_index * 5

                # Initialize parameters
                max_attempts = 5
                attempt = 0
                time = float('inf')

                while attempt < max_attempts and abs(time) >= 60:
                    # Generate random wind and TAS values
                    wind_dir = generate_three_digit_multiple_of_10()
                    wind_speed = generate_wind_strength()
                    tas = random_multiple_of_5(100, 300)

                    # Format wind direction for display (e.g., "270M")
                    wind_dir_display = f"{wind_dir:03d}M"

                    # Format the question text
                    question_text = predefined_question['text_template'].format(
                        dep_name_text=predefined_question['dep_name_text'],
                        arr_name_text=predefined_question['arr_name_text'],
                        track_name=predefined_question['track_name'],
                        etp_dest1_name_text=predefined_question['etp_dest1_name_text'],
                        etp_dest2_name_text=predefined_question['etp_dest2_name_text'],
                        wind_dir_display=wind_dir_display,
                        wind_speed=wind_speed,
                        tas=tas,
                        reference=predefined_question['reference'],
                    )

                    dep1 = find_airport_by_name(dep.name, reference, airports)
                    arr1 = find_airport_by_name(arr.name, reference, airports)
                    land1_map = find_airport_by_name(land1.name, reference, airports)
                    land2_map = find_airport_by_name(land2.name, reference, airports)

                    # Calculate geodesic data
                    P1 = (dep.lat, dep.long)
                    P2 = (arr.lat, arr.long)
                    P3 = (land1.lat, land1.long)
                    P4 = (land2.lat, land2.long)
                    P5 = (dep1.lat, dep1.long)
                    P6 = (arr1.lat, arr1.long)
                    P7 = (land1_map.lat, land1_map.long)
                    P8 = (land2_map.lat, land2_map.long)
                    question_reference = predefined_question['reference'] # Use a different variable name to avoid conflict

                    geodesic_results = calculate_geodesic1(P1, P2, P3, P4, tas, wind_speed, wind_dir)
                    if geodesic_results is None:
                        print("   -> Calculation failed. Continuing to next plan.")
                        continue
                    # Only calculate map geodesic if show_map is True
                    geodesic_results_1 = None

                    distance_p3 = geodesic_results['distance_to_P3_nm_1']
                    distance_p4 = geodesic_results['distance_to_P4_nm']
                    critical_point_data = geodesic_results.get('critical_point')
                    distance_to_P3_nm = geodesic_results['distance_to_P3_nm']
                    distance_p1 = geodesic_results['distance_to_P1_nm']

                    if isinstance(critical_point_data, (list, tuple)) and len(critical_point_data) == 2:
                        critical_point_obj = Point(critical_point_data[0], critical_point_data[1])
                    elif isinstance(critical_point_data, dict) and 'lat' in critical_point_data and 'long' in critical_point_data:
                        critical_point_obj = Point(critical_point_data['lat'], critical_point_data['long'])
                    else:
                        raise ValueError(f"Invalid critical_point_data format: {critical_point_data}")

                    land1_obj = Point(land1.lat, land1.long)
                    land2_obj = Point(land2.lat, land2.long)

                    nav = Navigation()
                    mid_house = nav.get_midpoint(critical_point_obj, land1_obj)
                    mid_land1 = nav.get_midpoint(critical_point_obj, land2_obj)
                    course_from_home = nav.get_track_angle(mid_house, land2_obj)
                    course_from_land1 = nav.get_track_angle(mid_land1, land2_obj)

                    def calculate_ground_speed(true_course, tas, wind_dir, wind_speed):
                        tc_rad = math.radians(true_course)
                        wd_rad = math.radians(wind_dir)
                        wca_rad = math.asin((wind_speed / tas) * math.sin(wd_rad - tc_rad))
                        gs = tas * math.cos(wca_rad) - wind_speed * math.cos(wd_rad - tc_rad)
                        return gs

                    gs = calculate_ground_speed(course_from_home, tas, wind_dir, wind_speed)
                    cs = calculate_ground_speed(course_from_land1, tas, wind_dir, wind_speed)
                    time_p3 = distance_p3 / gs
                    time_p4 = distance_p4 / cs
                    time_p3_1 = distance_p3 / gs
                    time_p4_1 = distance_p4 / cs
                    time = (time_p3 - time_p4) * 3600  # In seconds

                    attempt += 1

                # If time difference is within 60 seconds, proceed with response
                if abs(time) < 30:
                    distance_to_degree = geodesic_results['distance_to_degree']

                    # Add distance between P3 and P4 for 2-mark questions
                    distance_p3_p4 = geodesic_results['distance_p3_p4']
                    P3toP4 = haversine_distance(land1.lat, land1.long, land2.lat, land2.long)
                    question_text = question_text.replace("is -", f" Given that the distance between {land1.name} and {land2.name} is {distance_p3_p4:.1f} nm, is -")
                    steps = [
                        {
                            "step_number": 1,
                            "title": "Calculate Critical Point Distance",
                            "description": f"Draw a line from {land1.name} to {land2.name}. Mark the point halfway along the {dep.code}-{arr.code} line. ",
                            "calculation": f"This distance should be {round(P3toP4)}NM and the mid-point should be {round(P3toP4/2)}NM.",

                        },
                        {
                            "step_number": 2,
                            "title": f"Draw a line at right angles to the {land1.name} - {land2.name} line across the {dep.code}-{arr.code} Track. This point will be the ETP in nil wind",
                        },
                        {
                            "step_number": 3,
                            "title": f"Calculate the wind vector that will affect the nil wind ETP",
                            "description": f'''To do this you will need the aircraft's Single Engine TAS ({tas}KTS) and using the calculated nil
                                wind time interval, multiply this by the wind speed to determine the length of
                                time the wind affects the flight.
                                (note: since the question for asked single engine critical point, we will use single engine TAS)
                                In this case, the TAS is {tas} knots and the distance from the nil wind ETP
                                to either airport is {round( distance_to_P3_nm)}NM
                                The nil wind time to either airport is { round (distance_to_P3_nm/tas,2)} hours (Dist./TAS).
                                The wind is {wind_speed} knots , {round(distance_to_P3_nm/tas,2)}hrs worth is ({round( distance_to_P3_nm/tas,2)} x {wind_speed} = {round(distance_to_degree,2)} NM.)
                                   '''
                        },
                        {
                            "step_number": 4,
                            "title": f"Using a protractor draw a wind vector from the nil wind ETP",
                            "description": f"From the nil wind ETP {round(distance_to_degree)} on wind vector. Now draw a line parallel to the original line that bisects {land1.name} and {land2.name}. Where this line intersects the {dep.code}-{arr.code} track is the actual ETP for continuing to {land1.name} or diverting to {land2.name}. ",
                            "result": f"In this case the actual ETP lies <span class'large'> {round( distance_p1)}</span> NM from {dep.name}   "
                        },
                        {
                            "step_number": 5,
                            "title": "Verification: ",
                            "description": f"We can verify if this answer is correct by calculating the time required to fly to either {land1.name} or {land2.name} and comparing. Ideally, the times should be the same (+-1 minute).\n"
                            f"Distance from Critical Point to {land1.name}: {round( distance_p3)}NM "
                            f"Average Track from Critical Point to {land1.name}: {round(course_from_home,2)}M "
                            f"Groundspeed from Critical Point to {land1.name}: { round(gs ,2)}KTS "
                            f"Time= Distance/Speed. Therefore = {round(time_p3_1*60,2):.1f}Mins ",
                        },
                        {
                            "step_number": 6,
                            "title": "Verification: ",
                            "description": f"We can verify if this answer is correct by calculating the time required to fly to either {land1.name} or {land2.name} and comparing. Ideally, the times should be the same (+-1 minute)."
                            f"Distance from Critical Point to {land2.name}: {round (distance_p4)}NM "
                            f"Average Track from Critical Point to {land2.name}: {round (course_from_land1,2)}M "
                            f"Groundspeed from Critical Point to {land2.name}: {round( cs,2)}KTS "
                            f"Time= Distance/Speed. Therefore = {round( time_p4_1*60,2):.1f}Mins ",
                        }
                    ]
                    options = {
                        "A": round(distance_p1),
                        "B": round(distance_p1 + 27),
                        "C": round(distance_p1 + 35),
                        "D": round(distance_p1 + 40),
                    }
                    map_json = {
                        "question_details": {
                            "departure_name": dep.name,
                            "arrival_name": arr.name,
                            "land1_name": land1.name,
                            "land2_name": land2.name,
                            "tas_single_engine": tas,
                            "wind_single_engine": {
                                "speed": wind_speed,
                                "direction": wind_dir
                            }
                        },
                        "reference": question_reference
                    }
                    parameter={
                        "departure": dep.name,
                        "departure_code":dep.code,
                        "arrival": arr.name,
                        "departure_code":arr.code,
                        "alternate1": land1.name,
                        "alternate1_code": land1.code,
                        "alternate2": land2.name,
                        "alternate2_code": land2.code,
                        "true_airspeed": tas,
                        "wind": f"{wind_speed}/{wind_dir}",
                        'ground_speed_to_alt_1': round(gs,2),
                        'ground_speed_to_alt_2': round(cs,2),
                        'time_difference': int(time),
                    }
                    print(f"Question Attempt : {question_text}")
                    response_data = {
                        'question': question_text,
                        'show_map': show_map,
                        'details': {
                            'departure': dep.code,
                            'departure_name': dep.name,
                            'arrival': arr.code,
                            'arrival_name': arr.name,
                            'land1': land1.code,
                            'land1_name': land1.name,
                            'land2': land2.code,
                            'land2_name': land2.name,
                            'cruise_level': "FL180",  # Default for 2-mark questions
                            'tas_normal': tas,
                            'tas_single_engine': tas,
                            'wind_normal': {'direction': wind_dir, 'speed': wind_speed},
                            'wind_single_engine': {'direction': wind_dir, 'speed': wind_speed},
                            'shape_type': "ETP",  # Default for 2-mark questions
                            'reference': question_reference,
                            'geodesic': geodesic_results,
                            'gs': gs,
                            'cs': cs,
                            'time1': time_p3,
                            'time2': time_p4,
                            'time': int(time),
                            'steps': steps,
                            'Ans':round( distance_p1),
                            'options':options,
                            'map_json':map_json,
                            'parameter':parameter
                        }
                    }
                    if show_map:
                        geodesic_results_1 = calculate_geodesic(P5, P6, P7, P8, tas, wind_speed, wind_dir, chart_id=question_reference)
                    # Add map data only if requested
                    if show_map and geodesic_results_1:
                        response_data['details']['geodesic_1'] = geodesic_results_1
                        response_data['map_data'] = {
                            'chart_reference': question_reference,
                            'airports': {
                                'departure': {'code': dep1.code, 'name': dep1.name, 'lat': dep1.lat, 'long': dep1.long},
                                'arrival': {'code': arr1.code, 'name': arr1.name, 'lat': arr1.lat, 'long': arr1.long},
                                'land1': {'code': land1_map.code, 'name': land1_map.name, 'lat': land1_map.lat, 'long': land1_map.long},
                                'land2': {'code': land2_map.code, 'name': land2_map.name, 'lat': land2_map.lat, 'long': land2_map.long}
                            }
                        }
                    return jsonify(response_data)
        else:  # 3-mark questions - keep existing logic
            # Generate the base question
            question = generator.generate_question_with_reference(reference, num_airports)
            
            # Extract details for geodesic calculation
            dep = question.details.departure
            arr = question.details.arrival
            land1 = question.details.land1
            land2 = question.details.land2
            tas_single = question.details.tas_single_engine
            wind_speed = question.details.wind_single_engine['speed']
            wind_dir = question.details.wind_single_engine['direction'] % 360
            reference = question.details.reference
            reference_point=question.details.rondom_choice
            

            
            dep1 = find_airport_by_name(dep.name, reference, airports)
            arr1 = find_airport_by_name(arr.name, reference, airports)
            land1_map = find_airport_by_name(land1.name, reference, airports)
            land2_map = find_airport_by_name(land2.name, reference, airports)

            P1 = (dep.lat, dep.long)
            P2 = (arr.lat, arr.long)
            P3 = (land1.lat, land1.long)
            P4 = (land2.lat, land2.long)
            P5 = (dep1.lat, dep1.long)
            P6 = (arr1.lat, arr1.long)
            P7 = (land1_map.lat, land1_map.long)
            P8 = (land2_map.lat, land2_map.long)
            reference = question.details.reference
            
            geodesic_results = calculate_geodesic1(P1, P2, P3, P4, tas_single, wind_speed, wind_dir)
            distance_to_P3_nm=geodesic_results['distance_to_P3_nm']
            degreesdistance=geodesic_results['distance_to_degree']           
            # Only calculate map geodesic if show_map is True
            geodesic_results_1 = None
            if show_map:
                geodesic_results_1 = calculate_geodesic(P5, P6, P7, P8, tas_single, wind_speed, wind_dir, chart_id=reference)
            distance_p1=geodesic_results['distance_to_P1_nm']
           
            distance_p3 = geodesic_results['distance_to_P3_nm_1']
            
            
            distance_p4 = geodesic_results['distance_to_P4_nm']
            critical_point_data = geodesic_results.get('critical_point')
            
            
            if isinstance(critical_point_data, (list, tuple)) and len(critical_point_data) == 2:
                critical_point_obj = Point(critical_point_data[0], critical_point_data[1])
            elif hasattr(critical_point_data, 'lat') and hasattr(critical_point_data, 'long'):
                critical_point_obj = critical_point_data
            else:
                logging.error(f"Invalid critical_point type: {type(critical_point_data)}")
                return jsonify({'error': f'Invalid critical_point type: {type(critical_point_data)}'}), 500
                        
            distancefrom2=haversine_distance(critical_point_obj.lat,critical_point_obj.long,arr.lat,arr.long)
            P3toP4=haversine_distance(land1.lat,land1.long,land2.lat,land2.long)
            cp_distance = distance_p1 if reference_point == dep.name else distancefrom2
            # Calculate track angles 
            nav = Navigation()  
            mid_house = nav.get_midpoint(critical_point_obj, land1)
            mid_land1 = nav.get_midpoint(critical_point_obj, land2) 
            course_from_home = nav.get_track_angle(mid_house, land1)
            course_from_land1 = nav.get_track_angle(mid_land1, land2)
            
            def calculate_ground_speed(true_course, tas, wind_dir, wind_speed):
                """
                Calculate ground speed given true course, true airspeed, wind direction, and wind speed.
                
                Args:
                    true_course (float): Intended flight path in degrees (clockwise from north).
                    tas (float): True airspeed in knots.
                    wind_dir (float): Direction wind is coming from in degrees (clockwise from north).
                    wind_speed (float): Wind speed in knots.
                
                Returns:
                    float: Ground speed in knots.
                """
                tc_rad = math.radians(true_course)
                wd_rad = math.radians(wind_dir)
                wca_rad = math.asin((wind_speed / tas) * math.sin(wd_rad - tc_rad))
                gs = tas * math.cos(wca_rad) - wind_speed * math.cos(wd_rad - tc_rad)
                return gs
            
            gs = calculate_ground_speed(course_from_home, tas_single, wind_dir, wind_speed)
            cs = calculate_ground_speed(course_from_land1, tas_single, wind_dir, wind_speed)
            time_p3 = distance_p3/gs
            time_p4 = distance_p4/cs
            time = (time_p3-time_p4)*3600
            time_p3_1 = distance_p3/gs*60
            time_p4_1 = distance_p4/cs*60

            # Base question text from the generator
            full_question = question.question  # For 3-mark questions, use as-is
            steps = [
            {
                "step_number": 1,
                "title": "Calculate Critical Point Distance",
                "description": f"Draw a line from {land1.name} to {land2.name}. Mark the point halfway along the {dep.code}-{arr.code} line. ",
                "calculation": f"This distance should be {round(P3toP4,2)}NM and the mid-point should be {round(  P3toP4/2,2)}NM.",
            },
            {
                "step_number": 2,
                "title": f"Draw a line at right angles to the {land1.name} - {land2.name}  line across the {dep.code}-{arr.code} Track. This point will be the ETP in nil wind",
                
            },
            {
                "step_number": 3,
                "title": f"Calculate the wind vector that will affect the nil wind ETP",
                "description": f'''To do this you will need the aircraft's Single Engine TAS ({tas_single}KTS) and using the calculated nil  

                                    wind time interval, multiply this by the wind speed to determine the length of  

                                    time the wind affects the flight. 

                                    (note: since the question for asked single engine critical point, we will use single engine TAS)  

                                    In this case, the TAS is  knots and the distance from the nil wind ETP 
                                    to either airport is {round(distance_to_P3_nm),2}NM
                                    The nil wind time to either airport is {round( distance_to_P3_nm/tas_single,2)} hours (Dist./TAS).  

                                    The wind is {wind_speed} knots (at single engine cruse level), {round( distance_to_P3_nm/tas_single,2)}hrs worth is ({ round(distance_to_P3_nm/tas_single,2)} x {wind_speed} = {round( degreesdistance,2)} NM.) 
                                       '''
            },
            {
                "step_number": 4,
                "title": f"Using a protractor draw a wind vector from the nil wind ETP",
                "description": f"From the nil wind ETP {round( degreesdistance,2)} on wind vector.Now draw a line  parallel to the original line that bisects {land1.name} and {land2.name} .Where this line  intersects the {dep.code}-{arr.code} track is the actual ETP for continuing to {land1.name}  or  diverting to {land2.name}. ",
                "result": f"In this case the actual ETP lies <span class='large'>{round(distance_p1)} NM</span>  from {dep.name}, or <span class='large'> {round( distancefrom2)} NM</span>  from {arr.name}.  "
            },
            {
                "step_number": 5,
                "title": "Verification: ",
                "description": f"We can verify if this answer is correct by calculating the time required to fly to either {land1.name} or {land2.name} and comparing. Ideally, the times should be the same (+-1 minute).\n"
                f"Distance from Critical Point to {land1.name}: {round( distance_p3,2)} NM "
                f"Average Track from Critical Point to {land1.name}: {round( course_from_home,2)} M "
                f"Groundspeed from Critical Point to {land1.name}: {round( gs,2)} KTS "
                f"Time= Distance/Speed. Therefore =  {round( time_p3_1,2)} Mins ",
                

                
            },
            {
                "step_number": 6,
                "title": f"Verification: ",
                "description": f"We can verify if this answer is correct by calculating the time required to fly to either {land1.name} or {land2.name} and comparing. Ideally, the times should be the same (+-1 minute)."
                f"Distance from Critical Point to {land2.name}: {distance_p4} NM "
                f"Average Track from Critical Point to {land2.name}: {round (course_from_land1,2)} M "
                f"Groundspeed from Critical Point to {land2.name}: {round( cs,2)} KTS "
                f"Time= Distance/Speed. Therefore =  {round( time_p4_1,2)} Mins ",
            }
        ]


        
            options = {
                        "A": round(cp_distance),
                        "B": round(cp_distance + 27),
                        "C": round(cp_distance + 37),
                        "D": round(cp_distance + 40),
                    }
            parameter={
            "departure": dep.name,
            "departure_code":dep.code,
            "arrival": arr.name,
            "departure_code":arr.code,
            "alternate1": land1.name,
            "alternate1_code": land1.code,
            "alternate2": land2.name,
            "alternate2_code": land2.code,
            "true_airspeed": tas_single,
            "wind": f"{wind_speed}/{wind_dir}",
            'ground_speed_to_alt_1': round(gs,2),
            'ground_speed_to_alt_2': round(cs,2),
            'time_difference': int(time),
            }

            map_json = {
        "question_details": {
            "departure_name": dep.name,
            "arrival_name": arr.name,
            "land1_name": land1.name,
            "land2_name": land2.name,
            "tas_single_engine": tas_single,
            "wind_single_engine": {
                "speed": wind_speed,
                "direction": wind_dir
            }
        },
        "reference": reference
    }

            # Prepare the response
            response_data = {
                'question': full_question,
                'show_map': show_map,
                'details': {
                    'maganitute': course_from_home,
                    'maganitute_1': course_from_land1,
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
                    'Ans': round(cp_distance),
                    'options':options,   
                    'map_json':map_json,
                    'gs': gs,
                    'cs': cs,
                    'time1': time_p3,
                    'time2': time_p4,
                    'time': int(time),
                    'steps': steps, 
                    'parameter':parameter
                }
            }
            
            
            # Add map data only if requested
            if show_map and geodesic_results_1:
                response_data['details']['geodesic_1'] = geodesic_results_1
                response_data['map_data'] = {
                    'chart_reference': reference,
                    'airports': {
                        'departure': {'code': dep1.code, 'name': dep1.name, 'lat': dep1.lat, 'long': dep1.long},
                        'arrival': {'code': arr1.code, 'name': arr1.name, 'lat': arr1.lat, 'long': arr1.long},
                        'land1': {'code': land1_map.code, 'name': land1_map.name, 'lat': land1_map.lat, 'long': land1_map.long},
                        'land2': {'code': land2_map.code, 'name': land2_map.name, 'lat': land2_map.lat, 'long': land2_map.long}
                    }
                }
            
            return jsonify(response_data)
            
    except ValueError as ve:
        logging.error(f"ValueError: {str(ve)}")
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500
