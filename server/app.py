# server/app.py

import os
import json
import math
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import csv
from io import StringIO
import secrets

from api.auth import requires_auth
from api.db import (
    init_db, get_session, Query, Template, UploadedFile, User, 
    Organization, OrganizationInvitation, OrganizationRole, InvitationStatus,
    get_or_create_user, add_user_to_organization, remove_user_from_organization,
    user_organization_memberships
)
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

# Configure CORS to allow frontend access
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Organization-Id"],
        "expose_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_SIZE

# Initialize database
init_db(DATABASE_URL)

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_current_user():
    """Get current user from request context"""
    if not AUTH0_ENABLED:
        # Return a mock user for development without Auth0
        session = get_session()
        if session:
            # Get or create a default user for development
            user = session.query(User).filter(User.email == "dev@localhost").first()
            if not user:
                user = get_or_create_user(
                    provider_id="dev-user-1",
                    email="dev@localhost",
                    display_name="Development User"
                )
            session.close()
            return user
        return None
    
    user_data = getattr(request, "user", None)
    if not user_data:
        return None
    
    provider_id = user_data.get("sub")
    email = user_data.get("email")
    name = user_data.get("name") or user_data.get("nickname")
    picture = user_data.get("picture")
    
    user = get_or_create_user(provider_id=provider_id, email=email, display_name=name)
    
    # Update avatar if provided
    if user and picture and not user.avatar_url:
        session = get_session()
        if session:
            try:
                user.avatar_url = picture
                session.commit()
                session.close()
            except:
                session.close()
    
    return user

def get_user_organization():
    """Get the current organization context from request headers"""
    org_id = request.headers.get("X-Organization-Id")
    if not org_id:
        return None
    
    try:
        org_id = int(org_id)
        session = get_session()
        if not session:
            return None
        
        org = session.query(Organization).filter(Organization.id == org_id).first()
        session.close()
        return org
    except:
        return None

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "auth_enabled": AUTH0_ENABLED,
        "domain": AUTH0_DOMAIN,
        "audience": AUTH0_AUDIENCE,
        "database_connected": get_session() is not None
    })

# ======================
# AI Query Endpoints
# ======================

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
                current_org = get_user_organization()
                
                query_record = Query(
                    prompt=prompt,
                    response=response,
                    user_id=current_user.id if current_user else None,
                    organization_id=current_org.id if current_org else (current_user.personal_organization_id if current_user else None)
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
        current_org = get_user_organization()
        
        query = session.query(Query)
        
        if AUTH0_ENABLED and current_user:
            if current_org:
                query = query.filter(Query.organization_id == current_org.id)
            else:
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

# ======================
# Template Endpoints
# ======================

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
        current_org = get_user_organization()
        
        query = session.query(Template)
        
        if AUTH0_ENABLED and current_user:
            if current_org:
                # Get organization templates and user's personal templates
                query = query.filter(
                    (Template.organization_id == current_org.id) |
                    (Template.user_id == current_user.id) |
                    (Template.is_public == True)
                )
            else:
                # Get user's templates
                query = query.filter(Template.user_id == current_user.id)
        
        templates = query.order_by(Template.created_at.desc()).all()
        
        result = []
        for t in templates:
            result.append(t.to_dict())
        
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
    description = data.get("description", "").strip()
    is_organization_template = data.get("is_organization_template", False)
    
    if not name or not prompt:
        return jsonify({"error": "Name and prompt are required"}), 400
    
    session = get_session()
    if not session:
        return jsonify({"error": "Database not available"}), 500
    
    try:
        current_user = get_current_user() if AUTH0_ENABLED else None
        current_org = get_user_organization()
        
        template = Template(
            name=name,
            prompt=prompt,
            description=description if description else None,
            user_id=current_user.id if current_user else None,
            organization_id=current_org.id if current_org else (current_user.personal_organization_id if current_user else None),
            is_organization_template=is_organization_template
        )
        session.add(template)
        session.commit()
        
        result = template.to_dict()
        
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
            if "description" in data:
                template.description = data.get("description", "").strip() or None
            session.commit()
            
            result = template.to_dict()
            
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

# ======================
# Upload Endpoints
# ======================

@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Upload a file"""
    if AUTH0_ENABLED:
        # Require auth for uploads
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

# ======================
# Organization Endpoints
# ======================

@app.route("/api/organizations", methods=["GET", "POST"])
def organizations():
    """Organization management"""
    # Only require auth if AUTH0 is enabled
    if AUTH0_ENABLED:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authentication required"}), 401
    
    if request.method == "GET":
        return get_organizations()
    elif request.method == "POST":
        return create_organization()

def get_organizations():
    """Get user's organizations"""
    session = get_session()
    if not session:
        return jsonify({"organizations": []})
    
    try:
        current_user = get_current_user()
        if not current_user:
            session.close()
            return jsonify({"error": "User not found"}), 404
        
        # Get all organizations user is a member of
        from sqlalchemy import and_
        
        # Get organization IDs where user is a member
        membership_query = session.query(user_organization_memberships.c.organization_id).filter(
            and_(
                user_organization_memberships.c.user_id == current_user.id,
                user_organization_memberships.c.is_active == True
            )
        )
        
        org_ids = [row[0] for row in membership_query.all()]
        
        # Get organization details
        orgs = session.query(Organization).filter(Organization.id.in_(org_ids)).all()
        
        result = [org.to_dict() for org in orgs]
        
        session.close()
        return jsonify({"organizations": result})
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500

def create_organization():
    """Create a new organization"""
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    slug = data.get("slug", "").strip()
    description = data.get("description", "").strip()
    website = data.get("website", "").strip()
    plan_type = data.get("plan_type", "free")
    
    if not name or not slug:
        return jsonify({"error": "Name and slug are required"}), 400
    
    session = get_session()
    if not session:
        return jsonify({"error": "Database not available"}), 500
    
    try:
        current_user = get_current_user()
        if not current_user:
            session.close()
            return jsonify({"error": "User not found"}), 404
        
        # Check if slug is already taken
        existing = session.query(Organization).filter(Organization.slug == slug).first()
        if existing:
            session.close()
            return jsonify({"error": "Slug already taken"}), 400
        
        # Create organization
        org = Organization(
            name=name,
            slug=slug,
            description=description if description else None,
            website=website if website else None,
            plan_type=plan_type,
            owner_id=current_user.id,
            is_personal=False
        )
        
        session.add(org)
        session.flush()  # Get org ID
        
        # Add creator as owner member
        from sqlalchemy import insert
        stmt = insert(user_organization_memberships).values(
            user_id=current_user.id,
            organization_id=org.id,
            role=OrganizationRole.OWNER
        )
        session.execute(stmt)
        
        session.commit()
        
        result = org.to_dict()
        
        session.close()
        return jsonify({"organization": result}), 201
        
    except Exception as e:
        session.rollback()
        session.close()
        return jsonify({"error": str(e)}), 500

@app.route("/api/organizations/<int:org_id>", methods=["GET", "PUT", "DELETE"])
def organization_detail(org_id):
    """Get, update, or delete organization"""
    # Only require auth if AUTH0 is enabled
    if AUTH0_ENABLED:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authentication required"}), 401
    
    session = get_session()
    if not session:
        return jsonify({"error": "Database not available"}), 500
    
    try:
        current_user = get_current_user()
        if not current_user:
            session.close()
            return jsonify({"error": "User not found"}), 404
        
        org = session.query(Organization).filter(Organization.id == org_id).first()
        if not org:
            session.close()
            return jsonify({"error": "Organization not found"}), 404
        
        # Check if user has access
        user_role = current_user.get_role_in_organization(org_id)
        if not user_role:
            session.close()
            return jsonify({"error": "Access denied"}), 403
        
        if request.method == "GET":
            result = org.to_dict()
            session.close()
            return jsonify({"organization": result})
        
        elif request.method == "PUT":
            # Only admins and owners can update
            if user_role not in [OrganizationRole.OWNER, OrganizationRole.ADMIN]:
                session.close()
                return jsonify({"error": "Insufficient permissions"}), 403
            
            data = request.get_json() or {}
            
            if "name" in data:
                org.name = data["name"].strip()
            if "description" in data:
                org.description = data["description"].strip() or None
            if "website" in data:
                org.website = data["website"].strip() or None
            if "max_members" in data and user_role == OrganizationRole.OWNER:
                org.max_members = int(data["max_members"])
            
            session.commit()
            result = org.to_dict()
            
            session.close()
            return jsonify({"organization": result})
        
        elif request.method == "DELETE":
            # Only owners can delete
            if user_role != OrganizationRole.OWNER:
                session.close()
                return jsonify({"error": "Only owners can delete organizations"}), 403
            
            if org.is_personal:
                session.close()
                return jsonify({"error": "Cannot delete personal organization"}), 400
            
            session.delete(org)
            session.commit()
            session.close()
            return jsonify({"message": "Organization deleted"})
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500

@app.route("/api/organizations/<int:org_id>/members", methods=["GET"])
def get_organization_members(org_id):
    """Get organization members"""
    # Only require auth if AUTH0 is enabled
    if AUTH0_ENABLED:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authentication required"}), 401
    
    session = get_session()
    if not session:
        return jsonify({"members": []})
    
    try:
        current_user = get_current_user()
        if not current_user:
            session.close()
            return jsonify({"error": "User not found"}), 404
        
        # Check if user has access
        user_role = current_user.get_role_in_organization(org_id)
        if not user_role:
            session.close()
            return jsonify({"error": "Access denied"}), 403
        
        # Get members
        from sqlalchemy import and_
        members_data = session.query(
            User, user_organization_memberships.c.role, user_organization_memberships.c.joined_at
        ).join(
            user_organization_memberships,
            User.id == user_organization_memberships.c.user_id
        ).filter(
            and_(
                user_organization_memberships.c.organization_id == org_id,
                user_organization_memberships.c.is_active == True
            )
        ).all()
        
        result = []
        for user, role, joined_at in members_data:
            result.append({
                "id": user.id,
                "email": user.email,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url,
                "role": role.value if hasattr(role, 'value') else role,
                "joined_at": joined_at.isoformat() if joined_at else None,
                "is_active": True
            })
        
        session.close()
        return jsonify({"members": result})
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500

@app.route("/api/organizations/<int:org_id>/members/<int:member_id>", methods=["PUT", "DELETE"])
def manage_organization_member(org_id, member_id):
    """Update or remove organization member"""
    # Only require auth if AUTH0 is enabled
    if AUTH0_ENABLED:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authentication required"}), 401
    
    session = get_session()
    if not session:
        return jsonify({"error": "Database not available"}), 500
    
    try:
        current_user = get_current_user()
        if not current_user:
            session.close()
            return jsonify({"error": "User not found"}), 404
        
        # Check if user has admin/owner access
        user_role = current_user.get_role_in_organization(org_id)
        if user_role not in [OrganizationRole.OWNER, OrganizationRole.ADMIN]:
            session.close()
            return jsonify({"error": "Insufficient permissions"}), 403
        
        if request.method == "PUT":
            # Update member role
            data = request.get_json() or {}
            new_role = data.get("role")
            
            if not new_role:
                session.close()
                return jsonify({"error": "Role is required"}), 400
            
            try:
                role_enum = OrganizationRole(new_role)
            except ValueError:
                session.close()
                return jsonify({"error": "Invalid role"}), 400
            
            # Can't change owner role unless you're the owner
            if role_enum == OrganizationRole.OWNER and user_role != OrganizationRole.OWNER:
                session.close()
                return jsonify({"error": "Only owners can assign owner role"}), 403
            
            from sqlalchemy import update, and_
            stmt = update(user_organization_memberships).where(
                and_(
                    user_organization_memberships.c.user_id == member_id,
                    user_organization_memberships.c.organization_id == org_id
                )
            ).values(role=role_enum)
            
            session.execute(stmt)
            session.commit()
            session.close()
            return jsonify({"message": "Member role updated"})
        
        elif request.method == "DELETE":
            # Remove member
            success = remove_user_from_organization(member_id, org_id)
            if success:
                return jsonify({"message": "Member removed"})
            else:
                return jsonify({"error": "Failed to remove member"}), 500
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500

@app.route("/api/organizations/<int:org_id>/invite", methods=["POST"])
def invite_to_organization(org_id):
    """Invite user to organization"""
    # Only require auth if AUTH0 is enabled
    if AUTH0_ENABLED:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authentication required"}), 401
    
    session = get_session()
    if not session:
        return jsonify({"error": "Database not available"}), 500
    
    try:
        current_user = get_current_user()
        if not current_user:
            session.close()
            return jsonify({"error": "User not found"}), 404
        
        # Check if user has admin/owner access
        user_role = current_user.get_role_in_organization(org_id)
        if user_role not in [OrganizationRole.OWNER, OrganizationRole.ADMIN]:
            session.close()
            return jsonify({"error": "Insufficient permissions"}), 403
        
        data = request.get_json() or {}
        email = data.get("email", "").strip()
        role = data.get("role", "member")
        message = data.get("message", "").strip()
        
        if not email:
            session.close()
            return jsonify({"error": "Email is required"}), 400
        
        try:
            role_enum = OrganizationRole(role)
        except ValueError:
            session.close()
            return jsonify({"error": "Invalid role"}), 400
        
        # Check if organization can add more members
        org = session.query(Organization).filter(Organization.id == org_id).first()
        if not org.can_add_member():
            session.close()
            return jsonify({"error": "Organization has reached maximum member limit"}), 400
        
        # Check if user already has a pending invitation
        existing_invite = session.query(OrganizationInvitation).filter(
            OrganizationInvitation.organization_id == org_id,
            OrganizationInvitation.email == email,
            OrganizationInvitation.status == InvitationStatus.PENDING
        ).first()
        
        if existing_invite:
            session.close()
            return jsonify({"error": "Invitation already sent to this email"}), 400
        
        # Find if invited user exists
        invited_user = session.query(User).filter(User.email == email).first()
        
        # Create invitation
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        invitation = OrganizationInvitation(
            organization_id=org_id,
            role=role_enum,
            email=email,
            invited_user_id=invited_user.id if invited_user else None,
            token=token,
            invited_by_id=current_user.id,
            message=message if message else None,
            expires_at=expires_at
        )
        
        session.add(invitation)
        session.commit()
        
        result = invitation.to_dict()
        
        session.close()
        return jsonify({"invitation": result}), 201
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500

@app.route("/api/organizations/<int:org_id>/invitations", methods=["GET"])
def get_organization_invitations(org_id):
    """Get organization invitations"""
    # Only require auth if AUTH0 is enabled
    if AUTH0_ENABLED:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authentication required"}), 401
    
    session = get_session()
    if not session:
        return jsonify({"invitations": []})
    
    try:
        current_user = get_current_user()
        if not current_user:
            session.close()
            return jsonify({"error": "User not found"}), 404
        
        # Check if user has access
        user_role = current_user.get_role_in_organization(org_id)
        if not user_role:
            session.close()
            return jsonify({"error": "Access denied"}), 403
        
        invitations = session.query(OrganizationInvitation).filter(
            OrganizationInvitation.organization_id == org_id
        ).order_by(OrganizationInvitation.created_at.desc()).all()
        
        result = [inv.to_dict() for inv in invitations]
        
        session.close()
        return jsonify({"invitations": result})
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500

@app.route("/api/organizations/<int:org_id>/invitations/<int:invitation_id>", methods=["DELETE"])
def revoke_invitation(org_id, invitation_id):
    """Revoke organization invitation"""
    # Only require auth if AUTH0 is enabled
    if AUTH0_ENABLED:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authentication required"}), 401
    
    session = get_session()
    if not session:
        return jsonify({"error": "Database not available"}), 500
    
    try:
        current_user = get_current_user()
        if not current_user:
            session.close()
            return jsonify({"error": "User not found"}), 404
        
        # Check if user has admin/owner access
        user_role = current_user.get_role_in_organization(org_id)
        if user_role not in [OrganizationRole.OWNER, OrganizationRole.ADMIN]:
            session.close()
            return jsonify({"error": "Insufficient permissions"}), 403
        
        invitation = session.query(OrganizationInvitation).filter(
            OrganizationInvitation.id == invitation_id,
            OrganizationInvitation.organization_id == org_id
        ).first()
        
        if not invitation:
            session.close()
            return jsonify({"error": "Invitation not found"}), 404
        
        invitation.status = InvitationStatus.EXPIRED
        session.commit()
        session.close()
        
        return jsonify({"message": "Invitation revoked"})
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500

# ======================
# Export Endpoint
# ======================

@app.route("/api/export")
def export_data():
    """Export user data"""
    format_type = request.args.get("format", "json").lower()
    
    session = get_session()
    if not session:
        return jsonify({"error": "Database not available"}), 500
    
    try:
        current_user = get_current_user() if AUTH0_ENABLED else None
        current_org = get_user_organization()
        
        # Get queries
        query_q = session.query(Query)
        if AUTH0_ENABLED and current_user:
            if current_org:
                query_q = query_q.filter(Query.organization_id == current_org.id)
            else:
                query_q = query_q.filter(Query.user_id == current_user.id)
        queries = query_q.order_by(Query.created_at.desc()).all()
        
        # Get templates
        template_q = session.query(Template)
        if AUTH0_ENABLED and current_user:
            if current_org:
                template_q = template_q.filter(Template.organization_id == current_org.id)
            else:
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
                    t.to_dict() for t in templates
                ]
            }
            return jsonify(data)
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500

# ======================
# Error Handlers
# ======================

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