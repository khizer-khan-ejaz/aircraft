import logging
from fuzzywuzzy import fuzz
import re
import ast
def load_airport_data(filepath="data.txt"):
    with open(filepath, "r") as f:
        content = f.read()
    return ast.literal_eval(content)

AIRPORT_DATA = load_airport_data()
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
def find(name,airports):
    """Find airport in airports_list by name (case insensitive partial match)"""
    name_lower = name.lower()
    for airport in airports:
        if name_lower in airport.name.lower():
            return airport  # Return the Airport object directly
    return None