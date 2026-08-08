#!/usr/bin/env python3
"""Unit tests for the pure safety-zone logic (Bible §10).

Run: pytest -q tests/scripts/test_safety_node.py
"""

import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, '..', '..', '..', '..',
                                'versions', 'V0.3_Ultron', 'software',
                                'jetson', 'src', 'ultron_onboard',
                                'ultron_onboard'))

from safety_logic import compute_safe_twist, min_range_in_front  # noqa: E402


def make_ranges(dist_m, n=360, arc=60):
    """Synthetic scan with `dist_m` at the forward ray, far elsewhere."""
    ranges = [10.0] * n
    # forward ray is index 0 (angle_min < 0 typically; approximate by center)
    idx = n // 2
    ranges[idx] = dist_m
    return ranges, -math.radians(45.0), math.radians(90.0) / n


def test_min_range_in_front_center():
    ranges, amin, ainc = make_ranges(0.5)
    d, i = min_range_in_front(ranges, amin, ainc, 60)
    assert d == 0.5


def test_min_range_ignores_side_obstacles():
    n = 360
    ranges = [10.0] * n
    amin = -math.pi
    ainc = 2 * math.pi / n
    ranges[0] = 0.2                      # 180 deg = behind -> out of arc
    ranges[90] = 0.2                     # +90 deg = left -> out of arc
    d, _ = min_range_in_front(ranges, amin, ainc, 60)
    assert d == 10.0


def test_stop_zone_zeroes_velocity():
    lin, ang = compute_safe_twist(0.3, 0.0, 0.30, None, False, False)
    assert (lin, ang) == (0.0, 0.0)


def test_slow_zone_scales_forward():
    # d=0.525 mid of [0.35, 0.70] -> scale 0.5
    lin, ang = compute_safe_twist(0.3, 0.0, 0.525, None, False, False)
    assert abs(lin - 0.15) < 1e-9


def test_slow_zone_allows_reverse_escape():
    lin, _ = compute_safe_twist(-0.3, 0.0, 0.525, None, False, False)
    assert lin == -0.3                   # reverse not scaled


def test_free_zone_passes_through():
    lin, ang = compute_safe_twist(0.3, 0.1, 0.8, None, False, False)
    assert abs(lin - 0.3) < 1e-9 and abs(ang - 0.1) < 1e-9


def test_lidar_priority_governs_exclusively():
    # Kinect very close (0.2) but lidar 0.8 -> lidar governs (d=0.8)
    lin, _ = compute_safe_twist(0.3, 0.0, 0.8, 0.2, False, False)
    assert abs(lin - 0.3) < 1e-9


def test_kinect_contributes_in_band():
    # lidar 1.5, kinect 1.2 -> effective d=1.2 (both > slow, no scaling)
    lin, _ = compute_safe_twist(0.3, 0.0, 1.5, 1.2, False, False)
    assert abs(lin - 0.3) < 1e-9
    # lidar 0.3 -> STOP regardless of kinect (lidar governs exclusively)
    lin, _ = compute_safe_twist(0.3, 0.0, 0.3, 1.0, False, False)
    assert lin == 0.0
    # lidar 0.5 (below priority, SLOW zone) -> kinect must NOT shrink it
    lin, _ = compute_safe_twist(0.3, 0.0, 0.5, 0.36, False, False)
    assert abs(lin - 0.3 * (0.5 - 0.35) / (0.70 - 0.35)) < 1e-9


def test_lidar_stale_stops():
    lin, ang = compute_safe_twist(0.3, 0.2, 0.8, None, True, False)
    assert (lin, ang) == (0.0, 0.0)


def test_kinect_stale_degrades_to_lidar():
    lin, _ = compute_safe_twist(0.3, 0.0, 0.8, 0.2, False, True)
    assert abs(lin - 0.3) < 1e-9          # kinect ignored


def test_clamp_to_max_speed():
    lin, ang = compute_safe_twist(5.0, 5.0, 10.0, None, False, False)
    assert abs(lin) <= 0.45 and abs(ang) <= 0.45


if __name__ == '__main__':
    import pytest
    sys.exit(pytest.main([__file__, '-v']))
