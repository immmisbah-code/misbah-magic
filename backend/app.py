"""
Misbah's Magic — Flask Application Factory
"""

import os
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from config import config


def create_app() -> Flask:
    frontend_dir = os.path.abspath(config.FRONTEND_DIR)
    app = Flask(__name__, static_folder=frontend_dir, static_url_path="")
    CORS(app)

    # ── Register Blueprints ───────────────────────────────────────
    from modules.auth            import auth_bp
    from modules.reconciliation  import recon_bp
    from modules.reports         import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(recon_bp)
    app.register_blueprint(reports_bp)

    # ── Serve frontend ────────────────────────────────────────────
    @app.route("/")
    def index():
        return send_from_directory(frontend_dir, "index.html")

    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "app": "Misbah's Magic"})

    return app


if __name__ == "__main__":
    app = create_app()
    print(f"\n✨ Misbah's Magic running → http://localhost:{config.PORT}\n")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
