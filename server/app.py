# server/app.py
import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from api.db import init_db
from api.routes import register_routes

load_dotenv()

AUTH0_ENABLED = os.getenv("AUTH0_ENABLED", "false").lower() == "true"
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
DATABASE_URL = os.getenv("DATABASE_URL")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024

app = Flask(__name__)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000") 

CORS(app, resources={
    r"/*": {
        "origins": [
            "http://localhost:3000",
            "http://localhost:3001", 
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            FRONTEND_URL
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Organization-Id"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "max_age": 3600
    }
})

app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_SIZE

init_db(DATABASE_URL)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

register_routes(app)

@app.route("/health")
def health():
    from api.db import get_session
    return jsonify({
        "status": "ok",
        "auth_enabled": AUTH0_ENABLED,
        "domain": AUTH0_DOMAIN,
        "audience": AUTH0_AUDIENCE,
        "database_connected": get_session() is not None
    })

@app.errorhandler(401)
def unauthorized(e):
    return jsonify({"error": "Unauthorized"}), 401

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(413)
def file_too_large(e):
    return jsonify({"error": "File too large"}), 413

if __name__ == "__main__":
    print("Starting Loominal Flask API Server 🚀")
    print(f"Auth0 Enabled: {AUTH0_ENABLED}")
    print(f"Database URL: {DATABASE_URL}")
    print(f"Upload Folder: {UPLOAD_FOLDER}")
    app.run(host="0.0.0.0", port=5000, debug=True)