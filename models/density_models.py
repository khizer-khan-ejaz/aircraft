import random

class PressureCalculator:
    @staticmethod
    def generate_pressure_params():
        elevation = random.choice(range(100, 3001, 10))
        qnh = random.choice(range(990, 1036, 10))
        return elevation, qnh

    @staticmethod
    def calculate_pressure_height(elevation, qnh):
        raw = elevation + (1013 - qnh) * 30
        rounded = int(50 * round(raw / 50))
        return rounded, raw

class DensityCalculator:
    @staticmethod
    def generate_density_question_params():
        pressure_height = random.choice(range(500, 10001, 500))
        oat = random.choice(range(-20, 36))
        return pressure_height, oat

    @staticmethod
    def calculate_isa_deviation(pressure_height, oat):
        thousands = pressure_height / 1000
        isa_temp = 15 - 2 * thousands
        isa_dev = oat - isa_temp
        return round(isa_temp, 1), int(round(isa_dev))