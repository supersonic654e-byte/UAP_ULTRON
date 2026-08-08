#!/usr/bin/env python3
"""safety_node — enforce safety zones and fuse LiDAR + Kinect (Bible §10).

Zones (params, defaults from the Bible):
  STOP zone:   <= 0.35 m -> zero velocity (both linear and angular)
  SLOW zone:   0.35-0.70 m -> scale = (d-0.35)/(0.70-0.35); forward motion is
               scaled, reverse (escape) passes through
  FREE zone:   > 0.70 m -> command passes (clamped to max_speed)

Fusion rules:
  LiDAR < 1.0 m governs EXCLUSIVELY.
  Kinect contributes only in [1.0, 3.0] m.
  LiDAR stale > 1.0 s -> STOP. Kinect stale > 1.0 s -> LiDAR only.

Outputs: /safe_cmd_vel (20 Hz), /ultron/heartbeat (10 Hz).
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist
from std_msgs.msg import UInt8

from ultron_onboard.safety_logic import min_range_in_front, compute_safe_twist

_BEST_EFFORT = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST, depth=2)
_RELIABLE = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    history=HistoryPolicy.KEEP_LAST, depth=10)


class SafetyNode(Node):
    def __init__(self):
        super().__init__('ultron_safety_node')
        self.declare_parameter('stop_dist', 0.35)
        self.declare_parameter('slow_dist', 0.70)
        self.declare_parameter('lidar_priority_dist', 1.0)
        self.declare_parameter('kinect_min', 1.0)
        self.declare_parameter('kinect_max', 3.0)
        self.declare_parameter('front_arc_deg', 60.0)
        self.declare_parameter('max_speed_mps', 0.45)
        self.declare_parameter('lidar_stale_sec', 1.0)
        self.declare_parameter('kinect_stale_sec', 1.0)
        self.declare_parameter('enforce_rate', 20.0)
        self.declare_parameter('heartbeat_rate', 10.0)

        self._stop = self.get_parameter('stop_dist').value
        self._slow = self.get_parameter('slow_dist').value
        self._lidar_prio = self.get_parameter('lidar_priority_dist').value
        self._kin_min = self.get_parameter('kinect_min').value
        self._kin_max = self.get_parameter('kinect_max').value
        self._arc = self.get_parameter('front_arc_deg').value
        self._max_speed = self.get_parameter('max_speed_mps').value

        self.create_subscription(Twist, '/cmd_vel', self._cmd_cb, _RELIABLE)
        self.create_subscription(LaserScan, '/scan', self._scan_cb, _BEST_EFFORT)
        self.create_subscription(LaserScan, '/kinect/scan',
                                 self._kin_cb, _BEST_EFFORT)
        self._safe_pub = self.create_publisher(Twist, '/safe_cmd_vel', _RELIABLE)
        self._hb_pub = self.create_publisher(UInt8, '/ultron/heartbeat', _RELIABLE)

        self._cmd = Twist()
        self._scan = None
        self._kinect = None
        self._scan_t = None
        self._kin_t = None
        self._seq = 0

        dt = 1.0 / self.get_parameter('enforce_rate').value
        self.create_timer(dt, self._enforce)
        dt_hb = 1.0 / self.get_parameter('heartbeat_rate').value
        self.create_timer(dt_hb, self._heartbeat)
        self.get_logger().info(
            f'Safety node active: STOP<={self._stop}m SLOW<={self._slow}m')

    def _cmd_cb(self, msg):
        self._cmd = msg

    def _scan_cb(self, msg):
        self._scan = msg
        self._scan_t = self.get_clock().now()

    def _kin_cb(self, msg):
        self._kinect = msg
        self._kin_t = self.get_clock().now()

    def _enforce(self):
        now = self.get_clock().now()
        lidar_stale = (self._scan is None or
                       (now - self._scan_t).nanoseconds > self._scan_stale_ns())
        kinect_stale = (self._kinect is None or
                        (now - self._kin_t).nanoseconds > self._kin_stale_ns())

        lidar_d = None
        if self._scan is not None:
            lidar_d, _ = min_range_in_front(
                self._scan.ranges, self._scan.angle_min,
                self._scan.angle_increment, self._arc)
        kin_d = None
        if self._kinect is not None:
            kin_d, _ = min_range_in_front(
                self._kinect.ranges, self._kinect.angle_min,
                self._kinect.angle_increment, self._arc)

        if lidar_d is None and not lidar_stale:
            lidar_d = float('inf')            # scan valid but empty front arc

        lin, ang = compute_safe_twist(
            self._cmd.linear.x, self._cmd.angular.z,
            lidar_d, kin_d, lidar_stale, kinect_stale,
            stop=self._stop, slow=self._slow,
            lidar_priority=self._lidar_prio, kin_min=self._kin_min,
            kin_max=self._kin_max, max_speed=self._max_speed)

        out = Twist()
        out.linear.x = lin
        out.angular.z = ang
        self._safe_pub.publish(out)

    def _heartbeat(self):
        self._seq = (self._seq + 1) & 0xFF
        m = UInt8()
        m.data = self._seq
        self._hb_pub.publish(m)

    def _scan_stale_ns(self):
        return int(self.get_parameter('lidar_stale_sec').value * 1e9)

    def _kin_stale_ns(self):
        return int(self.get_parameter('kinect_stale_sec').value * 1e9)


def main(args=None):
    rclpy.init(args=args)
    node = SafetyNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
