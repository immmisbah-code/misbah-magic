"""
Categorization Service — Magic Cat
Main orchestration layer.
Connects: data ingestion → rules → memory → GL matching → AI → output assembly.
"""

import re
import uuid
import pandas as pd
from datetime import datetime

from .rules_engine  import apply_rules
from .gl_matcher    import get_top3_gl
from .memory_store  import get_vendor_history, top_vendor_gl, get_recent_history, _vendor_key
from .ai_engine     import categorize_with_ai, categorize_with_rules_fallback
from config         import config


# ── Decision Weight Constants (per spec) ─────────────────────────────
W_IFRS     = 0.40
W_HISTORY  = 0.35
W_DESC     = 0.15
W_AMOUNT   = 0.10


# ── Input Normalisation ───────────────────────────────────────────────

def _normalise_amount(value) -> float:
    if pd.isna(value):
        return 0.0
    cleaned = re.sub(r"[,$£€\s]", "", str(value)).replace("(", "-").replace(")", "")
    try:
        return round(float(cleaned), 2)
    except ValueError:
        return 0.0


def _normalise_description(text) -> str:
    if not text or (isinstance(text, float) and pd.isna(text)):
        return ""
    return re.sub(r"\s+", " ", str(text).strip())


def load_transactions_from_file(filepath: str) -> list[dict]:
    """
    Load CSV or Excel file and return list of raw transaction dicts.
    Auto-detects date, description, amount columns.
    """
    ext = filepath.rsplit(".", 1)[-1].lower()
    if ext == "csv":
        df = pd.read_csv(filepath)
    else:
        df = pd.read_excel(filepath, engine="openpyxl")

    df.dropna(how="all", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Auto-detect columns
    date_kw   = ["date", "trans date", "transaction date", "posting date"]
    desc_kw   = ["description", "memo", "narration", "details", "particulars", "payee", "name"]
    amount_kw = ["amount", "credit", "debit", "net amount", "value", "transaction amount"]

    cols = {"date": None, "description": None, "amount": None}
    for col in df.columns:
        cl = col.lower().strip()
        if not cols["date"]        and any(k in cl for k in date_kw):
            cols["date"] = col
        elif not cols["description"] and any(k in cl for k in desc_kw):
            cols["description"] = col
        elif not cols["amount"]      and any(k in cl for k in amount_kw):
            cols["amount"] = col

    transactions = []
    for _, row in df.iterrows():
        transactions.append({
            "id"         : str(uuid.uuid4()),
            "date"       : str(pd.to_datetime(row.get(cols["date"]), errors="coerce").date())
                           if cols["date"] else str(datetime.utcnow().date()),
            "description": _normalise_description(row.get(cols["description"], "")),
            "amount"     : _normalise_amount(row.get(cols["amount"], 0)),
            "currency"   : "USD",
        })

    return [t for t in transactions if t["description"]]


# ── Core Categorization Pipeline ──────────────────────────────────────

def categorize_transaction(transaction: dict, use_ai: bool = True) -> dict:
    """
    Full 7-layer categorization pipeline for a single transaction.

    Layer 1: Data is already normalized by the caller.
    Layer 2: NLP vendor extraction (via memory key).
    Layer 3: IAS/IFRS rules engine.
    Layer 4: Company memory check.
    Layer 5: GL fuzzy matching.
    Layer 6: AI decision (Gemini) or rules fallback.
    Layer 7: Assemble final output.
    """
    desc   = transaction["description"]
    amount = float(transaction.get("amount", 0))

    # ── Layer 3: Rules Engine ─────────────────────────────────────────
    rules_hit = apply_rules(desc, amount)
    hint_code = rules_hit["gl_code"] if rules_hit else None

    # ── Layer 4: Company Memory ───────────────────────────────────────
    vendor_key     = _vendor_key(desc)
    vendor_history = get_vendor_history(vendor_key)
    memory_gl      = top_vendor_gl(vendor_key)

    # Memory overrides the hint if it exists (company history > rules)
    if memory_gl:
        hint_code = memory_gl

    # ── Layer 5: GL Fuzzy Matching ────────────────────────────────────
    top3 = get_top3_gl(desc, amount, hint_code=hint_code)

    # ── Layer 6: AI or Fallback ───────────────────────────────────────
    ai_result = None
    if use_ai and config.GEMINI_API_KEY:
        try:
            ai_result = categorize_with_ai(
                transaction,
                top3,
                vendor_history=vendor_history,
                recent_history=get_recent_history(50),
            )
            ai_result["source"] = "gemini_ai"
        except Exception as exc:
            ai_result = None
            fallback_note = str(exc)

    if not ai_result:
        ai_result = categorize_with_rules_fallback(transaction, rules_hit, top3)

    # ── Layer 7: Final Output Assembly ───────────────────────────────
    # Blend confidence: IFRS rule match boosts score
    raw_confidence  = int(ai_result.get("confidence", 50))
    if rules_hit:
        raw_confidence = min(100, raw_confidence + 10)
    if memory_gl and memory_gl == ai_result.get("primary_gl_code"):
        raw_confidence = min(100, raw_confidence + 10)

    return {
        # Transaction identity
        "id"                : transaction.get("id", str(uuid.uuid4())),
        "date"              : transaction.get("date", ""),
        "description"       : desc,
        "amount"            : amount,
        "currency"          : transaction.get("currency", "USD"),
        # GL Result
        "selected_gl_code"  : ai_result.get("primary_gl_code", "9999"),
        "selected_gl_name"  : ai_result.get("primary_gl_name", "Suspense / Unclassified"),
        "statement"         : ai_result.get("statement", "P&L"),
        "ifrs_reference"    : ai_result.get("ifrs_reference", "IAS 1"),
        # Intelligence
        "confidence"        : raw_confidence,
        "reasoning"         : ai_result.get("reasoning", ""),
        "risk_level"        : ai_result.get("risk_level", "Medium"),
        "risk_notes"        : ai_result.get("risk_notes", ""),
        "accrual_note"      : ai_result.get("accrual_note"),
        "tax_note"          : ai_result.get("tax_note"),
        # Suggestions
        "top3_gl"           : ai_result.get("top3_alternatives", []),
        # Context
        "rules_hit"         : rules_hit is not None,
        "memory_hit"        : memory_gl is not None,
        "source"            : ai_result.get("source", "unknown"),
        # Workflow
        "status"            : "Pending Approval",
        "human_override"    : False,
        "approved_gl"       : None,
    }


def categorize_batch(transactions: list[dict], use_ai: bool = True) -> dict:
    """
    Categorize a list of transactions.
    Returns summary + full results.
    """
    results = []
    errors  = []

    for tx in transactions:
        try:
            result = categorize_transaction(tx, use_ai=use_ai)
            results.append(result)
        except Exception as exc:
            errors.append({"id": tx.get("id", "?"), "error": str(exc)})

    # Summary stats
    high_risk  = sum(1 for r in results if r["risk_level"] == "High")
    med_risk   = sum(1 for r in results if r["risk_level"] == "Medium")
    low_risk   = sum(1 for r in results if r["risk_level"] == "Low")
    avg_conf   = round(sum(r["confidence"] for r in results) / len(results), 1) if results else 0
    ai_used    = sum(1 for r in results if r["source"] == "gemini_ai")
    rules_used = sum(1 for r in results if r["source"] in ("rules_fallback", "rules_engine"))

    return {
        "total"        : len(transactions),
        "categorized"  : len(results),
        "errors"       : len(errors),
        "error_details": errors,
        "summary"      : {
            "avg_confidence" : avg_conf,
            "high_risk"      : high_risk,
            "medium_risk"    : med_risk,
            "low_risk"       : low_risk,
            "ai_categorized" : ai_used,
            "rules_fallback" : rules_used,
        },
        "results"      : results,
    }
