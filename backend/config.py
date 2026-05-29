"""
Configuration Management
Loads settings from environment variables with sensible defaults.
"""

import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))


class Config:
    # Security — multi-user format: "user1:pass1,user2:pass2"
    USERS: str = os.getenv("USERS", "misbah:misbah2024")

    def get_users(self) -> dict:
        """Parse USERS env var into {username: password} dict."""
        users = {}
        for entry in self.USERS.split(","):
            entry = entry.strip()
            if ":" in entry:
                username, password = entry.split(":", 1)
                users[username.strip().lower()] = password.strip()
        return users

    # AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Server
    PORT: int = int(os.getenv("PORT", 8080))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    HOST: str = "0.0.0.0"

    # File handling
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", 50))
    ALLOWED_EXTENSIONS: set = {"xlsx", "xls", "csv", "pdf"}

    # Reconciliation tuning
    AMOUNT_TOLERANCE: float = float(os.getenv("AMOUNT_TOLERANCE", 0.01))
    DATE_TOLERANCE_DAYS: int = int(os.getenv("DATE_TOLERANCE_DAYS", 3))
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", 0.60))

    # ── Magic Cat — AI Categorization ────────────────────────────────
    # Materiality threshold: amounts above this may require asset capitalization
    MATERIALITY_THRESHOLD: float = float(os.getenv("MATERIALITY_THRESHOLD", 2500.0))

    # Persistent memory store (company learning data)
    MEMORY_STORE_PATH: str = os.getenv(
        "MEMORY_STORE_PATH",
        os.path.join(os.path.dirname(__file__), "..", "data", "magic_cat_memory.json"),
    )

    # Chart of Accounts path (optional — uses built-in default if absent)
    COA_PATH: str = os.getenv(
        "COA_PATH",
        os.path.join(os.path.dirname(__file__), "..", "data", "chart_of_accounts.json"),
    )

    # Frontend path (relative to backend/)
    FRONTEND_DIR: str = os.path.join(os.path.dirname(__file__), "..", "frontend")


config = Config()
