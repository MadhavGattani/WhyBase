# server/api/routes/organizations.py
import os
import re
import secrets
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from sqlalchemy import and_, insert, update
from api.db import (
    get_session, Organization, OrganizationInvitation, OrganizationRole, 
    InvitationStatus, User, user_organization_memberships,
    add_user_to_organization, remove_user_from_organization
)
from api.middleware import get_current_user
from api.utils.validators import validate_email, validate_url
from api.middleware.rate_limit import rate_limit, rate_limit_strict



organizations_bp = Blueprint('organizations', __name__)
AUTH0_ENABLED = os.getenv("AUTH0_ENABLED", "false").lower() == "true"

# ✅ Reserved slugs that cannot be used
RESERVED_SLUGS = {
    'admin', 'api', 'auth', 'login', 'logout', 'signup', 'register',
    'settings', 'dashboard', 'profile', 'user', 'users', 'organization',
    'organizations', 'org', 'orgs', 'team', 'teams', 'app', 'about',
    'help', 'support', 'contact', 'terms', 'privacy', 'security'
}

def validate_slug(slug: str) -> tuple[bool, str]:
    """
    Validate organization slug
    Returns: (is_valid, error_message)
    """
    if not slug:
        return False, "Slug is required"
    
    if len(slug) < 3:
        return False, "Slug must be at least 3 characters"
    
    if len(slug) > 50:
        return False, "Slug must be less than 50 characters"
    
    # Only lowercase letters, numbers, and hyphens
    if not re.match(r'^[a-z0-9-]+$', slug):
        return False, "Slug can only contain lowercase letters, numbers, and hyphens"
    
    # Cannot start or end with hyphen
    if slug.startswith('-') or slug.endswith('-'):
        return False, "Slug cannot start or end with a hyphen"
    
    # Cannot have consecutive hyphens
    if '--' in slug:
        return False, "Slug cannot contain consecutive hyphens"
    
    # Check reserved slugs
    if slug.lower() in RESERVED_SLUGS:
        return False, f"'{slug}' is a reserved slug and cannot be used"
    
    return True, ""

def validate_organization_name(name: str) -> tuple[bool, str]:
    """
    Validate organization name
    Returns: (is_valid, error_message)
    """
    if not name:
        return False, "Name is required"
    
    if len(name) < 2:
        return False, "Name must be at least 2 characters"
    
    if len(name) > 100:
        return False, "Name must be less than 100 characters"
    
    # Check for suspicious patterns
    if name.strip() != name:
        return False, "Name cannot have leading or trailing whitespace"
    
    return True, ""

@organizations_bp.route("/organizations", methods=["GET"])
def get_organizations():
    """Get user's organizations"""
    if AUTH0_ENABLED:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authentication required"}), 401
    
    session = get_session()
    if not session:
        return jsonify({"organizations": []})
    
    try:
        current_user = get_current_user()
        if not current_user:
            session.close()
            return jsonify({"error": "User not found"}), 404
        
        membership_query = session.query(user_organization_memberships.c.organization_id).filter(
            and_(
                user_organization_memberships.c.user_id == current_user.id,
                user_organization_memberships.c.is_active == True
            )
        )
        
        org_ids = [row[0] for row in membership_query.all()]
        orgs = session.query(Organization).filter(Organization.id.in_(org_ids)).all()
        result = [org.to_dict() for org in orgs]
        
        session.close()
        return jsonify({"organizations": result})
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500

@organizations_bp.route("/organizations", methods=["POST"])
@rate_limit_strict(max_requests=5, window_seconds=60)
def create_organization():
    """Create a new organization"""
    if AUTH0_ENABLED:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authentication required"}), 401
    
    data = request.get_json() or {}

    # ✅ Safe handling and validation
    name = (data.get("name") or "").strip()
    slug = (data.get("slug") or "").strip().lower()  # Force lowercase

    # ✅ Validate name
    name_valid, name_error = validate_organization_name(name)
    if not name_valid:
        return jsonify({"error": name_error}), 400
    
    # ✅ Validate slug
    slug_valid, slug_error = validate_slug(slug)
    if not slug_valid:
        return jsonify({"error": slug_error}), 400

    # ✅ Safe handling of optional fields
    desc_raw = data.get("description")
    description = desc_raw.strip() if isinstance(desc_raw, str) and desc_raw else None
    
    # ✅ Validate description length
    if description and len(description) > 500:
        return jsonify({"error": "Description must be less than 500 characters"}), 400

    website_raw = data.get("website")
    website = website_raw.strip() if isinstance(website_raw, str) and website_raw else None
    
    # ✅ Validate website URL
    if website:
        if not re.match(r'^https?://.+', website):
            return jsonify({"error": "Website must be a valid URL starting with http:// or https://"}), 400
        if len(website) > 255:
            return jsonify({"error": "Website URL is too long"}), 400

    plan_type = data.get("plan_type", "free")
    
    # ✅ Validate plan type
    if plan_type not in ["free", "pro", "enterprise"]:
        return jsonify({"error": "Invalid plan type"}), 400
    
    session = get_session()
    if not session:
        return jsonify({"error": "Database not available"}), 500
    
    try:
        current_user = get_current_user()
        if not current_user:
            session.close()
            return jsonify({"error": "User not found"}), 404
        
        # Check if slug already exists
        existing = session.query(Organization).filter(Organization.slug == slug).first()
        if existing:
            session.close()
            return jsonify({"error": f"Slug '{slug}' is already taken"}), 400
        
        org = Organization(
            name=name,
            slug=slug,
            description=description,
            website=website,
            plan_type=plan_type,
            owner_id=current_user.id,
            is_personal=False
        )
        
        session.add(org)
        session.flush()
        
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

@organizations_bp.route("/organizations/<int:org_id>", methods=["GET", "PUT", "DELETE"])
def organization_detail(org_id):
    """Get, update, or delete organization"""
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
        
        user_role = current_user.get_role_in_organization(org_id)
        if not user_role:
            session.close()
            return jsonify({"error": "Access denied"}), 403
        
        if request.method == "GET":
            result = org.to_dict()
            session.close()
            return jsonify({"organization": result})
        
        elif request.method == "PUT":
            if user_role not in [OrganizationRole.OWNER, OrganizationRole.ADMIN]:
                session.close()
                return jsonify({"error": "Insufficient permissions"}), 403
            
            data = request.get_json() or {}
            
            if "name" in data:
                org.name = (data["name"] or "").strip()
            if "description" in data:
                desc = data["description"]
                org.description = (desc.strip() if isinstance(desc, str) and desc.strip() else None)
            if "website" in data:
                web = data["website"]
                org.website = (web.strip() if isinstance(web, str) and web.strip() else None)
            if "max_members" in data and user_role == OrganizationRole.OWNER:
                org.max_members = int(data["max_members"])
            
            session.commit()
            result = org.to_dict()
            
            session.close()
            return jsonify({"organization": result})
        
        elif request.method == "DELETE":
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

@organizations_bp.route("/organizations/<int:org_id>/members", methods=["GET"])
def get_organization_members(org_id):
    """Get organization members"""
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
        
        user_role = current_user.get_role_in_organization(org_id)
        if not user_role:
            session.close()
            return jsonify({"error": "Access denied"}), 403
        
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

@organizations_bp.route("/organizations/<int:org_id>/members/<int:member_id>", methods=["PUT", "DELETE"])
def manage_organization_member(org_id, member_id):
    """Update or remove organization member"""
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
        
        user_role = current_user.get_role_in_organization(org_id)
        if user_role not in [OrganizationRole.OWNER, OrganizationRole.ADMIN]:
            session.close()
            return jsonify({"error": "Insufficient permissions"}), 403
        
        if request.method == "PUT":
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
            
            if role_enum == OrganizationRole.OWNER and user_role != OrganizationRole.OWNER:
                session.close()
                return jsonify({"error": "Only owners can assign owner role"}), 403
            
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
            success = remove_user_from_organization(member_id, org_id)
            if success:
                return jsonify({"message": "Member removed"})
            else:
                return jsonify({"error": "Failed to remove member"}), 500
        
    except Exception as e:
        session.close()
        return jsonify({"error": str(e)}), 500

@organizations_bp.route("/organizations/<int:org_id>/invite", methods=["POST"])
@rate_limit_strict(max_requests=10, window_seconds=60)
def invite_to_organization(org_id):
    """Invite user to organization"""
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
        
        user_role = current_user.get_role_in_organization(org_id)
        if user_role not in [OrganizationRole.OWNER, OrganizationRole.ADMIN]:
            session.close()
            return jsonify({"error": "Insufficient permissions"}), 403
        
        data = request.get_json() or {}

        email_raw = data.get("email")
        email = email_raw.strip() if isinstance(email_raw, str) else ""
        email_valid, email_error = validate_email(email)
        if not email_valid:
            session.close()
            return jsonify({"error": email_error}), 400
        role = data.get("role", "member")
        msg_raw = data.get("message")
        message = msg_raw.strip() if isinstance(msg_raw, str) and msg_raw.strip() else None
        
        if not email:
            session.close()
            return jsonify({"error": "Email is required"}), 400
        
        try:
            role_enum = OrganizationRole(role)
        except ValueError:
            session.close()
            return jsonify({"error": "Invalid role"}), 400
        
        org = session.query(Organization).filter(Organization.id == org_id).first()
        if not org.can_add_member():
            session.close()
            return jsonify({"error": "Organization has reached maximum member limit"}), 400
        
        existing_invite = session.query(OrganizationInvitation).filter(
            OrganizationInvitation.organization_id == org_id,
            OrganizationInvitation.email == email,
            OrganizationInvitation.status == InvitationStatus.PENDING
        ).first()
        
        if existing_invite:
            session.close()
            return jsonify({"error": "Invitation already sent to this email"}), 400
        
        invited_user = session.query(User).filter(User.email == email).first()
        
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        invitation = OrganizationInvitation(
            organization_id=org_id,
            role=role_enum,
            email=email,
            invited_user_id=invited_user.id if invited_user else None,
            token=token,
            invited_by_id=current_user.id,
            message=message,
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

@organizations_bp.route("/organizations/<int:org_id>/invitations", methods=["GET"])
def get_organization_invitations(org_id):
    """Get organization invitations"""
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

@organizations_bp.route("/organizations/<int:org_id>/invitations/<int:invitation_id>", methods=["DELETE"])
def revoke_invitation(org_id, invitation_id):
    """Revoke organization invitation"""
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
