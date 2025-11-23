# server/api/routes/queries.py
from flask import Blueprint, request, jsonify
from api.db import get_session, Query
from api.ai import call_ai
from api.middleware import get_current_user, get_user_organization
import os

queries_bp = Blueprint('queries', __name__)
AUTH0_ENABLED = os.getenv("AUTH0_ENABLED", "false").lower() == "true"

@queries_bp.route("/query", methods=["POST"])
def query_ai():
    """Main AI query endpoint"""
    data = request.get_json() or {}
    prompt = data.get("prompt", "").strip()
    
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    
    try:
        response = call_ai(prompt)
        
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

@queries_bp.route("/queries", methods=["GET"])
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