from flask import Flask, send_from_directory
from flask_cors import CORS
import os
from dotenv import load_dotenv
from database import initialize_db
from backend.routes import reports_bp, stats_bp, reviews_bp

load_dotenv()

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
CORS(app)

app.register_blueprint(reports_bp)
app.register_blueprint(stats_bp)
app.register_blueprint(reviews_bp)

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory('../uploads', filename)

if __name__ == '__main__':
    initialize_db()
    
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    app.run(host=host, port=port, debug=True)
