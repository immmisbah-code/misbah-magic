from flask import Blueprint

cat_bp = Blueprint("categorization", __name__, url_prefix="/api/categorize")

from . import routes  # noqa: F401, E402
