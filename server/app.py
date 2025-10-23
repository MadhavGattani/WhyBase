# server/app.py
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
    """
    Query params:
      - page (int, default 1)
      - per_page (int, default 10, max 100)
      - q (string, optional) -> search prompt/response (ILIKE %q%)
    """
    sess = get_session()
    if not sess:
        return jsonify({"error": "DB not connected"}), 500

    try:
        page = max(int(request.args.get("page", 1)), 1)
        per_page = min(int(request.args.get("per_page", 10)), 100)
    except ValueError:
        page = 1
        per_page = 10

    search_q = request.args.get("q", "").strip()

    query = sess.query(Query)
    if search_q:
        like = f"%{search_q}%"
        # SQLAlchemy ILIKE for case-insensitive (Postgres)
        query = query.filter((Query.prompt.ilike(like)) | (Query.response.ilike(like)))

    total = query.count()
    rows = query.order_by(Query.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    data = [
        {"id": q.id, "prompt": q.prompt, "response": q.response, "created_at": q.created_at.isoformat()}
        for q in rows
    ]
    sess.close()

    return jsonify({
        "history": data,
        "meta": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page
        }
    })


@app.route("/api/history/<int:item_id>", methods=["DELETE"])
def delete_history(item_id):
    sess = get_session()
    if not sess:
        return jsonify({"error": "DB not connected"}), 500
    try:
        row = sess.query(Query).filter(Query.id == item_id).first()
        if not row:
            return jsonify({"error": "Not found"}), 404
        sess.delete(row)
        sess.commit()
        sess.close()
        return jsonify({"ok": True})
    except Exception as e:
        print("[DB] Error deleting:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
