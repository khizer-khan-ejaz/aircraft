from flask import  Flask,Blueprint, request, jsonify, render_template
from utils.airport_utils import AIRPORT_DATA
import random
import ast
density_bp = Blueprint('density', __name__)
app = Flask(__name__)
@app.route("/dencity", methods=["GET", "POST"])
def density_home():
    if request.method == "POST":
        marks = request.form.get("marks")
        question_type = request.form.get("question_type")
        # Pass user selections to the questions.html page for displaying the question
        return render_template("home.html", marks=marks, question_type=question_type)
    return render_template("dencity.html")
def load_airport_data(filepath="data.txt"):
    with open(filepath, "r") as f:
        content = f.read()
    return ast.literal_eval(content)

AIRPORT_DATA = load_airport_data()

# ---------------------- PRESSURE ALTITUDE (1 mark) ----------------------
TEMPLATES_PRESSURE_1MARK = [
    "Calculate the pressure height for an aerodrome with a strip elevation of {elevation} ft when the QNH is {qnh} hPa. Round your answer to the nearest 50 feet.",
    "An airfield's elevation is {elevation} ft and the QNH at the time is {qnh} hPa. What is the pressure altitude? (Give your answer rounded to the nearest 50 ft.)",
    "The strip elevation is {elevation} feet. If the QNH reported is {qnh} hPa, determine the pressure altitude to the nearest 50 feet.",
    "What is the pressure altitude if the runway elevation is {elevation} ft and local QNH is {qnh} hPa? (Round off your answer to the nearest 50 feet.)",
    "Find the pressure height for a location where the elevation is {elevation} ft and the QNH is {qnh} hPa. (Round answer to nearest 50 ft.)"
]

def generate_pressure_params():
    elevation = random.choice(range(100, 3001, 10))
    qnh = random.choice(range(990, 1036, 10))
    return elevation, qnh

def calculate_pressure_height(elevation, qnh):
    raw = elevation + (1013 - qnh) * 30
    rounded = int(50 * round(raw / 50))
    return rounded, raw

def generate_pressure_mcq(correct_answer, raw_answer, elevation, qnh):
    calc_mistake = elevation + (1013 + qnh) * 30
    calc_mistake = int(50 * round(calc_mistake / 50))
    rounding_mistake = int(raw_answer)
    random_wrong = correct_answer + random.choice([-100, -50, 50, 100])
    options = [correct_answer, calc_mistake, rounding_mistake, random_wrong]
    options = list(dict.fromkeys(options))
    while len(options) < 4:
        options.append(correct_answer + random.choice([-150, 150]))
    random.shuffle(options)
    return options

def get_pressure_altitude_question():
    elevation, qnh = generate_pressure_params()
    correct, raw_answer = calculate_pressure_height(elevation, qnh)
    text = random.choice(TEMPLATES_PRESSURE_1MARK).format(elevation=elevation, qnh=qnh)
    display_type = random.choice(['mcq', 'typein'])
    options = generate_pressure_mcq(correct, raw_answer, elevation, qnh) if display_type == 'mcq' else []
    return {
        'marks': 1,
        'label': '1 Mark – Pressure Altitude',
        'category': 'pressure',
        'text': text,
        'type': display_type,
        'options': options,
        'correct': correct,
        'elev': elevation,
        'qnh': qnh
    }

# ---------------------- DENSITY ALTITUDE (1 mark) ----------------------
DENSITY_1MARK_TEMPLATES = [
    "Find the ISA deviation where the pressure height is {pressure_height} ft and the outside air temperature (OAT) is {oat} °C.",
    "Calculate the ISA deviation if the pressure altitude is {pressure_height} ft and the OAT is {oat} °C.",
    "Given a pressure height of {pressure_height} feet and OAT of {oat} °C, determine the ISA deviation.",
    "What is the ISA deviation when the pressure height is {pressure_height} ft with an outside air temperature of {oat} °C?",
    "Determine the ISA deviation for a location with pressure altitude {pressure_height} ft and OAT {oat} °C."
]

def generate_density_question_params():
    pressure_height = random.choice(range(500, 10001, 500))
    oat = random.choice(range(-20, 36))
    return pressure_height, oat

def calculate_isa_deviation(pressure_height, oat):
    thousands = pressure_height / 1000
    isa_temp = 15 - 2 * thousands
    isa_dev = oat - isa_temp
    return round(isa_temp, 1), int(round(isa_dev))

def generate_density_mcq(correct_answer):
    wrong_near = correct_answer + random.choice([-2, -1, 1, 2])
    sign_flip = -correct_answer
    off_by = correct_answer + random.choice([-3, 3])
    options = [correct_answer, wrong_near, sign_flip, off_by]
    options = list(dict.fromkeys(options))
    while len(options) < 4:
        options.append(correct_answer + random.choice([-4, 4]))
    random.shuffle(options)
    return options

def get_density_altitude_question():
    ph, oat = generate_density_question_params()
    isa_temp, correct = calculate_isa_deviation(ph, oat)
    text = random.choice(DENSITY_1MARK_TEMPLATES).format(pressure_height=ph, oat=oat)
    display_type = random.choice(['mcq', 'typein'])
    options = generate_density_mcq(correct) if display_type == 'mcq' else []
    return {
        'marks': 1,
        'label': '1 Mark – Density Altitude',
        'category': 'density',
        'text': text,
        'type': display_type,
        'options': options,
        'correct': correct,
        'pressure_height': ph,
        'oat': oat,
        'isa_temp': isa_temp
    }

# ---------------------- PRESSURE ALTITUDE (2 mark) ----------------------
PRESSURE_2MARK_TEMPLATES = [
    "On a particular day, the QNH at {airport} Airport was {qnh} hPa. Using the airport’s elevation, calculate the Pressure Height for that day. Round your final answer to the nearest 50 ft.",
    "The QNH recorded at {airport} Airport was {qnh} hPa. Find the pressure altitude using the elevation of the airport. Provide your answer rounded to the nearest 50 feet.",
    "Given that the QNH at {airport} Airport is {qnh} hPa and knowing the airport's elevation, calculate the pressure height. Round your answer to the nearest 50 ft.",
    "At {airport} Airport, the QNH was {qnh} hPa. Using the elevation from your reference, find the pressure altitude and round it to the nearest 50 feet.",
    "Calculate the pressure height for {airport} Airport with a QNH of {qnh} hPa. Use the known elevation of the airport and round the final result to the nearest 50 ft."
]

def generate_mcq_options_2mark(correct_answer, calc_value, elevation, qnh):
    calc_mistake_val = elevation + (1013 + qnh) * 30
    calc_mistake_val = int(50 * round(calc_mistake_val / 50))
    rounding_mistake = int(calc_value + elevation)
    random_wrong = correct_answer + random.choice([-100, -50, 50, 100])
    options = [correct_answer, calc_mistake_val, rounding_mistake, random_wrong]
    options = list(dict.fromkeys(options))
    while len(options) < 4:
        options.append(correct_answer + random.choice([-150, 150]))
    random.shuffle(options)
    return options

def generate_pressure_2mark_question():
    airport = random.choice(list(AIRPORT_DATA.keys()))
    elevation = AIRPORT_DATA[airport]
    qnh = random.choice(range(990, 1036, 10))
    calc_value = (1013 - qnh) * 30
    raw_answer = elevation + calc_value
    rounded_answer = int(50 * round(raw_answer / 50))
    question_text = random.choice(PRESSURE_2MARK_TEMPLATES).format(airport=airport, qnh=qnh)
    q_type = random.choice(['mcq', 'typein'])
    options = generate_mcq_options_2mark(rounded_answer, calc_value, elevation, qnh) if q_type == 'mcq' else []
    return {
        'marks': 2,
        'label': '2 Marks – Pressure Altitude',
        'category': 'pressure_2mark',
        'text': question_text,
        'type': q_type,
        'options': options,
        'correct': rounded_answer,
        'elev': elevation,
        'qnh': qnh,
        'airport': airport,
        'calculation_value': calc_value
    }

# ---------------------- DENSITY ALTITUDE (2 mark) ----------------------
def generate_density_2mark_mcq(correct_answer):
    wrong_1 = correct_answer + random.choice([-100, -50, 50, 100])
    wrong_2 = correct_answer + random.choice([-150, 150])
    wrong_3 = correct_answer + random.choice([-200, 200])
    options = [correct_answer, wrong_1, wrong_2, wrong_3]
    options = list(dict.fromkeys(options))
    while len(options) < 4:
        options.append(correct_answer + random.choice([-250, 250]))
    random.shuffle(options)
    return options
@app.route("/questions", methods=["POST"])
def api_question():
    data = request.get_json(force=True)
    marks = str(data.get("marks"))
    q_type = data.get("question_type")

    if q_type == "Random":
        q_type = random.choice(["Pressure", "Density"])

    # Generate question
    if marks == "1" and q_type == "Pressure":
        question = get_pressure_altitude_question()
    elif marks == "1" and q_type == "Density":
        question = get_density_altitude_question()
    elif marks == "2" and q_type == "Pressure":
        question = generate_pressure_2mark_question()
    elif marks == "2" and q_type == "Density":
        question = generate_density_2mark_question()
    else:
        return jsonify({"error": "Invalid combination"}), 400

    # Rename text → question
    question["question"] = question.pop("text", "")

    if "correct" in question:
        question["correct_answer"] = question.pop("correct")
        
    # Always convert options to A, B, C, D format when MCQ
    if question.get("type") == "mcq":
        labels = ["A", "B", "C", "D"]
        original_options = question.get("options", [])

        # Determine the unit for each category
        if question["category"] in ["pressure", "pressure_2mark", "density_2mark"]:
            suffix = " ft"
        elif question["category"] in ["density"]:
            suffix = " °C"
        else:
            suffix = ""

        question["options"] = [
            {
                "label": labels[i],
                "value": f"{original_options[i]}{suffix}"
            }
            for i in range(min(4, len(original_options)))
        ]

    return jsonify(question)


def generate_density_2mark_question():
    airport = random.choice(list(AIRPORT_DATA.keys()))
    elevation = AIRPORT_DATA[airport]
    qnh = random.choice(range(990, 1036, 10))
    oat = random.choice(range(-20, 36))
    ph_raw = elevation + (1013 - qnh) * 30
    ph_rounded = int(50 * round(ph_raw / 50))
    ph_thousands = ph_rounded / 1000
    isa_temp = 15 - 2 * ph_thousands
    isa_dev = oat - isa_temp
    temp_effect = isa_dev * 120
    dh_raw = ph_rounded + temp_effect
    dh_rounded = int(50 * round(dh_raw / 50))

    DENSITY_2MARK_TEMPLATES = [
        "At {airport}, the QNH is {qnh} hPa and the OAT is {oat} °C. Using the elevation of the airport, calculate the Density Altitude. Round your answer to the nearest 50 ft.",
        "Given the QNH of {qnh} hPa and OAT of {oat} °C at {airport}, find the Density Altitude using the airport's elevation. Round your final answer to nearest 50 feet.",
        "Calculate the Density Altitude for {airport} with QNH {qnh} hPa and OAT {oat} °C. Use the known elevation and round to nearest 50 ft.",
        "Given OAT {oat} °C and QNH {qnh} hPa at {airport}, determine the Density Altitude by using airport elevation. Round your answer to nearest 50 feet.",
        "At {airport} Airport, with QNH {qnh} hPa and OAT {oat} °C, compute the Density Altitude. Use elevation and round result to nearest 50 ft."
    ]
    question_text = random.choice(DENSITY_2MARK_TEMPLATES).format(
        airport=airport, qnh=qnh, oat=oat
    )
    q_type = random.choice(['mcq', 'typein'])
    options = generate_density_2mark_mcq(dh_rounded) if q_type == 'mcq' else []
    return {
        'marks': 2,
        'label': '2 Marks – Density Altitude',
        'category': 'density_2mark',
        'text': question_text,
        'type': q_type,
        'options': options,
        'correct': dh_rounded,
        'elev': elevation,
        'qnh': qnh,
        'oat': oat,
        'airport': airport,
        'ph_rounded': ph_rounded,
        'isa_temp': round(isa_temp, 1),
        'isa_dev': round(isa_dev, 1),
        'temp_effect': int(round(temp_effect)),
        'dh_raw': int(dh_raw),
    }
