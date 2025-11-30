import os
from sqlalchemy import create_engine, text
from typing import List, Dict, Tuple
from api.services.embedding_service import get_embedding_service
import json

def search_similar_embeddings(query: str, user_id: int, limit: int = 7, min_similarity: float = 0.3) -> List[Dict]:
    """
    Search for similar content using vector similarity (cosine distance).
    This is the core RAG retrieval function.
    
    Args:
        query: User's question
        user_id: User ID to scope the search
        limit: Maximum number of results to return
        min_similarity: Minimum similarity threshold (0-1)
    
    Returns:
        List of similar chunks with metadata and similarity scores
    """
    engine = create_engine(os.getenv("DATABASE_URL"))
    embedding_service = get_embedding_service()
    
    # Generate embedding for the query
    query_embedding = embedding_service.embed_text(query)
    embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
    
    with engine.connect() as conn:
        # Vector similarity search using cosine distance
        # <=> is the cosine distance operator in pgvector
        # Lower distance = higher similarity
        # We convert to similarity score: 1 - distance
        result = conn.execute(text("""
            SELECT 
                content,
                source_type,
                source_id,
                metadata,
                1 - (embedding <=> :query_embedding::vector) as similarity
            FROM embeddings
            WHERE metadata->>'user_id' = :user_id
            ORDER BY embedding <=> :query_embedding::vector
            LIMIT :limit
        """), {
            'query_embedding': embedding_str,
            'user_id': str(user_id),
            'limit': limit
        })
        
        results = []
        for row in result:
            similarity = float(row[4])
            
            # Skip if below threshold
            if similarity < min_similarity:
                continue
            
            # Parse metadata
            metadata_raw = row[3]
            if isinstance(metadata_raw, str):
                try:
                    metadata = json.loads(metadata_raw.replace("'", '"'))
                except:
                    metadata = {}
            else:
                metadata = metadata_raw or {}
            
            results.append({
                'content': row[0],
                'source_type': row[1],
                'source_id': row[2],
                'metadata': metadata,
                'similarity': similarity
            })
        
        return results

def get_all_context(query: str, user_id: int) -> Tuple[str, List[Dict], int]:
    """
    Get all relevant context for a query using RAG.
    This is the main function called by the query endpoint.
    
    Args:
        query: User's question
        user_id: User ID
    
    Returns:
        Tuple of (context_text, sources_list, total_sources)
        - context_text: Formatted context to inject into LLM prompt
        - sources_list: List of source citations for frontend display
        - total_sources: Number of unique sources found
    """
    # Search similar embeddings
    results = search_similar_embeddings(query, user_id, limit=7, min_similarity=0.3)
    
    if not results:
        return "", [], 0
    
    # Build context and sources
    context_parts = []
    sources = []
    seen_sources = set()
    
    for i, result in enumerate(results, 1):
        # Add to context with source reference
        content = result['content']
        context_parts.append(f"[Source {i}] {content}")
        
        # Build source citation (deduplicate by source_type + source_id)
        metadata = result['metadata']
        source_key = f"{result['source_type']}_{result['source_id']}"
        
        if source_key not in seen_sources:
            seen_sources.add(source_key)
            
            if result['source_type'] == 'issue':
                sources.append({
                    'type': 'issue',
                    'title': metadata.get('title', 'GitHub Issue'),
                    'url': metadata.get('url', ''),
                    'metadata': {
                        'repository': metadata.get('repository', ''),
                        'state': metadata.get('state', ''),
                        'similarity': round(result['similarity'], 2)
                    }
                })
            elif result['source_type'] == 'repository':
                sources.append({
                    'type': 'repository',
                    'title': metadata.get('name', 'GitHub Repository'),
                    'url': metadata.get('url', ''),
                    'metadata': {
                        'language': metadata.get('language', ''),
                        'stars': metadata.get('stars', 0),
                        'similarity': round(result['similarity'], 2)
                    }
                })
    
    context_text = "\n\n".join(context_parts)
    return context_text, sources, len(sources)

def build_contextualized_prompt(query: str, context: str, sources_count: int) -> str:
    """
    Build a prompt that includes retrieved context and instructs the LLM to cite sources.
    This is optimized for Groq/Claude/GPT models.
    
    Args:
        query: User's question
        context: Retrieved context from vector search
        sources_count: Number of sources found
    
    Returns:
        Formatted prompt for the LLM
    """
    return f"""You are an AI assistant with access to the user's GitHub data. Answer the following question using ONLY the provided context from their repositories and issues.

CONTEXT FROM GITHUB ({sources_count} sources):
{context}

QUESTION: {query}

INSTRUCTIONS:
1. Answer based ONLY on the provided context above
2. Always cite your sources using [Source 1], [Source 2], etc. when making claims
3. If the context doesn't contain enough information to fully answer the question, acknowledge this
4. Be concise but comprehensive
5. When referencing specific issues or repositories, include their names
6. If multiple sources say similar things, you can cite them all: [Source 1, 2, 3]

ANSWER:"""

def extract_sources_list(sources: List[Dict]) -> str:
    """
    Convert sources list to JSON string for database storage.
    
    Args:
        sources: List of source dictionaries
    
    Returns:
        JSON string
    """
    return json.dumps(sources)

# Legacy functions (for backward compatibility)
# These can be removed once you confirm RAG is working

def search_github_issues(query: str, user_id: int, limit: int = 5) -> List[Dict]:
    """
    DEPRECATED: Legacy keyword search for issues.
    Use search_similar_embeddings() instead for semantic search.
    """
    from api.db import Issue
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    keywords = query.lower().split()
    issues = session.query(Issue).filter_by(user_id=user_id).all()
    
    relevant_issues = []
    for issue in issues:
        title_lower = (issue.title or "").lower()
        body_lower = (issue.body or "")[:500].lower()
        
        match_count = sum(1 for kw in keywords if kw in title_lower or kw in body_lower)
        if match_count > 0:
            relevant_issues.append({
                'type': 'issue',
                'title': issue.title,
                'body': (issue.body or "")[:200],
                'url': issue.url,
                'repository': issue.repository_name,
                'state': issue.state,
                'relevance': match_count
            })
    
    relevant_issues.sort(key=lambda x: x['relevance'], reverse=True)
    session.close()
    
    return relevant_issues[:limit]

def search_github_repositories(query: str, user_id: int, limit: int = 3) -> List[Dict]:
    """
    DEPRECATED: Legacy keyword search for repositories.
    Use search_similar_embeddings() instead for semantic search.
    """
    from api.db import Repository
    from sqlalchemy.orm import sessionmaker
    
    engine = create_engine(os.getenv("DATABASE_URL"))
    Session = sessionmaker(bind=engine)
    session = Session()
    
    keywords = query.lower().split()
    repos = session.query(Repository).filter_by(user_id=user_id).all()
    
    relevant_repos = []
    for repo in repos:
        name_lower = (repo.name or "").lower()
        desc_lower = (repo.description or "").lower()
        
        match_count = sum(1 for kw in keywords if kw in name_lower or kw in desc_lower)
        if match_count > 0:
            relevant_repos.append({
                'type': 'repository',
                'name': repo.name,
                'description': repo.description,
                'url': repo.url,
                'language': repo.language,
                'stars': repo.stars,
                'relevance': match_count
            })
    
    relevant_repos.sort(key=lambda x: x['relevance'], reverse=True)
    session.close()
    
    return relevant_repos[:limit]