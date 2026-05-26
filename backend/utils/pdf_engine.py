"""
AI PDF Engine
Uses Google Gemini Pro Vision to extract transactions from PDF bank statements,
then reconciles them against QuickBooks data.
"""

import os
import json
import base64
import google.generativeai as genai
from .excel_engine import reconcile, read_excel_file, normalize_amount, normalize_description
import pandas as pd


def extract_transactions_from_pdf(pdf_path: str) -> list:
    """
    Send PDF to Gemini Pro Vision and extract transactions as structured JSON.
    Returns list of {date, description, amount} dicts.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in environment variables.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-pro")

    with open(pdf_path, "rb") as f:
        pdf_data = base64.b64encode(f.read()).decode("utf-8")

    prompt = """
You are a financial data extraction expert. Extract ALL transactions from this bank statement PDF.

Return ONLY a valid JSON array with this exact structure:
[
  {
    "date": "YYYY-MM-DD",
    "description": "transaction description",
    "amount": 123.45
  }
]

Rules:
- Credits (money in) are POSITIVE amounts
- Debits (money out) are NEGATIVE amounts
- If you cannot determine sign, use positive
- Use ISO date format (YYYY-MM-DD)
- Do NOT include balance rows
- Do NOT include header rows
- Return ONLY the JSON array, no other text
"""

    response = model.generate_content([
        {"mime_type": "application/pdf", "data": pdf_data},
        prompt
    ])

    text = response.text.strip()

    # Clean up response - extract JSON if wrapped in markdown
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    transactions = json.loads(text)

    # Normalize
    records = []
    for i, t in enumerate(transactions):
        records.append({
            "index": i,
            "date": pd.to_datetime(t.get("date"), errors="coerce"),
            "description": normalize_description(t.get("description", "")),
            "description_raw": str(t.get("description", "")),
            "amount": normalize_amount(t.get("amount", 0)),
            "matched": False,
        })

    return records


def reconcile_pdf_with_qb(pdf_path: str, qb_path: str) -> dict:
    """
    Full pipeline: Extract transactions from PDF using Gemini,
    then reconcile against QuickBooks Excel file.
    """
    bank_records = extract_transactions_from_pdf(pdf_path)
    qb_records = read_excel_file(qb_path, mode="quickbooks")
    result = reconcile(bank_records, qb_records)
    result["source"] = "pdf"
    result["extracted_count"] = len(bank_records)
    return result
