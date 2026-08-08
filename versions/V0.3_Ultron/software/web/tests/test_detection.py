#!/usr/bin/env python3
"""Unit tests for obstacle/object detection.

Run: pytest -q tests/test_detection.py   (from software/web)
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import detection  # noqa: E402


def make_scan(n=360, front=5.0, left=5.0, right=5.0):
    """Synthetic 360-beam scan with specified sector distances."""
    amin = -math.pi
    ainc = 2 * math.pi / n
    ranges = [20.0] * n
    for i in range(n):
        a = amin + ainc * i
        if -math.radians(15) <= a <= math.radians(15):
            ranges[i] = front
        if math.pi / 2 - math.radians(15) <= a <= math.pi / 2 + math.radians(15):
            ranges[i] = left
        if -math.pi / 2 - math.radians(15) <= a <= -math.pi / 2 + math.radians(15):
            ranges[i] = right
    return ranges, amin, ainc


def test_sector_ranges():
    r, amin, ainc = make_scan(front=0.5, left=2.0, right=1.2)
    sec = detection.sector_ranges(r, amin, ainc)
    assert abs(sec["front"] - 0.5) < 1e-9
    assert abs(sec["left"] - 2.0) < 1e-9
    assert abs(sec["right"] - 1.2) < 1e-9


def test_obstacle_status_stop_slow_free():
    r, amin, ainc = make_scan(front=0.3)
    st = detection.obstacle_status(r, amin, ainc)
    assert st["state"] == "stop"
    assert st["level"] == "danger"
    assert st["avoidance"]["clamp"] == 0.0

    r, amin, ainc = make_scan(front=0.5)
    st = detection.obstacle_status(r, amin, ainc)
    assert st["state"] == "slow"
    assert st["avoidance"]["clamp"] == 0.35

    r, amin, ainc = make_scan(front=3.0)
    st = detection.obstacle_status(r, amin, ainc)
    assert st["state"] == "free"
    assert st["avoidance"]["clamp"] == 0.45


def test_detect_clusters():
    n = 40
    ranges = [10.0] * n
    amin = -math.radians(30)
    ainc = math.radians(60) / n
    # an obstacle spanning a few beams near center
    for i in range(15, 22):
        ranges[i] = 1.0
    clusters = detection.detect_clusters(ranges, amin, ainc)
    assert len(clusters) == 1
    c = clusters[0]
    assert c["range_m"] == 1.0
    assert c["size_px"] == 7


def test_depth_row_obstacles():
    # 320 px row, 1.0 m in the middle band
    row = [0.0] * 320
    for x in range(140, 181):
        row[x] = 1.0
    obs, mn = detection.depth_row_obstacles(row, 574.05, 159.5)
    assert mn == 1.0
    assert len(obs) == 1
    assert abs(obs[0]["angle_deg"]) < 0.5     # centered
    assert obs[0]["width_px"] == 41


def test_depth_row_ignores_zero_and_far():
    row = [0.0] * 320
    row[100] = 10.0          # > max 4.0 -> ignored
    row[101] = 0.0           # invalid
    obs, mn = detection.depth_row_obstacles(row, 574.05, 159.5)
    assert obs == [] and mn is None


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
