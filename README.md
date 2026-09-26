# Marsh AI-Powered Insurance Pitch Generator

A FastAPI application that generates AI-powered, policy-grounded marketing pitch decks for insurance advisors. It builds company risk profiles, recommends policies, exports PowerPoint slides, and rigorously audits every claim against actual policy documents using a hybrid LLM pipeline.

## Features

- **Automated Risk Profiling**: Generates a tailored risk profile based on a given company name.
- **RAG-Powered Pitch Generation**: Maps company risks to specific policy benefits retrieved via cosine similarity.
- **Claim Auditing Pipeline**: Automatically audits every single claim generated on the slides against the source policy documents to prevent hallucinations. Uses a hybrid approach (Cosine Similarity + LLM verification).
- **PowerPoint Export**: Automatically compiles the generated content into a formatted `.pptx` presentation deck.
- **Visual Audit Report**: Provides a detailed breakdown in the UI, tagging claims as Supported, Partially Supported, Unsupported, or Degraded.

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Vanilla HTML/CSS/JS
- **LLM Providers**: Groq (`llama-3.3-70b-versatile` / `llama-3.1-8b-instant`) with OpenRouter fallback.
- **Embeddings & Vector Search**: `fastembed` (BAAI/bge-small-en-v1.5) with local/NumPy similarity search.
- **Document Processing**: `PyMuPDF` for parsing, `python-pptx` for deck generation.

---

## Local Setup Instructions

### 1. Prerequisites
- Python 3.9+ installed on your system.

### 2. Clone the Repository
```bash
git clone https://github.com/Krishana-DeepMind/AI-Pitch-Generator.git
cd "AI-Pitch-Generator"
```

### 3. Set Up Virtual Environment
Create and activate a virtual environment (recommended name: `pitch-gen`).

**Windows (PowerShell):**
```powershell
python -m venv pitch-gen
.\pitch-gen\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv pitch-gen
source pitch-gen/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy the example `.env` file and add your API keys.

```bash
cp .env.example .env
```
Open `.env` and add your keys:
- `GROQ_API_KEY` (Required for primary LLM generation and auditing)
- `OPENROUTER_API_KEY` (Optional, used as a fallback if Groq hits rate limits)

### 6. Run the Application
Start the FastAPI development server:

```bash
uvicorn app.main:app --reload --port 8000
```

### 7. Access the App
Open your web browser and navigate to:
**http://127.0.0.1:8000**
