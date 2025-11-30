# server/api/db.py - Enhanced with Organization System
import os
from enum import Enum
from sqlalchemy import create_engine, Column, Integer, Text, DateTime, String, ForeignKey, func, Boolean, Table, JSON
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
from sqlalchemy.exc import OperationalError
from sqlalchemy.types import Enum as SQLEnum
from datetime import datetime

Base = declarative_base()
engine = None
SessionLocal = None


# Enums for role-based permissions
class OrganizationRole(Enum):
    OWNER = "owner"          # Full control, can delete org
    ADMIN = "admin"          # Can manage members, settings, but not delete org
    MEMBER = "member"        # Can use org resources, create content
    VIEWER = "viewer"        # Read-only access

class InvitationStatus(Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"


# Association table for user-organization memberships
user_organization_memberships = Table(
    'user_organization_memberships',
    Base.metadata,
    Column('id', Integer, primary_key=True),
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
    Column('organization_id', Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False),
    Column('role', SQLEnum(OrganizationRole), nullable=False, default=OrganizationRole.MEMBER),
    Column('joined_at', DateTime, default=func.now()),
    Column('is_active', Boolean, default=True),
    # Prevent duplicate memberships
    # UniqueConstraint('user_id', 'organization_id', name='unique_user_org_membership')
)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    provider_id = Column(String(255), unique=True, nullable=True)  # for Auth0 / providers
    email = Column(String(255), unique=True, nullable=True)
    display_name = Column(String(255), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=func.now())
    last_active_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Personal workspace (every user has a default personal organization)
    personal_organization_id = Column(Integer, ForeignKey('organizations.id'), nullable=True)
    
    # Relationships
    templates = relationship("Template", back_populates="owner")
    uploads = relationship("UploadedFile", back_populates="owner")
    queries = relationship("Query", back_populates="user")
    owned_organizations = relationship("Organization", back_populates="owner", foreign_keys="Organization.owner_id")
    personal_organization = relationship("Organization", foreign_keys=[personal_organization_id], post_update=True)
    
    # Organization memberships (many-to-many through association table)
    organization_memberships = relationship(
        "Organization",
        secondary=user_organization_memberships,
        back_populates="members",
        overlaps="members,organization_memberships"
    )
    
    # Invitations sent and received
    sent_invitations = relationship("OrganizationInvitation", foreign_keys="OrganizationInvitation.invited_by_id", back_populates="invited_by")
    received_invitations = relationship("OrganizationInvitation", foreign_keys="OrganizationInvitation.invited_user_id", back_populates="invited_user")

    def get_role_in_organization(self, org_id):
        """Get user's role in a specific organization"""
        session = object_session(self)
        if not session:
            return None
        
        # Check if user is owner
        if self.owned_organizations:
            for org in self.owned_organizations:
                if org.id == org_id:
                    return OrganizationRole.OWNER
        
        # Check membership table
        from sqlalchemy import and_
        membership = session.query(user_organization_memberships).filter(
            and_(
                user_organization_memberships.c.user_id == self.id,
                user_organization_memberships.c.organization_id == org_id,
                user_organization_memberships.c.is_active == True
            )
        ).first()
        
        return OrganizationRole(membership.role) if membership else None

    def get_organizations(self, include_personal=True):
        """Get all organizations user belongs to"""
        orgs = list(self.organization_memberships)
        if include_personal and self.personal_organization:
            orgs.append(self.personal_organization)
        return orgs

    def can_access_organization(self, org_id):
        """Check if user can access an organization"""
        return self.get_role_in_organization(org_id) is not None


class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)  # URL-friendly identifier
    description = Column(Text, nullable=True)
    logo_url = Column(String(512), nullable=True)
    website = Column(String(255), nullable=True)
    
    # Organization settings
    is_personal = Column(Boolean, default=False)  # True for personal workspaces
    is_active = Column(Boolean, default=True)
    max_members = Column(Integer, default=50)  # Member limit
    
    # Billing and plan info (for future use)
    plan_type = Column(String(50), default="free")  # free, pro, enterprise
    billing_email = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Owner relationship
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    owner = relationship("User", back_populates="owned_organizations", foreign_keys=[owner_id])
    
    # Members (many-to-many through association table)
    members = relationship(
        "User",
        secondary=user_organization_memberships,
        back_populates="organization_memberships",
        overlaps="members,organization_memberships"
    )
    
    # Organization content
    templates = relationship("Template", back_populates="organization")
    uploads = relationship("UploadedFile", back_populates="organization")
    queries = relationship("Query", back_populates="organization")
    invitations = relationship("OrganizationInvitation", back_populates="organization")

    def get_member_count(self):
        """Get total number of active members"""
        session = object_session(self)
        if not session:
            return 0
        
        from sqlalchemy import and_
        return session.query(user_organization_memberships).filter(
            and_(
                user_organization_memberships.c.organization_id == self.id,
                user_organization_memberships.c.is_active == True
            )
        ).count()

    def get_members_by_role(self, role=None):
        """Get members filtered by role"""
        session = object_session(self)
        if not session:
            return []
        
        from sqlalchemy import and_
        query = session.query(User).join(user_organization_memberships).filter(
            and_(
                user_organization_memberships.c.organization_id == self.id,
                user_organization_memberships.c.is_active == True
            )
        )
        
        if role:
            query = query.filter(user_organization_memberships.c.role == role)
        
        return query.all()

    def can_add_member(self):
        """Check if organization can add more members"""
        return self.get_member_count() < self.max_members

    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "logo_url": self.logo_url,
            "website": self.website,
            "is_personal": self.is_personal,
            "is_active": self.is_active,
            "max_members": self.max_members,
            "member_count": self.get_member_count(),
            "plan_type": self.plan_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class OrganizationInvitation(Base):
    __tablename__ = "organization_invitations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Organization and role info
    organization_id = Column(Integer, ForeignKey('organizations.id', ondelete='CASCADE'), nullable=False)
    role = Column(SQLEnum(OrganizationRole), nullable=False, default=OrganizationRole.MEMBER)
    
    # Invitee info
    email = Column(String(255), nullable=False)  # Email of person being invited
    invited_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # If user exists
    
    # Invitation metadata
    token = Column(String(255), unique=True, nullable=False)  # Unique invitation token
    status = Column(SQLEnum(InvitationStatus), default=InvitationStatus.PENDING)
    invited_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Optional invitation message
    message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False)  # Invitation expiry
    responded_at = Column(DateTime, nullable=True)  # When user responded
    
    # Relationships
    organization = relationship("Organization", back_populates="invitations")
    invited_by = relationship("User", foreign_keys=[invited_by_id], back_populates="sent_invitations")
    invited_user = relationship("User", foreign_keys=[invited_user_id], back_populates="received_invitations")

    def is_expired(self):
        """Check if invitation has expired"""
        from datetime import datetime
        return datetime.utcnow() > self.expires_at

    def can_be_accepted(self):
        """Check if invitation can still be accepted"""
        return (self.status == InvitationStatus.PENDING and 
                not self.is_expired() and 
                self.organization.is_active)

    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            "id": self.id,
            "organization": self.organization.to_dict() if self.organization else None,
            "role": self.role.value,
            "email": self.email,
            "status": self.status.value,
            "message": self.message,
            "invited_by": {
                "id": self.invited_by.id,
                "display_name": self.invited_by.display_name,
                "email": self.invited_by.email
            } if self.invited_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "responded_at": self.responded_at.isoformat() if self.responded_at else None
        }


# Enhanced existing models with organization support
class Query(Base):
    __tablename__ = "queries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # User and organization associations
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="queries")
    organization = relationship("Organization", back_populates="queries")
    citations = relationship("Citation", back_populates="query", cascade="all, delete-orphan")


class Citation(Base):
    __tablename__ = "citations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    query_id = Column(Integer, ForeignKey("queries.id", ondelete="CASCADE"), nullable=False)
    
    source_type = Column(String(50), nullable=False)
    source_title = Column(String(512), nullable=False)
    source_url = Column(String(1024), nullable=False)
    source_metadata = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    query = relationship("Query", back_populates="citations")
    
class Embedding(Base):
    __tablename__ = "embeddings"
    
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    embedding = Column(Text)  # Will store as string, pgvector handles conversion
    source_type = Column(String(50), nullable=False)  # 'issue', 'repository'
    source_id = Column(Integer, nullable=False)
    source_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class Template(Base):
    __tablename__ = "templates"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    prompt = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    
    # Sharing and visibility
    is_public = Column(Boolean, default=False)  # Can be shared across organizations
    is_organization_template = Column(Boolean, default=False)  # Organization-wide template
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # User and organization associations
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Template creator
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="templates")
    organization = relationship("Organization", back_populates="templates")

    def to_dict(self):
        """Convert to dictionary for JSON responses"""
        return {
            "id": self.id,
            "name": self.name,
            "prompt": self.prompt,
            "description": self.description,
            "is_public": self.is_public,
            "is_organization_template": self.is_organization_template,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "owner": {
                "id": self.owner.id,
                "display_name": self.owner.display_name
            } if self.owner else None
        }


class UploadedFile(Base):
    __tablename__ = "uploaded_files"
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(512), nullable=False)
    stored_path = Column(String(1024), nullable=False)
    content_type = Column(String(255), nullable=True)
    size = Column(Integer, nullable=True)
    
    # Sharing and visibility
    is_public = Column(Boolean, default=False)
    is_organization_file = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now())
    
    # User and organization associations
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="uploads")
    organization = relationship("Organization", back_populates="uploads")


# Database initialization and helper functions
def init_db(db_url):
    global engine, SessionLocal
    if not db_url:
        print("[DB] No DATABASE_URL provided, skipping DB init.")
        return
    try:
        engine = create_engine(db_url)
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        print("[DB] Connected and initialized successfully with organization support.")
    except OperationalError as e:
        print(f"[DB] Could not connect to database: {e}")
        engine = None
        SessionLocal = None


def get_session():
    if not SessionLocal:
        print("[DB] No database session available.")
        return None
    return SessionLocal()


# Enhanced user helper functions
def get_or_create_user(provider_id: str = None, email: str = None, display_name: str = None):
    """
    Find or create a user, and ensure they have a personal organization.
    """
    sess = get_session()
    if not sess:
        return None
    
    user = None
    try:
        # Find existing user
        if provider_id:
            user = sess.query(User).filter(User.provider_id == provider_id).first()
        if not user and email:
            user = sess.query(User).filter(User.email == email).first()
        
        # Create new user if not found
        if not user:
            user = User(provider_id=provider_id, email=email, display_name=display_name)
            sess.add(user)
            sess.flush()  # Get user ID
            
            # Create personal organization for new user
            personal_org = create_personal_organization(user, sess)
            user.personal_organization_id = personal_org.id
            
            sess.commit()
            sess.refresh(user)
        
        # Ensure existing user has personal organization
        elif not user.personal_organization_id:
            personal_org = create_personal_organization(user, sess)
            user.personal_organization_id = personal_org.id
            sess.commit()
        
        sess.close()
        return user
        
    except Exception as e:
        print("[DB] get_or_create_user error:", e)
        sess.rollback()
        sess.close()
        return None


def create_personal_organization(user, session=None):
    """Create a personal organization for a user"""
    if not session:
        session = get_session()
        if not session:
            return None
    
    try:
        # Generate unique slug for personal organization
        base_slug = f"personal-{user.email.split('@')[0]}" if user.email else f"user-{user.id}"
        slug = base_slug
        counter = 1
        
        # Ensure slug is unique
        while session.query(Organization).filter(Organization.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        # Create personal organization
        personal_org = Organization(
            name=f"{user.display_name or user.email or 'User'}'s Workspace",
            slug=slug,
            description="Personal workspace",
            is_personal=True,
            owner_id=user.id,
            max_members=1  # Personal organizations have only 1 member
        )
        
        session.add(personal_org)
        session.flush()  # Get org ID
        
        # Add user as member with owner role
        from sqlalchemy import insert
        stmt = insert(user_organization_memberships).values(
            user_id=user.id,
            organization_id=personal_org.id,
            role=OrganizationRole.OWNER
        )
        session.execute(stmt)
        
        return personal_org
        
    except Exception as e:
        print("[DB] create_personal_organization error:", e)
        return None


def add_user_to_organization(user_id, organization_id, role=OrganizationRole.MEMBER):
    """Add a user to an organization with specified role"""
    session = get_session()
    if not session:
        return False
    
    try:
        from sqlalchemy import insert, and_
        
        # Check if membership already exists
        existing = session.query(user_organization_memberships).filter(
            and_(
                user_organization_memberships.c.user_id == user_id,
                user_organization_memberships.c.organization_id == organization_id
            )
        ).first()
        
        if existing:
            # Update existing membership
            from sqlalchemy import update
            stmt = update(user_organization_memberships).where(
                and_(
                    user_organization_memberships.c.user_id == user_id,
                    user_organization_memberships.c.organization_id == organization_id
                )
            ).values(role=role, is_active=True)
            session.execute(stmt)
        else:
            # Create new membership
            stmt = insert(user_organization_memberships).values(
                user_id=user_id,
                organization_id=organization_id,
                role=role
            )
            session.execute(stmt)
        
        session.commit()
        session.close()
        return True
        
    except Exception as e:
        print("[DB] add_user_to_organization error:", e)
        session.rollback()
        session.close()
        return False


def remove_user_from_organization(user_id, organization_id):
    """Remove a user from an organization"""
    session = get_session()
    if not session:
        return False
    
    try:
        from sqlalchemy import update, and_
        
        # Mark membership as inactive instead of deleting
        stmt = update(user_organization_memberships).where(
            and_(
                user_organization_memberships.c.user_id == user_id,
                user_organization_memberships.c.organization_id == organization_id
            )
        ).values(is_active=False)
        
        session.execute(stmt)
        session.commit()
        session.close()
        return True
        
    except Exception as e:
        print("[DB] remove_user_from_organization error:", e)
        session.rollback()
        session.close()
        return False


# Import session utilities
try:
    from sqlalchemy.orm import object_session
except ImportError:
    def object_session(obj):
        return None