#!/usr/bin/env python3
"""Unit tests for the SQLite store.

Run: pytest -q tests/test_store.py   (from software/web)
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import auth, store as store_mod  # noqa: E402


def make_store():
    tmp = tempfile.mkdtemp()
    path = os.path.join(tmp, "test.db")
    return store_mod.Store(path), path


def test_defaults_created():
    s, _ = make_store()
    assert s.get("user_pin") is not None
    assert auth.pin_ok(s.get("user_pin"))
    assert s.get("admin_hash") is not None
    assert s.get("admin_salt") is not None
    assert len(s.get("token_secret")) == 64
    assert "room1" in s.get_rooms()


def test_first_run_secrets():
    s, _ = make_store()
    assert s.first_run_secrets is not None
    assert auth.pin_ok(s.first_run_secrets.get("user_pin", ""))
    # admin password must NOT be persisted plaintext
    assert s.get("admin_password") is None
    assert len(s.first_run_secrets.get("admin_password", "")) == 10


def test_settings_roundtrip():
    s, _ = make_store()
    s.set("user_pin", "4321")
    assert s.get("user_pin") == "4321"


def test_activity_log():
    s, _ = make_store()
    s.log_activity("user", "cmd_twist", "vx=0.2")
    s.log_activity("admin", "change_pin")
    rows = s.recent_activity()
    assert len(rows) == 2
    assert rows[0]["role"] == "admin"
    assert rows[0]["action"] == "change_pin"


def test_notifications():
    s, _ = make_store()
    s.notify("info", "hello")
    s.notify("warning", "watch")
    assert len(s.unread_notifications()) == 2
    s.mark_notifications_seen()
    assert len(s.unread_notifications()) == 0
    assert len(s.all_notifications()) == 2


def test_missions():
    s, _ = make_store()
    s.upsert_mission("M001", "completed", {"d": 5})
    s.upsert_mission("M001", "aborted", {"d": 5})
    s.upsert_mission("M002", "planned")
    ms = s.missions()
    assert len(ms) == 2
    m1 = [m for m in ms if m["id"] == "M001"][0]
    assert m1["status"] == "aborted"


def test_rooms_json():
    s, _ = make_store()
    s.set_rooms({"hall": {"x": 1, "y": 1, "theta": 0, "label": "Hall"}})
    rooms = s.get_rooms()
    assert rooms["hall"]["label"] == "Hall"
