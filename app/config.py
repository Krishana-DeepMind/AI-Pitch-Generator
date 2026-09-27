"""Marsh AI-Powered Insurance Pitch Generator - Configuration."""

import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    
    # Supabase
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_KEY", "")
    
    # LLM Models
    groq_generation_model: str = "openai/gpt-oss-120b"
    groq_structured_model: str = "openai/gpt-oss-20b"
    openrouter_fallback_model: str = "meta-llama/llama-3.1-8b-instruct:free"
    
    # Embedding model
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    
    # Paths
    policy_docs_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "policy_docs")
    data_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    generated_decks_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "submission_material", "generated_decks")
    audit_reports_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "submission_material", "audit_reports")
    static_dir: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    
    # Retrieval settings
    similarity_threshold: float = 0.85
    llm_audit_threshold: float = 0.60  # Below this, use LLM to verify
    top_k_chunks: int = 8
    
    # Chunk settings
    chunk_size: int = 500
    chunk_overlap: int = 100
    
    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()

# Ensure directories exist
os.makedirs(settings.data_dir, exist_ok=True)
os.makedirs(settings.generated_decks_dir, exist_ok=True)
os.makedirs(settings.audit_reports_dir, exist_ok=True)
os.makedirs(settings.policy_docs_dir, exist_ok=True)
