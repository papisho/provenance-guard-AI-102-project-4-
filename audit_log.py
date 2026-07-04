
import json
import os
from datetime import datetime, timezone

LOG_FILE = os.path.join(os.path.dirname(__file__), "audit_log.json")


def _read_all_entries() -> list:
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _write_all_entries(entries: list) -> None:
    with open(LOG_FILE, "w") as f:
        json.dump(entries, f, indent=2)


def log_entry(entry: dict) -> None:
    """
    Appends a structured entry to the audit log.

    Expected fields (grows over Milestones 3-5):
        content_id, creator_id, timestamp, attribution, confidence,
        signal_1_score, signal_2_score, status, appeal_reasoning
    """
    entries = _read_all_entries()
    entries.append(entry)
    _write_all_entries(entries)


def get_log(limit: int = 20) -> list:
    """Returns the most recent audit log entries, newest first."""
    entries = _read_all_entries()
    return list(reversed(entries))[:limit]


def find_entry_by_content_id(content_id: str) -> dict | None:
    """Finds the most recent entry matching a given content_id."""
    entries = _read_all_entries()
    for entry in reversed(entries):
        if entry.get("content_id") == content_id:
            return entry
    return None


def update_entry_status(content_id: str, status: str, appeal_reasoning: str = None, appeal_timestamp: str = None) -> bool:
    """
    Updates the status of an entry matching content_id (used by the appeals
    workflow in Milestone 5). Returns True if an entry was found and updated.
    """
    entries = _read_all_entries()
    updated = False
    for entry in entries:
        if entry.get("content_id") == content_id:
            entry["status"] = status
            if appeal_reasoning is not None:
                entry["appeal_reasoning"] = appeal_reasoning
            if appeal_timestamp is not None:
                entry["appeal_timestamp"] = appeal_timestamp
            updated = True
    if updated:
        _write_all_entries(entries)
    return updated


def current_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"