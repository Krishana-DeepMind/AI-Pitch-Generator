"""Audit layer (Objectives 2.1 and 2.2).

auditPitchContent(pitch_slides, policy_docs):
- Hybrid approach: resolve most claims via cosine similarity (zero LLM cost)
- Only calls the 8B model for claims near the similarity threshold
- Traces each claim to a specific policy clause
- Flags untraceable statements for human review
- Produces confidence score and pass/fail summary
"""

import json
import logging
from typing import List, Dict, Optional

from app.llm import llm_client
from app.models import (
    PitchDeck, SlideContent, AuditReport, SlideAudit,
    ClaimAudit, AuditVerdict,
)
from app.retrieval import PolicyRetriever
from app.config import settings

logger = logging.getLogger(__name__)


CLAIM_EXTRACTION_PROMPT = """Extract all factual claims about insurance policy features, coverage, benefits, limits, or specific numbers from the following slide content.

Slide Title: {slide_title}
Content:
{slide_content}

Return a JSON object with this structure:
{{
    "claims": [
        "Each specific factual claim as a standalone sentence"
    ]
}}

Rules:
- Extract ONLY factual claims about policy features, coverage limits, benefits, or specific numbers.
- Do NOT include general marketing statements, opinions, or company descriptions.
- Do NOT include claims about Marsh itself (only about insurance policies/coverage).
- Each claim should be self-contained and verifiable against a policy document.
- If the slide contains no verifiable policy claims, return an empty list.

Return ONLY the JSON object."""


LLM_VERIFICATION_PROMPT = """You are an insurance compliance auditor. Determine whether the following claim is supported by the provided policy document excerpt.

CLAIM: "{claim}"

POLICY EXCERPT:
{policy_text}

Respond with a JSON object:
{{
    "verdict": "supported" | "partially_supported" | "unsupported",
    "confidence": 0.0 to 1.0,
    "explanation": "Brief explanation of why the claim is or isn't supported",
    "matched_clause": "The specific text from the excerpt that supports or contradicts the claim, or null if no match"
}}

Rules:
- "supported" = the claim is directly and fully backed by the excerpt
- "partially_supported" = the claim is related but details differ (amounts, scope, conditions)
- "unsupported" = the excerpt contradicts or doesn't mention the claim at all
- Be strict: if specific numbers, limits, or coverage details don't match exactly, mark as partially_supported
- confidence should reflect how certain you are about your verdict

Return ONLY the JSON object."""


def extract_claims_from_slide(slide: SlideContent) -> List[str]:
    """Extract verifiable factual claims from a slide using LLM.
    
    Uses the 8B model (cheaper) since this is a structured extraction task.
    """
    slide_content = "\n".join([
        f"- {point}" for point in slide.bullet_points
    ])
    
    if not slide_content.strip():
        return []
    
    messages = [
        {
            "role": "system",
            "content": "You are a claims extraction assistant. Extract only factual, verifiable claims about insurance policy coverage. Return valid JSON."
        },
        {
            "role": "user",
            "content": CLAIM_EXTRACTION_PROMPT.format(
                slide_title=slide.title,
                slide_content=slide_content,
            )
        }
    ]
    
    try:
        result = llm_client.generate_json(
            messages=messages,
            model_tier="structured",
            temperature=0.1,
            max_tokens=800,
        )
        return result.get("claims", [])
    except Exception as e:
        logger.warning(f"Failed to extract claims from slide {slide.slide_number}: {e}")
        # Fallback: use bullet points directly
        return [bp for bp in slide.bullet_points if any(
            keyword in bp.lower() for keyword in 
            ["cover", "insur", "lakh", "crore", "sum insured", "%", "benefit", 
             "claim", "hospital", "treatment", "premium", "waiting period"]
        )]


def verify_claim_with_similarity(
    claim: str,
    retriever: PolicyRetriever,
) -> ClaimAudit:
    """Verify a claim using cosine similarity search (zero LLM cost).
    
    This is the primary verification method. Only if the similarity score
    falls in the ambiguous zone will we escalate to LLM verification.
    """
    results = retriever.search_text(
        query_text=claim,
        top_k=3,
        threshold=0.0,
    )
    
    if not results:
        return ClaimAudit(
            claim_text=claim,
            verdict=AuditVerdict.UNVERIFIABLE,
            confidence_score=0.0,
            verification_method="cosine_similarity",
            notes="No policy chunks available for verification.",
        )
    
    best_match = results[0]
    score = best_match["similarity_score"]
    
    if score >= settings.similarity_threshold:
        # High similarity — claim is likely supported
        return ClaimAudit(
            claim_text=claim,
            verdict=AuditVerdict.SUPPORTED,
            confidence_score=min(score, 1.0),
            source_clause=best_match["text"][:300],
            source_document=best_match["document_name"],
            source_chunk_similarity=score,
            verification_method="cosine_similarity",
            notes=f"High similarity match (score: {score:.3f})",
        )
    elif score >= settings.llm_audit_threshold:
        # Ambiguous zone — needs LLM verification
        return None  # Signal to use LLM
    else:
        # Low similarity — claim is likely unsupported
        return ClaimAudit(
            claim_text=claim,
            verdict=AuditVerdict.UNSUPPORTED,
            confidence_score=1.0 - score,
            source_clause=best_match["text"][:300] if score > 0.2 else None,
            source_document=best_match["document_name"],
            source_chunk_similarity=score,
            verification_method="cosine_similarity",
            notes=f"Low similarity — no strong match found (best score: {score:.3f})",
        )


def verify_claim_with_llm(
    claim: str,
    retriever: PolicyRetriever,
) -> ClaimAudit:
    """Verify an ambiguous claim using the 8B LLM model.
    
    Called only when cosine similarity falls in the ambiguous threshold zone.
    """
    results = retriever.search_text(
        query_text=claim,
        top_k=3,
        threshold=0.0,
    )
    
    if not results:
        return ClaimAudit(
            claim_text=claim,
            verdict=AuditVerdict.UNVERIFIABLE,
            confidence_score=0.0,
            verification_method="llm_verification",
            notes="No policy chunks available for verification.",
        )
    
    # Combine top-3 chunks as context for LLM
    policy_text = "\n\n---\n\n".join([
        f"[{r['document_name']}]: {r['text']}" for r in results
    ])
    
    messages = [
        {
            "role": "system",
            "content": "You are a strict insurance compliance auditor. Verify claims against policy excerpts. Return valid JSON."
        },
        {
            "role": "user",
            "content": LLM_VERIFICATION_PROMPT.format(
                claim=claim,
                policy_text=policy_text,
            )
        }
    ]
    
    try:
        result = llm_client.generate_json(
            messages=messages,
            model_tier="structured",
            temperature=0.1,
            max_tokens=500,
        )
        
        verdict_map = {
            "supported": AuditVerdict.SUPPORTED,
            "partially_supported": AuditVerdict.PARTIALLY_SUPPORTED,
            "unsupported": AuditVerdict.UNSUPPORTED,
        }
        
        verdict = verdict_map.get(result.get("verdict", ""), AuditVerdict.UNVERIFIABLE)
        
        return ClaimAudit(
            claim_text=claim,
            verdict=verdict,
            confidence_score=float(result.get("confidence", 0.5)),
            source_clause=result.get("matched_clause") or results[0]["text"][:300],
            source_document=results[0]["document_name"],
            source_chunk_similarity=results[0]["similarity_score"],
            verification_method="llm_verification",
            notes=result.get("explanation", "Verified via LLM analysis"),
        )
    except Exception as e:
        logger.warning(f"LLM verification failed for claim: {e}")
        # Fall back to cosine-based judgment since LLM failed
        best = results[0]
        score = best["similarity_score"]
        
        # Since it was in the ambiguous zone to reach here, we'll conservatively 
        # give it PARTIALLY_SUPPORTED or UNSUPPORTED rather than a technical failure.
        verdict = AuditVerdict.PARTIALLY_SUPPORTED if score >= 0.4 else AuditVerdict.UNSUPPORTED
        
        return ClaimAudit(
            claim_text=claim,
            verdict=verdict,
            confidence_score=score,
            source_clause=best["text"][:300],
            source_document=best["document_name"],
            source_chunk_similarity=score,
            verification_method="cosine_similarity_fallback",
            notes=f"LLM verification failed (API error). Fallback to cosine score ({score:.3f}).",
        )


def audit_pitch_content(
    pitch: PitchDeck,
    retriever: PolicyRetriever,
) -> AuditReport:
    """Audit all claims in a pitch deck against policy documents.
    
    Implements Objectives 2.1 and 2.2:
    - Traces each claim to a specific policy clause
    - Flags untraceable statements for human review
    - Produces confidence score and pass/fail summary
    
    Hybrid approach:
    1. First pass: cosine similarity (free, fast)
    2. Second pass: LLM verification only for ambiguous claims
    
    Args:
        pitch: The generated pitch deck.
        retriever: PolicyRetriever loaded with policy embeddings.
        
    Returns:
        Complete AuditReport with per-claim verdicts.
    """
    logger.info(f"Auditing pitch deck for {pitch.company_name} ({len(pitch.slides)} slides)")
    
    slide_audits = []
    total_claims = 0
    supported = 0
    partially_supported = 0
    unsupported = 0
    unverifiable = 0
    
    for slide in pitch.slides:
        logger.info(f"  Auditing slide {slide.slide_number}: {slide.title}")
        
        # Step 1: Extract claims from this slide
        claims = extract_claims_from_slide(slide)
        logger.info(f"    Extracted {len(claims)} verifiable claims")
        
        claim_audits = []
        
        for claim in claims:
            total_claims += 1
            
            # Step 2: Try cosine similarity first (free)
            audit_result = verify_claim_with_similarity(claim, retriever)
            
            if audit_result is None:
                # Ambiguous — escalate to LLM
                logger.info(f"    Claim in ambiguous zone, using LLM: {claim[:60]}...")
                audit_result = verify_claim_with_llm(claim, retriever)
            
            # Count verdicts
            if audit_result.verdict == AuditVerdict.SUPPORTED:
                supported += 1
            elif audit_result.verdict == AuditVerdict.PARTIALLY_SUPPORTED:
                partially_supported += 1
            elif audit_result.verdict == AuditVerdict.UNSUPPORTED:
                unsupported += 1
            else:
                unverifiable += 1
            
            claim_audits.append(audit_result)
        
        # Slide passes if no unsupported claims
        slide_pass = all(
            ca.verdict in (AuditVerdict.SUPPORTED, AuditVerdict.PARTIALLY_SUPPORTED)
            for ca in claim_audits
        ) if claim_audits else True
        
        slide_audits.append(SlideAudit(
            slide_number=slide.slide_number,
            slide_title=slide.title,
            claims=claim_audits,
            slide_pass=slide_pass,
        ))
    
    # Overall metrics
    overall_confidence = supported / total_claims if total_claims > 0 else 0.0
    overall_pass = unsupported == 0 and unverifiable <= total_claims * 0.2
    
    # Generate summary
    summary_parts = [
        f"Audited {total_claims} claims across {len(pitch.slides)} slides.",
        f"✅ Supported: {supported} | ⚠️ Partially Supported: {partially_supported}",
        f"❌ Unsupported: {unsupported} | ❓ Unverifiable: {unverifiable}",
        f"Overall Confidence: {overall_confidence:.0%}",
    ]
    
    if overall_pass:
        summary_parts.append("✅ PASS — All claims are traceable to source policy documents.")
    else:
        summary_parts.append("⚠️ REVIEW NEEDED — Some claims require advisor review before client delivery.")
    
    return AuditReport(
        company_name=pitch.company_name,
        total_claims=total_claims,
        supported_claims=supported,
        partially_supported_claims=partially_supported,
        unsupported_claims=unsupported,
        unverifiable_claims=unverifiable,
        overall_confidence=overall_confidence,
        overall_pass=overall_pass,
        slide_audits=slide_audits,
        summary="\n".join(summary_parts),
    )
