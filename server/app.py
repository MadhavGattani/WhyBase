from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
from api.ai import call_ai
from api.db import init_db, get_session

load_dotenv('.env')
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

from flask_cors import CORS
CORS(app)

init_db(os.getenv("DATABASE_URL"))

@app.route("/api/health")
def health():
    return jsonify({"status":"ok"})

@app.route("/api/query", methods=["POST"])
def query():
    body = request.json or {}
    prompt = body.get("prompt") or ""
    if not prompt:
        return jsonify({"error":"no prompt provided"}), 400

    ai_resp = call_ai(prompt)

    try:
        sess = get_session()
        sess.insert_query(prompt, ai_resp)
    except Exception as e:
        app.logger.warn("DB save failed: %s", e)

    return jsonify({"response": ai_resp})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=int(os.environ.get("FLASK_DEBUG", "0")))
