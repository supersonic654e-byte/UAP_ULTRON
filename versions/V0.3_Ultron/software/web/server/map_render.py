"""Dependency-free PNG rendering for the live map and camera feed.

Implements a minimal PNG encoder (zlib + struct) so the web server needs no
PIL/image libraries inside the container. `render_map` draws the occupancy
grid with the robot pose overlay; `render_depth` colorizes a depth frame and
overlays detected obstacles.
"""

import math
import struct
import zlib

UNKNOWN = -1
FREE = 0
OCCUPIED = 100


def _chunk(tag, data):
    payload = tag + data
    return (struct.pack(">I", len(data)) + payload +
            struct.pack(">I", zlib.crc32(payload) & 0xFFFFFFFF))


def png_from_rgba(width, height, pixels):
    """pixels: iterable of (r, g, b, a) ints, row-major, length w*h."""
    raw = bytearray()
    for y in range(height):
        raw.append(0)  # filter: None
        base = y * width
        for x in range(width):
            r, g, b, a = pixels[base + x]
            raw += bytes((r & 0xFF, g & 0xFF, b & 0xFF, a & 0xFF))
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    out = b"\x89PNG\r\n\x1a\n"
    out += _chunk(b"IHDR", ihdr)
    out += _chunk(b"IDAT", zlib.compress(bytes(raw), 6))
    out += _chunk(b"IEND", b"")
    return out


def _jet(t):
    """Jet-like colormap t in [0,1] -> (r, g, b)."""
    t = max(0.0, min(1.0, t))
    r = max(0.0, min(1.0, 1.5 - abs(4.0 * t - 3.0)))
    g = max(0.0, min(1.0, 1.5 - abs(4.0 * t - 2.0)))
    b = max(0.0, min(1.0, 1.5 - abs(4.0 * t - 1.0)))
    return int(r * 255), int(g * 255), int(b * 255)


def render_map(data, width, height, resolution,
               origin_x=0.0, origin_y=0.0, robot=None, robot_theta=0.0,
               scale=None):
    """Render an OccupancyGrid into an RGBA PNG.

    data: int8 list, -1 unknown / 0 free / 100 occupied (row-major).
    robot: (x, y) in map meters (drawn as a direction arrow).
    Returns PNG bytes (and downsamples if the grid is large).
    """
    if scale is None:
        scale = 3          # px per cell; maps get scaled down for the web
    w = max(1, width * scale)
    h = max(1, height * scale)
    pixels = [(128, 134, 145, 255)] * (w * h)
    for y in range(height):
        for x in range(width):
            v = data[y * width + x]
            if v == OCCUPIED:
                c = (18, 26, 40, 255)
            elif v == FREE:
                c = (240, 245, 250, 255)
            else:
                c = (178, 186, 196, 255)
            for dy in range(scale):
                for dx in range(scale):
                    px = x * scale + dx
                    py = y * scale + dy
                    if 0 <= px < w and 0 <= py < h:
                        pixels[py * w + px] = c

    if robot is not None:
        rx = int((robot[0] - origin_x) / resolution * scale)
        ry = int((robot[1] - origin_y) / resolution * scale)
        marker = (20, 130, 240, 255)
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                px, py = rx + dx, ry + dy
                if 0 <= px < w and 0 <= py < h:
                    pixels[py * w + px] = marker
        # heading arrow
        dx = int(6 * math.cos(robot_theta))
        dy = int(6 * math.sin(robot_theta))
        for k in range(1, 5):
            px, py = rx + dx * k // 2, ry + dy * k // 2
            if 0 <= px < w and 0 <= py < h:
                pixels[py * w + px] = (250, 160, 40, 255)

    return png_from_rgba(w, h, pixels)


def render_depth(depth_mm, width, height, min_m=0.3, max_m=4.0,
                 obstacles=None):
    """Colorize a uint16 depth frame (mm) into a PNG.

    obstacles: list of {'angle_deg','range_m','width_px'} (camera overlay),
               projected using the Kinect model (fx=574.05, cx=159.5).
    Returns PNG bytes at full ROI resolution.
    """
    fx = 574.0527954
    cx = 159.5
    cy = (height - 1) / 2.0
    pixels = [(8, 12, 20, 255)] * (width * height)
    for y in range(height):
        base = y * width
        for x in range(width):
            d = depth_mm[base + x]
            if d <= 0:
                continue
            dm = d / 1000.0
            t = (dm - min_m) / (max_m - min_m)
            if t < 0:
                t = 0.0
            pixels[base + x] = _jet(t) + (255,)

    # Obstacle overlay: vertical red bars + range label color.
    for ob in (obstacles or []):
        ang = math.radians(ob["angle_deg"])
        px = int(cx + fx * math.tan(ang))
        color = (230, 60, 70, 255) if ob["range_m"] <= 0.35 else \
                (250, 170, 40, 255) if ob["range_m"] <= 0.70 else \
                (40, 200, 120, 255)
        wpx = max(3, min(ob.get("width_px", 4), 12))
        for yy in range(height):
            for xx in range(max(0, px - wpx // 2),
                            min(width, px + wpx // 2 + 1)):
                pixels[yy * width + xx] = color
        # horizontal band at the obstacle row
        row = int(cy)
        if 0 <= row < height:
            for xx in range(max(0, px - 20), min(width, px + 21)):
                pixels[row * width + xx] = (255, 255, 255, 255)
    return png_from_rgba(width, height, pixels)
