"""Demo/simulation mode for the web control system (no robot, no ROS).

Generates believable robot data (heartbeat, odometry, battery, LiDAR/Kinect
obstacles, a synthetic map and depth frames) so the admin dashboard and user
panel can be demonstrated and screenshot. Enabled ONLY with `--sim`; the
`/api/demo/session` endpoint and `?demo=1` login hook are then available.
"""

import math
import threading
import time


class Simulator:
    def __init__(self, state, bridge):
        self.state = state
        self.bridge = bridge
        self._running = False
        self._thread = None
        # sim frames injected into the bridge renderers
        self._depth_w = 320
        self._depth_h = 120
        self._map_w = 60
        self._map_h = 60

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _run(self):
        t = 0.0
        while self._running:
            try:
                self._step(t)
            except Exception as e:
                print(f"[sim] error: {e}")
            t += 0.1
            time.sleep(0.1)

    def _step(self, t):
        s = self.state
        s.update_heartbeat(int(t * 10) % 256)
        # drive a slow circle in world units
        s.update_odom(1.6 * math.sin(0.12 * t), 1.6 * math.cos(0.12 * t),
                      0.12 * t, 0.28, 0.12)
        s.update_battery(12.65 - 0.002 * t, True)
        s.update_faults(0)
        s.set_mode("teleop" if t % 60 < 15 else "idle")
        # LiDAR: an obstacle slowly approaches the front sector
        front = max(0.28, 2.6 - (t % 12) * 0.5)
        s.update_lidar(front, 3.1, 2.4, front)
        s.update_lidar_rate()
        s.lidar.update(status="stop" if front <= 0.35 else
                       "slow" if front <= 0.70 else "free",
                       level="danger" if front <= 0.35 else
                       "warning" if front <= 0.70 else "ok",
                       avoidance={"hint": "simulated", "clamp": 0.0},
                       clusters=[{"angle_deg": 0.0, "range_m": round(front, 2),
                                  "width_deg": 8.0, "size_px": 16}])
        s.update_kinect(max(1.2, front), max(1.2, front))
        s.kinect.update(clusters=[{"angle_deg": 0.0,
                                   "range_m": round(max(1.2, front), 2),
                                   "width_deg": 6.0, "size_px": 12}])
        self._frames(t, front)

    def _frames(self, t, front_m):
        # synthetic depth (mm) — a near band in the middle, far background
        w, h = self._depth_w, self._depth_h
        mm = [3000] * (w * h)
        cx = w // 2
        for y in range(h):
            base = y * w
            for x in range(max(0, cx - 26), min(w, cx + 26)):
                mm[base + x] = int(front_m * 1000)
            for x in range(max(0, cx - 90), min(w, cx - 60)):
                mm[base + x] = 1400
        self.bridge._sim_depth = {"w": w, "h": h, "mm": mm}

        # synthetic occupancy grid (walls + inner obstacles)
        mw, mh = self._map_w, self._map_h
        grid = [0] * (mw * mh)
        for i in range(mw):
            grid[i] = 100                 # top wall
            grid[(mh - 1) * mw + i] = 100 # bottom wall
        for j in range(mh):
            grid[j * mw] = 100            # left wall
            grid[j * mw + mw - 1] = 100   # right wall
        for i in range(10, 14):           # inner block
            for j in range(8, 20):
                grid[j * mw + i] = 100
        for i in range(45, 52):
            for j in range(34, 48):
                grid[j * mw + i] = 100
        for k in range(0, 60, 6):         # keep a diagonal free-ish path visible
            grid[(k + 5) * mw + k] = 100
        self.bridge._sim_map = list(grid)
        self.bridge._sim_map_meta = {"width": mw, "height": mh,
                                     "resolution": 0.1,
                                     "origin_x": -3.0, "origin_y": -3.0}
