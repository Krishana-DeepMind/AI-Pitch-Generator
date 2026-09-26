"""Pydantic models for request/response schemas."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


# ── Request Models ──────────────────────────────────────────────

class PitchRequest(BaseModel):
    """Request body for pitch generation."""
    company_name: str = Field(..., min_length=1, max_length=200, description="Name of the target company")
    selected_policies: Optional[List[str]] = Field(
        default=None, 
        description="Optional list of policy document names to use. If None, all available policies are used."
    )


# ── Company Profile Models ──────────────────────────────────────

class CompanyProfile(BaseModel):
    """Company risk profile generated from LLM analysis."""
    company_name: str
    industry: str
    industry_sector: Optional[str] = None
    estimated_size: str  # e.g., "Large (10,000+ employees)"
    headquarters: Optional[str] = None
    key_risks: List[str]
    employee_demographics: Optional[str] = None
    risk_summary: str
    assumptions: List[str] = Field(
        default_factory=list,
        description="Explicitly labeled assumptions where real data was unavailable"
    )


# ── Pitch Slide Models ──────────────────────────────────────────

class SlideContent(BaseModel):
    """Content for a single pitch deck slide."""
    slide_number: int
    title: str
    subtitle: Optional[str] = None
    bullet_points: List[str]
    speaker_notes: Optional[str] = None
    slide_type: str = "content"  # "title", "content", "recommendation", "summary"


class PitchDeck(BaseModel):
    """Complete pitch deck with all slides."""
    company_name: str
    slides: List[SlideContent]
    recommended_policy: str
    recommendation_rationale: str


# ── Audit Models ────────────────────────────────────────────────

class AuditVerdict(str, Enum):
    """Verdict for an individual claim audit."""
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    UNSUPPORTED = "unsupported"
    UNVERIFIABLE = "unverifiable"


class ClaimAudit(BaseModel):
    """Audit result for a single claim extracted from the pitch."""
    claim_text: str
    verdict: AuditVerdict
    confidence_score: float = Field(ge=0.0, le=1.0)
    source_clause: Optional[str] = None
    source_document: Optional[str] = None
    source_chunk_similarity: Optional[float] = None
    verification_method: str = "cosine_similarity"  # or "llm_verification"
    notes: Optional[str] = None


class SlideAudit(BaseModel):
    """Audit results for all claims in a single slide."""
    slide_number: int
    slide_title: str
    claims: List[ClaimAudit]
    slide_pass: bool


class AuditReport(BaseModel):
    """Complete audit report for the pitch deck."""
    company_name: str
    total_claims: int
    supported_claims: int
    partially_supported_claims: int
    unsupported_claims: int
    unverifiable_claims: int
    overall_confidence: float
    overall_pass: bool
    slide_audits: List[SlideAudit]
    summary: str


# ── Response Models ─────────────────────────────────────────────

class PitchResponse(BaseModel):
    """Full response from the pitch generation pipeline."""
    company_name: str
    profile: CompanyProfile
    deck_filename: str
    deck_download_url: str
    slides_preview: List[SlideContent]
    audit_report: AuditReport
    recommended_policy: str


class PolicyInfo(BaseModel):
    """Information about an available policy document."""
    name: str
    filename: str
    num_chunks: int
    source: str  # "precomputed" or "uploaded"


class ErrorResponse(BaseModel):
    """Structured error response."""
    error: str
    detail: str
    error_type: str  # "validation", "no_policies", "generation_failure", "audit_failure"


# ── Internal Models ─────────────────────────────────────────────

class PolicyChunk(BaseModel):
    """A chunk of text from a policy document with its embedding."""
    text: str
    document_name: str
    chunk_index: int
    page_number: Optional[int] = None
    embedding: Optional[List[float]] = None
    
    class Config:
        arbitrary_types_allowed = True
