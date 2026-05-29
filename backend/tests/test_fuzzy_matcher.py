"""
Tests for modules/reconciliation/fuzzy_matcher.py

Run with:  pytest backend/tests/
"""

import pytest
from modules.reconciliation.fuzzy_matcher import (
    normalize_amount,
    normalize_description,
)


class TestNormalizeAmount:
    def test_positive_number(self):
        assert normalize_amount(100.0) == 100.0

    def test_string_with_dollar(self):
        assert normalize_amount("$1,234.56") == 1234.56

    def test_negative_becomes_absolute(self):
        # Debits stored as negatives should still match
        assert normalize_amount(-500.0) == 500.0

    def test_zero(self):
        assert normalize_amount(0) == 0.0

    def test_none_returns_zero(self):
        assert normalize_amount(None) == 0.0


class TestNormalizeDescription:
    def test_lowercase(self):
        result = normalize_description("AMAZON PRIME")
        assert result == result.lower()

    def test_strips_whitespace(self):
        assert normalize_description("  PayPal  ") == normalize_description("PayPal")

    def test_empty_string(self):
        assert normalize_description("") == ""

    def test_none(self):
        assert normalize_description(None) == ""
