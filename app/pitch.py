"""Marketing pitch generation (Objective 1.3).

generateMarketingPitch():
- Produces a 3–5 slide deck covering:
  1. Company overview
  2. Why choose Marsh
  3. Policy benefits mapped to company risk exposures
  4. Recommended policy
- Uses the 70B model for creative, high-quality content
- Grounded in retrieved policy document chunks
"""

import json
import logging
from typing import List, Dict, Optional

from app.llm import llm_client
from app.models import CompanyProfile, SlideContent, PitchDeck

logger = logging.getLogger(__name__)


PITCH_GENERATION_PROMPT = """You are a senior marketing strategist at Marsh, a leading global insurance brokerage. Your task is to create a compelling, client-specific marketing pitch deck for group medical insurance.

## Company Profile
{company_profile}

## Available Policy Information
The following are actual excerpts from policy documents that are relevant to this company's risks. Every claim in your pitch MUST be based on these excerpts — do not fabricate policy features or coverage details.

{policy_context}

## Requirements
Create a pitch deck with exactly 4-5 slides as a JSON object. The deck must cover:

1. **Slide 1 - Company Overview**: Brief analysis of the company, their industry, workforce characteristics, and key health risk exposures. Show the company you understand their business.

2. **Slide 2 - Why Choose Marsh**: Marsh's value proposition — advisory expertise, global network, claims advocacy, and how Marsh helps navigate complex insurance decisions. This should be compelling but not over-specific about coverage (that comes next).

3. **Slide 3 - Policy Benefits Mapped to Risks**: Map SPECIFIC policy benefits from the provided policy documents to the company's identified risk exposures. For example, if the company has high-stress employees, highlight relevant mental health or wellness coverage. ONLY cite benefits that appear in the policy excerpts above.

4. **Slide 4 - Coverage Comparison** (optional): If multiple policies are available, briefly compare their key differentiators relevant to this company.

5. **Final Slide - Recommended Policy**: Name ONE recommended policy and explain WHY it's the best fit for this company's specific risk profile. The recommendation must be justified based on the company's risks and the policy's actual coverage.

## Output Format
Return a JSON object with this structure:
{{
    "company_name": "{company_name}",
    "slides": [
        {{
            "slide_number": 1,
            "title": "Slide title",
            "subtitle": "Optional subtitle",
            "bullet_points": ["Point 1", "Point 2", "Point 3", "Point 4"],
            "speaker_notes": "Notes for the presenter",
            "slide_type": "content"
        }}
    ],
    "recommended_policy": "Name of the recommended policy",
    "recommendation_rationale": "2-3 sentences explaining why this policy is recommended for this company"
}}

## Critical Rules
1. ONLY cite coverage details, limits, and features that appear in the policy excerpts provided above.
2. Each bullet point should be concrete and specific — avoid vague marketing language.
3. Use actual numbers (Sum Insured amounts, coverage percentages, waiting periods) from the policies.
4. The recommendation must be data-driven, not generic.
5. Keep bullet points concise (1-2 lines each).
6. Include 3-5 bullet points per slide.

Return ONLY the JSON object."""


def generate_marketing_pitch(
    company_profile: CompanyProfile,
    policy_chunks: List[Dict],
) -> PitchDeck:
    """Generate a marketing pitch deck grounded in policy documents.
    
    Uses the 70B model for creative, high-quality content generation.
    All claims are grounded in the retrieved policy chunks.
    
    Args:
        company_profile: The company's risk profile.
        policy_chunks: Relevant policy document chunks from retrieval.
        
    Returns:
        PitchDeck with 3-5 slides.
        
    Raises:
        LLMError: If all LLM providers fail.
    """
    logger.info(f"Generating marketing pitch for: {company_profile.company_name}")
    
    # Format company profile
    profile_text = f"""Company: {company_profile.company_name}
Industry: {company_profile.industry} ({company_profile.industry_sector or 'General'})
Size: {company_profile.estimated_size}
Headquarters: {company_profile.headquarters or 'Not specified'}
Key Risks: {', '.join(company_profile.key_risks)}
Employee Demographics: {company_profile.employee_demographics or 'Not specified'}
Risk Summary: {company_profile.risk_summary}
Assumptions: {', '.join(company_profile.assumptions) if company_profile.assumptions else 'None'}"""
    
    # Format policy context
    policy_context_parts = []
    for i, chunk in enumerate(policy_chunks):
        doc_name = chunk.get("document_name", "Unknown")
        text = chunk.get("text", "")
        score = chunk.get("similarity_score", 0)
        policy_context_parts.append(
            f"[Source: {doc_name} | Relevance: {score:.2f}]\n{text}"
        )
    
    policy_context = "\n\n---\n\n".join(policy_context_parts) if policy_context_parts else "No policy documents available."
    
    messages = [
        {
            "role": "system",
            "content": "You are a Marsh marketing strategist. Generate compelling, factually grounded pitch content. Return only valid JSON."
        },
        {
            "role": "user",
            "content": PITCH_GENERATION_PROMPT.format(
                company_profile=profile_text,
                policy_context=policy_context,
                company_name=company_profile.company_name,
            )
        }
    ]
    
    result = llm_client.generate_json(
        messages=messages,
        model_tier="generation",
        temperature=0.7,
        max_tokens=5000,
    )
    
    # Parse slides
    slides = []
    for s in result.get("slides", []):
        slides.append(SlideContent(
            slide_number=s.get("slide_number", len(slides) + 1),
            title=s.get("title", ""),
            subtitle=s.get("subtitle"),
            bullet_points=s.get("bullet_points", []),
            speaker_notes=s.get("speaker_notes"),
            slide_type=s.get("slide_type", "content"),
        ))
    
    pitch = PitchDeck(
        company_name=result.get("company_name", company_profile.company_name),
        slides=slides,
        recommended_policy=result.get("recommended_policy", ""),
        recommendation_rationale=result.get("recommendation_rationale", ""),
    )
    
    logger.info(f"Generated pitch with {len(pitch.slides)} slides, recommending: {pitch.recommended_policy}")
    
    return pitch
