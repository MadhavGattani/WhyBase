# server/app.py

import os
import json
import math
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from datetime import datetime
import csv
from io import StringIO

from api.auth import requires_auth
from api.db import init_db, get_session, Query, Template, UploadedFile, User, get_or_create_user
from api.ai import call_ai

# Load environment variables
load_dotenv()

AUTH0_ENABLED = os.getenv("AUTH0_ENABLED", "false").lower() == "true"
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
DATABASE_URL = os.getenv("DATABASE_URL")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_SIZE

# Initialize database
init_db(DATABASE_URL)

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_current_user():
    """Get current user from request context"""
    if not AUTH0_ENABLED:
        return None
    user_data = getattr(request, "user", None)
    if not user_data:
        return None
    
    provider_id = user_data.get("sub")
    email = user_data.get("email")
    name = user_data.get("name") or user_data.get("nickname")
    
    return get_or_create_user(provider_id=provider_id, email=email, display_name=name)

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "auth_enabled": AUTH0_ENABLED,
        "domain": AUTH0_DOMAIN,
        "audience": AUTH0_AUDIENCE,
        "database_connected": get_session() is not None
    })

@app.route("/api/query", methods=["POST"])
def query_ai():
    """Main AI query endpoint"""
    data = request.get_json() or {}
    prompt = data.get("prompt", "").strip()
    
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    
    try:
        # Call AI
        response = call_ai(prompt)
        
        # Save to database if available
        session = get_session()
        if session:
            try:
                current_user = get_current_user() if AUTH0_ENABLED else None
                query_record = Query(
                    prompt=prompt,
                    response=response,
                    user_id=current_user.id if current_user else None
                )
                session.add(query_record)
                session.commit()
                session.close()
            except Exception as e:
                print(f"[DB] Failed to save query: {e}")
                session.close()
        
        return jsonify({"response": response})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/queries", methods=["GET"])
def get_queries():
    """Get query history"""
    session = get_session()
    if not session:
        return jsonify({"queries": []})
    
    try:
        current_user = get_current_user() if AUTH0_ENABLED else None
        
        query = session.query(Query)
        if AUTH0_ENABLED and current_user:
            query = query.filter(Query.user_id == current_user.id)
        
        queries = query.order_by(Query.created_at.desc()).limit(20).all()
        
        result = []
        for q in queries:
            result.append({
                "id": q.id,
                "prompt": q.prompt,
                "response": q.response,
                "created_at": q.created_at.isoformat() if q.created_at else None
            })
        
        session.close()
        return jsonify({"queries": result})
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500

@app.route("/api/templates", methods=["GET", "POST"])
def templates():
    """Template management"""
    if request.method == "GET":
        return get_templates()
    elif request.method == "POST":
        if AUTH0_ENABLED:
            return create_template_protected()
        else:
            return create_template()

def get_templates():
    """Get all templates"""
    session = get_session()
    if not session:
        return jsonify({"templates": []})
    
    try:
        current_user = get_current_user() if AUTH0_ENABLED else None
        
        query = session.query(Template)
        if AUTH0_ENABLED and current_user:
            query = query.filter(Template.user_id == current_user.id)
        
        templates = query.order_by(Template.created_at.desc()).all()
        
        result = []
        for t in templates:
            result.append({
                "id": t.id,
                "name": t.name,
                "prompt": t.prompt,
                "created_at": t.created_at.isoformat() if t.created_at else None
            })
        
        session.close()
        return jsonify({"templates": result})
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500

@requires_auth
def create_template_protected():
    return create_template()

def create_template():
    """Create a new template"""
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    prompt = data.get("prompt", "").strip()
    
    if not name or not prompt:
        return jsonify({"error": "Name and prompt are required"}), 400
    
    session = get_session()
    if not session:
        return jsonify({"error": "Database not available"}), 500
    
    try:
        current_user = get_current_user() if AUTH0_ENABLED else None
        
        template = Template(
            name=name,
            prompt=prompt,
            user_id=current_user.id if current_user else None
        )
        session.add(template)
        session.commit()
        
        result = {
            "id": template.id,
            "name": template.name,
            "prompt": template.prompt,
            "created_at": template.created_at.isoformat() if template.created_at else None
        }
        
        session.close()
        return jsonify({"template": result}), 201
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500

@app.route("/api/templates/<int:template_id>", methods=["PUT", "DELETE"])
def template_detail(template_id):
    """Update or delete a template"""
    if AUTH0_ENABLED:
        return template_detail_protected(template_id)
    else:
        return template_detail_unprotected(template_id)

@requires_auth
def template_detail_protected(template_id):
    return template_detail_unprotected(template_id)

def template_detail_unprotected(template_id):
    session = get_session()
    if not session:
        return jsonify({"error": "Database not available"}), 500
    
    try:
        current_user = get_current_user() if AUTH0_ENABLED else None
        
        query = session.query(Template).filter(Template.id == template_id)
        if AUTH0_ENABLED and current_user:
            query = query.filter(Template.user_id == current_user.id)
        
        template = query.first()
        if not template:
            session.close()
            return jsonify({"error": "Template not found"}), 404
        
        if request.method == "PUT":
            data = request.get_json() or {}
            name = data.get("name", "").strip()
            prompt = data.get("prompt", "").strip()
            
            if not name or not prompt:
                session.close()
                return jsonify({"error": "Name and prompt are required"}), 400
            
            template.name = name
            template.prompt = prompt
            session.commit()
            
            result = {
                "id": template.id,
                "name": template.name,
                "prompt": template.prompt,
                "created_at": template.created_at.isoformat() if template.created_at else None
            }
            
            session.close()
            return jsonify({"template": result})
        
        elif request.method == "DELETE":
            session.delete(template)
            session.commit()
            session.close()
            return jsonify({"message": "Template deleted"})
    
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500

@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Upload a file"""
    if AUTH0_ENABLED:
        return upload_file_protected()
    else:
        return upload_file_unprotected()

@requires_auth
def upload_file_protected():
    return upload_file_unprotected()

def upload_file_unprotected():
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"error": "Invalid filename"}), 400
    
    # Create unique filename to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{timestamp}_{filename}"
    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
    
    try:
        file.save(filepath)
        file_size = os.path.getsize(filepath)
        
        # Save to database if available
        session = get_session()
        if session:
            try:
                current_user = get_current_user() if AUTH0_ENABLED else None
                
                upload_record = UploadedFile(
                    filename=filename,
                    stored_path=filepath,
                    content_type=file.content_type,
                    size=file_size,
                    user_id=current_user.id if current_user else None
                )
                session.add(upload_record)
                session.commit()
                
                result = {
                    "id": upload_record.id,
                    "filename": upload_record.filename,
                    "size": upload_record.size,
                    "content_type": upload_record.content_type,
                    "created_at": upload_record.created_at.isoformat() if upload_record.created_at else None
                }
                
                session.close()
                return jsonify({"upload": result}), 201
            
            except Exception as e:
                session.close()
                print(f"[DB] Failed to save upload record: {e}")
        
        return jsonify({
            "message": "File uploaded successfully",
            "filename": filename,
            "size": file_size
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/uploads", methods=["GET"])
def get_uploads():
    """Get uploaded files list"""
    session = get_session()
    if not session:
        return jsonify({"uploads": [], "meta": {"page": 1, "pages": 1}})
    
    try:
        current_user = get_current_user() if AUTH0_ENABLED else None
        
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
        
        query = session.query(UploadedFile)
        if AUTH0_ENABLED and current_user:
            query = query.filter(UploadedFile.user_id == current_user.id)
        
        total = query.count()
        pages = math.ceil(total / per_page) if total > 0 else 1
        
        uploads = query.order_by(UploadedFile.created_at.desc())\
                      .offset((page - 1) * per_page)\
                      .limit(per_page).all()
        
        result = []
        for u in uploads:
            result.append({
                "id": u.id,
                "filename": u.filename,
                "size": u.size,
                "content_type": u.content_type,
                "created_at": u.created_at.isoformat() if u.created_at else None
            })
        
        session.close()
        return jsonify({
            "uploads": result,
            "meta": {"page": page, "pages": pages, "total": total}
        })
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500

@app.route("/api/download/<int:file_id>")
def download_file(file_id):
    """Download a file"""
    session = get_session()
    if not session:
        return jsonify({"error": "Database not available"}), 500
    
    try:
        current_user = get_current_user() if AUTH0_ENABLED else None
        
        query = session.query(UploadedFile).filter(UploadedFile.id == file_id)
        if AUTH0_ENABLED and current_user:
            query = query.filter(UploadedFile.user_id == current_user.id)
        
        upload = query.first()
        if not upload:
            session.close()
            return jsonify({"error": "File not found"}), 404
        
        if not os.path.exists(upload.stored_path):
            session.close()
            return jsonify({"error": "File no longer exists on disk"}), 404
        
        session.close()
        return send_file(upload.stored_path, as_attachment=True, download_name=upload.filename)
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500

@app.route("/api/export")
def export_data():
    """Export user data"""
    format_type = request.args.get("format", "json").lower()
    
    session = get_session()
    if not session:
        return jsonify({"error": "Database not available"}), 500
    
    try:
        current_user = get_current_user() if AUTH0_ENABLED else None
        
        # Get queries
        query_q = session.query(Query)
        if AUTH0_ENABLED and current_user:
            query_q = query_q.filter(Query.user_id == current_user.id)
        queries = query_q.order_by(Query.created_at.desc()).all()
        
        # Get templates
        template_q = session.query(Template)
        if AUTH0_ENABLED and current_user:
            template_q = template_q.filter(Template.user_id == current_user.id)
        templates = template_q.order_by(Template.created_at.desc()).all()
        
        session.close()
        
        if format_type == "csv":
            # Export as CSV
            output = StringIO()
            writer = csv.writer(output)
            
            # Write queries
            writer.writerow(["Type", "ID", "Name/Prompt", "Response/Content", "Created At"])
            for q in queries:
                writer.writerow([
                    "Query",
                    q.id,
                    q.prompt,
                    q.response,
                    q.created_at.isoformat() if q.created_at else ""
                ])
            
            # Write templates
            for t in templates:
                writer.writerow([
                    "Template",
                    t.id,
                    t.name,
                    t.prompt,
                    t.created_at.isoformat() if t.created_at else ""
                ])
            
            output.seek(0)
            return output.getvalue(), 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': 'attachment; filename=loominal_export.csv'
            }
        
        else:
            # Export as JSON
            data = {
                "exported_at": datetime.now().isoformat(),
                "queries": [
                    {
                        "id": q.id,
                        "prompt": q.prompt,
                        "response": q.response,
                        "created_at": q.created_at.isoformat() if q.created_at else None
                    }
                    for q in queries
                ],
                "templates": [
                    {
                        "id": t.id,
                        "name": t.name,
                        "prompt": t.prompt,
                        "created_at": t.created_at.isoformat() if t.created_at else None
                    }
                    for t in templates
                ]
            }
            return jsonify(data)
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500

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