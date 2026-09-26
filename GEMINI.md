# Marsh AI-Powered Insurance Pitch Generator

## Project Overview
A FastAPI web application that generates AI-powered, policy-grounded marketing pitch decks for insurance advisors at Marsh. Advisors input a company name, and the system builds a risk profile, generates a tailored pitch deck (.pptx), and audits every claim against actual policy documents.

## Virtual Environment Rule
**CRITICAL**: All packages and libraries for this project MUST be installed in the virtual environment named `pitch-gen` located inside this project directory. NEVER install packages globally.

- **Activation (PowerShell)**: `.\pitch-gen\Scripts\Activate.ps1`
- **Activation (cmd)**: `.\pitch-gen\Scripts\activate.bat`
- **Install packages**: Always activate venv first, then `pip install <package>`

## Tech Stack
| Layer | Tool |
|---|---|
| Backend | FastAPI (serves API + static frontend) |
| Embeddings | fastembed (ONNX, BAAI/bge-small-en-v1.5) |
| Vector Storage | Precomputed pickle (offline) + Supabase pgvector (runtime) |
| Similarity Search | NumPy cosine similarity |
| LLM (Generation) | Groq API, llama-3.3-70b-versatile |
| LLM (Structured) | Groq API, llama-3.1-8b-instant |
| LLM Fallback | OpenRouter free-tier models |
| Audit | Hybrid: cosine similarity + LLM fallback |
| Deck Generation | python-pptx |
| PDF Parsing | PyMuPDF |
| Frontend | Plain HTML/CSS/JS |
| Deployment | Render free tier |

## Project Structure
```
insurance pitch generator/
├── GEMINI.md
├── pitch-gen/                 # Virtual environment (NOT committed to git)
├── policy_docs/               # Source policy PDFs
├── data/                      # Precomputed embeddings (pickle)
├── generated_decks/           # Output .pptx files
├── static/                    # Frontend files (HTML/CSS/JS)
│   ├── index.html
│   ├── style.css
│   └── app.js
├── app/                       # Backend Python package
│   ├── __init__.py
│   ├── main.py               # FastAPI app entry point
│   ├── config.py             # Settings and env vars
│   ├── ingestion.py          # PDF parsing, chunking, embedding
│   ├── retrieval.py          # Cosine similarity search
│   ├── profile.py            # Company profile generation
│   ├── pitch.py              # Marketing pitch generation
│   ├── audit.py              # Claim auditing (hybrid approach)
│   ├── deck.py               # PPTX generation
│   ├── llm.py                # LLM wrapper with retry/fallback
│   └── models.py             # Pydantic models
├── scripts/
│   └── ingest_policies.py    # Offline ingestion script
├── requirements.txt
├── render.yaml
└── .env                      # API keys (not committed)
```

## API Endpoints
- `POST /generate-pitch` — Full pipeline: profile → retrieval → generation → audit
- `POST /admin/add-policy` — Upload new policy PDF
- `GET /policies` — List available policy documents

## Build Progress
- [x] Phase 1: Repo structure, FastAPI skeleton, frontend shell
- [ ] Phase 2: Offline ingestion pipeline
- [ ] Phase 3: Retrieval layer
- [ ] Phase 4: Company profile + pitch generation
- [ ] Phase 5: Audit layer
- [ ] Phase 6: PPTX export
- [ ] Phase 7: Frontend UI wiring
- [ ] Phase 8: Admin endpoint + Supabase
- [ ] Phase 9: End-to-end testing
- [ ] Phase 10: Deployment config

## Key Design Decisions
- Policy documents are dynamically discovered, never hardcoded
- All LLM calls wrapped in retry-with-backoff + provider fallback
- Audit uses hybrid approach: cosine similarity first, LLM only for ambiguous claims
- Assumptions in company profiles are explicitly labeled
