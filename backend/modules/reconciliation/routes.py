"""
Reconciliation Routes
Handles file uploads and triggers the appropriate reconciliation engine.
"""

import os
import uuid
import tempfile
from flask import request, jsonify
from werkzeug.utils import secure_filename

from config import config
from core.dirs import get_upload_dir, get_report_dir
from . import recon_bp
from .excel_engine import run_excel_reconciliation
from .pdf_engine   import run_pdf_reconciliation
from ..reports.generator import generate_excel_report

# Temp directories (managed centrally in dirs.py)
_UPLOAD_DIR = get_upload_dir()
_REPORT_DIR = get_report_dir()


def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in config.ALLOWED_EXTENSIONS


def _save_upload(file_obj) -> str:
    """Save an uploaded file to temp dir; return its path."""
    filename = secure_filename(file_obj.filename)
    unique   = f"{uuid.uuid4().hex}_{filename}"
    path     = os.path.join(_UPLOAD_DIR, unique)
    file_obj.save(path)
    return path


def _cleanup(*paths):
    for p in paths:
        try:
            os.remove(p)
        except OSError:
            pass


# ── Excel endpoint ────────────────────────────────────────────────────

@recon_bp.route("/excel", methods=["POST"])
def reconcile_excel():
    """
    POST /api/reconcile/excel
    form-data: bank_file, qb_file
    """
    bank = request.files.get("bank_file")
    qb   = request.files.get("qb_file")

    if not bank or not qb:
        return jsonify({"error": "Both bank_file and qb_file are required"}), 400
    if not _allowed(bank.filename) or not _allowed(qb.filename):
        return jsonify({"error": "Unsupported file type"}), 415

    bank_path = _save_upload(bank)
    qb_path   = _save_upload(qb)

    try:
        result      = run_excel_reconciliation(bank_path, qb_path)
        report_path = generate_excel_report(result, _REPORT_DIR)
        result["report_filename"] = os.path.basename(report_path)
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        _cleanup(bank_path, qb_path)


# ── PDF endpoint ──────────────────────────────────────────────────────

@recon_bp.route("/pdf", methods=["POST"])
def reconcile_pdf():
    """
    POST /api/reconcile/pdf
    form-data: pdf_file, qb_file
    Requires GEMINI_API_KEY in .env
    """
    if not config.GEMINI_API_KEY:
        return jsonify({"error": "GEMINI_API_KEY is not configured on the server"}), 501

    pdf = request.files.get("pdf_file")
    qb  = request.files.get("qb_file")

    if not pdf or not qb:
        return jsonify({"error": "Both pdf_file and qb_file are required"}), 400

    pdf_path = _save_upload(pdf)
    qb_path  = _save_upload(qb)

    try:
        result      = run_pdf_reconciliation(pdf_path, qb_path)
        report_path = generate_excel_report(result, _REPORT_DIR)
        result["report_filename"] = os.path.basename(report_path)
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        _cleanup(pdf_path, qb_path)


