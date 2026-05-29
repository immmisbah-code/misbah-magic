"""
GL Matcher — Magic Cat
Matches transactions to Chart of Accounts (COA) using fuzzy matching
and returns ranked top-3 GL suggestions.
"""

import re
import json
import os
from difflib import SequenceMatcher

from config import config


# ── Default Chart of Accounts (IFRS-aligned) ─────────────────────────
DEFAULT_COA: list[dict] = [
    # Assets
    {"code": "1000", "name": "Cash & Cash Equivalents",       "type": "Asset",   "statement": "Balance Sheet", "ifrs": "IAS 7"},
    {"code": "1100", "name": "Accounts Receivable",           "type": "Asset",   "statement": "Balance Sheet", "ifrs": "IFRS 9"},
    {"code": "1200", "name": "Inventory",                     "type": "Asset",   "statement": "Balance Sheet", "ifrs": "IAS 2"},
    {"code": "1300", "name": "Prepaid Expenses",              "type": "Asset",   "statement": "Balance Sheet", "ifrs": "IAS 1"},
    {"code": "1400", "name": "Other Current Assets",          "type": "Asset",   "statement": "Balance Sheet", "ifrs": "IAS 1"},
    {"code": "1500", "name": "Property, Plant & Equipment",   "type": "Asset",   "statement": "Balance Sheet", "ifrs": "IAS 16"},
    {"code": "1510", "name": "Accumulated Depreciation",      "type": "Asset",   "statement": "Balance Sheet", "ifrs": "IAS 16"},
    {"code": "1600", "name": "Intangible Assets",             "type": "Asset",   "statement": "Balance Sheet", "ifrs": "IAS 38"},
    {"code": "1700", "name": "Right-of-Use Assets",           "type": "Asset",   "statement": "Balance Sheet", "ifrs": "IFRS 16"},
    {"code": "1800", "name": "Long-term Investments",         "type": "Asset",   "statement": "Balance Sheet", "ifrs": "IAS 28"},
    # Liabilities
    {"code": "2000", "name": "Accounts Payable",              "type": "Liability","statement": "Balance Sheet", "ifrs": "IAS 1"},
    {"code": "2100", "name": "Accrued Liabilities",           "type": "Liability","statement": "Balance Sheet", "ifrs": "IAS 37"},
    {"code": "2200", "name": "Deferred Revenue",              "type": "Liability","statement": "Balance Sheet", "ifrs": "IFRS 15"},
    {"code": "2300", "name": "Tax Payable",                   "type": "Liability","statement": "Balance Sheet", "ifrs": "IAS 12"},
    {"code": "2400", "name": "Lease Liability",               "type": "Liability","statement": "Balance Sheet", "ifrs": "IFRS 16"},
    {"code": "2500", "name": "Loans Payable",                 "type": "Liability","statement": "Balance Sheet", "ifrs": "IFRS 9"},
    {"code": "2600", "name": "Other Current Liabilities",     "type": "Liability","statement": "Balance Sheet", "ifrs": "IAS 1"},
    # Equity
    {"code": "3000", "name": "Share Capital",                 "type": "Equity",  "statement": "Balance Sheet", "ifrs": "IAS 1"},
    {"code": "3100", "name": "Retained Earnings",             "type": "Equity",  "statement": "Balance Sheet", "ifrs": "IAS 1"},
    {"code": "3200", "name": "Additional Paid-in Capital",    "type": "Equity",  "statement": "Balance Sheet", "ifrs": "IAS 1"},
    {"code": "3500", "name": "Dividends Paid",                "type": "Equity",  "statement": "Balance Sheet", "ifrs": "IAS 32"},
    # Revenue
    {"code": "4000", "name": "Revenue",                       "type": "Revenue", "statement": "P&L",           "ifrs": "IFRS 15"},
    {"code": "4100", "name": "Service Revenue",               "type": "Revenue", "statement": "P&L",           "ifrs": "IFRS 15"},
    {"code": "4200", "name": "Other Income",                  "type": "Revenue", "statement": "P&L",           "ifrs": "IAS 1"},
    # Cost of Sales
    {"code": "5000", "name": "Salaries & Wages Expense",      "type": "Expense", "statement": "P&L",           "ifrs": "IAS 19"},
    {"code": "5100", "name": "Cost of Goods Sold",            "type": "Expense", "statement": "P&L",           "ifrs": "IAS 2"},
    {"code": "5200", "name": "Direct Labor",                  "type": "Expense", "statement": "P&L",           "ifrs": "IAS 19"},
    # Operating Expenses
    {"code": "6100", "name": "Depreciation Expense",          "type": "Expense", "statement": "P&L",           "ifrs": "IAS 16"},
    {"code": "6200", "name": "Cloud & Hosting Expense",       "type": "Expense", "statement": "P&L",           "ifrs": "IAS 1"},
    {"code": "6210", "name": "Software Subscription Expense", "type": "Expense", "statement": "P&L",           "ifrs": "IAS 1"},
    {"code": "6300", "name": "Travel & Entertainment Expense","type": "Expense", "statement": "P&L",           "ifrs": "IAS 1"},
    {"code": "6310", "name": "Meals & Entertainment Expense", "type": "Expense", "statement": "P&L",           "ifrs": "IAS 1"},
    {"code": "6400", "name": "Office Supplies Expense",       "type": "Expense", "statement": "P&L",           "ifrs": "IAS 1"},
    {"code": "6500", "name": "Utilities Expense",             "type": "Expense", "statement": "P&L",           "ifrs": "IAS 1"},
    {"code": "6600", "name": "Marketing & Advertising Expense","type": "Expense","statement": "P&L",           "ifrs": "IAS 38 / IAS 1"},
    {"code": "6700", "name": "Insurance Expense",             "type": "Expense", "statement": "P&L",           "ifrs": "IAS 1"},
    {"code": "6800", "name": "Professional Services Expense", "type": "Expense", "statement": "P&L",           "ifrs": "IAS 1"},
    {"code": "6900", "name": "Research & Development Expense","type": "Expense", "statement": "P&L",           "ifrs": "IAS 38"},
    {"code": "6950", "name": "General & Administrative Expense","type": "Expense","statement": "P&L",          "ifrs": "IAS 1"},
    # Finance Costs
    {"code": "7000", "name": "Finance Costs",                 "type": "Expense", "statement": "P&L",           "ifrs": "IFRS 9 / IAS 23"},
    {"code": "7100", "name": "Gain on Disposal",              "type": "Revenue", "statement": "P&L",           "ifrs": "IAS 16"},
    {"code": "7200", "name": "Loss on Disposal",              "type": "Expense", "statement": "P&L",           "ifrs": "IAS 16"},
    {"code": "7500", "name": "Tax Expense",                   "type": "Expense", "statement": "P&L",           "ifrs": "IAS 12"},
    {"code": "9999", "name": "Suspense / Unclassified",       "type": "Other",   "statement": "Balance Sheet", "ifrs": "IAS 1"},
]


def load_coa() -> list[dict]:
    """Load COA: company-uploaded file if present, else default."""
    path = config.COA_PATH
    if path and os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            pass
    return DEFAULT_COA


def save_coa(accounts: list[dict]) -> None:
    """Persist a custom COA."""
    path = config.COA_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(accounts, fh, indent=2)


def _score(description: str, amount: float, account: dict) -> float:
    """Score how well a transaction matches a GL account."""
    desc_lower = description.lower()
    name_lower = account["name"].lower()

    # Text similarity between transaction description and GL name
    text_sim = SequenceMatcher(None, desc_lower, name_lower).ratio()

    # Keyword overlap bonus
    desc_words = set(re.findall(r"\b\w{3,}\b", desc_lower))
    name_words = set(re.findall(r"\b\w{3,}\b", name_lower))
    overlap = len(desc_words & name_words) / max(len(name_words), 1)

    # Amount heuristic: large amounts (>2500) lean toward Balance Sheet items
    amount_hint = 0.0
    if abs(amount) > 2500 and account["statement"] == "Balance Sheet":
        amount_hint = 0.05
    elif abs(amount) <= 2500 and account["statement"] == "P&L":
        amount_hint = 0.05

    return (text_sim * 0.5) + (overlap * 0.4) + amount_hint


def get_top3_gl(description: str, amount: float,
                hint_code: str | None = None) -> list[dict]:
    """
    Return top-3 ranked GL suggestions for a transaction.
    If hint_code is provided (from rules engine / memory), boost that account.
    """
    coa = load_coa()
    scored = []

    for account in coa:
        score = _score(description, amount, account)
        # Boost the hinted GL to always be #1
        if hint_code and account["code"] == hint_code:
            score += 0.5
        scored.append((score, account))

    scored.sort(key=lambda x: x[0], reverse=True)
    top3 = [
        {**acc, "match_score": round(score, 3)}
        for score, acc in scored[:3]
    ]
    return top3


def find_by_code(code: str) -> dict | None:
    """Look up a GL account by its code."""
    for acc in load_coa():
        if acc["code"] == code:
            return acc
    return None
