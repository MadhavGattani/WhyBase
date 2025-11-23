# server/api/routes/templates.py
from flask import Blueprint, request, jsonify
from api.db import get_session, Template
from api.middleware import get_current_user, get_user_organization
from api.utils import requires_auth_conditional
import os

templates_bp = Blueprint('templates', __name__)
AUTH0_ENABLED = os.getenv("AUTH0_ENABLED", "false").lower() == "true"

@templates_bp.route("/templates", methods=["GET"])
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
                query = query.filter(
                    (Template.organization_id == current_org.id) |
                    (Template.user_id == current_user.id) |
                    (Template.is_public == True)
                )
            else:
                query = query.filter(Template.user_id == current_user.id)
        
        templates = query.order_by(Template.created_at.desc()).all()
        result = [t.to_dict() for t in templates]
        
        session.close()
        return jsonify({"templates": result})
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500

@templates_bp.route("/templates", methods=["POST"])
@requires_auth_conditional
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

@templates_bp.route("/templates/<int:template_id>", methods=["PUT"])
@requires_auth_conditional
def update_template(template_id):
    """Update a template"""
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
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500

@templates_bp.route("/templates/<int:template_id>", methods=["DELETE"])
@requires_auth_conditional
def delete_template(template_id):
    """Delete a template"""
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
        
        session.delete(template)
        session.commit()
        session.close()
        return jsonify({"message": "Template deleted"})
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500