"""Retrieval layer: cosine similarity search over policy chunk vectors.

Uses plain NumPy — no FAISS needed for this dataset size.
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def cosine_similarity_batch(query_vec: np.ndarray, corpus_matrix: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between a query vector and a corpus matrix.
    
    Args:
        query_vec: Shape (d,)
        corpus_matrix: Shape (n, d)
    
    Returns:
        Array of shape (n,) with similarity scores.
    """
    query_norm = np.linalg.norm(query_vec)
    if query_norm == 0:
        return np.zeros(corpus_matrix.shape[0])
    
    corpus_norms = np.linalg.norm(corpus_matrix, axis=1)
    # Avoid division by zero
    corpus_norms = np.where(corpus_norms == 0, 1e-10, corpus_norms)
    
    similarities = np.dot(corpus_matrix, query_vec) / (corpus_norms * query_norm)
    return similarities


class PolicyRetriever:
    """Retrieves relevant policy chunks using cosine similarity search."""

    def __init__(self, chunks: List[Dict]):
        """Initialize with a list of chunk dicts (must have 'embedding' key).
        
        Args:
            chunks: List of chunk dictionaries from the ingestion pipeline.
        """
        self.chunks = chunks
        
        if chunks:
            self.embeddings_matrix = np.array([c["embedding"] for c in chunks], dtype=np.float32)
        else:
            self.embeddings_matrix = np.array([], dtype=np.float32).reshape(0, 0)
        
        logger.info(f"PolicyRetriever initialized with {len(chunks)} chunks")

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 8,
        threshold: float = 0.0,
        filter_documents: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Find the top-k most similar chunks to a query embedding.
        
        Args:
            query_embedding: The query vector.
            top_k: Number of results to return.
            threshold: Minimum similarity score to include.
            filter_documents: If provided, only search within these document names.
            
        Returns:
            List of chunk dicts with added 'similarity_score' key, sorted by relevance.
        """
        if len(self.chunks) == 0:
            return []
        
        query_vec = np.array(query_embedding, dtype=np.float32)
        
        # Apply document filter if specified
        if filter_documents:
            indices = [
                i for i, c in enumerate(self.chunks)
                if c["document_name"] in filter_documents
            ]
            if not indices:
                return []
            filtered_matrix = self.embeddings_matrix[indices]
            filtered_chunks = [self.chunks[i] for i in indices]
        else:
            filtered_matrix = self.embeddings_matrix
            filtered_chunks = self.chunks
        
        # Compute similarities
        similarities = cosine_similarity_batch(query_vec, filtered_matrix)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score >= threshold:
                chunk = dict(filtered_chunks[idx])
                chunk["similarity_score"] = score
                # Remove embedding from results (large, not needed downstream)
                chunk.pop("embedding", None)
                results.append(chunk)
        
        return results

    def search_text(
        self,
        query_text: str,
        top_k: int = 8,
        threshold: float = 0.0,
        filter_documents: Optional[List[str]] = None,
    ) -> List[Dict]:
        """Search using text (embeds the query first).
        
        Args:
            query_text: The search query.
            top_k: Number of results to return.
            threshold: Minimum similarity score.
            filter_documents: Optional list of document names to filter by.
            
        Returns:
            List of relevant chunks with similarity scores.
        """
        from app.ingestion import get_embedding_model
        
        model = get_embedding_model()
        query_embedding = list(model.embed([query_text]))[0]
        
        return self.search(
            query_embedding=query_embedding,
            top_k=top_k,
            threshold=threshold,
            filter_documents=filter_documents,
        )

    def get_document_names(self) -> List[str]:
        """Return the unique document names available in the index."""
        return list(set(c["document_name"] for c in self.chunks))
