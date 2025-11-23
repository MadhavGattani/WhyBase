# server/api/middleware/context.py
import os
from flask import request
from api.db import get_session, User, Organization, get_or_create_user

AUTH0_ENABLED = os.getenv("AUTH0_ENABLED", "false").lower() == "true"

def get_current_user():
    """Get current user from request context"""
    if not AUTH0_ENABLED:
        session = get_session()
        if session:
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