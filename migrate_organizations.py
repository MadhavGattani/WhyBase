#!/usr/bin/env python3
"""
Robust PostgreSQL migration script for adding organization support to Loominal.
This version checks existing schema and adapts accordingly.

Usage:
    python migrate_organizations_robust.py

Make sure to:
1. Backup your database first
2. Set your DATABASE_URL environment variable
3. Have the required dependencies installed (psycopg2-binary)
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text, MetaData, Table, inspect
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_column_exists(inspector, table_name, column_name):
    """Check if a column exists in a table"""
    try:
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except:
        return False

def check_table_exists(inspector, table_name):
    """Check if a table exists"""
    return table_name in inspector.get_table_names()

def run_migration():
    """Run the organization migration for PostgreSQL"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("❌ ERROR: DATABASE_URL not found in environment variables")
        return False
    
    print("🚀 Starting Loominal Organization Migration (PostgreSQL - Robust)...")
    print(f"📊 Database: {DATABASE_URL}")
    
    try:
        # Connect to database
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        inspector = inspect(engine)
        
        print("✅ Connected to database")
        
        # Check existing schema
        print("\n🔍 Analyzing existing database schema...")
        
        existing_tables = inspector.get_table_names()
        print(f"📋 Found tables: {', '.join(existing_tables)}")
        
        # Check if migration is needed
        if 'organizations' in existing_tables:
            print("ℹ️  Organizations table already exists. Migration may have been run before.")
            response = input("Do you want to continue anyway? (y/N): ")
            if response.lower() not in ['y', 'yes']:
                print("Migration cancelled.")
                return False
        
        print("\n🔧 Creating organization tables...")
        
        # Create organizations table (PostgreSQL syntax)
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS organizations (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                slug VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                logo_url VARCHAR(512),
                website VARCHAR(255),
                is_personal BOOLEAN DEFAULT FALSE,
                is_active BOOLEAN DEFAULT TRUE,
                max_members INTEGER DEFAULT 50,
                plan_type VARCHAR(50) DEFAULT 'free',
                billing_email VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                owner_id INTEGER NOT NULL
            )
        """))
        
        # Create user-organization memberships table (PostgreSQL syntax)
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS user_organization_memberships (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                organization_id INTEGER NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                UNIQUE(user_id, organization_id)
            )
        """))
        
        # Create organization invitations table (PostgreSQL syntax)
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS organization_invitations (
                id SERIAL PRIMARY KEY,
                organization_id INTEGER NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'member',
                email VARCHAR(255) NOT NULL,
                invited_user_id INTEGER,
                token VARCHAR(255) UNIQUE NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                invited_by_id INTEGER NOT NULL,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                responded_at TIMESTAMP
            )
        """))
        
        print("✅ Organization tables created")
        
        print("\n🔧 Adding organization support to existing tables...")
        
        # Check and add columns to users table
        if check_table_exists(inspector, 'users'):
            print("📋 Users table found, checking columns...")
            
            users_columns = [
                ("avatar_url", "VARCHAR(512)"),
                ("last_active_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
                ("is_active", "BOOLEAN DEFAULT TRUE"),
                ("personal_organization_id", "INTEGER")
            ]
            
            for column, definition in users_columns:
                if not check_column_exists(inspector, 'users', column):
                    try:
                        session.execute(text(f"ALTER TABLE users ADD COLUMN {column} {definition}"))
                        print(f"✅ Added {column} to users")
                    except Exception as e:
                        print(f"⚠️  Could not add {column} to users: {e}")
                else:
                    print(f"ℹ️  {column} column already exists in users")
        else:
            print("⚠️  Users table not found, creating basic structure...")
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    provider_id VARCHAR(255) UNIQUE,
                    email VARCHAR(255) UNIQUE,
                    display_name VARCHAR(255),
                    avatar_url VARCHAR(512),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    personal_organization_id INTEGER
                )
            """))
            print("✅ Created users table")
        
        # Check and update other tables
        tables_columns = [
            ("queries", [
                ("user_id", "INTEGER"),
                ("organization_id", "INTEGER"),
                ("prompt", "TEXT"),
                ("response", "TEXT"),
                ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            ]),
            ("templates", [
                ("user_id", "INTEGER"),
                ("name", "VARCHAR(255)"),
                ("prompt", "TEXT"),
                ("description", "TEXT"),
                ("is_public", "BOOLEAN DEFAULT FALSE"),
                ("is_organization_template", "BOOLEAN DEFAULT FALSE"),
                ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
                ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
                ("organization_id", "INTEGER")
            ]),
            ("uploaded_files", [
                ("user_id", "INTEGER"),
                ("filename", "VARCHAR(512)"),
                ("stored_path", "VARCHAR(1024)"),
                ("content_type", "VARCHAR(255)"),
                ("size", "INTEGER"),
                ("is_public", "BOOLEAN DEFAULT FALSE"),
                ("is_organization_file", "BOOLEAN DEFAULT FALSE"),
                ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
                ("organization_id", "INTEGER")
            ])
        ]
        
        for table_name, columns in tables_columns:
            if check_table_exists(inspector, table_name):
                print(f"📋 {table_name} table found, checking columns...")
                for column, definition in columns:
                    if not check_column_exists(inspector, table_name, column):
                        try:
                            session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column} {definition}"))
                            print(f"✅ Added {column} to {table_name}")
                        except Exception as e:
                            print(f"⚠️  Could not add {column} to {table_name}: {e}")
                    else:
                        print(f"ℹ️  {column} column already exists in {table_name}")
            else:
                print(f"⚠️  {table_name} table not found, creating basic structure...")
                
                if table_name == "queries":
                    session.execute(text("""
                        CREATE TABLE IF NOT EXISTS queries (
                            id SERIAL PRIMARY KEY,
                            prompt TEXT NOT NULL,
                            response TEXT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            user_id INTEGER,
                            organization_id INTEGER
                        )
                    """))
                elif table_name == "templates":
                    session.execute(text("""
                        CREATE TABLE IF NOT EXISTS templates (
                            id SERIAL PRIMARY KEY,
                            name VARCHAR(255) NOT NULL,
                            prompt TEXT NOT NULL,
                            description TEXT,
                            is_public BOOLEAN DEFAULT FALSE,
                            is_organization_template BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            user_id INTEGER,
                            organization_id INTEGER
                        )
                    """))
                elif table_name == "uploaded_files":
                    session.execute(text("""
                        CREATE TABLE IF NOT EXISTS uploaded_files (
                            id SERIAL PRIMARY KEY,
                            filename VARCHAR(512) NOT NULL,
                            stored_path VARCHAR(1024) NOT NULL,
                            content_type VARCHAR(255),
                            size INTEGER,
                            is_public BOOLEAN DEFAULT FALSE,
                            is_organization_file BOOLEAN DEFAULT FALSE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            user_id INTEGER,
                            organization_id INTEGER
                        )
                    """))
                print(f"✅ Created {table_name} table")
        
        # Refresh inspector after schema changes
        inspector = inspect(engine)
        
        print("\n👥 Creating personal organizations for existing users...")
        
        # Get all existing users
        try:
            users = session.execute(text("SELECT id, email, display_name FROM users")).fetchall()
            
            if not users:
                print("ℹ️  No existing users found.")
            else:
                for user in users:
                    user_id, email, display_name = user
                    
                    # Check if user already has a personal organization
                    existing_personal = session.execute(text(
                        "SELECT id FROM organizations WHERE owner_id = :user_id AND is_personal = TRUE"
                    ), {"user_id": user_id}).fetchone()
                    
                    if not existing_personal:
                        # Generate unique slug
                        base_slug = f"personal-{email.split('@')[0]}" if email else f"user-{user_id}"
                        slug = base_slug
                        counter = 1
                        
                        while session.execute(text("SELECT id FROM organizations WHERE slug = :slug"), {"slug": slug}).fetchone():
                            slug = f"{base_slug}-{counter}"
                            counter += 1
                        
                        # Create personal organization
                        org_name = f"{display_name or email or 'User'}'s Workspace"
                        result = session.execute(text("""
                            INSERT INTO organizations (name, slug, description, is_personal, owner_id, max_members)
                            VALUES (:name, :slug, :description, TRUE, :user_id, 1)
                            RETURNING id
                        """), {
                            "name": org_name,
                            "slug": slug,
                            "description": "Personal workspace",
                            "user_id": user_id
                        })
                        
                        # Get the created organization ID
                        org_id = result.fetchone()[0]
                        
                        # Update user's personal_organization_id
                        session.execute(text(
                            "UPDATE users SET personal_organization_id = :org_id WHERE id = :user_id"
                        ), {"org_id": org_id, "user_id": user_id})
                        
                        # Add user as owner member of their personal organization
                        session.execute(text("""
                            INSERT INTO user_organization_memberships (user_id, organization_id, role)
                            VALUES (:user_id, :org_id, 'owner')
                        """), {"user_id": user_id, "org_id": org_id})
                        
                        print(f"✅ Created personal organization for user {user_id} ({email})")
                    else:
                        print(f"ℹ️  User {user_id} already has a personal organization")
        except Exception as e:
            print(f"⚠️  Could not process users: {e}")
        
        print("\n📦 Migrating existing content to personal organizations...")
        
        # Migrate queries to personal organizations (only if columns exist)
        if (check_table_exists(inspector, 'queries') and 
            check_column_exists(inspector, 'queries', 'user_id') and 
            check_column_exists(inspector, 'queries', 'organization_id')):
            try:
                result = session.execute(text("""
                    UPDATE queries 
                    SET organization_id = (
                        SELECT personal_organization_id 
                        FROM users 
                        WHERE users.id = queries.user_id
                    )
                    WHERE user_id IS NOT NULL AND organization_id IS NULL
                """))
                print(f"✅ Migrated {result.rowcount} queries to personal organizations")
            except Exception as e:
                print(f"⚠️  Could not migrate queries: {e}")
        else:
            print("ℹ️  Skipping query migration (columns not ready)")
        
        # Migrate templates to personal organizations (only if columns exist)
        if (check_table_exists(inspector, 'templates') and 
            check_column_exists(inspector, 'templates', 'user_id') and 
            check_column_exists(inspector, 'templates', 'organization_id')):
            try:
                result = session.execute(text("""
                    UPDATE templates 
                    SET organization_id = (
                        SELECT personal_organization_id 
                        FROM users 
                        WHERE users.id = templates.user_id
                    )
                    WHERE user_id IS NOT NULL AND organization_id IS NULL
                """))
                print(f"✅ Migrated {result.rowcount} templates to personal organizations")
            except Exception as e:
                print(f"⚠️  Could not migrate templates: {e}")
        else:
            print("ℹ️  Skipping template migration (columns not ready)")
        
        # Migrate uploaded files to personal organizations (only if columns exist)
        if (check_table_exists(inspector, 'uploaded_files') and 
            check_column_exists(inspector, 'uploaded_files', 'user_id') and 
            check_column_exists(inspector, 'uploaded_files', 'organization_id')):
            try:
                result = session.execute(text("""
                    UPDATE uploaded_files 
                    SET organization_id = (
                        SELECT personal_organization_id 
                        FROM users 
                        WHERE users.id = uploaded_files.user_id
                    )
                    WHERE user_id IS NOT NULL AND organization_id IS NULL
                """))
                print(f"✅ Migrated {result.rowcount} uploaded files to personal organizations")
            except Exception as e:
                print(f"⚠️  Could not migrate uploaded files: {e}")
        else:
            print("ℹ️  Skipping uploaded files migration (columns not ready)")
        
        # Commit all changes
        session.commit()
        session.close()
        
        print("\n🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Replace your server/api/ files with the new organization-enabled versions")
        print("2. Restart your Flask application")
        print("3. Test the organization features in your frontend")
        print("4. Check that existing data is properly associated with personal organizations")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure your database is accessible")
        print("2. Make sure no other applications are using the database")
        print("3. Check that DATABASE_URL is correct")
        print("4. Verify you have backup of your data")
        print("5. Install PostgreSQL driver: pip install psycopg2-binary")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False


if __name__ == "__main__":
    print("Loominal Organization Migration Tool (PostgreSQL - Robust)")
    print("==========================================================")
    
    # Safety check
    print("\n⚠️  IMPORTANT: This will modify your database structure.")
    print("Please ensure you have backed up your database before proceeding.")
    response = input("\nHave you backed up your data? (y/N): ")
    
    if response.lower() not in ['y', 'yes']:
        print("❌ Please backup your database before running this migration.")
        print("You can backup PostgreSQL with: pg_dump your_database > backup.sql")
        sys.exit(1)
    
    success = run_migration()
    if success:
        print("\n✨ Migration successful! Your database now supports organizations.")
        print("🚀 You can now use the organization features in your Loominal app.")
    else:
        print("\n💥 Migration failed. Please check the errors above and try again.")
        sys.exit(1)