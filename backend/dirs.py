"""
dirs.py — Shared temporary directory handles.
Centralises temp paths so reconciliation and reports modules
don't need to import each other (avoids circular imports).
"""

import tempfile

_UPLOAD_DIR = tempfile.mkdtemp(prefix="misbah_up_")
_REPORT_DIR = tempfile.mkdtemp(prefix="misbah_rp_")


def get_upload_dir() -> str:
    return _UPLOAD_DIR


def get_report_dir() -> str:
    return _REPORT_DIR
