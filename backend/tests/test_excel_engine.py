"""
Tests for modules/reconciliation/excel_engine.py

Run with:  pytest backend/tests/
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock


class TestLoadFile:
    """Test the internal _load_file helper."""

    def test_csv_loads_correctly(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("Date,Description,Amount\n2024-01-01,Test,100.00\n")

        from modules.reconciliation.excel_engine import _load_file
        df = _load_file(str(csv_file))

        assert len(df) == 1
        assert "Date" in df.columns

    def test_drops_all_na_rows(self, tmp_path):
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("Date,Description,Amount\n,,\n2024-01-01,Test,100\n")

        from modules.reconciliation.excel_engine import _load_file
        df = _load_file(str(csv_file))

        assert len(df) == 1


class TestBuildRecords:
    """Test the _build_records normalisation."""

    def test_basic_record_shape(self):
        df = pd.DataFrame({
            "Date": ["2024-01-15"],
            "Description": ["Coffee Shop"],
            "Amount": [12.50],
        })

        from modules.reconciliation.excel_engine import _build_records
        records = _build_records(df)

        assert len(records) == 1
        assert "amount" in records[0]
        assert "desc_norm" in records[0]
        assert records[0]["matched"] is False
