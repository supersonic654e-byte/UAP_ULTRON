"""SQLite persistence for the Ultron V0.3 web control system.

Tables:
  settings   — key/value: user_pin, admin_salt, admin_hash, token_secret,
               robot_name, rooms (JSON), mission_id.
  activity   — append-only operator activity log (role, action, detail, ts).
  notifications — event queue shown in both dashboards.
  missions   — pilot mission records (mirrors data_pilot/ artifacts).
"""

import json
import os
import sqlite3
import threading
import time


class Store:
    def __init__(self, path):
        self._path = path
        self._lock = threading.RLock()
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()
        self.first_run_secrets = self._ensure_defaults()

    # ---- schema -----------------------------------------------------------
    def _init_schema(self):
        with self._lock:
            cur = self._conn.cursor()
            cur.executescript("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                role TEXT NOT NULL,
                action TEXT NOT NULL,
                detail TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                level TEXT NOT NULL DEFAULT 'info',
                text TEXT NOT NULL,
                seen INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS missions (
                id TEXT PRIMARY KEY,
                ts REAL NOT NULL,
                status TEXT DEFAULT 'planned',
                meta TEXT DEFAULT '{}'
            );
            """)
            self._conn.commit()

    def _ensure_defaults(self):
        """Create defaults if missing. Returns dict of secrets generated on a
        FIRST run so main.py can print them once to the operator console:
        {'user_pin': str, 'admin_password': str}. The admin password is stored
        only as a salted hash — never plaintext. The PIN is stored plaintext
        (server-side) so the admin dashboard can view/change it."""
        from server import auth
        generated = {}
        with self._lock:
            if self.get("user_pin") is None:
                generated["user_pin"] = auth.new_pin()
                self.set("user_pin", generated["user_pin"])
            if self.get("admin_salt") is None or self.get("admin_hash") is None:
                salt = auth._salt()
                pw = auth.new_admin_password()
                self.set("admin_salt", salt.hex())
                self.set("admin_hash", auth.hash_secret(pw, salt))
                generated["admin_password"] = pw
            if self.get("token_secret") is None:
                self.set("token_secret", os.urandom(32).hex())
            if self.get("rooms") is None:
                self.set("rooms", json.dumps({
                    "room1": {"x": 2.0, "y": 0.0, "theta": 0.0, "label": "Room 1"},
                    "room2": {"x": 0.0, "y": 2.0, "theta": 1.5708, "label": "Room 2"},
                    "room3": {"x": -2.0, "y": 0.0, "theta": 3.1416, "label": "Room 3"},
                    "base": {"x": 0.0, "y": 0.0, "theta": 0.0, "label": "Return to base"},
                }))
            self._conn.commit()
        return generated

    # ---- settings ---------------------------------------------------------
    def get(self, key):
        with self._lock:
            row = self._conn.execute(
                "SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            return row["value"] if row else None

    def set(self, key, value):
        with self._lock:
            self._conn.execute(
                "INSERT INTO settings(key,value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, str(value)))
            self._conn.commit()

    def get_rooms(self):
        try:
            return json.loads(self.get("rooms") or "{}")
        except json.JSONDecodeError:
            return {}

    def set_rooms(self, rooms):
        self.set("rooms", json.dumps(rooms))

    # ---- activity ---------------------------------------------------------
    def log_activity(self, role, action, detail=""):
        with self._lock:
            self._conn.execute(
                "INSERT INTO activity(ts, role, action, detail) VALUES(?,?,?,?)",
                (time.time(), role, action, str(detail)[:500]))
            self._conn.commit()

    def recent_activity(self, limit=50):
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM activity ORDER BY ts DESC LIMIT ?",
                (limit,)).fetchall()
            return [dict(r) for r in rows]

    # ---- notifications ----------------------------------------------------
    def notify(self, level, text):
        with self._lock:
            self._conn.execute(
                "INSERT INTO notifications(ts, level, text) VALUES(?,?,?)",
                (time.time(), level, str(text)[:300]))
            self._conn.commit()

    def unread_notifications(self):
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM notifications WHERE seen=0 "
                "ORDER BY ts DESC LIMIT 50").fetchall()
            return [dict(r) for r in rows]

    def mark_notifications_seen(self):
        with self._lock:
            self._conn.execute("UPDATE notifications SET seen=1")
            self._conn.commit()

    def all_notifications(self, limit=100):
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM notifications ORDER BY ts DESC LIMIT ?",
                (limit,)).fetchall()
            return [dict(r) for r in rows]

    # ---- missions ---------------------------------------------------------
    def upsert_mission(self, mission_id, status, meta=None):
        with self._lock:
            self._conn.execute(
                "INSERT INTO missions(id, ts, status, meta) VALUES(?,?,?,?) "
                "ON CONFLICT(id) DO UPDATE SET status=excluded.status, "
                "meta=excluded.meta",
                (mission_id, time.time(), status,
                 json.dumps(meta or {})))
            self._conn.commit()

    def missions(self):
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM missions ORDER BY ts DESC").fetchall()
            return [dict(r) for r in rows]
