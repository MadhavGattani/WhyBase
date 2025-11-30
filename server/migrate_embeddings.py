import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def migrate_embeddings():
    """
    Create embeddings table with pgvector support.
    Run this once to set up the RAG infrastructure.
    """
    engine = create_engine(os.getenv("DATABASE_URL"))
    
    with engine.connect() as conn:
        # Enable pgvector extension
        print("🔧 Enabling pgvector extension...")
        try:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            print("✅ pgvector extension enabled")
        except Exception as e:
            print(f"⚠️  Warning: Could not enable pgvector extension: {e}")
            print("   Make sure your PostgreSQL instance supports pgvector")
            print("   For Neon/Supabase, it should be available by default")
            return
        
        # Create embeddings table
        print("📦 Creating embeddings table...")
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                embedding vector(384),  -- all-MiniLM-L6-v2 produces 384-dimensional vectors
                source_type VARCHAR(50) NOT NULL,  -- 'issue', 'repository', 'pr'
                source_id INTEGER NOT NULL,
                source_metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.commit()
        print("✅ Embeddings table created")
        
        # Create vector similarity index for fast searches
        print("🔍 Creating vector similarity index...")
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS embeddings_vector_idx 
            ON embeddings 
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """))
        conn.commit()
        print("✅ Vector index created")
        
        # Create source lookup index
        print("🔍 Creating source index...")
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_embeddings_source 
            ON embeddings(source_type, source_id);
        """))
        conn.commit()
        print("✅ Source index created")
        
        # Check table status
        result = conn.execute(text("SELECT COUNT(*) FROM embeddings"))
        count = result.scalar()
        
        print(f"\n✅ Migration completed successfully!")
        print(f"📊 Current embeddings count: {count}")
        print(f"\nNext steps:")
        print(f"1. Install sentence-transformers: pip install sentence-transformers")
        print(f"2. Sync your GitHub data: python sync_embeddings.py <user_id>")

if __name__ == "__main__":
    migrate_embeddings()