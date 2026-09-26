"""Offline ingestion script — run once to precompute policy embeddings.

Usage (from project root, with venv activated):
    python scripts/ingest_policies.py

This processes all PDFs in the policy_docs/ directory and saves
embeddings to data/policy_embeddings.pkl.
"""

import os
import sys
import time

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.config import settings
from app.ingestion import ingest_all_policies


def main():
    print("=" * 60)
    print("Marsh Insurance Pitch Generator — Policy Ingestion")
    print("=" * 60)
    
    policy_dir = settings.policy_docs_dir
    output_path = os.path.join(settings.data_dir, "policy_embeddings.pkl")
    
    print(f"\nPolicy directory: {policy_dir}")
    print(f"Output path: {output_path}")
    
    # List available PDFs
    pdfs = [f for f in os.listdir(policy_dir) if f.lower().endswith(".pdf")]
    print(f"\nFound {len(pdfs)} PDF files:")
    for pdf in sorted(pdfs):
        size_mb = os.path.getsize(os.path.join(policy_dir, pdf)) / (1024 * 1024)
        print(f"  - {pdf} ({size_mb:.1f} MB)")
    
    if not pdfs:
        print("\n[ERROR] No PDF files found in policy_docs/. Please add policy documents first.")
        sys.exit(1)
    
    print(f"\nStarting ingestion...")
    start_time = time.time()
    
    stats = ingest_all_policies(policy_dir, output_path)
    
    elapsed = time.time() - start_time
    
    print(f"\n{'=' * 60}")
    print(f"[OK] Ingestion complete in {elapsed:.1f}s")
    print(f"\nResults:")
    total_chunks = 0
    for doc_name, num_chunks in stats.items():
        print(f"  - {doc_name}: {num_chunks} chunks")
        total_chunks += num_chunks
    
    print(f"\n  Total: {total_chunks} chunks")
    print(f"  Saved to: {output_path}")
    
    # Verify the file
    file_size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"  File size: {file_size:.1f} MB")
    print("=" * 60)


if __name__ == "__main__":
    main()
