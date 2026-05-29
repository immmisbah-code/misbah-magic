"""
Rules Engine — Magic Cat
IAS / IFRS accounting rules applied before AI inference.
Provides deterministic overrides for well-known transaction patterns.
"""

import re

# ── IAS / IFRS keyword rules ──────────────────────────────────────────
# Each rule: (regex pattern, gl_code, gl_name, statement, ifrs_ref, note)
_RULES: list[tuple] = [
    # ── Fixed Assets (IAS 16 — Property, Plant & Equipment) ─────────
    (r"\b(machinery|equipment|forklift|vehicle|truck|server rack|computer equipment)\b",
     "1500", "Property, Plant & Equipment", "Balance Sheet",
     "IAS 16", "Tangible asset — capitalize if above materiality threshold"),

    # ── Intangible Assets (IAS 38) ───────────────────────────────────
    (r"\b(software license|trademark|patent|goodwill|intangible)\b",
     "1600", "Intangible Assets", "Balance Sheet",
     "IAS 38", "Intangible asset — capitalize if recognition criteria met"),

    # ── Lease / Right-of-Use (IFRS 16) ──────────────────────────────
    (r"\b(lease|rent|right.of.use|rou asset|operating lease)\b",
     "1700", "Right-of-Use Assets", "Balance Sheet",
     "IFRS 16", "Lease — recognize ROU asset and liability"),

    # ── Prepaid Expenses (IAS 1 / accrual basis) ─────────────────────
    (r"\b(prepaid|advance payment|deposit paid|insurance prepaid)\b",
     "1300", "Prepaid Expenses", "Balance Sheet",
     "IAS 1", "Payment before service delivery — record as asset (prepaid)"),

    # ── Inventory (IAS 2) ─────────────────────────────────────────────
    (r"\b(inventory|stock|raw material|goods for resale|merchandise)\b",
     "1200", "Inventory", "Balance Sheet",
     "IAS 2", "Inventory — record at lower of cost or NRV"),

    # ── Revenue (IFRS 15) ─────────────────────────────────────────────
    (r"\b(sales revenue|service revenue|consulting fee received|income received)\b",
     "4000", "Revenue", "P&L",
     "IFRS 15", "Revenue recognized when performance obligation satisfied"),

    # ── Cloud / SaaS Subscriptions ────────────────────────────────────
    (r"\b(aws|amazon web services|azure|google cloud|gcp|digitalocean|cloudflare)\b",
     "6200", "Cloud & Hosting Expense", "P&L",
     "IAS 1", "Period expense — cloud infrastructure / hosting"),

    # ── Software Subscriptions ────────────────────────────────────────
    (r"\b(slack|notion|github|jira|figma|adobe|canva|zoom|dropbox|hubspot|salesforce)\b",
     "6210", "Software Subscription Expense", "P&L",
     "IAS 1", "Period expense — SaaS software subscription"),

    # ── Travel & Entertainment ────────────────────────────────────────
    (r"\b(uber|lyft|taxi|airbnb|hotel|flight|airline|delta|united|southwest|american airlines)\b",
     "6300", "Travel & Entertainment Expense", "P&L",
     "IAS 1", "Business travel — period expense"),

    # ── Meals & Dining ────────────────────────────────────────────────
    (r"\b(restaurant|doordash|grubhub|uber eats|starbucks|mcdonald|chipotle|catering)\b",
     "6310", "Meals & Entertainment Expense", "P&L",
     "IAS 1", "Meals expense — note local deductibility rules"),

    # ── Office Supplies ───────────────────────────────────────────────
    (r"\b(staples|office depot|amazon|printer|stationery|supplies|postage)\b",
     "6400", "Office Supplies Expense", "P&L",
     "IAS 1", "Immaterial supplies — period expense"),

    # ── Utilities ─────────────────────────────────────────────────────
    (r"\b(electricity|water bill|gas bill|utility|con edison|pge|utility bill)\b",
     "6500", "Utilities Expense", "P&L",
     "IAS 1", "Utility cost — period expense on accrual basis"),

    # ── Payroll / Salaries ────────────────────────────────────────────
    (r"\b(payroll|salary|wages|adp|paychex|gusto|compensation)\b",
     "5000", "Salaries & Wages Expense", "P&L",
     "IAS 19", "Employee benefit — recognize in period of service"),

    # ── Marketing & Advertising ───────────────────────────────────────
    (r"\b(facebook ads|google ads|meta ads|advertising|marketing|promotion|pr agency)\b",
     "6600", "Marketing & Advertising Expense", "P&L",
     "IAS 38 / IAS 1", "Marketing — expense as incurred (not capitalized)"),

    # ── Insurance ─────────────────────────────────────────────────────
    (r"\b(insurance premium|liability insurance|health insurance|workers comp)\b",
     "6700", "Insurance Expense", "P&L",
     "IAS 1", "Insurance — expense over coverage period; prepaid if paid in advance"),

    # ── Professional Services ─────────────────────────────────────────
    (r"\b(audit fee|legal fee|consulting|accountant|attorney|lawyer|advisory)\b",
     "6800", "Professional Services Expense", "P&L",
     "IAS 1", "Professional fees — period expense when service rendered"),

    # ── Bank Charges / Interest Expense ───────────────────────────────
    (r"\b(bank fee|service charge|wire fee|bank charge|interest expense|loan interest)\b",
     "7000", "Finance Costs", "P&L",
     "IFRS 9 / IAS 23", "Finance cost — expense in period; capitalize if qualifying asset"),

    # ── Tax Payments ──────────────────────────────────────────────────
    (r"\b(income tax|corporate tax|sales tax|vat|gst|withholding tax|payroll tax)\b",
     "7500", "Tax Expense", "P&L",
     "IAS 12", "Tax — current tax liability; recognize per IAS 12"),

    # ── Loan / Debt Proceeds ──────────────────────────────────────────
    (r"\b(loan proceeds|bank loan|credit line|sba loan|term loan drawdown)\b",
     "2500", "Loans Payable", "Balance Sheet",
     "IFRS 9", "Financial liability — recognize at fair value on initial recognition"),

    # ── Accounts Payable / Vendor Payments ────────────────────────────
    (r"\b(payment to vendor|vendor payment|supplier payment|accounts payable)\b",
     "2000", "Accounts Payable", "Balance Sheet",
     "IAS 1", "Settlement of trade payable — reduce liability"),

    # ── Accounts Receivable / Customer Receipts ───────────────────────
    (r"\b(customer payment|payment received|accounts receivable|invoice payment)\b",
     "1100", "Accounts Receivable", "Balance Sheet",
     "IFRS 15 / IFRS 9", "Collection of receivable — reduce AR balance"),

    # ── Cash & Cash Equivalents ───────────────────────────────────────
    (r"\b(bank transfer|wire transfer|ach transfer|interbank|cash deposit|cash withdrawal)\b",
     "1000", "Cash & Cash Equivalents", "Balance Sheet",
     "IAS 7", "Cash movement — statement of cash flows item"),

    # ── Dividends ─────────────────────────────────────────────────────
    (r"\b(dividend paid|shareholder distribution|equity distribution)\b",
     "3500", "Dividends Paid", "Balance Sheet",
     "IAS 1 / IAS 32", "Distribution to owners — debit equity"),

    # ── R&D Expense ───────────────────────────────────────────────────
    (r"\b(research|development cost|r&d|lab supplies|prototype)\b",
     "6900", "Research & Development Expense", "P&L",
     "IAS 38", "Research — expense; Development — capitalize if criteria met"),
]


def apply_rules(description: str, amount: float) -> dict | None:
    """
    Check description against IAS/IFRS rules.
    Returns the best matching rule dict, or None if no rule matches.
    """
    desc_lower = description.lower()

    for pattern, gl_code, gl_name, statement, ifrs_ref, note in _RULES:
        if re.search(pattern, desc_lower, re.IGNORECASE):
            return {
                "gl_code"  : gl_code,
                "gl_name"  : gl_name,
                "statement": statement,
                "ifrs_ref" : ifrs_ref,
                "note"     : note,
                "source"   : "rules_engine",
            }
    return None


def get_all_rules_summary() -> list[dict]:
    """Return a summary of all built-in rules (for the prompt context)."""
    return [
        {"gl_code": r[1], "gl_name": r[2], "statement": r[3], "ifrs_ref": r[4]}
        for r in _RULES
    ]
