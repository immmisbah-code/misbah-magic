"""
Excel Reconciliation Engine
Handles reading Bank Statement and QuickBooks Excel files,
then reconciles them by matching transactions.
"""

import pandas as pd
from difflib import SequenceMatcher
from datetime import timedelta
import re


def normalize_amount(value):
    """Normalize amount to float, handling currency symbols and commas."""
    if pd.isna(value):
        return 0.0
    s = str(value).strip().replace(',', '').replace('$', '').replace('(', '-').replace(')', '')
    try:
        return round(float(s), 2)
    except ValueError:
        return 0.0


def normalize_description(text):
    """Lowercase, strip extra spaces, remove special chars for comparison."""
    if pd.isna(text):
        return ""
    return re.sub(r'\s+', ' ', str(text).lower().strip())


def similarity_score(a, b):
    """Returns similarity ratio between two strings (0.0 to 1.0)."""
    return SequenceMatcher(None, a, b).ratio()


def detect_columns(df, mode):
    """
    Auto-detect Date, Description, Amount columns from a dataframe.
    mode: 'bank' or 'quickbooks'
    """
    col_map = {"date": None, "description": None, "amount": None}

    date_hints = ['date', 'transaction date', 'trans date', 'posting date']
    desc_hints = ['description', 'memo', 'details', 'narration', 'particulars', 'payee', 'name']
    amount_hints = ['amount', 'credit', 'debit', 'transaction amount', 'net amount']

    cols_lower = {col: col.lower().strip() for col in df.columns}

    for col, col_l in cols_lower.items():
        if any(h in col_l for h in date_hints) and not col_map["date"]:
            col_map["date"] = col
        elif any(h in col_l for h in desc_hints) and not col_map["description"]:
            col_map["description"] = col
        elif any(h in col_l for h in amount_hints) and not col_map["amount"]:
            col_map["amount"] = col

    return col_map


def read_excel_file(filepath, mode='bank'):
    """
    Read an Excel or CSV file and return a normalized DataFrame.
    Returns list of dicts with keys: date, description, amount, raw_row
    """
    try:
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath, engine='openpyxl')
    except Exception as e:
        raise ValueError(f"Could not read file: {e}")

    df.dropna(how='all', inplace=True)
    df.reset_index(drop=True, inplace=True)

    col_map = detect_columns(df, mode)

    records = []
    for idx, row in df.iterrows():
        date_val = row.get(col_map["date"]) if col_map["date"] else None
        desc_val = row.get(col_map["description"]) if col_map["description"] else ""
        amount_val = row.get(col_map["amount"]) if col_map["amount"] else 0.0

        records.append({
            "index": idx,
            "date": pd.to_datetime(date_val, errors='coerce'),
            "description": normalize_description(desc_val),
            "description_raw": str(desc_val),
            "amount": normalize_amount(amount_val),
            "matched": False,
        })

    return records


def reconcile(bank_records, qb_records, amount_tolerance=0.01, date_tolerance_days=3, similarity_threshold=0.6):
    """
    Core reconciliation algorithm.
    Matches bank transactions to QuickBooks transactions.

    Returns:
        matched     - Transactions found in both
        missing_in_qb   - In bank, not in QB
        missing_in_bank - In QB, not in bank
        duplicates  - Duplicate entries detected
        discrepancies - Same description, different amount
    """
    matched = []
    discrepancies = []

    qb_used = [False] * len(qb_records)

    for bank in bank_records:
        best_match = None
        best_score = 0

        for i, qb in enumerate(qb_records):
            if qb_used[i]:
                continue

            # Amount must be within tolerance
            amount_diff = abs(bank["amount"] - qb["amount"])
            if amount_diff > amount_tolerance:
                continue

            # Date proximity check (if both dates are valid)
            date_ok = True
            if pd.notna(bank["date"]) and pd.notna(qb["date"]):
                day_diff = abs((bank["date"] - qb["date"]).days)
                if day_diff > date_tolerance_days:
                    date_ok = False

            if not date_ok:
                continue

            # Description similarity
            score = similarity_score(bank["description"], qb["description"])
            if score > best_score:
                best_score = score
                best_match = (i, qb)

        if best_match and best_score >= similarity_threshold:
            idx, qb = best_match
            qb_used[idx] = True
            bank["matched"] = True
            matched.append({
                "bank_description": bank["description_raw"],
                "qb_description": qb["description_raw"],
                "bank_amount": bank["amount"],
                "qb_amount": qb["amount"],
                "bank_date": bank["date"].strftime("%Y-%m-%d") if pd.notna(bank["date"]) else "",
                "qb_date": qb["date"].strftime("%Y-%m-%d") if pd.notna(qb["date"]) else "",
                "similarity": round(best_score * 100, 1),
            })
        else:
            # Check for discrepancy (same desc, different amount)
            for i, qb in enumerate(qb_records):
                if qb_used[i]:
                    continue
                score = similarity_score(bank["description"], qb["description"])
                if score >= similarity_threshold:
                    discrepancies.append({
                        "bank_description": bank["description_raw"],
                        "qb_description": qb["description_raw"],
                        "bank_amount": bank["amount"],
                        "qb_amount": qb["amount"],
                        "difference": round(abs(bank["amount"] - qb["amount"]), 2),
                        "bank_date": bank["date"].strftime("%Y-%m-%d") if pd.notna(bank["date"]) else "",
                        "qb_date": qb["date"].strftime("%Y-%m-%d") if pd.notna(qb["date"]) else "",
                    })
                    break

    # Missing in QB (in bank but not matched)
    missing_in_qb = [
        {
            "description": b["description_raw"],
            "amount": b["amount"],
            "date": b["date"].strftime("%Y-%m-%d") if pd.notna(b["date"]) else "",
        }
        for b in bank_records if not b["matched"]
    ]

    # Missing in bank (in QB but not matched)
    missing_in_bank = [
        {
            "description": qb_records[i]["description_raw"],
            "amount": qb_records[i]["amount"],
            "date": qb_records[i]["date"].strftime("%Y-%m-%d") if pd.notna(qb_records[i]["date"]) else "",
        }
        for i, used in enumerate(qb_used) if not used
    ]

    # Detect duplicates within bank records
    seen = {}
    duplicates = []
    for b in bank_records:
        key = (round(b["amount"], 2), b["description"])
        if key in seen:
            duplicates.append({
                "description": b["description_raw"],
                "amount": b["amount"],
                "date": b["date"].strftime("%Y-%m-%d") if pd.notna(b["date"]) else "",
            })
        else:
            seen[key] = True

    return {
        "matched": matched,
        "missing_in_qb": missing_in_qb,
        "missing_in_bank": missing_in_bank,
        "duplicates": duplicates,
        "discrepancies": discrepancies,
        "summary": {
            "total_bank": len(bank_records),
            "total_qb": len(qb_records),
            "matched_count": len(matched),
            "missing_in_qb_count": len(missing_in_qb),
            "missing_in_bank_count": len(missing_in_bank),
            "duplicates_count": len(duplicates),
            "discrepancies_count": len(discrepancies),
        }
    }
