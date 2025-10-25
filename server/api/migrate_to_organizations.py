# server/api/migrate_to_organizations.py
"""
Database migration script to add organization support to existing Loominal database.
Run this script to upgrade your existing database schema.
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration():
    """Run the organization migration"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("ERROR: DATABASE_URL not found in environment variables")
        return False
    
    print("🚀 Starting Loominal Organization Migration...")
    print(f"Database: {DATABASE_URL}")
    
    try:
        # Connect to database
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("✅ Connected to database")
        
        # Step 1: Create new organization-related tables
        print("\n📊 Creating organization tables...")
        
        # Create organizations table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS organizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL,
                slug VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                logo_url VARCHAR(512),
                website VARCHAR(255),
                is_personal BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                max_members INTEGER DEFAULT 50,
                plan_type VARCHAR(50) DEFAULT 'free',
                billing_email VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                owner_id INTEGER NOT NULL,
                FOREIGN KEY (owner_id) REFERENCES users (id)
            )
        """))
        
        # Create user-organization memberships table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS user_organization_memberships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                organization_id INTEGER NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'member',
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (organization_id) REFERENCES organizations (id) ON DELETE CASCADE,
                UNIQUE(user_id, organization_id)
            )
        """))
        
        # Create organization invitations table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS organization_invitations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                organization_id INTEGER NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'member',
                email VARCHAR(255) NOT NULL,
                invited_user_id INTEGER,
                token VARCHAR(255) UNIQUE NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                invited_by_id INTEGER NOT NULL,
                message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                responded_at DATETIME,
                FOREIGN KEY (organization_id) REFERENCES organizations (id) ON DELETE CASCADE,
                FOREIGN KEY (invited_user_id) REFERENCES users (id),
                FOREIGN KEY (invited_by_id) REFERENCES users (id)
            )
        """))
        
        print("✅ Organization tables created")
        
        # Step 2: Add new columns to existing tables
        print("\n🔧 Adding organization support to existing tables...")
        
        # Add columns to users table
        try:
            session.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(512)"))
            print("✅ Added avatar_url to users")
        except:
            print("ℹ️  avatar_url column already exists in users")
        
        try:
            session.execute(text("ALTER TABLE users ADD COLUMN last_active_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
            print("✅ Added last_active_at to users")
        except:
            print("ℹ️  last_active_at column already exists in users")
        
        try:
            session.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"))
            print("✅ Added is_active to users")
        except:
            print("ℹ️  is_active column already exists in users")
        
        try:
            session.execute(text("ALTER TABLE users ADD COLUMN personal_organization_id INTEGER"))
            print("✅ Added personal_organization_id to users")
        except:
            print("ℹ️  personal_organization_id column already exists in users")
        
        # Add columns to queries table
        try:
            session.execute(text("ALTER TABLE queries ADD COLUMN organization_id INTEGER"))
            print("✅ Added organization_id to queries")
        except:
            print("ℹ️  organization_id column already exists in queries")
        
        # Add columns to templates table
        try:
            session.execute(text("ALTER TABLE templates ADD COLUMN description TEXT"))
            print("✅ Added description to templates")
        except:
            print("ℹ️  description column already exists in templates")
        
        try:
            session.execute(text("ALTER TABLE templates ADD COLUMN is_public BOOLEAN DEFAULT 0"))
            print("✅ Added is_public to templates")
        except:
            print("ℹ️  is_public column already exists in templates")
        
        try:
            session.execute(text("ALTER TABLE templates ADD COLUMN is_organization_template BOOLEAN DEFAULT 0"))
            print("✅ Added is_organization_template to templates")
        except:
            print("ℹ️  is_organization_template column already exists in templates")
        
        try:
            session.execute(text("ALTER TABLE templates ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"))
            print("✅ Added updated_at to templates")
        except:
            print("ℹ️  updated_at column already exists in templates")
        
        try:
            session.execute(text("ALTER TABLE templates ADD COLUMN organization_id INTEGER"))
            print("✅ Added organization_id to templates")
        except:
            print("ℹ️  organization_id column already exists in templates")
        
        # Add columns to uploaded_files table
        try:
            session.execute(text("ALTER TABLE uploaded_files ADD COLUMN is_public BOOLEAN DEFAULT 0"))
            print("✅ Added is_public to uploaded_files")
        except:
            print("ℹ️  is_public column already exists in uploaded_files")
        
        try:
            session.execute(text("ALTER TABLE uploaded_files ADD COLUMN is_organization_file BOOLEAN DEFAULT 0"))
            print("✅ Added is_organization_file to uploaded_files")
        except:
            print("ℹ️  is_organization_file column already exists in uploaded_files")
        
        try:
            session.execute(text("ALTER TABLE uploaded_files ADD COLUMN organization_id INTEGER"))
            print("✅ Added organization_id to uploaded_files")
        except:
            print("ℹ️  organization_id column already exists in uploaded_files")
        
        # Step 3: Create personal organizations for existing users
        print("\n👥 Creating personal organizations for existing users...")
        
        # Get all existing users
        users = session.execute(text("SELECT id, email, display_name FROM users")).fetchall()
        
        for user in users:
            user_id, email, display_name = user
            
            # Check if user already has a personal organization
            existing_personal = session.execute(text(
                "SELECT id FROM organizations WHERE owner_id = ? AND is_personal = 1"
            ), (user_id,)).fetchone()
            
            if not existing_personal:
                # Generate unique slug
                base_slug = f"personal-{email.split('@')[0]}" if email else f"user-{user_id}"
                slug = base_slug
                counter = 1
                
                while session.execute(text("SELECT id FROM organizations WHERE slug = ?"), (slug,)).fetchone():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                # Create personal organization
                org_name = f"{display_name or email or 'User'}'s Workspace"
                session.execute(text("""
                    INSERT INTO organizations (name, slug, description, is_personal, owner_id, max_members)
                    VALUES (?, ?, ?, 1, ?, 1)
                """), (org_name, slug, "Personal workspace", user_id))
                
                # Get the created organization ID
                org_id = session.execute(text("SELECT last_insert_rowid()")).fetchone()[0]
                
                # Update user's personal_organization_id
                session.execute(text(
                    "UPDATE users SET personal_organization_id = ? WHERE id = ?"
                ), (org_id, user_id))
                
                # Add user as owner member of their personal organization
                session.execute(text("""
                    INSERT INTO user_organization_memberships (user_id, organization_id, role)
                    VALUES (?, ?, 'owner')
                """), (user_id, org_id))
                
                print(f"✅ Created personal organization for user {user_id} ({email})")
        
        # Step 4: Migrate existing content to personal organizations
        print("\n📦 Migrating existing content to personal organizations...")
        
        # Migrate queries to personal organizations
        session.execute(text("""
            UPDATE queries 
            SET organization_id = (
                SELECT personal_organization_id 
                FROM users 
                WHERE users.id = queries.user_id
            )
            WHERE user_id IS NOT NULL AND organization_id IS NULL
        """))
        
        # Migrate templates to personal organizations
        session.execute(text("""
            UPDATE templates 
            SET organization_id = (
                SELECT personal_organization_id 
                FROM users 
                WHERE users.id = templates.user_id
            )
            WHERE user_id IS NOT NULL AND organization_id IS NULL
        """))
        
        # Migrate uploaded files to personal organizations
        session.execute(text("""
            UPDATE uploaded_files 
            SET organization_id = (
                SELECT personal_organization_id 
                FROM users 
                WHERE users.id = uploaded_files.user_id
            )
            WHERE user_id IS NOT NULL AND organization_id IS NULL
        """))
        
        print("✅ Content migrated to personal organizations")
        
        # Commit all changes
        session.commit()
        session.close()
        
        print("\n🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Replace your server/api/db.py with the new organization-enabled version")
        print("2. Restart your Flask application")
        print("3. Test the organization features")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure your database is accessible")
        print("2. Make sure no other applications are using the database")
        print("3. Check that DATABASE_URL is correct")
        if session:
            session.rollback()
            session.close()
        return False


if __name__ == "__main__":
    print("Loominal Organization Migration Tool")
    print("=====================================")
    
    # Safety check
    response = input("\n⚠️  This will modify your database. Have you backed up your data? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print("Please backup your database before running this migration.")
        sys.exit(1)
    
    success = run_migration()
    if success:
        print("\n✨ Migration successful! Your database now supports organizations.")
    else:
        print("\n💥 Migration failed. Please check the errors above.")
        sys.exit(1)