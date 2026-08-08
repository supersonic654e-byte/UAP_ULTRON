"""Obstacle / object detection from LiDAR + depth scans (no ROS imports).

Pure functions used by the web server to produce live obstacle status,
avoidance hints, and per-sector ranges for the camera overlay and dashboards.
Mirrors the safety zone constants of the firmware/safety node.
"""

import math

STOP_M = 0.35
SLOW_M = 0.70
LIDAR_PRIORITY_M = 1.0


def sector_ranges(ranges, angle_min, angle_increment, sectors=("front",
                                                               "left",
                                                               "right")):
    """Minimum finite range within each 60-deg sector (front = 0 deg).

    Returns a dict {sector: range_m or None}.
    """
    half = math.radians(30.0)
    out = {s: None for s in sectors}
    for i, r in enumerate(ranges):
        a = angle_min + angle_increment * i
        if not (r > 0.0 and math.isfinite(r)):
            continue
        if "front" in sectors and -half <= a <= half:
            if out["front"] is None or r < out["front"]:
                out["front"] = float(r)
        if "left" in sectors and math.pi / 2 - half <= a <= math.pi / 2 + half:
            if out["left"] is None or r < out["left"]:
                out["left"] = float(r)
        if "right" in sectors and -math.pi / 2 - half <= a <= -math.pi / 2 + half:
            if out["right"] is None or r < out["right"]:
                out["right"] = float(r)
    return out


def obstacle_status(ranges, angle_min, angle_increment):
    """Derive a compact status dict for the dashboards."""
    sec = sector_ranges(ranges, angle_min, angle_increment)
    front = sec.get("front")
    state = "free"
    if front is not None and front <= STOP_M:
        state = "stop"
    elif front is not None and front <= SLOW_M:
        state = "slow"
    level = {"stop": "danger", "slow": "warning", "free": "ok"}[state]
    return {
        "front_m": front,
        "left_m": sec.get("left"),
        "right_m": sec.get("right"),
        "state": state,
        "level": level,
        "avoidance": {
            "hint": ("STOP — obstacle <= 0.35 m" if state == "stop"
                     else "SLOW — reduce speed" if state == "slow"
                     else "clear"),
            "clamp": 0.0 if state == "stop" else
                     0.35 if state == "slow" else 0.45,
        },
    }


def detect_clusters(ranges, angle_min, angle_increment,
                    max_range=3.0, gap_rad=0.35):
    """Group consecutive valid beams into obstacle clusters.

    Each cluster: {'angle_deg': center, 'range_m': nearest, 'width_deg',
    'size_px': beam count}. Used for the camera-feed overlay and object list.
    """
    clusters = []
    cur = None
    for i, r in enumerate(ranges):
        a = angle_min + angle_increment * i
        valid = r > 0.0 and math.isfinite(r) and r <= max_range
        if valid:
            if cur is None:
                cur = {"start": a, "end": a, "min": r, "n": 1}
            else:
                if abs(a - cur["end"]) > gap_rad:
                    clusters.append(cur)
                    cur = {"start": a, "end": a, "min": r, "n": 1}
                else:
                    cur["end"] = a
                    cur["min"] = min(cur["min"], r)
                    cur["n"] += 1
        else:
            if cur is not None:
                clusters.append(cur)
                cur = None
    if cur is not None:
        clusters.append(cur)
    out = []
    for c in clusters:
        center = (c["start"] + c["end"]) / 2.0
        out.append({
            "angle_deg": round(math.degrees(center), 1),
            "range_m": round(c["min"], 2),
            "width_deg": round(math.degrees(c["end"] - c["start"]), 1),
            "size_px": c["n"],
        })
    return out


def depth_row_obstacles(row_m, fx, cx, min_m=0.3, max_m=4.0):
    """Turn a middle-row depth array (meters, 0 = invalid) into obstacles.

    Returns (obstacles, min_front_m) where each obstacle is
    {'angle_deg', 'range_m', 'width_px'} for overlaying on the camera feed.
    """
    n = len(row_m)
    obstacles = []
    min_front = None
    cur = None
    for i, d in enumerate(row_m):
        valid = d >= min_m and d <= max_m
        if valid:
            if cur is None:
                cur = {"start": i, "end": i, "min": d}
            else:
                cur["end"] = i
                cur["min"] = min(cur["min"], d)
        else:
            if cur is not None:
                obstacles.append(cur)
                cur = None
    if cur is not None:
        obstacles.append(cur)
    out = []
    for c in obstacles:
        center_px = (c["start"] + c["end"]) / 2.0
        angle = math.degrees(math.atan((center_px - cx) / fx))
        r = c["min"]
        if min_front is None or r < min_front:
            min_front = r
        out.append({"angle_deg": round(angle, 1), "range_m": round(r, 2),
                    "width_px": c["end"] - c["start"] + 1})
    return out, min_front
