# server/app.py
<<<<<<< HEAD
from flask import Flask, request, jsonify, send_file
from dotenv import load_dotenv
import os
from api.ai import call_ai
from api.db import init_db, get_session, Query, Template, UploadedFile, get_or_create_user
from flask_cors import CORS
from werkzeug.utils import secure_filename
import csv
import io
=======
import os
import io
import csv
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from api.auth import requires_auth
from api.db import init_db, get_session, Query, Template, UploadedFile, get_or_create_user
from api.ai import call_ai

# Load environment variables
load_dotenv()

AUTH0_ENABLED = os.getenv("AUTH0_ENABLED", "false").lower() == "true"
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///loominal.db")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
>>>>>>> 276c147 (feat(auth): add Auth0 integration and login UI)

load_dotenv(".env")
app = Flask(__name__)
CORS(app)

<<<<<<< HEAD
# uploads folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
=======
# Initialize database
init_db(DATABASE_URL)

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_user_id_from_request():
    """Extract user_id from JWT if authenticated, else return None"""
    user = getattr(request, "user", None)
    if not user:
        return None
    
    sub = user.get("sub")
    email = user.get("email")
    name = user.get("name")
    
    if sub:
        db_user = get_or_create_user(provider_id=sub, email=email, display_name=name)
        return db_user.id if db_user else None
    return None

>>>>>>> 276c147 (feat(auth): add Auth0 integration and login UI)

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


<<<<<<< HEAD
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
=======
@app.route("/api/query", methods=["POST"])
def query_ai():
    """Handle AI query - optionally authenticated"""
    data = request.get_json() or {}
    prompt = data.get("prompt", "").strip()
    
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    
    try:
        # Call AI
        response = call_ai(prompt)
        
        # Save to database
        sess = get_session()
        if sess:
            user_id = get_user_id_from_request() if AUTH0_ENABLED else None
            query = Query(prompt=prompt, response=response, user_id=user_id)
            sess.add(query)
            sess.commit()
            sess.close()
        
        return jsonify({"response": response}), 200
    except Exception as e:
        app.logger.error(f"Query error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/queries", methods=["GET"])
def get_queries():
    """Get query history - optionally filtered by user"""
    sess = get_session()
    if not sess:
        return jsonify({"queries": []}), 200
    
    try:
        user_id = get_user_id_from_request() if AUTH0_ENABLED else None
        
        query = sess.query(Query)
        if user_id:
            query = query.filter(Query.user_id == user_id)
        
        queries = query.order_by(Query.created_at.desc()).limit(20).all()
        
        result = [{
            "id": q.id,
            "prompt": q.prompt,
            "response": q.response,
            "created_at": q.created_at.isoformat() if q.created_at else None
        } for q in queries]
        
        sess.close()
        return jsonify({"queries": result}), 200
    except Exception as e:
        sess.close()
        app.logger.error(f"Get queries error: {e}")
        return jsonify({"queries": []}), 200


@app.route("/api/templates", methods=["GET", "POST"])
def templates():
    """Get or create templates"""
    sess = get_session()
    if not sess:
        return jsonify({"templates": []}), 200
    
    if request.method == "GET":
        try:
            user_id = get_user_id_from_request() if AUTH0_ENABLED else None
            
            query = sess.query(Template)
            if user_id:
                query = query.filter(Template.user_id == user_id)
            
            templates = query.order_by(Template.created_at.desc()).all()
            
            result = [{
                "id": t.id,
                "name": t.name,
                "prompt": t.prompt,
                "created_at": t.created_at.isoformat() if t.created_at else None
            } for t in templates]
            
            sess.close()
            return jsonify({"templates": result}), 200
        except Exception as e:
            sess.close()
            app.logger.error(f"Get templates error: {e}")
            return jsonify({"templates": []}), 200
    
    elif request.method == "POST":
        try:
            data = request.get_json() or {}
            name = data.get("name", "").strip()
            prompt = data.get("prompt", "").strip()
            
            if not name or not prompt:
                sess.close()
                return jsonify({"error": "Name and prompt are required"}), 400
            
            user_id = get_user_id_from_request() if AUTH0_ENABLED else None
            
            template = Template(name=name, prompt=prompt, user_id=user_id)
            sess.add(template)
            sess.commit()
            sess.refresh(template)
            
            result = {
                "id": template.id,
                "name": template.name,
                "prompt": template.prompt,
                "created_at": template.created_at.isoformat() if template.created_at else None
            }
            
            sess.close()
            return jsonify({"template": result}), 201
        except Exception as e:
            sess.close()
            app.logger.error(f"Create template error: {e}")
            return jsonify({"error": str(e)}), 500


@app.route("/api/templates/<int:template_id>", methods=["PUT", "DELETE"])
def template_detail(template_id):
    """Update or delete a template"""
    sess = get_session()
    if not sess:
        return jsonify({"error": "Database not available"}), 500
    
    try:
        template = sess.query(Template).filter(Template.id == template_id).first()
        
        if not template:
            sess.close()
            return jsonify({"error": "Template not found"}), 404
        
        # Check ownership if auth enabled
        if AUTH0_ENABLED:
            user_id = get_user_id_from_request()
            if template.user_id != user_id:
                sess.close()
                return jsonify({"error": "Unauthorized"}), 403
        
        if request.method == "DELETE":
            sess.delete(template)
            sess.commit()
            sess.close()
            return jsonify({"message": "Template deleted"}), 200
        
        elif request.method == "PUT":
            data = request.get_json() or {}
            name = data.get("name", "").strip()
            prompt = data.get("prompt", "").strip()
            
            if name:
                template.name = name
            if prompt:
                template.prompt = prompt
            
            sess.commit()
            sess.refresh(template)
            
            result = {
                "id": template.id,
                "name": template.name,
                "prompt": template.prompt,
                "created_at": template.created_at.isoformat() if template.created_at else None
            }
            
            sess.close()
            return jsonify({"template": result}), 200
    except Exception as e:
        sess.close()
        app.logger.error(f"Template detail error: {e}")
        return jsonify({"error": str(e)}), 500
>>>>>>> 276c147 (feat(auth): add Auth0 integration and login UI)

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
    """Upload a file - optionally authenticated"""
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

<<<<<<< HEAD
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
=======
    try:
        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save file
        file.save(filepath)
        
        # Save to database
        sess = get_session()
        if sess:
            user_id = get_user_id_from_request() if AUTH0_ENABLED else None
            
            upload = UploadedFile(
                filename=filename,
                stored_path=filepath,
                content_type=file.content_type,
                size=os.path.getsize(filepath),
                user_id=user_id
            )
            sess.add(upload)
            sess.commit()
            sess.refresh(upload)
            
            result = {
                "id": upload.id,
                "filename": upload.filename,
                "size": upload.size,
                "created_at": upload.created_at.isoformat() if upload.created_at else None
            }
            
            sess.close()
            return jsonify({"upload": result}), 201
        
        return jsonify({
            "message": "File uploaded successfully",
            "filename": filename
        }), 201
    except Exception as e:
        app.logger.error(f"Upload error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/uploads", methods=["GET"])
def list_uploads():
    """List uploaded files with pagination"""
    sess = get_session()
    if not sess:
        return jsonify({"uploads": [], "meta": {"page": 1, "per_page": 6, "pages": 1}}), 200
    
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 6))
        
        user_id = get_user_id_from_request() if AUTH0_ENABLED else None
        
        query = sess.query(UploadedFile)
        if user_id:
            query = query.filter(UploadedFile.user_id == user_id)
        
        total = query.count()
        pages = (total + per_page - 1) // per_page
        
        uploads = query.order_by(UploadedFile.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        result = [{
            "id": u.id,
            "filename": u.filename,
            "size": u.size,
            "content_type": u.content_type,
            "created_at": u.created_at.isoformat() if u.created_at else None
        } for u in uploads]
        
        sess.close()
        return jsonify({
            "uploads": result,
            "meta": {"page": page, "per_page": per_page, "pages": pages, "total": total}
        }), 200
    except Exception as e:
        sess.close()
        app.logger.error(f"List uploads error: {e}")
        return jsonify({"uploads": [], "meta": {"page": 1, "per_page": 6, "pages": 1}}), 200


@app.route("/api/download/<int:file_id>", methods=["GET"])
def download_file(file_id):
    """Download a file"""
    sess = get_session()
    if not sess:
        return jsonify({"error": "Database not available"}), 500
    
    try:
        upload = sess.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        
        if not upload:
            sess.close()
            return jsonify({"error": "File not found"}), 404
        
        # Check ownership if auth enabled
        if AUTH0_ENABLED:
            user_id = get_user_id_from_request()
            if upload.user_id != user_id:
                sess.close()
                return jsonify({"error": "Unauthorized"}), 403
        
        if not os.path.exists(upload.stored_path):
            sess.close()
            return jsonify({"error": "File not found on disk"}), 404
        
        sess.close()
        return send_file(upload.stored_path, download_name=upload.filename, as_attachment=True)
    except Exception as e:
        sess.close()
        app.logger.error(f"Download error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/export", methods=["GET"])
def export_history():
    """Export query history as CSV or JSON"""
    format_type = request.args.get("format", "csv").lower()
    
    sess = get_session()
    if not sess:
        return jsonify({"error": "Database not available"}), 500
    
    try:
        user_id = get_user_id_from_request() if AUTH0_ENABLED else None
        
        query = sess.query(Query)
        if user_id:
            query = query.filter(Query.user_id == user_id)
        
        queries = query.order_by(Query.created_at.desc()).all()
        
        if format_type == "json":
            result = [{
                "id": q.id,
                "prompt": q.prompt,
                "response": q.response,
                "created_at": q.created_at.isoformat() if q.created_at else None
            } for q in queries]
            
            sess.close()
            return jsonify({"queries": result}), 200
        
        else:  # CSV
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["ID", "Prompt", "Response", "Created At"])
            
            for q in queries:
                writer.writerow([
                    q.id,
                    q.prompt,
                    q.response,
                    q.created_at.isoformat() if q.created_at else ""
                ])
            
            sess.close()
            
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode()),
                mimetype="text/csv",
                as_attachment=True,
                download_name="loominal_history.csv"
            )
    except Exception as e:
        sess.close()
        app.logger.error(f"Export error: {e}")
        return jsonify({"error": str(e)}), 500
>>>>>>> 276c147 (feat(auth): add Auth0 integration and login UI)


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
<<<<<<< HEAD
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
=======
    print("Starting Loominal Flask API Server 🚀")
    print(f"Auth0 Enabled: {AUTH0_ENABLED}")
    print(f"Database: {DATABASE_URL}")
    app.run(host="0.0.0.0", port=5000, debug=True)
>>>>>>> 276c147 (feat(auth): add Auth0 integration and login UI)
