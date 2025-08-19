from flask import Flask, render_template
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from controller.auth_controllers import auth_bp
from controller.question_controllers import question_bp
from controller.map_controller import map_bp
from controller.etp_controller import etp_bp
from controller.density_controller import density_bp
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = Flask(__name__, template_folder='views/templates')
CORS(app, resources={r"/*": {"origins": ["*", "http://127.0.0.1:5000"]}})
app.config["JWT_SECRET_KEY"] = "a-very-strong-and-secret-key-that-you-should-change"
app.config["ALLOWED_IPS"] = ["127.0.0.1", "82.25.126.162", "43.204.137.19", "147.93.20.219", "168.231.123.176"]
jwt = JWTManager(app)

app.register_blueprint(auth_bp)
app.register_blueprint(question_bp)
app.register_blueprint(map_bp)
app.register_blueprint(etp_bp)
app.register_blueprint(density_bp)

@app.route('/')
def index():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5000)