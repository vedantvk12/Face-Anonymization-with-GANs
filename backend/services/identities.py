import os
import json
from typing import List, Dict, Any, Optional

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONFIG_PATH = os.path.join(ROOT, "data", "synthetic_identities.json")
THUMBNAIL_DIR = os.path.join(ROOT, "data", "thumbnails")

_identities_cache: List[Dict[str, Any]] = []

def _load_identities():
    global _identities_cache
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                _identities_cache = json.load(f)
        except Exception as e:
            print("Failed to load synthetic identities config:", e)
            _identities_cache = []
    else:
        _identities_cache = []

def get_all_identities(style: Optional[str] = None) -> List[Dict[str, Any]]:
    global _identities_cache
    if not _identities_cache:
        _load_identities()

    if style and style.lower() != "all":
        return [item for item in _identities_cache if item.get("style", "").lower() == style.lower()]
    return list(_identities_cache)

def get_identities_by_style(style: str) -> List[str]:
    """Returns list of identity IDs matching the given style (or all realistic if none)."""
    items = get_all_identities(style)
    if not items:
        # Fallback to all
        items = get_all_identities()
    return [item["id"] for item in items]

def get_identity_by_id(identity_id: str) -> Optional[Dict[str, Any]]:
    global _identities_cache
    if not _identities_cache:
        _load_identities()
    for item in _identities_cache:
        if item["id"] == identity_id:
            return item
    return None

def get_thumbnail_path(filename: str) -> Optional[str]:
    path = os.path.join(THUMBNAIL_DIR, filename)
    if os.path.isfile(path):
        return path
    return None
