# server/api/models/integrations.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, func
from sqlalchemy.orm import relationship
from api.db import Base


class Integration(Base):
    """User's connected integrations (GitHub, etc.)"""
    __tablename__ = "integrations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    
    provider = Column(String(50), nullable=False)  # 'github', 'gitlab', etc.
    provider_user_id = Column(String(255), nullable=True)
    provider_username = Column(String(255), nullable=True)
    
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    
    scopes = Column(Text, nullable=True)  # comma-separated scopes
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_sync_at = Column(DateTime, nullable=True)
    
    # Relationships
    repositories = relationship("Repository", back_populates="integration", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "provider": self.provider,
            "provider_username": self.provider_username,
            "is_active": self.is_active,
            "scopes": self.scopes.split(",") if self.scopes else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None
        }


class Repository(Base):
    """Synced GitHub repositories"""
    __tablename__ = "repositories"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    integration_id = Column(Integer, ForeignKey("integrations.id", ondelete="CASCADE"), nullable=False)
    
    github_id = Column(Integer, nullable=False)
    name = Column(String(255), nullable=False)
    full_name = Column(String(512), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(512), nullable=False)
    
    is_private = Column(Boolean, default=False)
    default_branch = Column(String(100), default="main")
    language = Column(String(100), nullable=True)
    
    stars_count = Column(Integer, default=0)
    forks_count = Column(Integer, default=0)
    open_issues_count = Column(Integer, default=0)
    
    is_synced = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    integration = relationship("Integration", back_populates="repositories")
    issues = relationship("Issue", back_populates="repository", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "github_id": self.github_id,
            "name": self.name,
            "full_name": self.full_name,
            "description": self.description,
            "url": self.url,
            "is_private": self.is_private,
            "language": self.language,
            "stars_count": self.stars_count,
            "forks_count": self.forks_count,
            "open_issues_count": self.open_issues_count,
            "is_synced": self.is_synced,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Issue(Base):
    """Synced GitHub issues"""
    __tablename__ = "issues"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    repository_id = Column(Integer, ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False)
    
    github_id = Column(Integer, nullable=False)
    number = Column(Integer, nullable=False)
    title = Column(String(512), nullable=False)
    body = Column(Text, nullable=True)
    state = Column(String(20), default="open")  # open, closed
    url = Column(String(512), nullable=False)
    
    labels = Column(JSON, nullable=True)  # [{name, color}]
    assignees = Column(JSON, nullable=True)  # [{login, avatar_url}]
    
    author_login = Column(String(255), nullable=True)
    author_avatar = Column(String(512), nullable=True)
    
    comments_count = Column(Integer, default=0)
    
    github_created_at = Column(DateTime, nullable=True)
    github_updated_at = Column(DateTime, nullable=True)
    github_closed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    repository = relationship("Repository", back_populates="issues")
    
    def to_dict(self):
        return {
            "id": self.id,
            "github_id": self.github_id,
            "number": self.number,
            "title": self.title,
            "body": self.body[:500] if self.body else None,
            "state": self.state,
            "url": self.url,
            "labels": self.labels or [],
            "assignees": self.assignees or [],
            "author_login": self.author_login,
            "comments_count": self.comments_count,
            "github_created_at": self.github_created_at.isoformat() if self.github_created_at else None,
            "github_updated_at": self.github_updated_at.isoformat() if self.github_updated_at else None
        }