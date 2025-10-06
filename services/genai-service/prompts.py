# genai-service/prompts.py
"""
Handles loading prompts mapping from a JSON file. The JSON should be a simple
object mapping keys -> template strings. Template strings may include {feedbacks} and {date}.

Example prompts.json:
{
  "daily_summary": "You are an assistant analyzing feedbacks for {date}...\n{feedbacks}\nTask: ...",
  "safety_check": "..."
}
"""

import json
import logging
from typing import Dict

logger = logging.getLogger("genai-service.prompts")

def load_prompts(path: str) -> Dict[str, str]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            if not isinstance(data, dict):
                logger.warning("prompts.json does not contain an object at top-level; using empty dict.")
                return {}
            return data
    except FileNotFoundError:
        logger.info("prompts file not found at %s — using empty prompts map", path)
        return {}
    except Exception as exc:
        logger.exception("Failed to load prompts: %s", exc)
        return {}

def get_prompt_template(prompts: Dict[str, str], key: str) -> str:
    v = prompts.get(key)
    if v is None:
        raise KeyError(f"Prompt key '{key}' not found")
    return v
