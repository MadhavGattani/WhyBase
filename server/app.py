# server/app.py
from flask import Flask, request, jsonify, send_file
from dotenv import load_dotenv
import os
from api.ai import call_ai
from api.db import init_db, get_session, Query, Template, UploadedFile, get_or_create_user
from flask_cors import CORS
from werkzeug.utils import secure_filename
import csv
import io

load_dotenv(".env")
app = Flask(__name__)
CORS(app)

# uploads folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# config
init_db(os.getenv("DATABASE_URL"))
AUTH0_ENABLED = os.getenv("AUTH0_ENABLED", "false").lower() in ("1", "true", "yes")
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))

# --- Auth skeleton ---
def extract_user_from_request():
    """
    Skeleton: if AUTH0_ENABLED is true, expect Authorization: Bearer <token>
    We do NOT validate token here — replace with real JWT verification in production.
    This function extracts a provider_id (the token string in this skeleton) and calls get_or_create_user.
    """
    if not AUTH0_ENABLED:
        return None
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    # In a real implementation you would verify the JWT and extract the subject/email.
    provider_id = token  # placeholder: treat token as provider_id in dev
    # Optionally extract email/display_name from a decoded token
    user = get_or_create_user(provider_id=provider_id, email=None, display_name=None)
    return user

# --- routes ---
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
            user = extract_user_from_request()
            q = Query(prompt=prompt, response=ai_resp, user_id=(user.id if user else None))
            sess.add(q)
            sess.commit()
            sess.close()
        except Exception as e:
            print("[DB] Failed to save:", e)

    return jsonify({"response": ai_resp})


# Templates CRUD
@app.route("/api/templates", methods=["GET", "POST"])
def templates():
    sess = get_session()
    if not sess:
        return jsonify({"error": "DB not connected"}), 500

    if request.method == "GET":
        # optional: filter by user if authenticated
        user = extract_user_from_request()
        query = sess.query(Template)
        if user:
            query = query.filter(Template.user_id == user.id)
        rows = query.order_by(Template.created_at.desc()).all()
        data = [{"id": r.id, "name": r.name, "prompt": r.prompt, "created_at": r.created_at.isoformat()} for r in rows]
        sess.close()
        return jsonify({"templates": data})

    # POST - create
    body = request.json or {}
    name = body.get("name", "").strip()
    prompt = body.get("prompt", "").strip()
    if not name or not prompt:
        return jsonify({"error": "name and prompt required"}), 400
    try:
        user = extract_user_from_request()
        t = Template(name=name, prompt=prompt, user_id=(user.id if user else None))
        sess.add(t)
        sess.commit()
        res = {"id": t.id, "name": t.name, "prompt": t.prompt}
        sess.close()
        return jsonify(res), 201
    except Exception as e:
        print("[DB] Template create error:", e)
        return jsonify({"error": str(e)}), 500


@app.route("/api/templates/<int:tid>", methods=["PUT", "DELETE"])
def template_modify(tid):
    sess = get_session()
    if not sess:
        return jsonify({"error": "DB not connected"}), 500
    t = sess.query(Template).filter(Template.id == tid).first()
    if not t:
        sess.close()
        return jsonify({"error": "Not found"}), 404

    # If user authenticated, prevent editing other users' templates
    user = extract_user_from_request()
    if user and t.user_id and t.user_id != user.id:
        sess.close()
        return jsonify({"error": "Forbidden"}), 403

    if request.method == "DELETE":
        try:
            sess.delete(t)
            sess.commit()
            sess.close()
            return jsonify({"ok": True})
        except Exception as e:
            print("[DB] Template delete error:", e)
            return jsonify({"error": str(e)}), 500

    # PUT - update
    body = request.json or {}
    t.name = body.get("name", t.name)
    t.prompt = body.get("prompt", t.prompt)
    try:
        sess.commit()
        res = {"id": t.id, "name": t.name, "prompt": t.prompt}
        sess.close()
        return jsonify(res)
    except Exception as e:
        print("[DB] Template update error:", e)
        return jsonify({"error": str(e)}), 500


# File upload
ALLOWED_EXT = None  # allow all for now; set tuple like ('png','pdf','txt') to restrict

@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error": "No selected file"}), 400
    filename = secure_filename(f.filename)
    if ALLOWED_EXT:
        ext = filename.rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_EXT:
            return jsonify({"error": "File type not allowed"}), 400

    # enforce size limit (server side)
    max_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    f.stream.seek(0, os.SEEK_END)
    size = f.stream.tell()
    f.stream.seek(0)
    if size > max_bytes:
        return jsonify({"error": f"File too large. Max {MAX_UPLOAD_SIZE_MB} MB allowed."}), 413

    stored_name = f"{int(os.times()[4]*1000)}_{filename}"
    stored_path = os.path.join(UPLOAD_DIR, stored_name)
    f.save(stored_path)

    sess = get_session()
    if sess:
        try:
            user = extract_user_from_request()
            uf = UploadedFile(filename=filename, stored_path=stored_path, content_type=f.mimetype, size=size, user_id=(user.id if user else None))
            sess.add(uf)
            sess.commit()
            res = {"id": uf.id, "filename": uf.filename, "size": uf.size}
            sess.close()
            return jsonify(res), 201
        except Exception as e:
            print("[DB] Upload save error:", e)
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "DB not available"}), 500


# list uploaded files with pagination
@app.route("/api/uploads", methods=["GET"])
def list_uploads():
    sess = get_session()
    if not sess:
        return jsonify({"error": "DB not connected"}), 500
    try:
        page = max(int(request.args.get("page", 1)), 1)
        per_page = min(int(request.args.get("per_page", 10)), 100)
    except ValueError:
        page = 1
        per_page = 10

    user = extract_user_from_request()
    query = sess.query(UploadedFile)
    if user:
        query = query.filter(UploadedFile.user_id == user.id)

    total = query.count()
    rows = query.order_by(UploadedFile.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    data = [
        {
            "id": r.id,
            "filename": r.filename,
            "size": r.size,
            "content_type": r.content_type,
            "created_at": r.created_at.isoformat()
        }
        for r in rows
    ]
    sess.close()
    return jsonify({
        "uploads": data,
        "meta": {"page": page, "per_page": per_page, "total": total, "pages": (total + per_page - 1) // per_page}
    })


@app.route("/api/download/<int:file_id>", methods=["GET"])
def download_file(file_id):
    sess = get_session()
    if not sess:
        return jsonify({"error": "DB not connected"}), 500
    rec = sess.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    sess.close()
    if not rec:
        return jsonify({"error": "Not found"}), 404
    if not os.path.exists(rec.stored_path):
        return jsonify({"error": "File missing on server"}), 410
    return send_file(rec.stored_path, as_attachment=True, download_name=rec.filename)


# Export history (CSV or JSON)
@app.route("/api/export", methods=["GET"])
def export_history():
    fmt = request.args.get("format", "csv").lower()
    sess = get_session()
    if not sess:
        return jsonify({"error": "DB not connected"}), 500
    rows = sess.query(Query).order_by(Query.created_at.desc()).all()
    sess.close()

    data = [{"id": r.id, "prompt": r.prompt, "response": r.response, "created_at": r.created_at.isoformat()} for r in rows]

    if fmt == "json":
        return jsonify({"data": data})

    # csv fallback
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "created_at", "prompt", "response"])
    for r in data:
        writer.writerow([r["id"], r["created_at"], r["prompt"].replace("\n", "\\n"), r["response"].replace("\n", "\\n")])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode("utf-8")), mimetype="text/csv", as_attachment=True, download_name="loominal_history.csv")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
