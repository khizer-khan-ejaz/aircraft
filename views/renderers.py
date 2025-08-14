from flask import jsonify, render_template
import logging

# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def render_question_response(data, show_map=False):
    """
    Render a response for question endpoints.
    Args:
        data (dict): The question data to render, containing 'question' and 'details'.
        show_map (bool): Whether to include map data in the response (e.g., for map visualization).
    Returns:
        Response: JSON response or rendered HTML template based on the request context.
    """
    logger.debug("Rendering question response with show_map=%s", show_map)
    
    if show_map:
        # If map is requested, ensure map data is included and return JSON
        # Map data should be preprocessed in geo_utils and included in 'data'
        logger.debug("Returning JSON with map data")
        return jsonify(data)
    else:
        # For non-map responses, check if data is suitable for JSON or HTML
        if 'question' in data and 'details' in data:
            logger.debug("Returning JSON response for question data")
            return jsonify(data)
        else:
            # Render HTML template if JSON is not appropriate
            logger.debug("Rendering HTML template: question.html")
            try:
                return render_template('question.html', question_data=data)
            except Exception as e:
                logger.error("Error rendering template: %s", str(e))
                return jsonify({'error': 'Failed to render template'}), 500
 
            