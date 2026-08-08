#!/usr/bin/env python3
"""depth_to_scan_node — convert the ROI depth middle row to a LaserScan.

P1 (engineering audit): the camera model now comes from the LIVE
/kinect/depth/camera_info message (fx, cx) instead of hardcoded intrinsics, so
the Kinect 1414 is a drop-in-replaceable module (RealSense D455 publishes its
own camera_info and this node adapts without a rebuild). The kinect_driver
already publishes the ROI-corrected K matrix (cx shifted by the ROI offset).

Fallback: before the first camera_info arrives (or if it stops), the node uses
the declared kinect_fx / cx_roi params so a stale-info or info-less driver
still produces a valid scan.

v4.2r3: matches the 8 FPS / 320x120 ROI. Applies the -10° mount tilt
correction, publishes BEST_EFFORT ~8 Hz with range_max = 4.0 m (mid-field
fusion zone only — LiDAR owns < 1.0 m).

Publishes: /kinect/scan  (sensor_msgs/LaserScan, frame = kinect_depth_frame)
Subscribes: /kinect/depth/image_raw (Image 16UC1)
            /kinect/depth/camera_info (CameraInfo, ROI-corrected K)
"""

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image, CameraInfo, LaserScan

from ultron_onboard.depth_scan_logic import depth_row_to_scan, \
    select_camera_model

_BEST_EFFORT = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST, depth=2)


class DepthToScanNode(Node):
    def __init__(self):
        super().__init__('depth_to_scan')
        self.declare_parameter('roi_w', 320)
        self.declare_parameter('roi_h', 120)
        # Fallback intrinsics (used only until / until camera_info arrives).
        self.declare_parameter('kinect_fx', 574.0527954)
        self.declare_parameter('cx_roi', 159.5)
        self.declare_parameter('tilt_deg', -10.0)
        self.declare_parameter('min_range_m', 0.5)
        self.declare_parameter('max_range_m', 4.0)
        self.declare_parameter('frame_id', 'kinect_depth_frame')

        self._w = int(self.get_parameter('roi_w').value)
        self._h = int(self.get_parameter('roi_h').value)
        self._fallback_fx = float(self.get_parameter('kinect_fx').value)
        self._fallback_cx = float(self.get_parameter('cx_roi').value)
        self._tilt = math.radians(float(self.get_parameter('tilt_deg').value))
        self._min = float(self.get_parameter('min_range_m').value)
        self._max = float(self.get_parameter('max_range_m').value)
        self._frame = self.get_parameter('frame_id').value

        # Live camera model from camera_info (P1). None until the first info.
        self._fx = self._fallback_fx
        self._cx = self._fallback_cx
        self._using_live_info = False

        self.create_subscription(Image, '/kinect/depth/image_raw',
                                 self._img_cb, _BEST_EFFORT)
        self.create_subscription(CameraInfo, '/kinect/depth/camera_info',
                                 self._info_cb, _BEST_EFFORT)
        self._scan_pub = self.create_publisher(LaserScan, '/kinect/scan',
                                               _BEST_EFFORT)

    def _info_cb(self, msg):
        # K = [fx 0 cx; 0 fy cy; 0 0 1] — ROI-corrected by the driver.
        fx, cx, live = select_camera_model(
            list(msg.k), self._fallback_fx, self._fallback_cx)
        if live and not self._using_live_info:
            self._fx, self._cx = fx, cx
            self._using_live_info = True
            self.get_logger().info(
                'depth_to_scan: using live camera_info '
                f'(fx={self._fx:.2f} cx={self._cx:.2f})')
        elif not live and self._using_live_info:
            self._fx, self._cx = fx, cx
            self._using_live_info = False
            self.get_logger().warn('depth_to_scan: camera_info K invalid; '
                                   'falling back to params')

    def _img_cb(self, msg):
        if msg.encoding != '16UC1':
            self.get_logger().warn(
                f'Unexpected encoding {msg.encoding}; expected 16UC1')
            return
        data = memoryview(msg.data).cast('H')   # native-endian uint16
        try:
            ranges, angle_min, angle_inc = depth_row_to_scan(
                data, msg.width, msg.height, self._fx, self._cx,
                self._tilt, self._min, self._max)
        except ValueError as e:
            self.get_logger().warn(f'depth_to_scan: {e}')
            return

        scan = LaserScan()
        scan.header.stamp = msg.header.stamp
        scan.header.frame_id = self._frame
        scan.angle_min = angle_min
        scan.angle_max = angle_min + angle_inc * (len(ranges) - 1)
        scan.angle_increment = angle_inc
        scan.time_increment = 0.0
        scan.scan_time = 1.0 / 8.0
        scan.range_min = self._min
        scan.range_max = self._max
        scan.ranges = ranges
        self._scan_pub.publish(scan)


def main(args=None):
    rclpy.init(args=args)
    node = DepthToScanNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
