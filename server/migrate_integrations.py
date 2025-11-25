#!/usr/bin/env python3
"""
Migration script for adding GitHub integration support to Loominal.
Run: python migrate_integrations.py
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

def run_migration():
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ ERROR: DATABASE_URL not found")
        return False
    
    print("🚀 Starting Integrations Migration...")
    
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        inspector = inspect(engine)
        
        existing_tables = inspector.get_table_names()
        print(f"📋 Existing tables: {', '.join(existing_tables)}")
        
        # Create integrations table
        if "integrations" not in existing_tables:
            print("Creating integrations table...")
            session.execute(text("""
                CREATE TABLE integrations (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
                    provider VARCHAR(50) NOT NULL,
                    provider_user_id VARCHAR(255),
                    provider_username VARCHAR(255),
                    access_token TEXT NOT NULL,
                    refresh_token TEXT,
                    token_expires_at TIMESTAMP,
                    scopes TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_sync_at TIMESTAMP
                )
            """))
            print("✅ integrations table created")
        else:
            print("ℹ️  integrations table already exists")
        
        # Create repositories table
        if "repositories" not in existing_tables:
            print("Creating repositories table...")
            session.execute(text("""
                CREATE TABLE repositories (
                    id SERIAL PRIMARY KEY,
                    integration_id INTEGER NOT NULL REFERENCES integrations(id) ON DELETE CASCADE,
                    github_id INTEGER NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    full_name VARCHAR(512) NOT NULL,
                    description TEXT,
                    url VARCHAR(512) NOT NULL,
                    is_private BOOLEAN DEFAULT FALSE,
                    default_branch VARCHAR(100) DEFAULT 'main',
                    language VARCHAR(100),
                    stars_count INTEGER DEFAULT 0,
                    forks_count INTEGER DEFAULT 0,
                    open_issues_count INTEGER DEFAULT 0,
                    is_synced BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✅ repositories table created")
        else:
            print("ℹ️  repositories table already exists")
        
        # Create issues table
        if "issues" not in existing_tables:
            print("Creating issues table...")
            session.execute(text("""
                CREATE TABLE issues (
                    id SERIAL PRIMARY KEY,
                    repository_id INTEGER NOT NULL REFERENCES repositories(id) ON DELETE CASCADE,
                    github_id INTEGER NOT NULL,
                    number INTEGER NOT NULL,
                    title VARCHAR(512) NOT NULL,
                    body TEXT,
                    state VARCHAR(20) DEFAULT 'open',
                    url VARCHAR(512) NOT NULL,
                    labels JSONB,
                    assignees JSONB,
                    author_login VARCHAR(255),
                    author_avatar VARCHAR(512),
                    comments_count INTEGER DEFAULT 0,
                    github_created_at TIMESTAMP,
                    github_updated_at TIMESTAMP,
                    github_closed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✅ issues table created")
        else:
            print("ℹ️  issues table already exists")
        
        # Create indexes
        print("Creating indexes...")
        
        indexes = [
            ("idx_integrations_user", "CREATE INDEX IF NOT EXISTS idx_integrations_user ON integrations(user_id)"),
            ("idx_integrations_provider", "CREATE INDEX IF NOT EXISTS idx_integrations_provider ON integrations(provider)"),
            ("idx_repositories_integration", "CREATE INDEX IF NOT EXISTS idx_repositories_integration ON repositories(integration_id)"),
            ("idx_repositories_github_id", "CREATE INDEX IF NOT EXISTS idx_repositories_github_id ON repositories(github_id)"),
            ("idx_issues_repository", "CREATE INDEX IF NOT EXISTS idx_issues_repository ON issues(repository_id)"),
            ("idx_issues_github_id", "CREATE INDEX IF NOT EXISTS idx_issues_github_id ON issues(github_id)"),
            ("idx_issues_state", "CREATE INDEX IF NOT EXISTS idx_issues_state ON issues(state)"),
        ]
        
        for name, sql in indexes:
            try:
                session.execute(text(sql))
                print(f"✅ Index {name} created")
            except Exception as e:
                print(f"ℹ️  Index {name}: {e}")
        
        session.commit()
        session.close()
        
        print("\n🎉 Migration completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False


if __name__ == "__main__":
    print("Loominal Integrations Migration")
    print("================================")
    success = run_migration()
    sys.exit(0 if success else 1)