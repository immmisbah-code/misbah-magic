"""
Fuzzy Matcher
Core matching algorithm: amount tolerance + date proximity + description similarity.
"""

import re
import pandas as pd
from difflib import SequenceMatcher


def normalize_amount(value) -> float:
    """Strip currency symbols/commas and convert to float."""
    if pd.isna(value):
        return 0.0
    cleaned = re.sub(r"[,$£€\s]", "", str(value)).replace("(", "-").replace(")", "")
    try:
        return round(float(cleaned), 2)
    except ValueError:
        return 0.0


def normalize_description(text: str) -> str:
    """Lowercase and collapse whitespace for comparison."""
    if pd.isna(text):
        return ""
    return re.sub(r"\s+", " ", str(text).lower().strip())


def text_similarity(a: str, b: str) -> float:
    """Return similarity ratio [0.0 – 1.0] between two strings."""
    return SequenceMatcher(None, a, b).ratio()


def auto_detect_columns(df: pd.DataFrame) -> dict:
    """
    Heuristically detect Date, Description, and Amount columns.
    Returns {'date': col, 'description': col, 'amount': col}
    """
    date_keywords    = ["date", "trans date", "transaction date", "posting date", "value date"]
    desc_keywords    = ["description", "memo", "narration", "details", "particulars", "payee", "name", "reference"]
    amount_keywords  = ["amount", "credit", "debit", "net amount", "transaction amount", "value"]

    result = {"date": None, "description": None, "amount": None}

    for col in df.columns:
        col_l = col.lower().strip()
        if not result["date"] and any(k in col_l for k in date_keywords):
            result["date"] = col
        elif not result["description"] and any(k in col_l for k in desc_keywords):
            result["description"] = col
        elif not result["amount"] and any(k in col_l for k in amount_keywords):
            result["amount"] = col

    return result


def match_transactions(
    bank: list,
    qb: list,
    amount_tolerance: float = 0.01,
    date_tolerance_days: int = 3,
    similarity_threshold: float = 0.60,
) -> dict:
    """
    Core reconciliation algorithm.

    For each bank transaction, find the best-matching QB transaction by:
      1. Amount within tolerance
      2. Date within N days (if both dates are valid)
      3. Highest description similarity above threshold

    Returns categorised results: matched, missing_in_qb, missing_in_bank,
    duplicates (within bank), discrepancies (desc match but amount differs).
    """
    matched       = []
    discrepancies = []
    qb_consumed   = [False] * len(qb)

    for bank_tx in bank:
        best_idx   = None
        best_score = 0.0

        for i, qb_tx in enumerate(qb):
            if qb_consumed[i]:
                continue

            # ── Amount gate ──────────────────────────────────────
            if abs(bank_tx["amount"] - qb_tx["amount"]) > amount_tolerance:
                continue

            # ── Date gate ────────────────────────────────────────
            b_date = bank_tx.get("date")
            q_date = qb_tx.get("date")
            if pd.notna(b_date) and pd.notna(q_date):
                if abs((b_date - q_date).days) > date_tolerance_days:
                    continue

            # ── Description similarity ───────────────────────────
            score = text_similarity(bank_tx["desc_norm"], qb_tx["desc_norm"])
            if score > best_score:
                best_score = score
                best_idx   = i

        if best_idx is not None and best_score >= similarity_threshold:
            qb_tx = qb[best_idx]
            qb_consumed[best_idx] = True
            bank_tx["matched"] = True
            matched.append({
                "bank_description" : bank_tx["description"],
                "qb_description"   : qb_tx["description"],
                "bank_date"        : _fmt_date(bank_tx["date"]),
                "qb_date"          : _fmt_date(qb_tx["date"]),
                "bank_amount"      : bank_tx["amount"],
                "qb_amount"        : qb_tx["amount"],
                "similarity"       : round(best_score * 100, 1),
            })
        else:
            # Check discrepancy: same description, different amount
            for i, qb_tx in enumerate(qb):
                if qb_consumed[i]:
                    continue
                score = text_similarity(bank_tx["desc_norm"], qb_tx["desc_norm"])
                if score >= similarity_threshold:
                    discrepancies.append({
                        "bank_description" : bank_tx["description"],
                        "qb_description"   : qb_tx["description"],
                        "bank_date"        : _fmt_date(bank_tx["date"]),
                        "qb_date"          : _fmt_date(qb_tx["date"]),
                        "bank_amount"      : bank_tx["amount"],
                        "qb_amount"        : qb_tx["amount"],
                        "difference"       : round(abs(bank_tx["amount"] - qb_tx["amount"]), 2),
                        "similarity"       : round(score * 100, 1),
                    })
                    break

    missing_in_qb   = [_tx_dict(b) for b in bank if not b["matched"]]
    missing_in_bank = [_tx_dict(qb[i]) for i, used in enumerate(qb_consumed) if not used]

    # Detect duplicates within bank records
    seen       = {}
    duplicates = []
    for b in bank:
        key = (b["amount"], b["desc_norm"])
        if key in seen:
            duplicates.append(_tx_dict(b))
        else:
            seen[key] = True

    return {
        "matched"        : matched,
        "missing_in_qb"  : missing_in_qb,
        "missing_in_bank": missing_in_bank,
        "duplicates"     : duplicates,
        "discrepancies"  : discrepancies,
        "summary": {
            "total_bank"           : len(bank),
            "total_qb"             : len(qb),
            "matched_count"        : len(matched),
            "missing_in_qb_count"  : len(missing_in_qb),
            "missing_in_bank_count": len(missing_in_bank),
            "duplicates_count"     : len(duplicates),
            "discrepancies_count"  : len(discrepancies),
        },
    }


# ── Helpers ───────────────────────────────────────────────────────────

def _fmt_date(dt) -> str:
    if pd.isna(dt) or dt is None:
        return ""
    try:
        return pd.Timestamp(dt).strftime("%Y-%m-%d")
    except Exception:
        return str(dt)


def _tx_dict(tx: dict) -> dict:
    return {
        "description": tx["description"],
        "date"       : _fmt_date(tx.get("date")),
        "amount"     : tx["amount"],
    }
