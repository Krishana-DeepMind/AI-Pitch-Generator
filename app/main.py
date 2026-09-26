"""Marsh AI-Powered Insurance Pitch Generator — FastAPI Application.

Serves both the API endpoints and the static frontend from a single service.
Designed for deployment on Render's free tier.
"""

import os
import json
import logging
import pickle
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import (
    PitchRequest, PitchResponse, PolicyInfo, ErrorResponse,
    CompanyProfile, AuditReport,
)
from app.ingestion import (
    load_precomputed_embeddings, ingest_pdf, get_available_policies,
)
from app.retrieval import PolicyRetriever
from app.profile import generate_company_profile
from app.pitch import generate_marketing_pitch
from app.audit import audit_pitch_content
from app.deck import generate_deck

# ── Logging Setup ───────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── FastAPI App ─────────────────────────────────────────────────
app = FastAPI(
    title="Marsh Insurance Pitch Generator",
    description="AI-powered, policy-grounded marketing pitch deck generator for Marsh advisors.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global State ────────────────────────────────────────────────
# Loaded once at startup, refreshed when new policies are added
_policy_chunks: List[dict] = []
_retriever: Optional[PolicyRetriever] = None


def _get_embeddings_path() -> str:
    return os.path.join(settings.data_dir, "policy_embeddings.pkl")


def _load_retriever():
    """Load or reload the policy retriever from precomputed embeddings."""
    global _policy_chunks, _retriever
    _policy_chunks = load_precomputed_embeddings(_get_embeddings_path())
    _retriever = PolicyRetriever(_policy_chunks) if _policy_chunks else None
    logger.info(f"Retriever loaded with {len(_policy_chunks)} chunks")


@app.on_event("startup")
async def startup():
    """Load precomputed embeddings on startup."""
    _load_retriever()
    logger.info("Marsh Pitch Generator started successfully.")


# ── API Endpoints ───────────────────────────────────────────────

@app.post("/generate-pitch", response_model=PitchResponse)
async def generate_pitch(request: PitchRequest):
    """Full pipeline: profile → retrieval → generation → audit → deck.
    
    Takes a company name and runs the entire pitch generation and audit pipeline.
    Returns the deck download link and audit report.
    """
    # Validation: company name
    if not request.company_name or not request.company_name.strip():
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Missing company name",
                "detail": "Please enter a company name to generate a pitch.",
                "error_type": "validation",
            }
        )
    
    # Validation: policies available
    if _retriever is None or len(_policy_chunks) == 0:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "No policy documents available",
                "detail": "No policy documents have been ingested. Please upload policy documents first or run the ingestion pipeline.",
                "error_type": "no_policies",
            }
        )
    
    company_name = request.company_name.strip()
    
    try:
        # Step 1: Generate company risk profile
        logger.info(f"[Pipeline] Step 1: Generating profile for '{company_name}'")
        profile = generate_company_profile(company_name)
        
        # Step 2: Retrieve relevant policy chunks
        logger.info(f"[Pipeline] Step 2: Retrieving relevant policy chunks")
        query_text = (
            f"{profile.industry} {profile.risk_summary} "
            f"{' '.join(profile.key_risks)} "
            f"medical health insurance coverage benefits"
        )
        
        # Filter by selected policies if specified
        filter_docs = None
        if request.selected_policies:
            filter_docs = request.selected_policies
        
        # Two-stage retrieval: fetch top-20 candidate pool
        candidate_chunks = _retriever.search_text(
            query_text=query_text,
            top_k=20,
            threshold=0.0,
            filter_documents=filter_docs,
        )
        
        # Dedupe: filter out highly overlapping adjacent chunks
        relevant_chunks = []
        selected_indices = set()
        for chunk in candidate_chunks:
            doc = chunk.get("document_name")
            idx = chunk.get("chunk_index")
            # Skip if immediate neighbor chunk is already selected to maximize diversity
            if (doc, idx - 1) in selected_indices or (doc, idx + 1) in selected_indices:
                continue
            relevant_chunks.append(chunk)
            selected_indices.add((doc, idx))
            if len(relevant_chunks) >= settings.top_k_chunks:
                break
                
        # Fallback if filtered too aggressively
        if len(relevant_chunks) < settings.top_k_chunks:
            for chunk in candidate_chunks:
                if chunk not in relevant_chunks:
                    relevant_chunks.append(chunk)
                if len(relevant_chunks) >= settings.top_k_chunks:
                    break
                    
        logger.info(f"  Retrieved {len(relevant_chunks)} relevant chunks after deduping from {len(candidate_chunks)} candidates")
        
        # Step 3: Generate marketing pitch
        logger.info(f"[Pipeline] Step 3: Generating marketing pitch")
        pitch = generate_marketing_pitch(profile, relevant_chunks)
        
        # Step 4: Audit pitch content
        logger.info(f"[Pipeline] Step 4: Auditing pitch claims")
        audit_report = audit_pitch_content(pitch, _retriever)
        
        # Save audit report to disk
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_company_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '_')).rstrip()
        audit_filename = f"Audit_Report_{safe_company_name}_{timestamp}.json"
        audit_filepath = os.path.join(settings.audit_reports_dir, audit_filename)
        with open(audit_filepath, "w", encoding="utf-8") as f:
            f.write(audit_report.model_dump_json(indent=2))
        logger.info(f"Audit report saved to {audit_filepath}")
        
        # Step 5: Generate PPTX deck
        logger.info(f"[Pipeline] Step 5: Generating PPTX deck")
        deck_filename = generate_deck(pitch, settings.generated_decks_dir)
        
        # Build response
        return PitchResponse(
            company_name=company_name,
            profile=profile,
            deck_filename=deck_filename,
            deck_download_url=f"/download/{deck_filename}",
            slides_preview=pitch.slides,
            audit_report=audit_report,
            recommended_policy=pitch.recommended_policy,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pipeline failed for '{company_name}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Generation failed",
                "detail": f"An error occurred while generating the pitch: {str(e)}",
                "error_type": "generation_failure",
            }
        )


@app.get("/policies", response_model=List[PolicyInfo])
async def list_policies():
    """List all currently available policy documents.
    
    Reads dynamically from the data — never hardcoded.
    """
    policies = get_available_policies(_get_embeddings_path())
    return [
        PolicyInfo(
            name=p["name"],
            filename=p["name"] + ".pdf",
            num_chunks=p["num_chunks"],
            source=p["source"],
        )
        for p in policies
    ]


@app.post("/admin/add-policy")
async def add_policy(file: UploadFile = File(...)):
    """Upload and ingest a new policy PDF.
    
    Chunks it, embeds it via fastembed, and adds to the vector store.
    Uses the same ingestion pipeline as the initial offline setup.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid file",
                "detail": "Please upload a PDF file.",
                "error_type": "validation",
            }
        )
    
    try:
        # Save uploaded file temporarily
        temp_path = os.path.join(settings.policy_docs_dir, file.filename)
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Ingest using the same pipeline
        new_chunks = ingest_pdf(temp_path)
        
        # Add to existing embeddings
        existing = load_precomputed_embeddings(_get_embeddings_path())
        existing.extend(new_chunks)
        
        # Save updated embeddings
        with open(_get_embeddings_path(), "wb") as f:
            pickle.dump(existing, f)
        
        # Reload retriever
        _load_retriever()
        
        return {
            "status": "success",
            "message": f"Successfully ingested '{file.filename}' — {len(new_chunks)} chunks added.",
            "document_name": os.path.splitext(file.filename)[0],
            "num_chunks": len(new_chunks),
            "total_chunks": len(existing),
        }
        
    except Exception as e:
        logger.error(f"Failed to ingest policy '{file.filename}': {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Ingestion failed",
                "detail": f"Failed to process the uploaded document: {str(e)}",
                "error_type": "generation_failure",
            }
        )


@app.get("/download/{filename}")
async def download_deck(filename: str):
    """Download a generated pitch deck."""
    filepath = os.path.join(settings.generated_decks_dir, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=filename,
    )


@app.get("/health")
async def health_check():
    """Health check endpoint for Render."""
    return {
        "status": "healthy",
        "policies_loaded": len(_policy_chunks),
        "retriever_ready": _retriever is not None,
    }


# ── Serve Static Frontend ──────────────────────────────────────
# Mount static files LAST so API routes take precedence
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")


@app.get("/")
async def serve_frontend():
    """Serve the main HTML page."""
    index_path = os.path.join(settings.static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>Marsh Pitch Generator</h1><p>Frontend not found. Check static/index.html.</p>")
