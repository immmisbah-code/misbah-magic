"""
PDF Engine
Uses Google Gemini 1.5 Pro to extract transactions from PDF bank statements,
then reconciles them against a QuickBooks file.

Note: google-generativeai is imported lazily (inside the function) because
it is not compatible with Python 3.14. Excel mode works without it.
"""

import json
import base64
import pandas as pd

from config import config
from .fuzzy_matcher import normalize_amount, normalize_description, match_transactions
from .excel_engine import _load_file, _build_records


# ── Gemini extraction ─────────────────────────────────────────────────

_EXTRACTION_PROMPT = """
You are a precise financial data extraction assistant.
Extract EVERY transaction from this bank statement PDF.

Return ONLY a valid JSON array — no markdown, no commentary:
[
  { "date": "YYYY-MM-DD", "description": "...", "amount": 0.00 }
]

Rules:
- Credits / deposits  → POSITIVE amounts
- Debits / withdrawals → NEGATIVE amounts
- Use ISO 8601 date format (YYYY-MM-DD)
- Skip balance, header, and footer rows
- If a field is missing, use null for date or 0 for amount
"""


def extract_pdf_transactions(pdf_path: str) -> list:
    """Send PDF to Gemini and return normalised transaction records."""
    if not config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in .env")

    # Lazy import — google-generativeai not compatible with Python 3.14
    try:
        import google.generativeai as genai
    except (ImportError, TypeError) as exc:
        raise RuntimeError(
            "google-generativeai is not compatible with your Python version "
            f"({exc}). Use Excel mode instead, or install Python 3.11/3.12."
        )

    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-pro")

    with open(pdf_path, "rb") as fh:
        pdf_b64 = base64.b64encode(fh.read()).decode("utf-8")

    response = model.generate_content([
        {"mime_type": "application/pdf", "data": pdf_b64},
        _EXTRACTION_PROMPT,
    ])

    raw = response.text.strip()

    # Strip markdown fences if present
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.split("```")[0].strip()

    transactions = json.loads(raw)

    records = []
    for i, tx in enumerate(transactions):
        raw_date = tx.get("date")
        raw_desc = tx.get("description", "")
        raw_amt  = tx.get("amount", 0)
        records.append({
            "index"      : i,
            "date"       : pd.to_datetime(raw_date, errors="coerce"),
            "description": str(raw_desc).strip(),
            "desc_norm"  : normalize_description(raw_desc),
            "amount"     : normalize_amount(raw_amt),
            "matched"    : False,
        })

    return records


def run_pdf_reconciliation(pdf_path: str, qb_path: str) -> dict:
    """Full pipeline: PDF → Gemini → reconcile vs QuickBooks Excel."""
    bank_records = extract_pdf_transactions(pdf_path)
    qb_records   = _build_records(_load_file(qb_path))

    result = match_transactions(
        bank_records,
        qb_records,
        amount_tolerance     = config.AMOUNT_TOLERANCE,
        date_tolerance_days  = config.DATE_TOLERANCE_DAYS,
        similarity_threshold = config.SIMILARITY_THRESHOLD,
    )
    result["source"]          = "pdf"
    result["extracted_count"] = len(bank_records)
    return result
