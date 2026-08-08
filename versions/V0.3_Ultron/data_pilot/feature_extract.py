#!/usr/bin/env python3
"""Extract anonymous motion features from a pilot mission bag (Bible §17.4).

Converts a mission bag (mcap or sqlite3) into anonymous motion features:
occupancy deltas, flow counts, dwell maps, hot-zone timestamps. Runs OFFLINE
on the laptop. Raw depth/video is never extracted.

Dependencies:  pip install rosbags

Usage:
  python3 feature_extract.py <bag_dir> --mission MISSION_001 \
      --out-dir ./features/MISSION_001
"""

import argparse
import json
import math
import os
import sys

import numpy as np


def _resolve_typestore():
    from rosbags.highlevel import AnyReader
    from rosbags.typesys import Stores, get_typestore
    # Use the standard ROS2 typestore so message fields decode automatically.
    return AnyReader, get_typestore(Stores.ROS2_HUMBLE)


CELL_M = 0.20


class OccupancyGrid:
    """Sparse occupancy/dwell grid in the odom frame (anonymous)."""

    def __init__(self, cell=CELL_M):
        self.cell = cell
        self.cells = {}          # (ix, iy) -> count of times observed occupied

    def _key(self, x, y):
        return (int(math.floor(x / self.cell)), int(math.floor(y / self.cell)))

    def add(self, x, y):
        k = self._key(x, y)
        self.cells[k] = self.cells.get(k, 0) + 1

    def bounds(self):
        if not self.cells:
            return None
        xs = [k[0] for k in self.cells]
        ys = [k[1] for k in self.cells]
        return min(xs), max(xs), min(ys), max(ys)

    def size(self):
        return len(self.cells)

    def peak(self):
        return max(self.cells.values(), default=0)


def quat_yaw(q):
    # q: (x, y, z, w)
    return math.atan2(2.0 * (q[3] * q[2] + q[0] * q[1]),
                      1.0 - 2.0 * (q[1] ** 2 + q[2] ** 2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('bag', help='mission bag directory or .mcap/.db3 file')
    ap.add_argument('--mission', required=True)
    ap.add_argument('--out-dir', default='./features')
    ap.add_argument('--bin-seconds', type=float, default=10.0)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    try:
        AnyReader, typestore = _resolve_typestore()
    except ImportError:
        print('rosbags not installed. Run: pip install rosbags')
        raise SystemExit(1)

    # Topic -> typestore connection filter.
    wanted = {'/odom': 'nav_msgs/msg/Odometry',
              '/scan': 'sensor_msgs/msg/LaserScan',
              '/kinect/scan': 'sensor_msgs/msg/LaserScan'}

    dwell = OccupancyGrid()
    occ = OccupancyGrid()
    prev_pos = None
    prev_yaw = None
    total_dist = 0.0
    total_rot = 0.0
    peak_speed = 0.0
    n_odom = 0
    n_scan = 0
    n_kin = 0
    first_ts = None
    last_ts = None
    bins = {}                       # bin_index -> distance

    with AnyReader([args.bag], default_typestore=typestore) as reader:
        conns = []
        for c in reader.connections:
            if c.topic in wanted and c.msgtype == wanted[c.topic]:
                conns.append(c)
        for conn, ts, raw in reader.messages(connections=conns):
            if first_ts is None:
                first_ts = ts
            last_ts = ts
            msg = reader.deserialize(raw, conn.msgtype)
            t_sec = ts / 1e9

            if conn.topic == '/odom':
                x = msg.pose.pose.position.x
                y = msg.pose.pose.position.y
                q = (msg.pose.pose.orientation.x, msg.pose.pose.orientation.y,
                     msg.pose.pose.orientation.z, msg.pose.pose.orientation.w)
                yaw = quat_yaw(q)
                vx = msg.twist.twist.linear.x
                vy = msg.twist.twist.linear.y
                speed = math.hypot(vx, vy)
                peak_speed = max(peak_speed, speed)
                n_odom += 1
                dwell.add(x, y)
                if prev_pos is not None:
                    total_dist += math.hypot(x - prev_pos[0], y - prev_pos[1])
                    dy = yaw - prev_yaw
                    while dy > math.pi:
                        dy -= 2 * math.pi
                    while dy < -math.pi:
                        dy += 2 * math.pi
                    total_rot += abs(dy)
                    bin_idx = int((t_sec - first_ts / 1e9) /
                                  args.bin_seconds)
                    bins[bin_idx] = bins.get(bin_idx, 0.0) + \
                        math.hypot(x - prev_pos[0], y - prev_pos[1])
                prev_pos = (x, y)
                prev_yaw = yaw

            elif conn.topic in ('/scan', '/kinect/scan'):
                if conn.topic == '/scan':
                    n_scan += 1
                else:
                    n_kin += 1
                # Occupancy deltas: project finite ranges into the odom frame.
                if prev_pos is None:
                    continue
                ox, oy, oyaw = prev_pos[0], prev_pos[1], prev_yaw
                a = msg.angle_min
                for r in msg.ranges:
                    if not (0.0 < r < msg.range_max) or not math.isfinite(r):
                        a += msg.angle_increment
                        continue
                    wx = ox + r * math.cos(oyaw + a)
                    wy = oy + r * math.sin(oyaw + a)
                    occ.add(wx, wy)
                    a += msg.angle_increment

    if n_odom == 0:
        print('No /odom messages found; nothing to summarize.')
        raise SystemExit(1)

    dur = (last_ts - first_ts) / 1e9 if last_ts and first_ts else 0.0
    hot = sorted(occ.cells.items(),
                 key=lambda kv: kv[1], reverse=True)[:10]

    summary = {
        'mission_id': args.mission,
        'start_unix_s': round(first_ts / 1e9, 3) if first_ts else None,
        'end_unix_s': round(last_ts / 1e9, 3) if last_ts else None,
        'duration_s': round(dur, 1),
        'odom_samples': n_odom,
        'scan_samples': n_scan,
        'kinect_scan_samples': n_kin,
        'total_distance_m': round(total_dist, 3),
        'total_rotation_rad': round(total_rot, 3),
        'peak_speed_mps': round(peak_speed, 3),
        'dwell_cells': dwell.size(),
        'dwell_peak_visits': dwell.peak(),
        'occupancy_cells': occ.size(),
        'occupancy_peak_hits': occ.peak(),
        'hot_zone_timestamps': [
            {'ix': k[0], 'iy': k[1], 'hits': v} for k, v in hot
        ],
        'retention_days': 0,          # set per site policy (docs/30)
    }

    with open(os.path.join(args.out_dir, 'mission_summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)

    with open(os.path.join(args.out_dir, 'features.csv'), 'w') as f:
        f.write('bin_start_s,bin_distance_m\n')
        for k in sorted(bins):
            f.write(f'{int(k * args.bin_seconds)},{bins[k]:.3f}\n')

    print(f'wrote: {args.out_dir}/mission_summary.json')
    print(f'wrote: {args.out_dir}/features.csv')
    print(f'distance={summary["total_distance_m"]} m, '
          f'dur={summary["duration_s"]} s, '
          f'peak={summary["peak_speed_mps"]} m/s, '
          f'occupancy_cells={summary["occupancy_cells"]}')


if __name__ == '__main__':
    main()
