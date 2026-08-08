#!/usr/bin/env python3
"""Unit tests for the robot live-state model + command gating.

Run: pytest -q tests/test_robot_state.py   (from software/web)
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.robot_state import (RobotState, fault_bits_to_names,  # noqa: E402
                                MAX_TELEOP_MPS, MAX_GOAL_MPS)


def _live_state():
    s = RobotState()
    s.update_heartbeat(1)
    s.heartbeat_time = time.time()
    return s


def test_fault_names():
    assert fault_bits_to_names(0b0000001) == ["ESTOP"]
    assert "OVERCURRENT" in fault_bits_to_names(0b0000011)
    assert fault_bits_to_names(0) == []


def test_gate_rejects_unknown_role():
    s = _live_state()
    ok, reason, _, _ = s.gate_twist(0.2, 0.0, "admin")
    assert not ok and reason == "not_authorized"


def test_gate_rejects_when_not_live():
    s = RobotState()          # never got a heartbeat
    ok, reason, _, _ = s.gate_twist(0.2, 0.0, "user")
    assert not ok and reason == "robot_not_live"


def test_gate_clamps_velocity():
    s = _live_state()
    ok, reason, vx, wz = s.gate_twist(10.0, 10.0, "user")
    assert ok
    assert abs(vx) <= MAX_TELEOP_MPS + 1e-9
    assert abs(wz) <= 1.0


def test_gate_allows_user_and_admin_control():
    s = _live_state()
    ok, _, vx, _ = s.gate_twist(0.3, 0.0, "user")
    assert ok and abs(vx - 0.3) < 1e-9
    ok, _, vx, _ = s.gate_twist(-0.2, 0.0, "admin_control")
    assert ok and abs(vx + 0.2) < 1e-9


def test_goal_speed_capped():
    s = _live_state()
    assert s.gate_goal_speed(0.9) == MAX_GOAL_MPS
    assert s.gate_goal_speed(0.2) == 0.2


def test_snapshot_shape():
    s = _live_state()
    s.update_odom(1.0, 2.0, 0.0, 0.1, 0.0)
    s.update_battery(12.3, True)
    s.update_faults(0x02)
    snap = s.snapshot()
    assert snap["odom"]["x"] == 1.0
    assert snap["battery"]["voltage"] == 12.3
    assert snap["faults"]["names"] == ["OVERCURRENT"]
    assert snap["connected"] is True


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
