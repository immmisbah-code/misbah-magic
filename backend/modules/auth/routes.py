"""
Auth Routes
Handles username + password verification for secure access.
"""

from flask import request, jsonify
from config import config
from . import auth_bp


@auth_bp.route("/verify", methods=["POST"])
def verify():
    """POST /api/auth/verify — verify username and password."""
    data     = request.get_json(silent=True) or {}
    username = data.get("username", "").strip().lower()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required"}), 400

    users = config.get_users()
    if users.get(username) == password:
        return jsonify({"success": True})

    return jsonify({"success": False, "message": "Invalid username or password"}), 401
