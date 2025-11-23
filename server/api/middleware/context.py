# server/api/middleware/context.py
import os
from flask import request
from api.db import get_session, User, Organization

AUTH0_ENABLED = os.getenv("AUTH0_ENABLED", "false").lower() == "true"

def get_current_user():
    """Get current user from request context"""
    if not AUTH0_ENABLED:
        # ✅ Development mode: use or create dev user
        session = get_session()
        if not session:
            return None
        
        try:
            user = session.query(User).filter(User.email == "dev@localhost").first()
            if not user:
                # ✅ Create dev user inline instead of calling get_or_create_user
                user = User(
                    provider_id="dev-user-1",
                    email="dev@localhost",
                    display_name="Development User",
                    is_active=True
                )
                session.add(user)
                session.flush()
                
                # Create personal organization for dev user
                from api.db import create_personal_organization
                personal_org = create_personal_organization(user, session)
                if personal_org:
                    user.personal_organization_id = personal_org.id
                
                session.commit()
                session.refresh(user)
            
            # ✅ Return user and close session properly
            user_id = user.id
            user_email = user.email
            user_display_name = user.display_name
            session.close()
            
            # Return a detached user object (not bound to session)
            detached_user = User()
            detached_user.id = user_id
            detached_user.email = user_email
            detached_user.display_name = user_display_name
            return detached_user
            
        except Exception as e:
            print(f"[Middleware] Error getting dev user: {e}")
            session.rollback()
            session.close()
            return None
    
    # ✅ Production mode: use Auth0 token
    user_data = getattr(request, "user", None)
    if not user_data:
        return None
    
    provider_id = user_data.get("sub")
    email = user_data.get("email")
    name = user_data.get("name") or user_data.get("nickname")
    picture = user_data.get("picture")
    
    # ✅ Import here to avoid circular dependency
    from api.db import get_or_create_user
    
    user = get_or_create_user(provider_id=provider_id, email=email, display_name=name)
    
    # ✅ Update avatar if needed (in separate session)
    if user and picture and not user.avatar_url:
        session = get_session()
        if session:
            try:
                db_user = session.query(User).filter(User.id == user.id).first()
                if db_user:
                    db_user.avatar_url = picture
                    session.commit()
                session.close()
            except Exception as e:
                print(f"[Middleware] Error updating avatar: {e}")
                session.rollback()
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
        
        # ✅ Create detached copy before closing session
        if org:
            org_dict = org.to_dict()
            session.close()
            
            # Return a detached organization object
            detached_org = Organization()
            detached_org.id = org_dict['id']
            detached_org.name = org_dict['name']
            detached_org.slug = org_dict['slug']
            detached_org.is_personal = org_dict['is_personal']
            return detached_org
        else:
            session.close()
            return None
            
    except Exception as e:
        print(f"[Middleware] Error getting organization: {e}")
        if 'session' in locals():
            session.close()
        return None