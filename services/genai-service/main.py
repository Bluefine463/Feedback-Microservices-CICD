# genai-service/main.py
from fastapi import FastAPI, HTTPException, Path, status
from pydantic import BaseModel
from datetime import datetime, timedelta, date
import os
import logging
import json
import math

import google.generativeai as genai
from db import get_feedbacks_for_date
from prompts import load_prompts, get_prompt_template

app = FastAPI(title="GenAI Feedback Analysis Service", version="1.0")

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("genai-service")

# Configure Gemini API key (from env variable)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.warning("GEMINI_API_KEY not set. Calls to Gemini will fail until the env var is set.")
else:
    genai.configure(api_key=GEMINI_API_KEY)

# Load prompts mapping (prompts.json or fallback defaults)
PROMPTS_FILE = os.getenv("PROMPTS_FILE", "prompts.json")
prompts = load_prompts(PROMPTS_FILE)

# Limits (to avoid extremely large prompts)
MAX_PROMPT_CHARS = int(os.getenv("MAX_PROMPT_CHARS", "16000"))
FEEDBACK_TRUNCATE_PER_ITEM = int(os.getenv("FEEDBACK_TRUNCATE_PER_ITEM", "1000"))

# Default model
GENAI_MODEL = os.getenv("GENAI_MODEL", "gemini-1.5-flash")

class AnalyzeRequest(BaseModel):
    # Optional explicit date string in ISO format (YYYY-MM-DD). If omitted, use today.
    date: str | None = None
    # Optional list of additional instructions to append to the prompt
    extra_instructions: str | None = None
    # Optional override for prompt key
    prompt_key: str | None = None

@app.get("/", tags=["health"])
def root():
    return {"message": "GenAI Feedback Service running", "version": "1.0"}

@app.post("/analyze-today", tags=["analysis"])
def analyze_today():
    """
    Convenience endpoint: analyze feedbacks for today using default prompt.
    """
    req = AnalyzeRequest()
    return _run_analysis_for_request(req)

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "healthy"}

@app.post("/analyze", tags=["analysis"])
def analyze(req: AnalyzeRequest):
    """
    Analyze feedbacks for a specific date (YYYY-MM-DD) or today if omitted.
    You may provide extra_instructions to append to the prompt,
    or prompt_key to use a named prompt from prompts.json.
    """
    return _run_analysis_for_request(req)

@app.get("/prompts", tags=["prompts"])
def list_prompts():
    """Return available prompt keys and a short preview."""
    result = {}
    for k, v in prompts.items():
        preview = (v or "").strip().replace("\n", " ")
        result[k] = preview[:200] + ("..." if len(preview) > 200 else "")
    return {"available_prompt_keys": result}

@app.post("/prompt/{key}", tags=["prompts"])
def call_prompt_key(key: str = Path(..., description="The prompt key to run (from prompts.json)")):
    """
    Run the prompt identified by `key` against today's feedbacks.
    The prompt may contain interpolation tokens:
      {feedbacks} -> replaced with the concatenated feedback texts
      {date} -> date string used for the run
    """
    if key not in prompts:
        raise HTTPException(status_code=404, detail=f"Prompt key '{key}' not found.")
    prompt_template = get_prompt_template(prompts, key)
    # Build a request that uses this prompt key
    req = AnalyzeRequest(prompt_key=key)
    return _run_analysis_for_request(req, prompt_override=prompt_template)

def _run_analysis_for_request(req: AnalyzeRequest, prompt_override: str | None = None):
    # Determine date
    try:
        if req.date:
            run_date = datetime.strptime(req.date, "%Y-%m-%d").date()
        else:
            run_date = date.today()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    logger.info(f"Running analysis for date: {run_date.isoformat()}")

    # Fetch feedbacks from DB
    try:
        feedback_rows = get_feedbacks_for_date(run_date)
    except Exception as exc:
        logger.exception("DB query failed")
        raise HTTPException(status_code=500, detail=f"Failed to fetch feedbacks: {str(exc)}")

    if not feedback_rows:
        return {
            "date": run_date.isoformat(),
            "total_feedbacks": 0,
            "analysis": None,
            "message": "No feedbacks found for this date."
        }

    # Extract text field from rows. We support both dicts and SQLAlchemy Row objects.
    feedback_texts = []
    for r in feedback_rows:
        text = None
        # The row 'r' is a dictionary-like object because of RealDictCursor
        if isinstance(r, dict) and r.get("description"):
            text = str(r["description"])
        # Fallback for other object types
        elif hasattr(r, "description"):
            text = str(getattr(r, "description"))

        if not text:
            continue
        # truncate per item to avoid massive prompts
        if len(text) > FEEDBACK_TRUNCATE_PER_ITEM:
            text = text[:FEEDBACK_TRUNCATE_PER_ITEM] + " [truncated]"
        feedback_texts.append(text)
    # for r in feedback_rows:
    #     # Accept several possible column names
    #     text = None
    #     if isinstance(r, dict):
    #         for candidate in ("text", "feedback_text", "message", "comment", "body"):
    #             if candidate in r and r[candidate]:
    #                 text = str(r[candidate])
    #                 break
    #     else:
    #         # fallback to attribute access
    #         for candidate in ("text", "feedback_text", "message", "comment", "body"):
    #             if hasattr(r, candidate):
    #                 val = getattr(r, candidate)
    #                 if val:
    #                     text = str(val)
    #                     break
    #         # if still None, try first column
    #         if text is None:
    #             try:
    #                 text = str(r[0])
    #             except Exception:
    #                 text = None
    #     if not text:
    #         continue
    #     # truncate per item to avoid massive prompts
    #     if len(text) > FEEDBACK_TRUNCATE_PER_ITEM:
    #         text = text[:FEEDBACK_TRUNCATE_PER_ITEM] + " [truncated]"
    #     feedback_texts.append(text)

    # Build the feedbacks block
    feedbacks_block = "\n\n".join(f"- {t}" for t in feedback_texts)

    # Default prompt: either prompt_override, or prompt_key from prompts, or built-in
    if prompt_override:
        prompt_template = prompt_override
    elif req.prompt_key:
        if req.prompt_key not in prompts:
            raise HTTPException(status_code=404, detail=f"Prompt key '{req.prompt_key}' not found.")
        prompt_template = get_prompt_template(prompts, req.prompt_key)
    else:
        # Use default 'daily_summary' if present; otherwise build a default prompt
        prompt_template = prompts.get("daily_summary") or (
            "You are an assistant analyzing student mess feedback.\n"
            "Date: {date}\n\n"
            "Feedbacks:\n{feedbacks}\n\n"
            "Task:\n1. Summarize the overall sentiment briefly (single sentence).\n"
            "2. List top 3 complaints (short bullet list).\n"
            "3. List top 3 praises (short bullet list), if any.\n"
            "4. Suggest 3 actionable improvements.\n"
            "Format the result as JSON with keys: summary, sentiment, complaints, praises, suggestions.\n"
        )

    # Insert dynamic parts
    prompt = prompt_template.format(
        date=run_date.isoformat(),
        feedbacks=feedbacks_block,
        total=len(feedback_texts)
    )

    # Append extra_instructions if provided
    if req.extra_instructions:
        prompt += f"\n\nAdditional instructions: {req.extra_instructions}"

    # Truncate final prompt if exceeds the maximum
    if len(prompt) > MAX_PROMPT_CHARS:
        logger.warning("Prompt too long, truncating to MAX_PROMPT_CHARS")
        prompt = prompt[:MAX_PROMPT_CHARS] + "\n\n[TRUNCATED]"

    logger.debug("Final prompt length: %d", len(prompt))

    # Call Gemini (wrapped for error handling)
    try:
        model = genai.GenerativeModel(GENAI_MODEL)
        response = model.generate_content(prompt)
        ai_text = getattr(response, "text", None) or str(response)
    except Exception as exc:
        logger.exception("Error calling Gemini API")
        raise HTTPException(status_code=500, detail=f"GenAI API call failed: {str(exc)}")

    # Try to parse JSON out of response if it's JSON-like; else return raw text
    parsed = _try_extract_json(ai_text)

    return {
        "date": run_date.isoformat(),
        "total_feedbacks": len(feedback_texts),
        "prompt_used": prompt_template[:500] + ("..." if len(prompt_template) > 500 else ""),
        "ai_raw": ai_text,
        "analysis": parsed
    }

def _try_extract_json(text: str):
    """
    Many prompts request JSON output. Try to find and parse the first JSON object/array
    in the returned text. If none, return the raw text under 'raw'.
    """
    text = text.strip()
    # quick heuristic: find first '{' or '[' and try to json.loads from there
    start_indices = [i for i, ch in enumerate(text) if ch in ("{", "[")]
    for i in start_indices:
        candidate = text[i:]
        try:
            parsed = json.loads(candidate)
            return parsed
        except Exception:
            # maybe there's extra text after JSON; try to locate matching end by scanning
            try:
                # naive attempt: try progressively larger substrings until parse succeeds
                # limit attempts to avoid infinite loop
                max_len = min(len(candidate), 20000)
                for j in range(100, max_len, 100):
                    try:
                        parsed = json.loads(candidate[:j])
                        return parsed
                    except Exception:
                        continue
            except Exception:
                continue
    # if JSON not found, return as raw text
    return {"raw": text}
