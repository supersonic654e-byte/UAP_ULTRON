#!/usr/bin/env python3
"""Unit tests for depth-row -> LaserScan projection (Bible §9 NODE 2).

Run: pytest -q tests/scripts/test_depth_scan.py
"""

import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, '..', '..', '..', '..',
                                'versions', 'V0.3_Ultron', 'software',
                                'jetson', 'src', 'ultron_onboard',
                                'ultron_onboard'))

from depth_scan_logic import depth_row_to_scan, select_camera_model  # noqa: E402

W, H = 320, 120
FX = 574.0527954
CX = 159.5


# --- select_camera_model (P1: camera_info-driven intrinsics) ----------------

def test_info_valid_k_used():
    k = [600.0, 0.0, 200.0,
         0.0, 600.0, 100.0,
         0.0, 0.0, 1.0]
    fx, cx, live = select_camera_model(k, FX, CX)
    assert live is True
    assert fx == 600.0
    assert cx == 200.0


def test_info_invalid_k_falls_back():
    assert select_camera_model(None, FX, CX) == (FX, CX, False)
    assert select_camera_model([], FX, CX) == (FX, CX, False)
    assert select_camera_model([0.0, 0.0, 0.0], FX, CX) == (FX, CX, False)
    # fx <= 0 -> invalid even with 9 elements
    bad = [0.0] * 9
    assert select_camera_model(bad, FX, CX) == (FX, CX, False)


def test_info_d455_k_shifts_cx():
    # A D455 publishes its own K; the ROI principal point lands in [0, 320).
    k = [383.6, 0.0, 168.4,
         0.0, 383.6, 100.0,
         0.0, 0.0, 1.0]
    fx, cx, live = select_camera_model(k, FX, CX)
    assert live is True and cx == 168.4
    ranges, amin, ainc = depth_row_to_scan(
        flat_image(1000), W, H, fx, cx, 0.0, 0.5, 4.0)
    assert len(ranges) == W and not all(math.isinf(r) for r in ranges)


def flat_image(mm=1000):
    """A depth image where every pixel reads `mm` millimeters."""
    return [mm] * (W * H)


def test_all_invalid_is_inf():
    img = [0] * (W * H)
    ranges, amin, ainc = depth_row_to_scan(img, W, H, FX, CX, 0.0, 0.5, 4.0)
    assert len(ranges) == W
    assert all(math.isinf(r) for r in ranges)


def test_center_pixel_distance_and_tilt():
    img = flat_image(1000)               # 1.0 m
    ranges, amin, ainc = depth_row_to_scan(img, W, H, FX, CX, 0.0, 0.5, 4.0)
    # center ray: angle ~0 -> raw 1.0 m (cos0=1)
    center = ranges[len(ranges) // 2]
    assert abs(center - 1.0) < 1e-6
    # -10 deg tilt: horizontal distance = 1.0 * cos(10 deg)
    tilt = math.radians(-10.0)
    ranges_t, _, _ = depth_row_to_scan(img, W, H, FX, CX, tilt, 0.5, 4.0)
    center_t = ranges_t[len(ranges_t) // 2]
    assert abs(center_t - math.cos(10.0 * math.pi / 180.0)) < 1e-6


def test_out_of_range_becomes_inf():
    img = flat_image(5000)               # 5.0 m > max 4.0
    ranges, _, _ = depth_row_to_scan(img, W, H, FX, CX, 0.0, 0.5, 4.0)
    assert all(math.isinf(r) for r in ranges)


def test_angles_span_fov():
    img = flat_image(1000)
    ranges, amin, ainc = depth_row_to_scan(img, W, H, FX, CX, 0.0, 0.5, 4.0)
    amax = amin + ainc * (len(ranges) - 1)
    assert amin < 0 < amax
    assert abs(amin + math.atan(CX / FX)) < 1e-9


def test_too_small_image_raises():
    try:
        depth_row_to_scan([0] * 10, W, H, FX, CX, 0.0, 0.5, 4.0)
        assert False, 'should raise'
    except ValueError:
        pass


if __name__ == '__main__':
    import pytest
    sys.exit(pytest.main([__file__, '-v']))
