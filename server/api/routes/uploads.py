# server/api/routes/uploads.py
import os
import math
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from api.db import get_session, UploadedFile
from api.middleware import get_current_user, get_user_organization

uploads_bp = Blueprint('uploads', __name__)
AUTH0_ENABLED = os.getenv("AUTH0_ENABLED", "false").lower() == "true"
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024

# ✅ Allowed file extensions
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 
    'xls', 'xlsx', 'ppt', 'pptx', 'csv', 'json', 'xml', 'zip'
}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@uploads_bp.route("/upload", methods=["POST"])
def upload_file():
    """Upload a file"""
    if AUTH0_ENABLED:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authentication required"}), 401
    
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"error": "Invalid filename"}), 400
    
    # ✅ Validate file extension
    if not allowed_file(filename):
        return jsonify({"error": "File type not allowed"}), 400
    
    # ✅ Validate file size BEFORE saving
    if request.content_length and request.content_length > MAX_UPLOAD_SIZE:
        max_mb = MAX_UPLOAD_SIZE / (1024 * 1024)
        return jsonify({"error": f"File too large. Maximum size is {max_mb}MB"}), 413
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_filename = f"{timestamp}_{filename}"
    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
    
    try:
        # ✅ Save with size limit check
        file.save(filepath)
        
        # ✅ Double-check file size after save
        file_size = os.path.getsize(filepath)
        if file_size > MAX_UPLOAD_SIZE:
            os.remove(filepath)  # Delete if too large
            max_mb = MAX_UPLOAD_SIZE / (1024 * 1024)
            return jsonify({"error": f"File too large. Maximum size is {max_mb}MB"}), 413
        
        session = get_session()
        if session:
            try:
                current_user = get_current_user() if AUTH0_ENABLED else None
                current_org = get_user_organization()
                
                upload_record = UploadedFile(
                    filename=filename,
                    stored_path=filepath,
                    content_type=file.content_type,
                    size=file_size,
                    user_id=current_user.id if current_user else None,
                    organization_id=current_org.id if current_org else (current_user.personal_organization_id if current_user else None)
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
                # Don't delete file if DB fails, just continue
        
        return jsonify({
            "message": "File uploaded successfully",
            "filename": filename,
            "size": file_size
        }), 201
        
    except Exception as e:
        # ✅ Cleanup on error
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
        return jsonify({"error": str(e)}), 500

@uploads_bp.route("/uploads", methods=["GET"])
def get_uploads():
    """Get uploaded files list"""
    session = get_session()
    if not session:
        return jsonify({"uploads": [], "meta": {"page": 1, "pages": 1}})
    
    try:
        current_user = get_current_user() if AUTH0_ENABLED else None
        current_org = get_user_organization()
        
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 10))
        
        query = session.query(UploadedFile)
        
        if AUTH0_ENABLED and current_user:
            if current_org:
                query = query.filter(UploadedFile.organization_id == current_org.id)
            else:
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

@uploads_bp.route("/download/<int:file_id>")
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