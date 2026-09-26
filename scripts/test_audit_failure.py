import os
import sys
import pickle
import asyncio

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.config import settings
from app.models import PitchDeck, SlideContent
from app.retrieval import PolicyRetriever
from app.audit import audit_pitch_content
from app.ingestion import load_precomputed_embeddings

def main():
    print("==============================================")
    print("Testing Audit Layer with Fabricated Claim")
    print("==============================================")
    
    # 1. Load retriever
    embeddings_path = os.path.join(settings.data_dir, "policy_embeddings.pkl")
    chunks = load_precomputed_embeddings(embeddings_path)
    retriever = PolicyRetriever(chunks)
    print(f"Retriever loaded with {len(chunks)} chunks.")
    
    # 2. Create a fabricated pitch deck
    fabricated_claim = "This policy includes unlimited free annual dental implants."
    deck = PitchDeck(
        company_name="Fabricated Test Corp",
        slides=[
            SlideContent(
                slide_number=1,
                title="Amazing Coverage",
                bullet_points=[fabricated_claim],
                slide_type="content"
            )
        ],
        recommended_policy="Test Policy",
        recommendation_rationale="N/A"
    )
    
    print(f"\nDeliberately testing fabricated claim:\n\"{fabricated_claim}\"\n")
    
    # 3. Run audit
    report = audit_pitch_content(deck, retriever)
    
    # 4. Show results
    slide_audit = report.slide_audits[0]
    claim_audit = slide_audit.claims[0]
    
    print("--- AUDIT RESULT ---")
    print(f"Verdict: {claim_audit.verdict.value.upper()}")
    print(f"Confidence Score: {claim_audit.confidence_score:.4f}")
    print(f"Verification Method: {claim_audit.verification_method}")
    print(f"Notes/Rationale: {claim_audit.notes}")
    
if __name__ == "__main__":
    main()
