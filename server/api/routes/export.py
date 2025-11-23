# server/api/routes/export.py
import os
import csv
from io import StringIO
from datetime import datetime
from flask import Blueprint, request, jsonify
from api.db import get_session, Query, Template
from api.middleware import get_current_user, get_user_organization

export_bp = Blueprint('export', __name__)
AUTH0_ENABLED = os.getenv("AUTH0_ENABLED", "false").lower() == "true"

@export_bp.route("/export")
def export_data():
    """Export user data"""
    format_type = request.args.get("format", "json").lower()
    
    session = get_session()
    if not session:
        return jsonify({"error": "Database not available"}), 500
    
    try:
        current_user = get_current_user() if AUTH0_ENABLED else None
        current_org = get_user_organization()
        
        query_q = session.query(Query)
        if AUTH0_ENABLED and current_user:
            if current_org:
                query_q = query_q.filter(Query.organization_id == current_org.id)
            else:
                query_q = query_q.filter(Query.user_id == current_user.id)
        queries = query_q.order_by(Query.created_at.desc()).all()
        
        template_q = session.query(Template)
        if AUTH0_ENABLED and current_user:
            if current_org:
                template_q = template_q.filter(Template.organization_id == current_org.id)
            else:
                template_q = template_q.filter(Template.user_id == current_user.id)
        templates = template_q.order_by(Template.created_at.desc()).all()
        
        session.close()
        
        if format_type == "csv":
            output = StringIO()
            writer = csv.writer(output)
            
            writer.writerow(["Type", "ID", "Name/Prompt", "Response/Content", "Created At"])
            for q in queries:
                writer.writerow([
                    "Query",
                    q.id,
                    q.prompt,
                    q.response,
                    q.created_at.isoformat() if q.created_at else ""
                ])
            
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