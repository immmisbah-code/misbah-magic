"""
Reports Routes — file download endpoint.
"""

import os
from flask import send_file, jsonify
from . import reports_bp
from dirs import get_report_dir


@reports_bp.route("/download/<filename>", methods=["GET"])
def download(filename: str):
    """GET /api/reports/download/<filename>"""
    # Prevent directory traversal
    safe_name = os.path.basename(filename)
    filepath  = os.path.join(get_report_dir(), safe_name)

    if not os.path.isfile(filepath):
        return jsonify({"error": "Report not found"}), 404

    return send_file(filepath, as_attachment=True, download_name=safe_name)
