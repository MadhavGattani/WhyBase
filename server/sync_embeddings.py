import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from api.db import Issue, Repository
from api.services.embedding_service import get_embedding_service
import json

load_dotenv()

def sync_embeddings(user_id: int):
    """
    Sync embeddings for a user's GitHub data.
    This will:
    1. Load all GitHub issues and repositories for the user
    2. Chunk long content into smaller pieces
    3. Generate embeddings for each chunk
    4. Store in the embeddings table
    
    Args:
        user_id: The user ID to sync data for
    """
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    embedding_service = get_embedding_service()
    
    print(f"\n🔄 Syncing embeddings for user {user_id}...")
    print("=" * 60)
    
    # Get all issues for this user
    issues = session.query(Issue).filter_by(user_id=user_id).all()
    print(f"📋 Found {len(issues)} issues")
    
    # Get all repositories
    repos = session.query(Repository).filter_by(user_id=user_id).all()
    print(f"📁 Found {len(repos)} repositories")
    
    if not issues and not repos:
        print("\n⚠️  No GitHub data found for this user!")
        print("   Make sure you've synced your GitHub integration first.")
        session.close()
        return
    
    # Clear existing embeddings for this user
    print(f"\n🗑️  Clearing old embeddings...")
    with engine.connect() as conn:
        result = conn.execute(
            text("DELETE FROM embeddings WHERE metadata->>'user_id' = :uid"), 
            {"uid": str(user_id)}
        )
        conn.commit()
        print(f"   Deleted {result.rowcount} old embeddings")
    
    # Process issues (with chunking)
    print(f"\n📝 Processing issues...")
    all_chunks = []
    for i, issue in enumerate(issues, 1):
        issue_dict = {
            'id': issue.id,
            'title': issue.title,
            'body': issue.body,
            'repository_name': issue.repository_name,
            'state': issue.state,
            'url': issue.url
        }
        chunks = embedding_service.prepare_issue_for_embedding(issue_dict)
        
        # Add user_id to metadata
        for chunk in chunks:
            chunk['metadata']['user_id'] = user_id
        
        all_chunks.extend(chunks)
        
        if i % 10 == 0:
            print(f"   Processed {i}/{len(issues)} issues...")
    
    print(f"   ✅ Created {len(all_chunks)} chunks from {len(issues)} issues")
    
    # Process repositories
    print(f"\n📁 Processing repositories...")
    repo_items = []
    for repo in repos:
        repo_dict = {
            'id': repo.id,
            'name': repo.name,
            'description': repo.description,
            'language': repo.language,
            'stars': repo.stars,
            'url': repo.url
        }
        item = embedding_service.prepare_repository_for_embedding(repo_dict)
        item['metadata']['user_id'] = user_id
        repo_items.append(item)
    
    print(f"   ✅ Prepared {len(repo_items)} repositories")
    
    # Combine all items
    all_items = all_chunks + repo_items
    total_items = len(all_items)
    
    if total_items == 0:
        print("\n⚠️  No content to embed!")
        session.close()
        return
    
    print(f"\n🧠 Generating embeddings for {total_items} items...")
    print(f"   This may take a minute...")
    
    # Generate embeddings in batch (much faster than one-by-one)
    texts = [item['content'] for item in all_items]
    embeddings = embedding_service.embed_batch(texts, show_progress=True)
    
    # Insert into database
    print(f"\n💾 Saving to database...")
    with engine.connect() as conn:
        for i, (item, embedding) in enumerate(zip(all_items, embeddings), 1):
            # Convert embedding list to pgvector format
            embedding_str = '[' + ','.join(map(str, embedding)) + ']'
            
            # Convert metadata to proper JSON string
            metadata_json = json.dumps(item['metadata'])
            
            conn.execute(text("""
                INSERT INTO embeddings (content, embedding, source_type, source_id, metadata)
                VALUES (:content, :embedding::vector, :source_type, :source_id, :metadata::jsonb)
            """), {
                'content': item['content'],
                'embedding': embedding_str,
                'source_type': item['source_type'],
                'source_id': item['source_id'],
                'metadata': metadata_json
            })
            
            if i % 50 == 0:
                print(f"   Saved {i}/{total_items} embeddings...")
        
        conn.commit()
    
    print(f"\n✅ Successfully synced {total_items} embeddings!")
    print(f"   - {len(all_chunks)} issue chunks")
    print(f"   - {len(repo_items)} repositories")
    print(f"\n🎉 RAG is now active! Your queries will use semantic search.")
    
    session.close()

def show_stats():
    """Show current embedding statistics."""
    engine = create_engine(os.getenv("DATABASE_URL"))
    
    with engine.connect() as conn:
        # Total embeddings
        total = conn.execute(text("SELECT COUNT(*) FROM embeddings")).scalar()
        
        # By source type
        by_type = conn.execute(text("""
            SELECT source_type, COUNT(*) as count
            FROM embeddings
            GROUP BY source_type
            ORDER BY count DESC
        """))
        
        print("\n📊 Current Embedding Statistics")
        print("=" * 60)
        print(f"Total embeddings: {total}")
        print("\nBy source type:")
        for row in by_type:
            print(f"  - {row[0]}: {row[1]}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n❌ Error: Missing user_id")
        print("\nUsage:")
        print("  python sync_embeddings.py <user_id>      # Sync embeddings")
        print("  python sync_embeddings.py --stats         # Show statistics")
        print("\nExample:")
        print("  python sync_embeddings.py 1")
        sys.exit(1)
    
    if sys.argv[1] == "--stats":
        show_stats()
    else:
        try:
            user_id = int(sys.argv[1])
            sync_embeddings(user_id)
        except ValueError:
            print(f"\n❌ Error: '{sys.argv[1]}' is not a valid user_id")
            print("   user_id must be an integer")
            sys.exit(1)