from typing import Dict, List, NamedTuple
from .airport import Airport, Point, Navigation
from utils.geo_utils import calculate_geodesic1
from utils.airport_utils import find_airport_by_name
from utils.data_loader import sample_airports, airports
from utils.geo_utils import haversine_distance
from geographiclib.geodesic import Geodesic
import random
import math
import logging

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
    rondom_choice: str

class CurrentQuestion(NamedTuple):
    question: str
    details: QuestionDetails

class AirportQuestionGenerator:
    def __init__(self, airports: List[Airport]):
        self.airports = airports
    
    # ... (all methods from original AirportQuestionGenerator class, using utils for calculations)
    # For example, calculate_distance, calculate_angle, etc., can call utils if needed.
    # generate_question_with_reference logic here.