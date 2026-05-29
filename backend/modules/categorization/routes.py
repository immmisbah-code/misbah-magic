"""
Categorization Routes — Magic Cat
Handles all API endpoints for the AI categorization module.
"""

import os
import uuid
import json
from flask import request, jsonify, send_file
from werkzeug.utils import secure_filename

from config       import config
from core.dirs    import get_upload_dir
from . import cat_bp
from .service     import (
    load_transactions_from_file,
    categorize_transaction,
    categorize_batch,
)
from .memory_store import record_approval, get_recent_history, get_override_patterns
from .gl_matcher   import load_coa, save_coa

_UPLOAD_DIR = get_upload_dir()


def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"xlsx", "xls", "csv"}


def _save_upload(file_obj) -> str:
    filename = secure_filename(file_obj.filename)
    unique   = f"{uuid.uuid4().hex}_{filename}"
    path     = os.path.join(_UPLOAD_DIR, unique)
    file_obj.save(path)
    return path


# ── Batch upload + categorize ─────────────────────────────────────────

@cat_bp.route("/upload", methods=["POST"])
def upload_and_categorize():
    """
    POST /api/categorize/upload
    form-data: transactions_file (CSV or Excel)
    optional JSON param: use_ai=true/false
    """
    f = request.files.get("transactions_file")
    if not f:
        return jsonify({"error": "transactions_file is required"}), 400
    if not _allowed(f.filename):
        return jsonify({"error": "Only CSV, XLS, XLSX files are supported"}), 415

    use_ai  = request.form.get("use_ai", "true").lower() == "true"
    path    = _save_upload(f)

    try:
        transactions = load_transactions_from_file(path)
        if not transactions:
            return jsonify({"error": "No valid transactions found in file"}), 422

        result = categorize_batch(transactions, use_ai=use_ai)
        return jsonify(result)

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


# ── Single manual transaction ─────────────────────────────────────────

@cat_bp.route("/single", methods=["POST"])
def categorize_single():
    """
    POST /api/categorize/single
    JSON body: { date, description, amount, currency? }
    """
    data = request.get_json(silent=True) or {}

    if not data.get("description") or data.get("amount") is None:
        return jsonify({"error": "description and amount are required"}), 400

    transaction = {
        "id"         : str(uuid.uuid4()),
        "date"       : data.get("date", ""),
        "description": str(data["description"]).strip(),
        "amount"     : float(data["amount"]),
        "currency"   : data.get("currency", "USD"),
    }

    use_ai = data.get("use_ai", True)
    try:
        result = categorize_transaction(transaction, use_ai=use_ai)
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ── Approve / Override ────────────────────────────────────────────────

@cat_bp.route("/approve", methods=["POST"])
def approve():
    """
    POST /api/categorize/approve
    JSON body: { transaction, selected_gl, overridden }
    Records the decision into the memory store so the AI learns.
    """
    data = request.get_json(silent=True) or {}
    tx          = data.get("transaction")
    selected_gl = data.get("selected_gl")
    overridden  = bool(data.get("overridden", False))

    if not tx or not selected_gl:
        return jsonify({"error": "transaction and selected_gl are required"}), 400

    try:
        record_approval(tx, selected_gl, overridden=overridden)
        return jsonify({"success": True, "message": "Transaction approved and memory updated."})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ── Bulk approve ──────────────────────────────────────────────────────

@cat_bp.route("/approve/bulk", methods=["POST"])
def approve_bulk():
    """
    POST /api/categorize/approve/bulk
    JSON body: { approvals: [{ transaction, selected_gl, overridden }, ...] }
    """
    data      = request.get_json(silent=True) or {}
    approvals = data.get("approvals", [])

    if not approvals:
        return jsonify({"error": "approvals list is required"}), 400

    saved = 0
    errors = []
    for item in approvals:
        try:
            record_approval(
                item["transaction"],
                item["selected_gl"],
                overridden=item.get("overridden", False),
            )
            saved += 1
        except Exception as exc:
            errors.append(str(exc))

    return jsonify({"saved": saved, "errors": errors})


# ── History ───────────────────────────────────────────────────────────

@cat_bp.route("/history", methods=["GET"])
def history():
    """GET /api/categorize/history?limit=200"""
    limit = int(request.args.get("limit", 200))
    return jsonify({"history": get_recent_history(limit)})


# ── Overrides ─────────────────────────────────────────────────────────

@cat_bp.route("/overrides", methods=["GET"])
def overrides():
    """GET /api/categorize/overrides — human override patterns for review."""
    return jsonify({"overrides": get_override_patterns()})


# ── Chart of Accounts ─────────────────────────────────────────────────

@cat_bp.route("/coa", methods=["GET"])
def get_coa():
    """GET /api/categorize/coa"""
    return jsonify({"coa": load_coa()})


@cat_bp.route("/coa", methods=["POST"])
def update_coa():
    """
    POST /api/categorize/coa
    JSON body: { accounts: [...] }
    """
    data     = request.get_json(silent=True) or {}
    accounts = data.get("accounts", [])
    if not accounts:
        return jsonify({"error": "accounts array is required"}), 400
    try:
        save_coa(accounts)
        return jsonify({"success": True, "count": len(accounts)})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500
