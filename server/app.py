# server/app.py

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from api.auth import requires_auth

# Load environment variables
load_dotenv()

AUTH0_ENABLED = os.getenv("AUTH0_ENABLED", "false").lower() == "true"
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
DATABASE_URL = os.getenv("DATABASE_URL")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "auth_enabled": AUTH0_ENABLED,
        "domain": AUTH0_DOMAIN,
        "audience": AUTH0_AUDIENCE
    })


@app.route("/api/public")
def public():
    return jsonify({
        "message": "This is a public endpoint — no auth required."
    })


@app.route("/api/protected")
@requires_auth
def protected():
    user = getattr(request, "user", None)
    sub = user.get("sub") if user else None
    email = user.get("email") if user else None

    return jsonify({
        "message": "You accessed a protected endpoint!",
        "user_sub": sub,
        "email": email
    })


@app.route("/api/templates", methods=["GET", "POST"])
def templates():
    if request.method == "GET":
        return jsonify({
            "templates": [
                {"id": 1, "title": "Welcome Template", "prompt": "Write an intro paragraph"},
                {"id": 2, "title": "Product Template", "prompt": "Describe a product in 50 words"}
            ]
        })

    elif request.method == "POST":
        if AUTH0_ENABLED:
            return _create_template_protected()
        else:
            data = request.get_json() or {}
            data["created_by"] = "local-debug-user"
            return jsonify({"ok": True, "template": data}), 201


@requires_auth
def _create_template_protected():
    data = request.get_json() or {}
    user = getattr(request, "user", {})
    data["created_by"] = user.get("sub")
    return jsonify({"ok": True, "template": data}), 201


@app.route("/api/upload", methods=["POST"])
@requires_auth
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    upload_dir = os.path.join(os.getcwd(), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    path = os.path.join(upload_dir, file.filename)
    file.save(path)

    return jsonify({
        "message": "File uploaded successfully",
        "filename": file.filename
    }), 201


@app.errorhandler(401)
def unauthorized(e):
    return jsonify({"error": "Unauthorized"}), 401


@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    print("Starting Loominal Flask API Server 🚀")
    print(f"Auth0 Enabled: {AUTH0_ENABLED}")
    app.run(host="0.0.0.0", port=5000, debug=True)
