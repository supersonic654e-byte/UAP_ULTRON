#!/usr/bin/env python3
"""Unit tests for the PNG renderers (map + depth).

Run: pytest -q tests/test_map_render.py   (from software/web)
"""

import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server import map_render  # noqa: E402


def _png_ok(data):
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert data[12:16] == b"IHDR"
    assert data[37:41] == b"IDAT"
    assert data[-8:-4] == b"IEND"
    w, h = struct.unpack(">II", data[16:24])
    # verify IDAT decompresses without error
    zlib.decompress(data[41:-12])
    return w, h


def test_png_from_rgba():
    pixels = [(255, 0, 0, 255)] * 4
    w, h = _png_ok(map_render.png_from_rgba(2, 2, pixels))
    assert (w, h) == (2, 2)


def test_render_map_output():
    w, h = 10, 10
    data = [map_render.UNKNOWN] * (w * h)
    for i in range(w):
        data[i] = map_render.OCCUPIED      # top row occupied
        data[w * (h - 1) + i] = map_render.FREE
    out = map_render.render_map(data, w, h, 0.05, 0.0, 0.0, robot=(0.1, 0.1),
                                robot_theta=0.0)
    _png_ok(out)


def test_render_map_robot_marker():
    w, h = 5, 5
    data = [map_render.UNKNOWN] * (w * h)
    out = map_render.render_map(data, w, h, 0.1, 0.0, 0.0, robot=(0.2, 0.2))
    _png_ok(out)


def test_render_depth():
    w, h = 320, 120
    mm = [0] * (w * h)
    for x in range(120, 200):
        mm[(h // 2) * w + x] = 1500         # 1.5 m band in middle row
    out = map_render.render_depth(mm, w, h,
                                  obstacles=[{"angle_deg": 0.0,
                                              "range_m": 1.5,
                                              "width_px": 8}])
    _png_ok(out)


def test_render_depth_all_invalid():
    out = map_render.render_depth([0] * (320 * 120), 320, 120)
    _png_ok(out)


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
