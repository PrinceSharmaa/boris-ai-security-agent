import re
from fastapi import Header, HTTPException
from backend.config import settings

ATTACKS = [r"ignore (all )?(previous|prior) instructions", r"reveal (your )?(system|developer) prompt", r"you are now (the )?system", r"disable (all )?guardrails"]

def check_input(query: str) -> str:
    if not query.strip() or len(query) > 12000:
        raise ValueError("Query must be between 1 and 12000 characters")
    if any(re.search(p, query, re.I) for p in ATTACKS):
        raise ValueError("Instruction override attempt detected")
    return query.strip()

def verify_key(x_api_key: str | None = Header(default=None)) -> None:
    if x_api_key != settings.boris_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
