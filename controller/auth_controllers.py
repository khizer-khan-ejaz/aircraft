from flask import Blueprint, request, jsonify, current_app,Flask
from flask_jwt_extended import create_access_token
import logging

auth_bp = Blueprint('auth', __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def get_client_ip():
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
        logger.info(f"[IP Detection] X-Forwarded-For found: {x_forwarded_for}, client IP resolved to: {ip}")
    else:
        ip = request.remote_addr
        logger.info(f"[IP Detection] No X-Forwarded-For header. Using request.remote_addr: {ip}")
    return ip

@auth_bp.route('/login', methods=['POST'])
def login():
    client_ip = get_client_ip()
    logger.info(f"Login attempt from IP: {client_ip}")

    if client_ip not in current_app.config["ALLOWED_IPS"]:  # Fixed: Use current_app
        logger.warning(f"Access denied for IP: {client_ip}. Not in allowlist.")
        return jsonify({"msg": "Access denied: Your IP address is not authorized."}), 403

    additional_claims = {"ip": client_ip}
    access_token = create_access_token(identity=client_ip, additional_claims=additional_claims)
    
    logger.info(f"Token successfully issued for IP: {client_ip}")
    return jsonify(access_token=access_token)