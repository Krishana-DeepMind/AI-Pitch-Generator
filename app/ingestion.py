"""PDF ingestion pipeline: parsing → chunking → embedding → storage.

This module is the single code path for both:
- Initial offline ingestion of the 4 provided policy documents
- Runtime uploads of new policy documents via /admin/add-policy

It dynamically discovers policy documents — nothing is hardcoded.
"""

import os
import pickle
import logging
import json
from typing import List, Dict, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

# Lazy-loaded embedding model
_embedding_model = None


def get_embedding_model():
    """Lazy-load the fastembed model (heavy on first call)."""
    global _embedding_model
    if _embedding_model is None:
        from fastembed import TextEmbedding
        from app.config import settings
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        _embedding_model = TextEmbedding(model_name=settings.embedding_model)
        logger.info("Embedding model loaded successfully.")
    return _embedding_model


def extract_text_from_pdf(pdf_path: str) -> List[Dict[str, any]]:
    """Extract text from a PDF file, page by page.
    
    Returns:
        List of dicts with 'page_number' and 'text' keys.
    """
    import pymupdf
    
    pages = []
    doc = pymupdf.open(pdf_path)
    for page_num, page in enumerate(doc):
        text = page.get_text().strip()
        if text:
            pages.append({
                "page_number": page_num + 1,
                "text": text,
            })
    doc.close()
    return pages


def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
    page_number: Optional[int] = None,
    document_name: str = "",
) -> List[Dict[str, any]]:
    """Split text into overlapping chunks for embedding.
    
    Uses a simple character-based sliding window approach with
    sentence-boundary awareness for cleaner chunk boundaries.
    """
    if not text or len(text.strip()) < 20:
        return []
    
    chunks = []
    text = text.strip()
    
    # Split into sentences first for cleaner boundaries
    sentences = []
    current = ""
    for char in text:
        current += char
        if char in ".!?\n" and len(current.strip()) > 10:
            sentences.append(current.strip())
            current = ""
    if current.strip():
        sentences.append(current.strip())
    
    # Build chunks from sentences
    current_chunk = ""
    chunk_idx = 0
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += " " + sentence if current_chunk else sentence
        else:
            if current_chunk:
                chunks.append({
                    "text": current_chunk.strip(),
                    "document_name": document_name,
                    "chunk_index": chunk_idx,
                    "page_number": page_number,
                })
                chunk_idx += 1
                
                # Keep overlap from end of current chunk
                overlap_text = current_chunk[-chunk_overlap:] if len(current_chunk) > chunk_overlap else ""
                current_chunk = overlap_text + " " + sentence
            else:
                # Single sentence bigger than chunk_size — take it as-is
                chunks.append({
                    "text": sentence.strip(),
                    "document_name": document_name,
                    "chunk_index": chunk_idx,
                    "page_number": page_number,
                })
                chunk_idx += 1
                current_chunk = ""
    
    if current_chunk.strip():
        chunks.append({
            "text": current_chunk.strip(),
            "document_name": document_name,
            "chunk_index": chunk_idx,
            "page_number": page_number,
        })
    
    return chunks


def embed_chunks(chunks: List[Dict]) -> List[Dict]:
    """Compute embeddings for a list of text chunks.
    
    Uses fastembed (ONNX) — runs locally, no API call needed.
    """
    model = get_embedding_model()
    texts = [c["text"] for c in chunks]
    
    embeddings = list(model.embed(texts))
    
    for i, chunk in enumerate(chunks):
        chunk["embedding"] = embeddings[i].tolist()
    
    return chunks


def ingest_pdf(pdf_path: str) -> List[Dict]:
    """Full ingestion pipeline for a single PDF.
    
    Steps: extract text → chunk → embed.
    Returns list of chunk dicts with embeddings.
    """
    from app.config import settings
    
    document_name = os.path.splitext(os.path.basename(pdf_path))[0]
    logger.info(f"Ingesting PDF: {document_name}")
    
    # Step 1: Extract text
    pages = extract_text_from_pdf(pdf_path)
    logger.info(f"  Extracted {len(pages)} pages")
    
    # Step 2: Chunk
    all_chunks = []
    for page in pages:
        page_chunks = chunk_text(
            text=page["text"],
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            page_number=page["page_number"],
            document_name=document_name,
        )
        all_chunks.extend(page_chunks)
    
    logger.info(f"  Created {len(all_chunks)} chunks")
    
    # Step 3: Embed
    all_chunks = embed_chunks(all_chunks)
    logger.info(f"  Computed embeddings for {len(all_chunks)} chunks")
    
    return all_chunks


def ingest_all_policies(policy_dir: str, output_path: str) -> Dict[str, int]:
    """Ingest all PDF files in a directory and save embeddings to pickle.
    
    This is the offline preprocessing step — run once at build time.
    Returns a dict of {document_name: num_chunks}.
    """
    all_chunks = []
    stats = {}
    
    pdf_files = [f for f in os.listdir(policy_dir) if f.lower().endswith(".pdf")]
    
    if not pdf_files:
        logger.warning(f"No PDF files found in {policy_dir}")
        return stats
    
    for pdf_file in sorted(pdf_files):
        pdf_path = os.path.join(policy_dir, pdf_file)
        chunks = ingest_pdf(pdf_path)
        all_chunks.extend(chunks)
        stats[os.path.splitext(pdf_file)[0]] = len(chunks)
    
    # Save to pickle
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        pickle.dump(all_chunks, f)
    
    logger.info(f"Saved {len(all_chunks)} total chunks to {output_path}")
    return stats


def load_precomputed_embeddings(data_path: str) -> List[Dict]:
    """Load precomputed embeddings from pickle file."""
    if not os.path.exists(data_path):
        logger.warning(f"No precomputed embeddings found at {data_path}")
        return []
    
    with open(data_path, "rb") as f:
        chunks = pickle.load(f)
    
    logger.info(f"Loaded {len(chunks)} precomputed chunks from {data_path}")
    return chunks


def get_available_policies(data_path: str) -> List[Dict[str, any]]:
    """List all available policy documents from precomputed data.
    
    Dynamically reads from the data — never hardcoded.
    """
    chunks = load_precomputed_embeddings(data_path)
    
    policy_map = {}
    for chunk in chunks:
        doc_name = chunk["document_name"]
        if doc_name not in policy_map:
            policy_map[doc_name] = {"name": doc_name, "num_chunks": 0, "source": "precomputed"}
        policy_map[doc_name]["num_chunks"] += 1
    
    return list(policy_map.values())
