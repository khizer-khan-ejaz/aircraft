from venv import logger
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import random
import ast
import math
from math import cos, sin, atan2, sqrt, radians, degrees, asin
import datetime
import logging
from typing import Dict, List, NamedTuple
import logging
from fuzzywuzzy import fuzz

from geographiclib.geodesic import Geodesic
import scipy.optimize as optimize
from cal_func import calculate_geodesic
import firebase_admin
from firebase_admin import credentials, firestore
from flask_jwt_extended import create_access_token, jwt_required, JWTManager, get_jwt
# Import these libraries if available in your environment

logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["*", "http://127.0.0.1:5000"]}})
cred = credentials.Certificate({
    "type": "service_account",
    "project_id": "airplane-49087",
    "private_key_id": "84e969bd2c76953bb01f12cea7c94c37b338dcc6",
    "private_key": """-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCdsdQ2iNJsEzH6\nzzK7pLYaTn/u1cTla1RUkCda9AOQdA7DPN7Opyht4m40t7RRrJYozj8Ky4HStfv3\n5dOaL4356P0qIqbMjV34RYZtEe5jyHWosXPQNGaV+pBlL+fuSVSeDFEuYeqiAjqK\n4XkVBpkagpoDKRLHIGRNoAnqKY8X7iD2B/lNvEaQo0F9io/f5lvwJuZQAAA5kPK9\nK4+re0wcZGgbkpdCfmGULvMBfE+i+ExjkuIfX9nh0wIjP5zy//dHl+5tDvl0iOew\n5RcXsAzOGR0UwNohF7cNruBAGpW08OpkTkW658NQwS0mxGy5mn3tMz5DiIihl1y0\nNYdOfW//AgMBAAECggEAHTeaAIKoLgL+cyBZn3+ch9I8jNVJllIk/Uf6KrVkRarj\nI1RPWc2JxZY64gSZYbqO1b+k2YysIIy8Qwlvg7VE4mVDJr/l1KdqnjnPdrzoRM+a\n0ScTtKNI0IfsofrWx4UJqwDQN75HmT29eAbfhsBCtLE29Nfy1TcQrns06xBJJV8c\nd6dt2rfvWgXc4tHmPaiAQtL1RXIUx64jTxvY2OlCASxpzqhxJe100eU0DAq5BQpi\nj6FwvO/OsiMfaZMsYYs5Hoh8IhIbnRXdGQnCYMUsGIEl1rLf3G7n01xLfYXlto0Q\nzXZ+H1vEf7pNRRWmXsLvZF65Xj3kJPmYRg7knvZBQQKBgQDQA8Oynh2iLxldogZ2\nr0rciC8RBaV9iSU7T4H0Zf7fZ7YoZEh95TUXeqPB/eSiQrddkLyOuRnJ4SrrCo0E\nm4ZWN58kwAahX1LlGBY5fKNZlzWbG0R4G8v39CwPYfXlFGtna3F5w2FfIQ4HyPQx\nysMBjiaaz/PoZUQ9+5Ed+dDVvwKBgQDCEm5TcCdighYSmulpTdAR3Nj0hC/wcQwN\ngUQyx12PmXxAQzuj50L4Slmt54Z+SssOTNV0H3R8AwWPf0Zoowt6S8LNJJQZZiuJ\n4LxTL03UBAq/FjesFteCtmBWfCQ4nQFd2t2gsn23/cIoNw3V6nCDaseTgMCAgjL7\n+9ydaKR1wQKBgQCTPFbksy5egd/+epUApQrkFjDaZ5i/xrdnx9tAVoGVOB+jb3gw\nRHDT8aa/xSpz/60yuSP+Ed7DGnH6dDlkrYDkvfITXShUSNiv9+CjSCmHXJRA+Yf5\nTBOPqnEVYk1enJl5Vn+3pCfj4c3AjOjr5Y0qKKgCpHcMY8Ft7gbFpPHAmQKBgQCL\nixsfDa6UCzt5xz97w0KQBX9OWdnqhi6Ha2IxLN7eSRtpTa6NjNS/mR5gh/BR0M+u\niZqVs6RbIwUViAuFY272UZFRVjLTDH7T1e8z1PieMQXVHlGLgKUXTLF6niqhNmts\nI9pmGNGCwYigx+0/2iFqrRWxvssr2/Jy80dPO5W9QQKBgHxVkgeNeD8B9GOFH3mA\nMn05bNqKWFiJU2kBp4rTnzUy+0DiT15NL8SEGyHKRno0Mcm6//DdBTJexomccVvt\nYdVz6J3t67GQCD+FnCZSZvubaygog8/PSNdizRQrIHuLX11Urj9q4BeLA6vuYVRy\npY+B7jrN1sp81hvYQRsDKLbm\n-----END PRIVATE KEY-----\n""",  # ✅ Use triple quotes for multi-line strings
    "client_email": "firebase-adminsdk-fbsvc@airplane-49087.iam.gserviceaccount.com",
    "client_id": "107082013090178902883",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40airplane-49087.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
})
app.config["JWT_SECRET_KEY"] = "a-very-strong-and-secret-key-that-you-should-change" 
app.config["ALLOWED_IPS"] = ["127.0.0.1", "82.25.126.162","43.204.137.19","147.93.20.219","168.231.123.176"] 
jwt = JWTManager(app)
# 🔹 Step 2: Initialize Firebase App
firebase_admin.initialize_app(cred)

# 🔹 Step 3: Now safely use Firestore
db = firestore.client()
print("✅ Firebase & Firestore initialized successfully!")
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


# Remove this line:
# app = Flask(__name__)


def get_client_ip():
    """
    Correctly identifies the client's IP address, even behind a reverse proxy.
    Logs the IP detection process.
    """
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()  # first IP is the real client
        logger.info(f"[IP Detection] X-Forwarded-For found: {x_forwarded_for}, client IP resolved to: {ip}")
    else:
        ip = request.remote_addr
        logger.info(f"[IP Detection] No X-Forwarded-For header. Using request.remote_addr: {ip}")
    return ip
# ---- Adding wind effect and ground speed calculation functions from first code ----
class Navigation:
    def get_track_angle(self, dep, arr, magnetic=True, date=None):
        # Validate inputs
        if not (-90 <= dep.lat <= 90 and -180 <= dep.long <= 180 and 
                -90 <= arr.lat <= 90 and -180 <= arr.long <= 180):
            raise ValueError("Invalid latitude or longitude")
        if (dep.lat, dep.long) == (arr.lat, arr.long):
            return 0.0

        # Calculate true bearing using great-circle formula
        lat1 = math.radians(dep.lat)
        lon1 = math.radians(dep.long)
        lat2 = math.radians(arr.lat)
        lon2 = math.radians(arr.long)
        
        dlon = lon2 - lon1
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        true_bearing = math.degrees(math.atan2(y, x))
        true_bearing = (true_bearing + 360) % 360
        
        if not magnetic:
            return round(true_bearing, 2)
        
        # Convert to magnetic bearing
        magnetic_variation = self.get_magnetic_variation(dep.lat, dep.long, date)
        magnetic_bearing = (true_bearing - magnetic_variation + 360) % 360
        
        return round(magnetic_bearing, 2)

    def get_magnetic_variation(self, lat, lon, date=None):
        if geo is None:
            print("GeoMag unavailable. Using fallback magnetic variation (-12.0 for New York).")
            return -12.0  # Fallback for New York, 2023
        try:
            date = date or datetime.datetime.utcnow()
            dec_year = self.decimal_year(date)
            result = geo.calculate(glat=lat, glon=lon, alt=0, time=dec_year)
            return float(result.dec)
        except Exception as e:
            print(f"Error calculating magnetic variation: {e}")
            return -12.0  # Fallback for New York

    def decimal_year(self, date):
        """Convert a datetime object to decimal year."""
        year_start = datetime.datetime(date.year, 1, 1)
        year_end = datetime.datetime(date.year + 1, 1, 1)
        year_length = (year_end - year_start).total_seconds()
        seconds_into_year = (date - year_start).total_seconds()
        return date.year + seconds_into_year / year_length

    def get_midpoint(self, dep, arr):
        """Calculate the geographic midpoint between two points."""
        # Convert to radians
        lat1 = math.radians(dep.lat)
        lon1 = math.radians(dep.long)
        lat2 = math.radians(arr.lat)
        lon2 = math.radians(arr.long)
        
        # Convert to Cartesian coordinates
        x1 = math.cos(lat1) * math.cos(lon1)
        y1 = math.cos(lat1) * math.sin(lon1)
        z1 = math.sin(lat1)
        x2 = math.cos(lat2) * math.cos(lon2)
        y2 = math.cos(lat2) * math.sin(lon2)
        z2 = math.sin(lat2)
        
        # Average coordinates
        x = (x1 + x2) / 2
        y = (y1 + y2) / 2
        z = (z1 + z2) / 2
        
        # Convert back to lat/long
        lon = math.atan2(y, x)
        hyp = math.sqrt(x * x + y * y)
        lat = math.atan2(z, hyp)
        
        # Convert to degrees
        mid_lat = math.degrees(lat)
        mid_lon = math.degrees(lon)
        
        return Point(round(mid_lat, 4), round(mid_lon, 4))

    def get_route_magnitude(self, dep, arr, unit='km'):
        """Calculate great-circle distance between two points."""
        # Earth's radius (km)
        R = 6371.0  # Use 3440.1 for nautical miles, 3958.8 for statute miles
        
        lat1 = math.radians(dep.lat)
        lon1 = math.radians(dep.long)
        lat2 = math.radians(arr.lat)
        lon2 = math.radians(arr.long)
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c
        
        if unit == 'nm':
            distance *= 0.539957  # Convert km to nautical miles
        elif unit == 'mi':
            distance *= 0.621371  # Convert km to statute miles
            
        return round(distance, 2)

def decimal_year(date: datetime.datetime) -> float:
    """Calculate decimal year from datetime object."""
    year_start = datetime.datetime(date.year, 1, 1)
    next_year_start = datetime.datetime(date.year + 1, 1, 1)
    year_length = (next_year_start - year_start).total_seconds()
    elapsed = (date - year_start).total_seconds()
    return date.year + elapsed / year_length
import math

import math
@app.route('/login', methods=['POST'])
def login():
    client_ip = get_client_ip()
    logging.info(f"Login attempt from IP: {client_ip}")

    if client_ip not in app.config["ALLOWED_IPS"]:
        logging.warning(f"Access denied for IP: {client_ip}. Not in allowlist.")
        return jsonify({"msg": "Access denied: Your IP address is not authorized."}), 403

    # IP is allowed. Create a token and bind it to the IP for extra security.
    additional_claims = {"ip": client_ip}
    access_token = create_access_token(identity=client_ip, additional_claims=additional_claims)
    
    logging.info(f"Token successfully issued for IP: {client_ip}")
    return jsonify(access_token=access_token)

def haversine_distance(lat1, lon1, lat2, lon2, unit='nm'):
    """
    Calculate the great-circle distance between two points on the Earth.
    
    Parameters:
    lat1, lon1 (float): Latitude and longitude of point 1 (in degrees)
    lat2, lon2 (float): Latitude and longitude of point 2 (in degrees)
    unit (str): Unit of distance - 'nm' for nautical miles (default),
               'km' for kilometers, 'mi' for statute miles
    
    Returns:
    float: Distance between the two points in the specified unit
    """
    
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of Earth in kilometers
    r_km = 6371.0
    
    # Calculate distance in kilometers first
    distance = c * r_km
    
    # Convert to requested unit
    if unit == 'nm':
        # 1 nautical mile = 1.852 km
        distance /= 1.852
    elif unit == 'mi':
        # Convert to statute miles
        distance *= 0.621371
    # else keep in kilometers
    
    return distance

import random
def find_airport_by_name(name, reference, airports):
    """
    Find airport in airports list by matching either name or reference (case insensitive partial match).
    
    Parameters:
        name (str): Partial or full airport name to search.
        reference (str): Additional reference string to match.
        airports (list): List of airport objects (assumed to have a 'name' attribute).

    Returns:
        Airport object if a match is found, else None.
    """
    name_lower = name.lower()
    reference_lower = reference.lower()

    for airport in airports:
        airport_name_lower = airport.name.lower()
        if name_lower in airport_name_lower and reference_lower in airport_name_lower:
            return airport  # Return the first matched Airport object
    return None

import logging
from fuzzywuzzy import fuzz
import re

logger = logging.getLogger(__name__)

def find_airport_by_name(name, reference, airports):
    """
    Finds an airport with high accuracy while balancing strict reference matching
    with practical fallback options to prevent None returns.

    Parameters:
        name (str): The partial or full airport name/code to search for.
        reference (str | list): Reference string(s) for improved accuracy.
        airports (list): A list of Airport objects with 'code', 'name', 'reference' attributes.

    Returns:
        Airport object: The single best matching airport, or None if no match is found.
    """
    if not name or not airports:
        logger.debug("Invalid input: 'name' or 'airports' list is empty.")
        return None

    # Normalize inputs
    name_lower = name.lower().strip()
    name_upper = name.upper().strip()
    name_words = set(name_lower.split())

    # Normalize reference(s) to a list for consistent handling
    reference_list = []
    if isinstance(reference, list):
        reference_list = [ref.strip() for ref in reference if isinstance(ref, str) and ref.strip()]
    elif isinstance(reference, str) and reference.strip():
        reference_list = [reference.strip()]

    has_reference = bool(reference_list)
    
    candidates = []
    reference_matched_candidates = []
    perfect_matches = []

    for airport in airports:
        # Normalize airport data
        airport_name_clean = airport.name.lower().strip()
        airport_code_upper = airport.code.upper().strip()
        airport_reference = getattr(airport, 'reference', '') or ""
        airport_reference_clean = airport_reference.strip()
        airport_name_words = set(airport_name_clean.split())
        
        # Calculate fuzzy match scores
        fuzzy_score = fuzz.token_set_ratio(name_lower, airport_name_clean)
        code_fuzzy_score = fuzz.ratio(name_upper, airport_code_upper)

        score = 0
        match_reason = "No Match"
        reference_matched = False
        reference_match_strength = 0  # 0=none, 1=partial, 2=case-insensitive, 3=exact

        # Reference Matching with different strength levels
        if reference_list and airport_reference_clean:
            for ref in reference_list:
                ref_clean = ref.strip()
                airport_ref_clean = airport_reference_clean.strip()
                
                # Exact match (strongest)
                if ref_clean == airport_ref_clean:
                    reference_matched = True
                    reference_match_strength = 3
                    break
                # Case-insensitive exact match
                elif ref_clean.lower() == airport_ref_clean.lower():
                    reference_matched = True
                    reference_match_strength = 2
                    break
                # Partial match (weaker but still valid)
                elif (len(ref_clean) > 2 and len(airport_ref_clean) > 2 and 
                      (ref_clean.lower() in airport_ref_clean.lower() or 
                       airport_ref_clean.lower() in ref_clean.lower())):
                    reference_matched = True
                    reference_match_strength = 1
                    break

        # SCORING SYSTEM WITH MULTIPLE TIERS
        
        # Check for perfect matches first
        is_perfect_name = name_lower == airport_name_clean
        is_perfect_code = name_upper == airport_code_upper
        is_near_perfect_code = code_fuzzy_score >= 95 and len(name_upper) >= 3
        
        # TIER 1: Perfect matches with reference (highest priority)
        if reference_matched and (is_perfect_name or is_perfect_code or is_near_perfect_code):
            if is_perfect_name:
                score = 3000 + (reference_match_strength * 100)
                match_reason = f"Perfect Name + Ref({reference_match_strength})"
            elif is_perfect_code:
                score = 2900 + (reference_match_strength * 100)
                match_reason = f"Perfect Code + Ref({reference_match_strength})"
            elif is_near_perfect_code:
                score = 2800 + (reference_match_strength * 100)
                match_reason = f"Near-Perfect Code + Ref({reference_match_strength})"
            perfect_matches.append(True)
        
        # TIER 2: Perfect matches without reference
        elif is_perfect_name:
            score = 2000; match_reason = "Perfect Name"
            perfect_matches.append(True)
        elif is_perfect_code:
            score = 1900; match_reason = "Perfect Code"
            perfect_matches.append(True)
        elif is_near_perfect_code:
            score = 1800; match_reason = "Near-Perfect Code"
            perfect_matches.append(True)
        
        # TIER 3: Strong matches with reference
        elif reference_matched:
            perfect_matches.append(False)
            if len(name_words) > 1 and name_words.issubset(airport_name_words):
                score = 1500 + (reference_match_strength * 50)
                match_reason = f"All Words + Ref({reference_match_strength})"
            elif fuzzy_score >= 85:
                score = 1200 + fuzzy_score + (reference_match_strength * 50)
                match_reason = f"High Fuzzy({fuzzy_score}%) + Ref({reference_match_strength})"
            elif fuzzy_score >= 75:
                score = 1000 + fuzzy_score + (reference_match_strength * 50)
                match_reason = f"Good Fuzzy({fuzzy_score}%) + Ref({reference_match_strength})"
            elif name_lower in airport_name_clean and len(name_lower) > 2:
                score = 800 + (reference_match_strength * 50)
                match_reason = f"Substring + Ref({reference_match_strength})"
        
        # TIER 4: Good matches without reference
        elif len(name_words) > 1 and name_words.issubset(airport_name_words):
            score = 700; match_reason = "All Words Match"
            perfect_matches.append(False)
        elif fuzzy_score >= 90:
            score = 600 + fuzzy_score; match_reason = f"High Fuzzy({fuzzy_score}%)"
            perfect_matches.append(False)
        elif fuzzy_score >= 80:
            score = 500 + fuzzy_score; match_reason = f"Good Fuzzy({fuzzy_score}%)"
            perfect_matches.append(False)
        elif name_lower in airport_name_words and len(name_lower) > 2:
            score = 400; match_reason = "Word Match"
            perfect_matches.append(False)
        
        # TIER 5: Fallback matches
        elif fuzzy_score >= 70:
            score = 200 + fuzzy_score; match_reason = f"Medium Fuzzy({fuzzy_score}%)"
            perfect_matches.append(False)
        elif name_lower in airport_name_clean and len(name_lower) > 2:
            score = 150; match_reason = "Partial Match"
            perfect_matches.append(False)
        else:
            perfect_matches.append(False)

        # Add candidate if it meets minimum threshold
        if score > 0:
            candidate = {
                "airport": airport, 
                "score": score, 
                "reason": match_reason,
                "reference_matched": reference_matched,
                "reference_match_strength": reference_match_strength,
                "fuzzy_score": fuzzy_score,
                "is_perfect": perfect_matches[-1] if perfect_matches else False
            }
            
            candidates.append(candidate)
            
            if reference_matched:
                reference_matched_candidates.append(candidate)
            
            logger.debug(
                f"Candidate: {airport.name} ({airport.code}) [Ref: {airport_reference_clean}], "
                f"Score: {score:.2f}, Reason: {match_reason}"
            )

    if not candidates:
        logger.warning(f"No airport candidates found for name='{name}' and reference='{reference}'.")
        return None

    # INTELLIGENT CANDIDATE SELECTION
    
    # Sort all candidates by score
    candidates.sort(key=lambda x: (x["score"], -len(x["airport"].name)), reverse=True)
    
    # Strategy 1: If we have reference and reference-matched candidates, prefer them
    if has_reference and reference_matched_candidates:
        # Sort reference-matched candidates
        reference_matched_candidates.sort(key=lambda x: (x["score"], -len(x["airport"].name)), reverse=True)
        best_ref_candidate = reference_matched_candidates[0]
        
        # If the best reference match is reasonably good, use it
        if best_ref_candidate["score"] >= 800:
            logger.info(f"Selected reference-matched candidate: {best_ref_candidate['airport'].name}")
            return best_ref_candidate["airport"]
        
        # If reference match is weak but we have a perfect non-reference match, decide carefully
        best_overall = candidates[0]
        if (best_overall["is_perfect"] and 
            best_overall["score"] > best_ref_candidate["score"] + 500):
            logger.warning(
                f"Choosing perfect match '{best_overall['airport'].name}' over "
                f"weak reference match '{best_ref_candidate['airport'].name}'"
            )
            return best_overall["airport"]
        else:
            return best_ref_candidate["airport"]
    
    # Strategy 2: No reference provided or no reference matches found
    best_candidate = candidates[0]
    
    # Apply minimum thresholds
    min_threshold = 200 if has_reference else 150
    
    if best_candidate["score"] < min_threshold:
        logger.info(
            f"Best candidate '{best_candidate['airport'].name}' score {best_candidate['score']:.2f} "
            f"below threshold {min_threshold}"
        )
        return None

    logger.info(
        f"Selected: {best_candidate['airport'].name} ({best_candidate['airport'].code}) "
        f"Score: {best_candidate['score']:.2f} | {best_candidate['reason']}"
    )
    
    return best_candidate["airport"]


def find_airport_by_name_safe(name, reference, airports, fallback_name=None):
    """
    Safe wrapper that provides fallback options to prevent None returns.
    
    Parameters:
        name (str): Primary airport name/code to search for
        reference (str | list): Reference for accuracy
        airports (list): List of airport objects
        fallback_name (str): Alternative name to try if primary fails
    
    Returns:
        Airport object or None
    """
    # Try primary search
    result = find_airport_by_name(name, reference, airports)
    if result:
        return result
    
    # Try without reference if it was provided
    if reference:
        logger.info(f"Retrying search for '{name}' without reference constraint")
        result = find_airport_by_name(name, None, airports)
        if result:
            return result
    
    # Try fallback name if provided
    if fallback_name and fallback_name != name:
        logger.info(f"Trying fallback name '{fallback_name}'")
        result = find_airport_by_name(fallback_name, reference, airports)
        if result:
            return result
        
        # Try fallback without reference
        if reference:
            result = find_airport_by_name(fallback_name, None, airports)
            if result:
                return result
    
    logger.error(f"All search attempts failed for name='{name}', reference='{reference}'")
    return None

def get_track_angle(self, dep, arr, magnetic=True):
    # Calculate true bearing using great-circle formula
        lat1 = math.radians(dep.lat)
        lon1 = math.radians(dep.long)
        lat2 = math.radians(arr.lat)
        lon2 = math.radians(arr.long)
        
        dlon = lon2 - lon1
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        true_bearing = math.degrees(math.atan2(y, x))
        true_bearing = (true_bearing + 360) % 360
        
        if not magnetic:
            return true_bearing
        
        # Convert true bearing to magnetic bearing using your existing function
        magnetic_variation = self.get_magnetic_variation(dep.lat, dep.long)
        magnetic_bearing = (true_bearing + magnetic_variation) % 360
        
        return magnetic_bearing

def get_magnetic_variation( lat, lon, date=None):
        date = date or datetime.datetime.utcnow()
        dec_year = decimal_year(date)
        result = geo.calculate(glat=lat, glon=lon, alt=0, time=dec_year)
        return result.d
PREDEFINED_2_MARK_QUESTIONS = [
    {
        "text_template": "Refer to ERC {reference}.\n\nYou are planning a flight from {dep_name_text} to {arr_name_text} on {track_name}. TAS is {tas} and W/V {wind_dir_display}M/{wind_speed} kt\n.The question asks for the position of the Critical Point (CP) between {etp_dest1_name_text} and {etp_dest2_name_text} along the {dep_name_text} to {arr_name_text} track ,  as a distance from {dep_name_text}, is closest to -",
        "dep_name_text": "Launceston",
        "arr_name_text": "East sale",
        "track_name": "W-218",
        "etp_dest1_name_text": "East sale",
        "etp_dest2_name_text": "Latrobe Valley",
        "reference": "L1",
    },
    {
        "text_template": "Refer to ERC {reference}.\n\nYou are planning a flight from {dep_name_text} to {arr_name_text} on {track_name}. TAS is {tas} and W/V {wind_dir_display}M/{wind_speed} kt\n.The question asks for the position of the Critical Point (CP) between {etp_dest1_name_text} and {etp_dest2_name_text} along the {dep_name_text} to {arr_name_text} track ,  as a distance from {dep_name_text}, is closest to -",
        "reference": "L2",
        "dep_name_text": "Griffith",
        "arr_name_text": "Mildura",
        "track_name": "W-415",
        "etp_dest1_name_text": "Mildura",
        "etp_dest2_name_text": "Swan Hill",
    },
 
    {
    "text_template": "Refer to ERC {reference}.\n\nYou are planning a flight from {dep_name_text} to {arr_name_text} on {track_name}. TAS is {tas} and W/V {wind_dir_display}M/{wind_speed} kt\n.The question asks for the position of the Critical Point (CP) between {etp_dest1_name_text} and {etp_dest2_name_text} along the {dep_name_text} to {arr_name_text} track ,  as a distance from {dep_name_text}, is closest to -",
    "dep_name_text": "Inverell",
    "arr_name_text": "Walgett",
    "track_name": "W623",
    "tas": "200 kt",
    "wind_dir_display": "290",
    "wind_speed": "55",
    "etp_dest1_name_text": "Walgett",
    "etp_dest2_name_text": "Narrabri",
    "reference": "L3"
    },

    {
        "text_template": "Refer to ERC {reference}.\n\nYou are planning a flight from {dep_name_text} to {arr_name_text} on {track_name}.  TAS is {tas} and W/V {wind_dir_display}M/{wind_speed} kt\n.The question asks for the position of the Critical Point (CP) between {etp_dest1_name_text} and {etp_dest2_name_text} along the {dep_name_text} to {arr_name_text} track ,  as a distance from {dep_name_text}, is closest to -",
        "dep_name_text": "Emerald",
        "arr_name_text": "Charleville",
        "track_name": "W806",
        "etp_dest1_name_text": "Charleville",
        "etp_dest2_name_text": "Roma",
        "reference": "L4",
    },
        {
        "text_template": "Refer to ERC {reference}.\n\nYou are planning a flight from {dep_name_text} to {arr_name_text} on {track_name}.  TAS is {tas} and W/V {wind_dir_display}M/{wind_speed} kt\n.The question asks for the position of the Critical Point (CP) between {etp_dest1_name_text} and {etp_dest2_name_text} along the {dep_name_text} to {arr_name_text} track ,  as a distance from {dep_name_text}, is closest to -",
        "dep_name_text": "Dubbo ",
        "arr_name_text": "Bourke ",
        "track_name": "W540",
        "etp_dest1_name_text": "Bourke ",
        "etp_dest2_name_text": "Walgett ",
        "reference": "L5",
    },
       {
        "text_template": "Refer to ERC {reference}.\n\nYou are planning a flight from {dep_name_text} to {arr_name_text} on {track_name}.  TAS is {tas} and W/V {wind_dir_display}M/{wind_speed} kt\n.The question asks for the position of the Critical Point (CP) between {etp_dest1_name_text} and {etp_dest2_name_text} along the {dep_name_text} to {arr_name_text} track ,  as a distance from {dep_name_text}, is closest to -",
        "dep_name_text": "Tindal",
        "arr_name_text": "Tennant Creek",
        "track_name": "J30",
        "etp_dest1_name_text": "Tennant Creek",
        "etp_dest2_name_text": "Hooker Creek",
        "reference": "L6",
    },
    {
        "text_template": "Refer to ERC {reference}.\n\nYou are planning a flight from {dep_name_text} to {arr_name_text} on {track_name}.  TAS is {tas} and W/V {wind_dir_display}M/{wind_speed} kt\n.The question asks for the position of the Critical Point (CP) between {etp_dest1_name_text} and {etp_dest2_name_text} along the {dep_name_text} to {arr_name_text} track ,  as a distance from {dep_name_text}, is closest to -",
        "dep_name_text": "Whyalla ",
        "arr_name_text": "Coober Pedy",
        "track_name": "W274",
        "etp_dest1_name_text": "Coober Pedy",
        "etp_dest2_name_text": "Woomera",
        "reference": "L7",
    },
    {
        "text_template": "Refer to ERC {reference}.\n\nYou are planning a flight from {dep_name_text} to {arr_name_text} on {track_name}.  TAS is {tas} and W/V {wind_dir_display}M/{wind_speed} kt\n.The question asks for the position of the Critical Point (CP) between {etp_dest1_name_text} and {etp_dest2_name_text} along the {dep_name_text} to {arr_name_text} track ,  as a distance from {dep_name_text}, is closest to -",
        "dep_name_text": "Newman ",
        "arr_name_text": "Port Hedland",
        "track_name": "W125",
        "etp_dest1_name_text": "Port Hedland",
        "etp_dest2_name_text": "Paraburdoo",
        "reference": "L8",
    },
]
# Initialize generator
generator = AirportQuestionGenerator(sample_airports)
def find(name,airports):
    """Find airport in airports_list by name (case insensitive partial match)"""
    name_lower = name.lower()
    for airport in airports:
        if name_lower in airport.name.lower():
            return airport  # Return the Airport object directly
    return None
# Modify calculate_geodesic function to include ground speed calculations
@app.route('/generate_question', methods=['POST'])
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


# Additional endpoint to get map data for existing questions
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

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'online',
        'endpoints': {
            '/generate_question': 'POST - Generate questions for specific reference and num_airports',
            '/question': 'GET - Display question and map interface'
        }
    })
def calculate_etp(distance, gs_return, gs_outbound):
    """
    Calculate Equi-Time Point (ETP)
    wind_type: 'headwind' or 'tailwind'
    Returns ETP distance and time to ETP
    """
    
    
    # Calculate ETP distance
    etp_distance = (distance * gs_return) / (gs_outbound + gs_return)
    
    # Calculate time to ETP (in hours)
    time_to_etp = etp_distance / gs_outbound
    
    return round(etp_distance, 2), round(time_to_etp * 60, 2)  # Convert time to minutes

def generate_marks2_question():
    # Random parameters
    tas        = random.randint(20, 50) * 5       # 20..50 → 100..250 step 5
    tas_single = random.randint(20, 50) * 5
    distance   = random.randint(20, 50) * 10      # 20..50 → 200..500 step 10
    wind_speed = random.randint(2, 10) * 5        # 2..10  → 10..50  step 5

      # Wind speed in knots
    wind_type = random.choice(['headwind', 'tailwind'])
    engine=random.choice(['single','normal'])
    wind_reverse = 'tailwind' if wind_type == 'headwind' else 'headwind'
    if engine=='single':
        if wind_type == 'headwind':
            gs_outbound = tas - wind_speed
            gs_return = tas_single + wind_speed
            gs_outbound_wrong = tas - wind_speed
            gs_return_wrong = tas_single + wind_speed
            gs_return_falut=tas+wind_speed
        else:
            gs_outbound = tas + wind_speed
            gs_return = tas_single - wind_speed
            gs_outbound_wrong = tas_single + wind_speed
            gs_return_wrong = tas - wind_speed
            gs_return_falut=tas-wind_speed
    else:
        if wind_type == 'headwind':
            gs_outbound = tas - wind_speed
            gs_return = tas + wind_speed
            gs_outbound_wrong = tas_single - wind_speed
            gs_return_wrong = tas_single + wind_speed
            gs_return_falut=tas_single+wind_speed
        else:
            gs_outbound = tas + wind_speed
            gs_return = tas - wind_speed
            
            gs_outbound_wrong = tas_single - wind_speed
            gs_return_wrong = tas_single + wind_speed
            gs_return_falut=tas_single+wind_speed
    # Calculate ETP

    etp_distance, time_to_etp = calculate_etp(distance, gs_return, gs_outbound)
    etp_distance_wrong, time_to_etp_wrong = calculate_etp(distance, gs_return_falut, gs_outbound)
    etp_distance_wrong_1, time_to_etp_wrong_1 = calculate_etp(distance, gs_return_wrong, gs_outbound_wrong)
    etp_distance_wrong_2=etp_distance_wrong_1+10
    time_to_etp_wrong_2=time_to_etp_wrong_1+10
    options = {
                            "A": f'The time of etp {time_to_etp}min and the distance to the PNR is {etp_distance}nm',
                            "B": f'The time of etp {time_to_etp_wrong}min and the distance to the PNR is {etp_distance_wrong}nm',
                            "C": f'The time of etp {time_to_etp_wrong_1}min and the distance to the PNR is {etp_distance_wrong_1}nm',
                            "D": f'The time of etp {time_to_etp_wrong_2}min and the distance to the PNR is {etp_distance_wrong_2}nm',
                        }
    # Format the question
    question = (
    f"From A to B is {distance} nm, Normal engine TAS: {tas} kts, "
    f"Single engine TAS: {tas_single} kts, Forecast {wind_type.capitalize()} outbound: {wind_speed} kts, "
    f"Normal operation TAS: {tas} kts. Find the ETP from A (NM), answer to the nearest whole NM for {engine} engine."
)       
    dgs=distance*gs_return
    add=gs_return+gs_outbound
    solution={
    "formula": "ETP distance from A = (Total distance × GS_home) / (GS_home + GS_outbound)",
    "substitution": f"({distance} × {gs_return}) / ({gs_return }+ {gs_outbound})",
    "calculation": f"{dgs} / {add} = {etp_distance} nm",
    

    }
    
    return {
        'question': question,
        'parameters': {
            'tas': tas,
            'distance': distance,
            'wind_speed': wind_speed,
            'wind_type': wind_type,
            'wind_reverse':wind_reverse,
            'options':options,
            'solution':solution,
            'time':time_to_etp
        },
        'answer': {
            'etp_distance': etp_distance,
            'units': {  
                'distance': 'nautical miles',
                'time':time_to_etp
            }
        },
        'marks': 2
    }

def calculate_groundspeed(tas, course_deg, wind_speed, wind_dir_deg):
    """
    Calculate groundspeed given TAS, course, wind speed, and wind direction.
    Uses vector triangle method.
    """
    # Convert angles to radians
    course_rad = math.radians(course_deg)
    wind_dir_rad = math.radians(wind_dir_deg)
    
    # Wind direction relative to course
    theta = wind_dir_rad - course_rad
    
    # Ground speed formula
    gs = math.sqrt(tas**2 + wind_speed**2 - 2 * tas * wind_speed * math.cos(theta))
    return round(gs, 2)

def generate_marks3_question():
    import random

    tas = random.randrange(100, 251, 5)
    tas_single = random.randrange(100, 251, 5)
  # True Airspeed in knots
    distance = random.randrange(200, 501, 5)  # Total distance nm
    import random

    course_outbound = random.choice(list(range(90, 121)) + list(range(270, 361)))
  # Degrees
    wind_speed = random.randrange(10, 51, 10) # Wind speed knots
    wind_dir = random.randint(0, 359)  # Wind direction degrees

    # Outbound GS
    gs_outbound = calculate_groundspeed(tas, course_outbound, wind_speed, wind_dir)
    gs_outbound_wrong = calculate_groundspeed(tas_single, course_outbound, wind_speed, wind_dir)
    
    # Homebound GS (reverse course)
    home_course = (course_outbound + 180) % 360
    gs_homebound = calculate_groundspeed(tas, home_course, wind_speed, wind_dir)
    gs_homebound_wrong = calculate_groundspeed(tas_single, home_course, wind_speed, wind_dir)
    
    # Calculate ETP
    etp_distance = (distance * gs_homebound) / (gs_outbound + gs_homebound)
    time_to_etp = round((etp_distance / gs_outbound)*60)
    etp_distance_wrong = (distance * gs_homebound_wrong) / (gs_outbound_wrong + gs_homebound_wrong)
    time_to_etp_wrong = round((etp_distance / gs_outbound_wrong*60))
    
    question = (
        f"A to B {distance} eastbound"
        f"Normal operation TAS= {tas} "
        f"Asymmetric {tas_single} TAS kt"
        f"- Outbound course: {course_outbound}°\n"
        f"Wind {wind_dir}M/{wind_speed} kt"
        f"FIND (a) ETP from A (NM). (b) Time from A to the ETP (min). Nearest whole NM and minute . "
    
    )
    options = {
                            "A": f'The time of etp {time_to_etp}min and the distance to the Etp is {etp_distance}nm',
                            "B": f'The time of etp {time_to_etp_wrong}min and the distance to the Etp is {etp_distance_wrong}nm',
                            "C": f'The time of etp {time_to_etp}min and the distance to the Etp is {etp_distance_wrong}nm',
                            "D": f'The time of etp {time_to_etp_wrong}min and the distance to the Etp is {etp_distance}nm',
                        }
   
    return {
        'question': question,
        'parameters': {
            'tas': tas,
            'distance': distance,
            'course_outbound': course_outbound,
            'wind_speed': wind_speed,
            'wind_direction': wind_dir,
            'options':options
        },
        'answer': {
            'gs_outbound': gs_outbound,
            'gs_homebound': gs_homebound,
            'etp_distance': round(etp_distance, 2),
            'time_to_etp': round(time_to_etp * 60, 2),
            'units': {
                'groundspeed': 'knots',
                'distance': 'nautical miles',
                'time': 'minutes'
            }
        },
        'marks': 3
    }


@app.route('/etpwitout')
def index():
    return render_template('question.html')

@app.route('/api/question', methods=['POST'])
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

# Optional: Keep the original GET endpoints for backward compatibility
@app.route('/api/question/marks2', methods=['GET'])
def get_marks2_question():
    question_data = generate_marks2_question()
    return jsonify(question_data)

@app.route('/api/question/marks3', methods=['GET'])
def get_marks3_question():
    question_data = generate_marks3_question()
    return jsonify(question_data)

@app.route('/question')
def display_question():
    return render_template('genrator.html')

# Add a new endpoint to calculate wind effects and ground speed
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


# ---------------------- JSON API ROUTES ONLY ----------------------

# Route to serve the index.html page
@app.route("/dencity", methods=["GET", "POST"])
def density_home():
    if request.method == "POST":
        marks = request.form.get("marks")
        question_type = request.form.get("question_type")
        # Pass user selections to the questions.html page for displaying the question
        return render_template("home.html", marks=marks, question_type=question_type)
    return render_template("dencity.html")
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



@app.route("/api/check_answer", methods=["POST"])
def api_check_answer():
    """
    Expects JSON:
    {
        "user_answer": "number",
        "correct_answer": "number",
        "marks": 1 or 2,
        "category": "...",
        "label": "..."
    }
    Returns JSON whether the answer is correct and any extra info if desired.
    """
    data = request.get_json(force=True)
    try:
        correct_answer = int(data.get("correct_answer"))
        is_correct = int(data.get("user_answer")) == correct_answer
    except:
        is_correct = False
        correct_answer = None

    response = {
        "is_correct": is_correct,
        "user_answer": data.get("user_answer"),
        "correct_answer": correct_answer,
        "category": data.get("category"),
        "marks": data.get("marks"),
        "label": data.get("label")
    }
    return jsonify(response)

# Error handlers
@app.errorhandler(400)
def bad_request(e):
    return jsonify({'error': str(e.description)}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Resource not found'}), 404

if __name__ == '__main__':
    app.run(host="0.0.0.0",debug=True, port=5000)