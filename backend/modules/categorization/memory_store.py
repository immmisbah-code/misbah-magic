"""
Memory Store — Magic Cat
Persists company transaction history, GL decisions, vendor patterns, and human
overrides as a JSON file so the AI improves over time.
"""

import json
import os
import threading
from datetime import datetime

_lock = threading.Lock()


def _path() -> str:
    """Return the memory file path (set by dirs.py on first import of config)."""
    from config import config
    return config.MEMORY_STORE_PATH


def _load() -> dict:
    p = _path()
    if os.path.isfile(p):
        try:
            with open(p, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            pass
    return {"vendor_patterns": {}, "gl_history": [], "overrides": []}


def _save(data: dict) -> None:
    p = _path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, default=str)


# ── Public API ────────────────────────────────────────────────────────

def get_vendor_history(vendor_key: str) -> dict | None:
    """Return the most-common GL used for this vendor, or None."""
    with _lock:
        data = _load()
    return data["vendor_patterns"].get(vendor_key)


def record_approval(transaction: dict, selected_gl: str, overridden: bool = False) -> None:
    """
    Persist an approved transaction.
    - Updates vendor pattern frequency table
    - Appends to gl_history for pattern learning
    - Records override if the AI suggestion was changed
    """
    vendor_key = _vendor_key(transaction.get("description", ""))

    with _lock:
        data = _load()

        # Update vendor → GL frequency
        vp = data["vendor_patterns"].setdefault(vendor_key, {})
        vp[selected_gl] = vp.get(selected_gl, 0) + 1

        # Append to history
        data["gl_history"].append({
            "date"        : str(transaction.get("date", "")),
            "description" : transaction.get("description", ""),
            "amount"      : transaction.get("amount", 0),
            "gl"          : selected_gl,
            "overridden"  : overridden,
            "approved_at" : datetime.utcnow().isoformat(),
        })

        if overridden:
            data["overrides"].append({
                "description"    : transaction.get("description", ""),
                "ai_suggestion"  : transaction.get("suggested_gl", ""),
                "human_choice"   : selected_gl,
                "approved_at"    : datetime.utcnow().isoformat(),
            })

        _save(data)


def get_recent_history(limit: int = 200) -> list:
    """Return the most recent approved transactions."""
    with _lock:
        data = _load()
    return data["gl_history"][-limit:]


def get_override_patterns() -> list:
    """Return all human-override records (useful for re-training prompts)."""
    with _lock:
        data = _load()
    return data.get("overrides", [])


def top_vendor_gl(vendor_key: str) -> str | None:
    """Return the GL code most frequently used for this vendor."""
    history = get_vendor_history(vendor_key)
    if not history:
        return None
    return max(history, key=lambda k: history[k])


# ── Helpers ───────────────────────────────────────────────────────────

def _vendor_key(description: str) -> str:
    """Normalize description to a vendor key."""
    import re
    text = description.lower().strip()
    text = re.sub(r"[^a-z0-9 ]", "", text)
    # Take first 3 meaningful words as vendor key
    words = [w for w in text.split() if len(w) > 2]
    return "_".join(words[:3]) or "unknown"
