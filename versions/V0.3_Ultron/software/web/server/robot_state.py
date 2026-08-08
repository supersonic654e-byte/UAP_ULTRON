"""Robot live-state model and command gating (no ROS imports).

The web server keeps a single mutable `RobotState` that the ROS bridge
updates and WebSocket handlers stream. Command gating enforces the V0.3
safety rules server-side, independently of ROS:
  - teleop clamp at MAX_TELEOP_MPS (0.45)
  - autonomous/goal velocity clamp at MAX_GOAL_MPS (0.35)
  - commands rejected while the robot is not "live" (heartbeat stale)
  - admin may operate ONLY after the 10-char admin password is verified
    (role 'admin_control'); otherwise the admin dashboard is read-only.
"""

import math
import threading
import time

MAX_TELEOP_MPS = 0.45       # matches firmware MAX_SPEED_MPS
MAX_GOAL_MPS = 0.35         # Nav2 autonomous cap (B6)
MAX_YAW_RATE = 1.0
LIVE_TIMEOUT_S = 1.5        # heartbeat freshness for accepting commands

FAULT_NAMES = {
    0: "ESTOP", 1: "OVERCURRENT", 2: "WATCHDOG", 3: "IMU",
    4: "ENCODER", 5: "BATTERY", 6: "HEARTBEAT", 7: "RESERVED",
}


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def fault_bits_to_names(flags):
    return [FAULT_NAMES.get(i) for i in range(8) if flags & (1 << i)]


class RobotState:
    """Latest snapshot of everything the dashboards show."""

    def __init__(self):
        self.lock = threading.RLock()
        self.connected = False
        self.heartbeat_seq = 0
        self.heartbeat_time = 0.0
        self.odom = {"x": 0.0, "y": 0.0, "theta": 0.0,
                     "vx": 0.0, "wz": 0.0}
        self.battery = {"voltage": 0.0, "present": False}
        self.faults = {"flags": 0, "names": []}
        self.lidar = {"front": None, "left": None, "right": None,
                      "min": None, "rate": 0.0}
        self.kinect = {"front": None, "min": None}
        self.mode = "idle"          # idle | teleop | navigating | stopped
        self.last_cmd = {"vx": 0.0, "wz": 0.0, "ts": 0.0}
        self.ros_ready = False
        self.lidar_rate = 0.0
        self.last_scan_time = 0.0

    # ---- updates (called by the ROS bridge thread) ------------------------
    def update_heartbeat(self, seq):
        with self.lock:
            self.heartbeat_seq = seq
            self.heartbeat_time = time.time()
            self.connected = True

    def update_odom(self, x, y, theta, vx, wz):
        with self.lock:
            self.odom.update(x=x, y=y, theta=theta, vx=vx, wz=wz)

    def update_battery(self, voltage, present):
        with self.lock:
            self.battery.update(voltage=round(voltage, 3), present=bool(present))

    def update_faults(self, flags):
        with self.lock:
            self.faults.update(flags=flags, names=fault_bits_to_names(flags))

    def update_lidar(self, front, left, right, rmin):
        with self.lock:
            self.lidar.update(front=front, left=left, right=right, min=rmin)
            self.last_scan_time = time.time()

    def update_lidar_rate(self):
        now = time.time()
        dt = now - self.last_scan_time
        with self.lock:
            self.lidar_rate = round(1.0 / dt, 2) if dt > 0 else 0.0
            self.last_scan_time = now

    def update_kinect(self, front, rmin):
        with self.lock:
            self.kinect.update(front=front, min=rmin)

    def set_mode(self, mode):
        with self.lock:
            self.mode = mode

    # ---- readers ----------------------------------------------------------
    def snapshot(self):
        with self.lock:
            return {
                "connected": self.connected,
                "heartbeat_seq": self.heartbeat_seq,
                "last_heartbeat_age_s": round(time.time() - self.heartbeat_time,
                                              2) if self.heartbeat_time else None,
                "odom": dict(self.odom),
                "battery": dict(self.battery),
                "faults": dict(self.faults),
                "lidar": dict(self.lidar),
                "kinect": dict(self.kinect),
                "mode": self.mode,
                "last_cmd": dict(self.last_cmd),
                "ros_ready": self.ros_ready,
            }

    def is_live(self):
        if not self.connected:
            return False
        return (time.time() - self.heartbeat_time) < LIVE_TIMEOUT_S

    # ---- command gating ---------------------------------------------------
    def gate_twist(self, vx, wz, role, now=None):
        """Return (ok, reason, vx, wz) applying all safety rules."""
        now = now or time.time()
        if role not in ("user", "admin_control"):
            return False, "not_authorized", 0.0, 0.0
        if not self.is_live():
            return False, "robot_not_live", 0.0, 0.0
        vx = float(vx)
        wz = float(wz)
        vx = clamp(vx, -MAX_TELEOP_MPS, MAX_TELEOP_MPS)
        wz = clamp(wz, -MAX_YAW_RATE, MAX_YAW_RATE)
        return True, "ok", round(vx, 3), round(wz, 3)

    def gate_goal_speed(self, speed):
        """Clamp autonomous goal speed to the B6 cap."""
        return clamp(float(speed), 0.0, MAX_GOAL_MPS)

    def record_cmd(self, vx, wz):
        with self.lock:
            self.last_cmd.update(vx=round(vx, 3), wz=round(wz, 3),
                                 ts=time.time())
