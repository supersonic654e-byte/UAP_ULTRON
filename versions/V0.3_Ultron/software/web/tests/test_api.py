#!/usr/bin/env python3
"""API integration tests for the web control system (FastAPI TestClient).

Run: pytest -q tests/test_api.py   (from software/web)
"""

import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient  # noqa: E402

from server import auth, main as web  # noqa: E402
from server.robot_state import RobotState  # noqa: E402
from server.store import Store  # noqa: E402


class FakeBridge:
    def __init__(self):
        self.calls = []

    def publish_twist(self, vx, wz):
        self.calls.append(("twist", vx, wz))
        return True

    def stop_robot(self):
        self.calls.append(("stop",))
        return True

    def clear_faults(self):
        self.calls.append(("clear",))
        return True

    def send_goal(self, x, y, theta):
        self.calls.append(("goal", x, y, theta))
        return {"ok": True, "via": "navigate_to_pose"}

    def depth_png(self):
        return None

    def map_png(self):
        return None

    def map_meta(self):
        return {}


def _setup():
    tmp = tempfile.mkdtemp()
    store = Store(os.path.join(tmp, "t.db"))
    state = RobotState()
    bridge = FakeBridge()
    web.store = store
    web.state = state
    web.bridge = bridge
    web.token = auth.Token(os.urandom(32))
    web.limiter = auth.LoginRateLimiter()
    return store, state, bridge


def client():
    return TestClient(web.app)


def _make_live(state):
    state.update_heartbeat(1)
    state.heartbeat_time = time.time()


def test_user_login_wrong_pin():
    _setup()
    with client() as c:
        r = c.post("/api/login/user", json={"pin": "0000"})
        assert r.status_code == 401


def test_user_login_correct_pin():
    store, _, _ = _setup()
    with client() as c:
        r = c.post("/api/login/user", json={"pin": store.get("user_pin")})
        assert r.status_code == 200
        assert r.json()["role"] == "user"


def test_admin_login_correct_password():
    store, _, _ = _setup()
    pw = store.first_run_secrets["admin_password"]
    with client() as c:
        r = c.post("/api/login/admin", json={"password": pw})
        assert r.status_code == 200
        assert r.json()["role"] == "admin"
        r2 = c.post("/api/login/admin_control", json={"password": pw})
        assert r2.status_code == 200
        assert r2.json()["role"] == "admin_control"


def test_pin_show_and_change_admin_only():
    store, _, _ = _setup()
    pw = store.first_run_secrets["admin_password"]
    old_pin = store.get("user_pin")
    with client() as c:
        # admin can see the pin
        tok = c.post("/api/login/admin", json={"password": pw}).json()["token"]
        r = c.get("/api/admin/pin", headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 200 and r.json()["pin"] == old_pin
        # user cannot see/change the pin
        utok = c.post("/api/login/user", json={"pin": old_pin}).json()["token"]
        r = c.get("/api/admin/pin",
                  headers={"Authorization": f"Bearer {utok}"})
        assert r.status_code == 403
        # admin changes the pin
        r = c.post("/api/admin/pin", json={"pin": "9999"},
                   headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 200
        # old pin no longer works, new pin works
        assert c.post("/api/login/user",
                      json={"pin": old_pin}).status_code == 401
        assert c.post("/api/login/user", json={"pin": "9999"}).status_code == 200


def test_twist_requires_live_robot():
    store, _, _ = _setup()
    with client() as c:
        tok = c.post("/api/login/user",
                     json={"pin": store.get("user_pin")}).json()["token"]
        h = {"Authorization": f"Bearer {tok}"}
        r = c.post("/api/cmd/twist", json={"vx": 0.2, "wz": 0.0}, headers=h)
        assert r.status_code == 409            # robot_not_live
        assert r.json()["detail"] == "robot_not_live"


def test_twist_live_user_clamped():
    store, state, bridge = _setup()
    _make_live(state)
    with client() as c:
        tok = c.post("/api/login/user",
                     json={"pin": store.get("user_pin")}).json()["token"]
        h = {"Authorization": f"Bearer {tok}"}
        r = c.post("/api/cmd/twist", json={"vx": 9.0, "wz": 9.0}, headers=h)
        assert r.status_code == 200
        assert r.json()["vx"] == 0.45          # clamped to teleop cap
        assert ("twist", 0.45, 1.0) in bridge.calls


def test_admin_readonly_cannot_twist():
    store, state, _ = _setup()
    _make_live(state)
    pw = store.first_run_secrets["admin_password"]
    with client() as c:
        tok = c.post("/api/login/admin", json={"password": pw}).json()["token"]
        h = {"Authorization": f"Bearer {tok}"}
        assert c.post("/api/cmd/twist",
                      json={"vx": 0.1, "wz": 0.0},
                      headers=h).status_code == 403
        assert c.get("/api/status", headers=h).status_code == 403
        assert c.get("/api/admin/dashboard", headers=h).status_code == 200


def test_admin_control_can_twist():
    store, state, bridge = _setup()
    _make_live(state)
    pw = store.first_run_secrets["admin_password"]
    with client() as c:
        tok = c.post("/api/login/admin_control",
                     json={"password": pw}).json()["token"]
        h = {"Authorization": f"Bearer {tok}"}
        r = c.post("/api/cmd/twist", json={"vx": 0.2, "wz": 0.0}, headers=h)
        assert r.status_code == 200
        assert ("twist", 0.2, 0.0) in bridge.calls


def test_goal_unknown_room_404():
    store, state, _ = _setup()
    _make_live(state)
    with client() as c:
        tok = c.post("/api/login/user",
                     json={"pin": store.get("user_pin")}).json()["token"]
        h = {"Authorization": f"Bearer {tok}"}
        r = c.post("/api/cmd/goal", json={"room_id": "nope"}, headers=h)
        assert r.status_code == 404


def test_goal_room_live_sends_nav():
    store, state, bridge = _setup()
    _make_live(state)
    with client() as c:
        tok = c.post("/api/login/user",
                     json={"pin": store.get("user_pin")}).json()["token"]
        h = {"Authorization": f"Bearer {tok}"}
        r = c.post("/api/cmd/goal", json={"room_id": "room1"}, headers=h)
        assert r.status_code == 200
        assert r.json()["via"] == "navigate_to_pose"
        assert bridge.calls and bridge.calls[0][0] == "goal"


def test_status_accessible_to_user():
    store, state, _ = _setup()
    _make_live(state)
    state.update_battery(12.4, True)
    with client() as c:
        tok = c.post("/api/login/user",
                     json={"pin": store.get("user_pin")}).json()["token"]
        h = {"Authorization": f"Bearer {tok}"}
        r = c.get("/api/status", headers=h)
        assert r.status_code == 200
        assert r.json()["battery"]["voltage"] == 12.4


def test_activity_is_logged():
    store, state, bridge = _setup()
    _make_live(state)
    with client() as c:
        tok = c.post("/api/login/user",
                     json={"pin": store.get("user_pin")}).json()["token"]
        h = {"Authorization": f"Bearer {tok}"}
        c.post("/api/cmd/twist", json={"vx": 0.1, "wz": 0.0}, headers=h)
        c.post("/api/cmd/stop", headers=h)
        acts = store.recent_activity()
        actions = [a["action"] for a in acts]
        assert "cmd_twist" in actions and "cmd_stop" in actions


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
