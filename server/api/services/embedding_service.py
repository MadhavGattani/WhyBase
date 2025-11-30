from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict
import re

class EmbeddingService:
    """
    Local embedding service using Sentence Transformers (free, no API costs).
    Uses all-MiniLM-L6-v2 model which produces 384-dimensional embeddings.
    """
    
    def __init__(self):
        # Load the model once (will download ~80MB on first run)
        print("📥 Loading embedding model (all-MiniLM-L6-v2)...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Embedding model loaded!")
    
    def chunk_text(self, text: str, max_length: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into chunks with overlap for better context preservation.
        
        Args:
            text: Text to chunk
            max_length: Maximum characters per chunk
            overlap: Characters to overlap between chunks
        
        Returns:
            List of text chunks
        """
        if not text or len(text) <= max_length:
            return [text] if text else []
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + max_length
            
            # Try to break at sentence boundary for better coherence
            if end < len(text):
                chunk_text = text[start:end]
                
                # Look for sentence endings near the boundary
                last_period = chunk_text.rfind('. ')
                last_newline = chunk_text.rfind('\n')
                break_point = max(last_period, last_newline)
                
                # Only break at sentence if it's not too far back
                if break_point > max_length * 0.5:  # At least 50% of chunk
                    end = start + break_point + 1
            
            chunk = text[start:end].strip()
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)
            
            start = end - overlap
        
        return chunks
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
        
        Returns:
            384-dimensional embedding vector
        """
        if not text:
            # Return zero vector for empty text
            return [0.0] * 384
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str], show_progress: bool = True) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (faster than one-by-one).
        
        Args:
            texts: List of texts to embed
            show_progress: Show progress bar
        
        Returns:
            List of 384-dimensional embedding vectors
        """
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [t if t else " " for t in texts]
        
        embeddings = self.model.encode(
            valid_texts, 
            convert_to_numpy=True, 
            show_progress_bar=show_progress
        )
        return embeddings.tolist()
    
    def prepare_issue_for_embedding(self, issue: Dict) -> List[Dict]:
        """
        Prepare a GitHub issue for embedding by chunking and adding metadata.
        
        Args:
            issue: Issue dictionary with id, title, body, etc.
        
        Returns:
            List of chunks ready to embed with metadata
        """
        # Combine title and body for better context
        title = issue.get('title', '')
        body = issue.get('body', '') or ''
        
        full_text = f"{title}\n\n{body}".strip()
        
        if not full_text:
            return []
        
        # Chunk the text
        chunks = self.chunk_text(full_text, max_length=500)
        
        results = []
        for i, chunk in enumerate(chunks):
            results.append({
                'content': chunk,
                'source_type': 'issue',
                'source_id': issue['id'],
                'metadata': {
                    'title': issue.get('title', ''),
                    'repository': issue.get('repository_name', ''),
                    'state': issue.get('state', ''),
                    'url': issue.get('url', ''),
                    'chunk_index': i,
                    'total_chunks': len(chunks)
                }
            })
        
        return results
    
    def prepare_repository_for_embedding(self, repo: Dict) -> Dict:
        """
        Prepare a GitHub repository for embedding.
        Repositories are usually short, so no chunking needed.
        
        Args:
            repo: Repository dictionary with id, name, description, etc.
        
        Returns:
            Single item ready to embed with metadata
        """
        # Combine name and description
        name = repo.get('name', '')
        description = repo.get('description', '') or ''
        
        text = f"{name}\n{description}".strip()
        
        if not text:
            text = name  # At least use the name
        
        return {
            'content': text,
            'source_type': 'repository',
            'source_id': repo['id'],
            'metadata': {
                'name': repo.get('name', ''),
                'language': repo.get('language', ''),
                'stars': repo.get('stars', 0),
                'url': repo.get('url', '')
            }
        }

# Global singleton instance
_embedding_service = None

def get_embedding_service() -> EmbeddingService:
    """
    Get or create the global embedding service instance.
    Using singleton pattern to avoid loading the model multiple times.
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service