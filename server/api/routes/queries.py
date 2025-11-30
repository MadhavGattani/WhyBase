# REPLACE your server/api/routes/queries.py with this updated version

import math
import json
from flask import Blueprint, request, jsonify
from api.db import Citation
from api.db import get_session, Query
from api.ai import call_ai
from api.middleware import get_current_user, get_user_organization
from api.middleware.rate_limit import rate_limit 
from api.services.knowledge_retrieval import get_all_context, build_contextualized_prompt, extract_sources_list
from api.db import Citation
import os

queries_bp = Blueprint('queries', __name__)
AUTH0_ENABLED = os.getenv("AUTH0_ENABLED", "false").lower() == "true"

@queries_bp.route("/query", methods=["POST"])
@rate_limit(max_requests=30, window_seconds=60)
def query_ai():
    """Main AI query endpoint with context-aware responses"""
    data = request.get_json() or {}
    prompt = data.get("prompt", "").strip()
    use_context = data.get("use_context", True)  # Allow disabling context
    
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400
    
    if len(prompt) > 10000:
        return jsonify({"error": "Prompt is too long (max 10000 characters)"}), 400
    
    try:
        current_user = get_current_user() if AUTH0_ENABLED else None
        current_org = get_user_organization()
        
        # Get relevant context from GitHub
        context = {}
        sources = []
        if use_context and current_user:
            context = get_all_context(prompt, current_user.id)
            sources = extract_sources_list(context)
        
        # Build contextualized prompt
        if context.get("total_sources", 0) > 0:
            ai_prompt = build_contextualized_prompt(prompt, context)
        else:
            ai_prompt = prompt
        
        # Get AI response
        response = call_ai(ai_prompt)
        
        # Save to database with citations
        session = get_session()
        if session:
            try:
                query_record = Query(
                    prompt=prompt,
                    response=response,
                    user_id=current_user.id if current_user else None,
                    organization_id=current_org.id if current_org else (current_user.personal_organization_id if current_user else None)
                )
                session.add(query_record)
                session.flush()  # Get query ID
                
                # Add citations
                if sources:
                    from api.db import Citation
                    for source in sources:
                        citation = Citation(
                            query_id=query_record.id,
                            source_type=source["type"],
                            source_title=source["title"],
                            source_url=source["url"],
                            source_metadata=json.dumps(source.get("metadata", {}))
                        )
                        session.add(citation)
                
                session.commit()
                session.close()
            except Exception as e:
                print(f"[DB] Failed to save query: {e}")
                session.rollback()
                session.close()
        
        return jsonify({
            "response": response,
            "sources": sources,
            "context_used": len(sources) > 0
        })
        
    except Exception as e:
        print(f"[Query] Error: {e}")
        return jsonify({"error": str(e)}), 500


@queries_bp.route("/queries", methods=["GET"])
def get_queries():
    """Get query history with pagination and citations"""
    session = get_session()
    if not session:
        return jsonify({"queries": [], "meta": {"page": 1, "pages": 1, "total": 0}})
    
    try:
        page = int(request.args.get("page", 1))
        per_page = int(request.args.get("per_page", 20))
        
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 20
        
        current_user = get_current_user() if AUTH0_ENABLED else None
        current_org = get_user_organization()
        
        query = session.query(Query)
        
        if AUTH0_ENABLED and current_user:
            if current_org:
                query = query.filter(Query.organization_id == current_org.id)
            else:
                query = query.filter(Query.user_id == current_user.id)
        
        total = query.count()
        pages = math.ceil(total / per_page) if total > 0 else 1
        
        queries = query.order_by(Query.created_at.desc())\
                      .offset((page - 1) * per_page)\
                      .limit(per_page).all()
        
        result = []
        for q in queries:
            # Get citations for this query
            citations = []
            if q.citations:
                for citation in q.citations:
                    citations.append({
                        "type": citation.source_type,
                        "title": citation.source_title,
                        "url": citation.source_url,
                        "metadata": json.loads(citation.source_metadata) if citation.source_metadata else {}
                    })
            
            result.append({
                "id": q.id,
                "prompt": q.prompt,
                "response": q.response,
                "created_at": q.created_at.isoformat() if q.created_at else None,
                "sources": citations
            })
        
        session.close()
        return jsonify({
            "queries": result,
            "meta": {
                "page": page,
                "per_page": per_page,
                "pages": pages,
                "total": total
            }
        })
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500