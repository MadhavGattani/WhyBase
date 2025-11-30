#!/usr/bin/env python3
"""
Migration script to add citations table for source tracking.
Run: python migrate_citations.py
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
    
    print("🚀 Starting Citations Migration...")
    
    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        session = Session()
        inspector = inspect(engine)
        
        existing_tables = inspector.get_table_names()
        
        if "citations" not in existing_tables:
            print("Creating citations table...")
            session.execute(text("""
                CREATE TABLE citations (
                    id SERIAL PRIMARY KEY,
                    query_id INTEGER NOT NULL REFERENCES queries(id) ON DELETE CASCADE,
                    source_type VARCHAR(50) NOT NULL,
                    source_title VARCHAR(512) NOT NULL,
                    source_url VARCHAR(1024) NOT NULL,
                    source_metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("✅ citations table created")
        else:
            print("ℹ️  citations table already exists")
        
        # Create indexes
        print("Creating indexes...")
        try:
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_citations_query ON citations(query_id)"))
            print("✅ Index created")
        except Exception as e:
            print(f"ℹ️  Index: {e}")
        
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
    print("Loominal Citations Migration")
    print("============================")
    success = run_migration()
    sys.exit(0 if success else 1)