"""
AI Engine — Magic Cat
Uses Google Gemini to provide CPA-level transaction categorization.
Falls back to rules + fuzzy matching if Gemini is unavailable.
"""

import json
from config import config
from .gl_matcher import get_top3_gl, DEFAULT_COA


_SYSTEM_PROMPT = """
You are a Senior CPA and IFRS/IAS accounting expert embedded in an AI accounting engine.

Your task: Categorize a financial transaction with full CPA-level reasoning.

Instructions:
1. Analyze the transaction description, amount, and date carefully.
2. Apply the correct IAS/IFRS standard.
3. Select the PRIMARY GL account from the provided Chart of Accounts.
4. Provide exactly 3 ranked GL alternatives (including the primary as #1).
5. Determine if this is a P&L or Balance Sheet item.
6. Assign a Confidence Score (0-100).
7. Write a CPA-level reasoning explanation (2-4 sentences).
8. Assign a Risk Level: Low, Medium, or High.
9. NEVER hallucinate. If uncertain, say so and lower confidence.
10. Follow accrual basis accounting at all times.

Key Rules:
- Large capital expenditures (>company threshold) → Balance Sheet asset, not P&L
- Recurring vendor payments (AWS, Slack, etc.) → Operating expense P&L
- Prepayments → Asset until benefit consumed
- Tax components → Separate from expense; apply IAS 12
- Always cite the specific IAS/IFRS standard number

Return ONLY valid JSON, no markdown, no commentary:
{
  "primary_gl_code": "XXXX",
  "primary_gl_name": "...",
  "statement": "P&L | Balance Sheet",
  "ifrs_reference": "IAS/IFRS XX — Title",
  "confidence": 0-100,
  "reasoning": "CPA-level explanation in 2-4 sentences.",
  "risk_level": "Low | Medium | High",
  "risk_notes": "Why this risk level was assigned.",
  "top3_alternatives": [
    {"rank": 1, "gl_code": "XXXX", "gl_name": "...", "reason": "..."},
    {"rank": 2, "gl_code": "XXXX", "gl_name": "...", "reason": "..."},
    {"rank": 3, "gl_code": "XXXX", "gl_name": "...", "reason": "..."}
  ],
  "accrual_note": "Any accrual/prepaid treatment note or null.",
  "tax_note": "Any tax/VAT treatment note or null."
}
"""


def _build_context(transaction: dict, top3_gl: list, vendor_history: dict | None,
                   recent_history: list) -> str:
    """Build the full prompt context for Gemini."""
    coa_summary = "\n".join(
        f"  {a['code']} — {a['name']} ({a['statement']}, {a['ifrs']})"
        for a in DEFAULT_COA[:30]  # Send first 30 accounts to save tokens
    )

    history_ctx = ""
    if vendor_history:
        top_gl = max(vendor_history, key=lambda k: vendor_history[k])
        history_ctx = f"\nCompany Memory: This vendor was previously coded to GL {top_gl} ({vendor_history[top_gl]} times)."

    top3_ctx = "\n".join(
        f"  #{i+1}: {g['code']} — {g['name']} ({g['statement']})"
        for i, g in enumerate(top3_gl)
    )

    return f"""
TRANSACTION:
  Date: {transaction.get('date', 'Unknown')}
  Description: {transaction.get('description', '')}
  Amount: {transaction.get('amount', 0):.2f} USD
  {'(CREDIT/INCOME — positive)' if float(transaction.get('amount', 0)) > 0 else '(DEBIT/EXPENSE — negative)'}

CHART OF ACCOUNTS (partial):
{coa_summary}

TOP-3 GL CANDIDATES (from fuzzy matching):
{top3_ctx}
{history_ctx}

MATERIALITY THRESHOLD: {config.MATERIALITY_THRESHOLD} USD
(Amounts above this threshold may require asset capitalization instead of expense treatment.)

Categorize this transaction following all IAS/IFRS rules.
"""


def categorize_with_ai(transaction: dict, top3_gl: list,
                       vendor_history: dict | None = None,
                       recent_history: list | None = None) -> dict:
    """
    Call Gemini to categorize a transaction.
    Returns the AI result dict or raises RuntimeError.
    """
    if not config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not configured — AI categorization unavailable.")

    try:
        import google.generativeai as genai
    except (ImportError, TypeError) as exc:
        raise RuntimeError(f"google-generativeai unavailable: {exc}")

    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-pro")

    context = _build_context(
        transaction,
        top3_gl,
        vendor_history,
        recent_history or [],
    )

    response = model.generate_content([_SYSTEM_PROMPT, context])
    raw = response.text.strip()

    # Strip markdown fences
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.split("```")[0].strip()

    return json.loads(raw)


def categorize_with_rules_fallback(transaction: dict, rules_hit: dict | None,
                                   top3_gl: list) -> dict:
    """
    Fallback categorizer (no AI): uses rules engine + GL fuzzy match.
    Returns a structured result similar to the AI output.
    """
    primary = rules_hit or (top3_gl[0] if top3_gl else {})

    gl_code = primary.get("gl_code") or primary.get("code", "9999")
    gl_name = primary.get("gl_name") or primary.get("name", "Suspense / Unclassified")
    statement = primary.get("statement", "P&L")
    ifrs_ref = primary.get("ifrs_ref") or primary.get("ifrs", "IAS 1")
    note = primary.get("note", "")

    confidence = 75 if rules_hit else 45

    alts = []
    for i, g in enumerate(top3_gl[:3]):
        alts.append({
            "rank"   : i + 1,
            "gl_code": g.get("code", g.get("gl_code", "")),
            "gl_name": g.get("name", g.get("gl_name", "")),
            "reason" : "Fuzzy match on description keywords",
        })

    return {
        "primary_gl_code"  : gl_code,
        "primary_gl_name"  : gl_name,
        "statement"        : statement,
        "ifrs_reference"   : f"{ifrs_ref} — Rules Engine Match",
        "confidence"       : confidence,
        "reasoning"        : (
            f"Transaction matched via built-in IAS/IFRS rules engine. {note} "
            "AI categorization unavailable (no API key or quota exceeded)."
        ),
        "risk_level"       : "Medium",
        "risk_notes"       : "No AI validation — rules-only match. Human review recommended.",
        "top3_alternatives": alts,
        "accrual_note"     : None,
        "tax_note"         : None,
        "source"           : "rules_fallback",
    }
