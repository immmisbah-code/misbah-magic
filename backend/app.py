"""
Misbah's Magic — Flask Backend Server
Professional Bank & QuickBooks Reconciliation Tool
"""

import os
import uuid
import tempfile
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from utils.excel_engine import read_excel_file, reconcile
from utils.report_generator import generate_report

load_dotenv()

app = Flask(__name__)
CORS(app)

# Temp directory for uploaded files and generated reports
UPLOAD_DIR = tempfile.mkdtemp(prefix="misbah_uploads_")
REPORT_DIR = tempfile.mkdtemp(prefix="misbah_reports_")

# Simple access password (set in .env)
ACCESS_PASSWORD = os.getenv("ACCESS_PASSWORD", "misbah2024")


# ── Auth ──────────────────────────────────────────────────────────

@app.route("/api/auth/verify", methods=["POST"])
def verify_password():
    data = request.get_json()
    if data and data.get("password") == ACCESS_PASSWORD:
        return jsonify({"success": True, "token": "authenticated"})
    return jsonify({"success": False, "message": "Incorrect password"}), 401


# ── Excel Reconciliation ──────────────────────────────────────────

@app.route("/api/reconcile/excel", methods=["POST"])
def reconcile_excel():
    """
    Endpoint: POST /api/reconcile/excel
    Form data: bank_file (Excel/CSV), qb_file (Excel/CSV)
    Returns: reconciliation result as JSON
    """
    if "bank_file" not in request.files or "qb_file" not in request.files:
        return jsonify({"error": "Both bank_file and qb_file are required"}), 400

    bank_file = request.files["bank_file"]
    qb_file   = request.files["qb_file"]

    # Save uploaded files temporarily
    bank_ext = os.path.splitext(bank_file.filename)[1]
    qb_ext   = os.path.splitext(qb_file.filename)[1]

    bank_path = os.path.join(UPLOAD_DIR, f"bank_{uuid.uuid4().hex}{bank_ext}")
    qb_path   = os.path.join(UPLOAD_DIR, f"qb_{uuid.uuid4().hex}{qb_ext}")

    bank_file.save(bank_path)
    qb_file.save(qb_path)

    try:
        bank_records = read_excel_file(bank_path, mode="bank")
        qb_records   = read_excel_file(qb_path,   mode="quickbooks")
        result = reconcile(bank_records, qb_records)
        result["source"] = "excel"

        # Generate report
        report_path = generate_report(result, REPORT_DIR)
        report_name = os.path.basename(report_path)
        result["report_filename"] = report_name

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        # Clean up uploaded files
        for path in [bank_path, qb_path]:
            try:
                os.remove(path)
            except Exception:
                pass


# ── PDF Reconciliation ────────────────────────────────────────────

@app.route("/api/reconcile/pdf", methods=["POST"])
def reconcile_pdf():
    """
    Endpoint: POST /api/reconcile/pdf
    Form data: pdf_file (PDF bank statement), qb_file (Excel)
    Uses Gemini AI to extract transactions from PDF.
    """
    if "pdf_file" not in request.files or "qb_file" not in request.files:
        return jsonify({"error": "Both pdf_file and qb_file are required"}), 400

    if not os.getenv("GEMINI_API_KEY"):
        return jsonify({"error": "GEMINI_API_KEY not configured on server"}), 500

    pdf_file = request.files["pdf_file"]
    qb_file  = request.files["qb_file"]

    pdf_path = os.path.join(UPLOAD_DIR, f"pdf_{uuid.uuid4().hex}.pdf")
    qb_ext   = os.path.splitext(qb_file.filename)[1]
    qb_path  = os.path.join(UPLOAD_DIR, f"qb_{uuid.uuid4().hex}{qb_ext}")

    pdf_file.save(pdf_path)
    qb_file.save(qb_path)

    try:
        from utils.pdf_engine import reconcile_pdf_with_qb
        result = reconcile_pdf_with_qb(pdf_path, qb_path)

        report_path = generate_report(result, REPORT_DIR)
        result["report_filename"] = os.path.basename(report_path)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        for path in [pdf_path, qb_path]:
            try:
                os.remove(path)
            except Exception:
                pass


# ── Report Download ───────────────────────────────────────────────

@app.route("/api/download/<filename>", methods=["GET"])
def download_report(filename):
    """Download a generated reconciliation report."""
    filepath = os.path.join(REPORT_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404
    return send_file(filepath, as_attachment=True, download_name=filename)


# ── Health Check ──────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "app": "Misbah's Magic"})


# ── Run ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    print(f"\n🚀 Misbah's Magic backend running on http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=debug)
