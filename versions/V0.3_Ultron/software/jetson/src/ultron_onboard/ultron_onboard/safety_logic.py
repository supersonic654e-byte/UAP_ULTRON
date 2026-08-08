"""Pure safety-zone logic (no ROS imports) — Bible Section 10.

Separated from safety_node so the zone/fusion math can be unit-tested
standalone. `safety_node` is a thin ROS wrapper around these functions.
"""

import math


def min_range_in_front(ranges, angle_min, angle_increment, arc_deg):
    """Minimum finite range within +/-arc_deg of 0 deg (forward = +x).

    Returns (min_range, index) or (None, None) if no valid samples.
    """
    if not ranges:
        return None, None
    half = math.radians(arc_deg / 2.0)
    best = None
    best_i = None
    for i, r in enumerate(ranges):
        a = angle_min + angle_increment * i
        if a < -half or a > half:
            continue
        if r > 0.0 and math.isfinite(r):
            if best is None or r < best:
                best = r
                best_i = i
    return best, best_i


def compute_safe_twist(cmd_linear_x, cmd_angular_z,
                       lidar_d, kinect_d,
                       lidar_stale, kinect_stale,
                       stop=0.35, slow=0.70,
                       lidar_priority=1.0, kin_min=1.0, kin_max=3.0,
                       max_speed=0.45):
    """Apply STOP/SLOW zones and LiDAR-priority fusion to a velocity command.

    Returns (safe_linear_x, safe_angular_z).
    """
    if lidar_stale:
        return 0.0, 0.0                      # LiDAR timeout -> STOP

    d = lidar_d
    if d >= lidar_priority and not kinect_stale and kinect_d is not None:
        if kin_min <= kinect_d <= kin_max:   # Kinect contributes 1.0-3.0 m only
            d = min(d, kinect_d)

    lin = float(cmd_linear_x)
    ang = float(cmd_angular_z)

    if d <= stop:
        return 0.0, 0.0
    if d < slow:
        scale = (d - stop) / (slow - stop)
        lin = lin * scale if lin > 0.0 else lin   # forward scaled, reverse free
        ang = ang * scale
    # else: pass through

    lin = max(-max_speed, min(max_speed, lin))
    ang = max(-max_speed, min(max_speed, ang))
    return lin, ang
