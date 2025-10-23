from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
from api.ai import call_ai
from api.db import init_db, get_session, Query
from flask_cors import CORS

load_dotenv(".env")
app = Flask(__name__)
CORS(app)

init_db(os.getenv("DATABASE_URL"))


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/query", methods=["POST"])
def query():
    body = request.json or {}
    prompt = body.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    ai_resp = call_ai(prompt)

    # Save to DB
    sess = get_session()
    if sess:
        try:
            q = Query(prompt=prompt, response=ai_resp)
            sess.add(q)
            sess.commit()
            sess.close()
        except Exception as e:
            print("[DB] Failed to save:", e)

    return jsonify({"response": ai_resp})


@app.route("/api/history", methods=["GET"])
def history():
    sess = get_session()
    if not sess:
        return jsonify({"error": "DB not connected"}), 500

    try:
        rows = sess.query(Query).order_by(Query.created_at.desc()).limit(10).all()
        data = [
            {"id": q.id, "prompt": q.prompt, "response": q.response, "created_at": q.created_at.isoformat()}
            for q in rows
        ]
        return jsonify({"history": data})
    except Exception as e:
        print("[DB] Error fetching history:", e)
        return jsonify({"error": str(e)}), 500
    finally:
        sess.close()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
