"""
wsgi.py — Production WSGI entry point.

Used by gunicorn / Render / any WSGI host:
    gunicorn backend.wsgi:application
"""

from app import create_app

application = create_app()
