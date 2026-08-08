"""Pure depth-row -> LaserScan logic (no ROS imports) — Bible §9 NODE 2."""

import math


def select_camera_model(k, fallback_fx, fallback_cx):
    """Choose the fx/cx camera model from a camera_info K matrix.

    P1 (audit): the depth->scan node consumes the live CameraInfo so the depth
    sensor is drop-in replaceable. This pure helper decides the model:

      - A valid K (9 elements, positive fx) -> use fx = K[0], cx = K[2].
      - Invalid/absent K -> fall back to the declared params.
      - Returns (fx, cx, using_live).

    Args:
        k: camera_info K as a sequence of >= 9 floats (may be None/empty).
        fallback_fx, fallback_cx: param fallbacks (Kinect 1414 intrinsics).
    Returns:
        (fx, cx, using_live)
    """
    if k is not None and len(k) >= 9:
        fx = float(k[0])
        cx = float(k[2])
        if fx > 0.0:
            return fx, cx, True
    return fallback_fx, fallback_cx, False


def depth_row_to_scan(data, width, height,
                      fx, cx,
                      tilt_rad, min_m, max_m):
    """Project the middle row of a uint16 mm depth image into a LaserScan.

    Returns a (ranges, angle_min, angle_increment) tuple. Invalid / out-of-range
    samples become +inf. The horizontal range is corrected by cos(tilt) since
    the tilted plane foreshortens the horizontal distance.
    """
    if width < 2 or height < 2 or len(data) < height * width:
        raise ValueError('depth image too small for the requested ROI')
    row = height // 2
    base = row * width
    n = width
    half_angle = math.atan(cx / fx)
    angle_min = -half_angle
    angle_max = math.atan((n - 1 - cx) / fx)
    angle_inc = (angle_max - angle_min) / (n - 1)

    ranges = []
    cos_tilt = math.cos(tilt_rad)
    for i in range(n):
        raw = data[base + i]
        if raw <= 0:
            ranges.append(float('inf'))
            continue
        d = (raw / 1000.0) * cos_tilt
        if d < min_m or d > max_m:
            ranges.append(float('inf'))
        else:
            ranges.append(float(d))
    return ranges, angle_min, angle_inc
