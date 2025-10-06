# genai-service

A lightweight FastAPI microservice that fetches mess feedback from a Postgres DB,
prompts Google Gemini (via google-generativeai) and returns structured analysis.

## Files
- `main.py` - FastAPI app
- `db.py` - DB helper to fetch feedback rows for a given date
- `prompts.py` - load prompts mapping
- `prompts.json` - example prompt templates
- `requirements.txt` - Python dependencies
- `Dockerfile` - container image build

## Environment variables
Set these before running (or use `.env` or your pipeline secrets):
- `DATABASE_URL` - e.g. `postgresql://user:pass@host:5432/dbname`
- `GEMINI_API_KEY` - your Google Generative AI API key (free maker key)
- `FEEDBACK_TABLE` - (optional) table name, default `feedbacks`
- `TIMESTAMP_COL` - (optional) timestamp column for filtering, default `created_at`
- `PROMPTS_FILE` - path to prompts JSON, default `prompts.json`
- `GENAI_MODEL` - model name, default `gemini-1.5-flash`

## Endpoints
- `GET /` - health check
- `POST /analyze-today` - analyze today's feedbacks using default prompt
- `POST /analyze` - body: `{ "date": "YYYY-MM-DD", "extra_instructions": "...", "prompt_key": "..." }`
- `GET /prompts` - list available prompt keys
- `POST /prompt/{key}` - run named prompt for today's feedbacks

## Run locally
```bash
export DATABASE_URL="postgresql://user:pass@host:5432/db"
export GEMINI_API_KEY="..."
uvicorn main:app --reload --host 0.0.0.0 --port 8000
