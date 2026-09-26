"""Company profile generation (Objective 1.2).

generateCompanyProfile(company_name):
- Gathers company info (industry, size, key risks)
- Falls back to clearly-labelled assumptions if data is unavailable
- Uses the 8B model (structured/classification tasks)
"""

import json
import logging
from typing import Optional

from app.llm import llm_client
from app.models import CompanyProfile

logger = logging.getLogger(__name__)


COMPANY_PROFILE_PROMPT = """You are a risk analyst at Marsh, a global insurance brokerage. Your job is to create a company risk profile for insurance advisory purposes.

Given the company name "{company_name}", produce a detailed risk profile as a JSON object with exactly these fields:

{{
    "company_name": "{company_name}",
    "industry": "The industry/sector the company operates in",
    "industry_sector": "Specific sub-sector if known",
    "estimated_size": "Company size estimate (e.g., 'Large (10,000+ employees)', 'Mid-size (1,000-10,000 employees)', 'Small (<1,000 employees)')",
    "headquarters": "City/Country of headquarters",
    "key_risks": ["List of 4-6 key health/insurance risk exposures relevant to this company's workforce"],
    "employee_demographics": "Brief description of typical employee demographics and work patterns",
    "risk_summary": "A 2-3 sentence summary of why this company needs group medical insurance and what their key risk exposures are",
    "assumptions": ["List every piece of information you're uncertain about, prefixed with 'ASSUMPTION: '. If you don't have reliable data about the company, explicitly state it here rather than guessing silently."]
}}

CRITICAL RULES:
1. If you don't know specific facts about the company (employee count, exact industry, etc.), DO NOT silently guess. Instead, provide your best estimate AND add it to the "assumptions" list with the prefix "ASSUMPTION: ".
2. Every assumption must be clearly labeled — the advisor using this tool needs to know what's verified vs estimated.
3. Key risks should be specific to the company's industry and workforce — consider occupational hazards, lifestyle factors, stress levels, travel requirements, etc.
4. Focus on risks relevant to MEDICAL/HEALTH insurance (not property, liability, etc.).

Return ONLY the JSON object, no other text."""


def generate_company_profile(company_name: str) -> CompanyProfile:
    """Generate a company risk profile using LLM.
    
    Uses the 8B structured model (cheaper, sufficient for extraction tasks).
    All uncertain information is explicitly labeled as an assumption.
    
    Args:
        company_name: Name of the target company.
        
    Returns:
        CompanyProfile with all fields populated.
        
    Raises:
        LLMError: If all LLM providers fail.
    """
    logger.info(f"Generating company profile for: {company_name}")
    
    messages = [
        {
            "role": "system",
            "content": "You are a risk analyst at Marsh. Respond only with valid JSON. Always label assumptions explicitly."
        },
        {
            "role": "user",
            "content": COMPANY_PROFILE_PROMPT.format(company_name=company_name)
        }
    ]
    
    result = llm_client.generate_json(
        messages=messages,
        model_tier="structured",
        temperature=0.3,
        max_tokens=800,
    )
    
    # Ensure assumptions are properly prefixed
    if "assumptions" in result:
        result["assumptions"] = [
            a if a.startswith("ASSUMPTION:") else f"ASSUMPTION: {a}"
            for a in result["assumptions"]
        ]
    else:
        result["assumptions"] = ["ASSUMPTION: All company details are based on publicly available information and may not reflect current state."]
    
    profile = CompanyProfile(**result)
    logger.info(f"Profile generated: {profile.industry}, {profile.estimated_size}, {len(profile.key_risks)} risks, {len(profile.assumptions)} assumptions")
    
    return profile
