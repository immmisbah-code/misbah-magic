"""
Excel Engine
Reads Bank Statement and QuickBooks Excel/CSV files,
normalises them, then passes to the fuzzy matcher.
"""

import pandas as pd
from .fuzzy_matcher import (
    normalize_amount,
    normalize_description,
    auto_detect_columns,
    match_transactions,
)
from config import config


def _load_file(filepath: str) -> pd.DataFrame:
    """Load Excel or CSV into a DataFrame."""
    ext = filepath.rsplit(".", 1)[-1].lower()
    if ext == "csv":
        df = pd.read_csv(filepath)
    else:
        df = pd.read_excel(filepath, engine="openpyxl")
    df.dropna(how="all", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def _build_records(df: pd.DataFrame) -> list:
    """Convert a DataFrame to list of normalised transaction dicts."""
    cols = auto_detect_columns(df)
    records = []

    for idx, row in df.iterrows():
        raw_date  = row.get(cols["date"])        if cols["date"]        else None
        raw_desc  = row.get(cols["description"]) if cols["description"] else ""
        raw_amt   = row.get(cols["amount"])      if cols["amount"]      else 0

        records.append({
            "index"      : idx,
            "date"       : pd.to_datetime(raw_date, errors="coerce"),
            "description": str(raw_desc).strip() if raw_desc else "",
            "desc_norm"  : normalize_description(raw_desc),
            "amount"     : normalize_amount(raw_amt),
            "matched"    : False,
        })

    return records


def run_excel_reconciliation(bank_path: str, qb_path: str) -> dict:
    """
    Full pipeline for Excel-to-Excel reconciliation.
    Returns reconciliation result dict.
    """
    bank_df = _load_file(bank_path)
    qb_df   = _load_file(qb_path)

    bank_records = _build_records(bank_df)
    qb_records   = _build_records(qb_df)

    result = match_transactions(
        bank_records,
        qb_records,
        amount_tolerance    = config.AMOUNT_TOLERANCE,
        date_tolerance_days = config.DATE_TOLERANCE_DAYS,
        similarity_threshold= config.SIMILARITY_THRESHOLD,
    )
    result["source"] = "excel"
    return result
