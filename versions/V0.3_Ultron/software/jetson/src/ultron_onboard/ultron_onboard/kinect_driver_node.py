#!/usr/bin/env python3
"""kinect_driver_node — acquire Kinect 1414 depth, crop ROI, publish.

Publishes (BEST_EFFORT):
  /kinect/depth/image_raw   Image (16UC1)  ~TARGET_FPS
  /kinect/depth/camera_info CameraInfo     ~1 Hz

v4.2r3: default 8 FPS, ROI 320x120 (160,180,320,120) to cut Nano load.
The Kinect must be on a DIRECT Jetson USB port (H1) — never the shared hub.
"""

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import Image, CameraInfo

_BEST_EFFORT = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST, depth=2)

# Kinect 1414 intrinsics (Bible §9 NODE 1)
KINECT_FX = 574.0527954
KINECT_FY = 574.0527954
KINECT_CX = 319.5
KINECT_CY = 239.5


class KinectDriverNode(Node):
    def __init__(self):
        super().__init__('kinect_driver')
        self.declare_parameter('roi_x', 160)
        self.declare_parameter('roi_y', 180)
        self.declare_parameter('roi_w', 320)
        self.declare_parameter('roi_h', 120)
        self.declare_parameter('target_fps', 8.0)
        self.declare_parameter('frame_id', 'kinect_depth_frame')
        self.declare_parameter('tilt_deg', 0.0)

        self._x = int(self.get_parameter('roi_x').value)
        self._y = int(self.get_parameter('roi_y').value)
        self._w = int(self.get_parameter('roi_w').value)
        self._h = int(self.get_parameter('roi_h').value)
        self._fps = float(self.get_parameter('target_fps').value)
        self._frame_id = self.get_parameter('frame_id').value

        self._depth_pub = self.create_publisher(Image, '/kinect/depth/image_raw',
                                                _BEST_EFFORT)
        self._info_pub = self.create_publisher(CameraInfo,
                                               '/kinect/depth/camera_info',
                                               _BEST_EFFORT)

        # Import lazily so the module loads even without libfreenect.
        self._fn = None
        self._fn_err = None
        try:
            import freenect  # python3-freenect
            self._fn = freenect
            if hasattr(freenect, 'sync_set_tilt_degs'):
                try:
                    freenect.sync_set_tilt_degs(
                        float(self.get_parameter('tilt_deg').value))
                except Exception as e:
                    self.get_logger().warn(f'tilt failed: {e}')
        except ImportError as e:
            self._fn_err = str(e)
            self.get_logger().error(f'python3-freenect unavailable: {e}')

        interval = 1.0 / self._fps
        self.create_timer(interval, self._capture)
        self._info_tick = 0
        self.get_logger().info(
            f'Kinect driver: ROI=({self._x},{self._y},{self._w},{self._h}) '
            f'FPS={self._fps:.0f}')

    def _capture(self):
        if self._fn is None:
            if self._fn_err is not None:
                self.get_logger().warn('Kinect driver disabled: '
                                       f'{self._fn_err}')
                self._fn_err = None  # log once
            return
        try:
            depth, _ts = self._fn.sync_get_depth()
        except Exception as e:
            self.get_logger().error(f'Kinect frame error: {e}')
            return
        if depth is None:
            return

        # Crop ROI (x, y, w, h). Depth is 640x480 uint16 (mm, 11-bit).
        roi = depth[self._y:self._y + self._h, self._x:self._x + self._w]

        stamp = self.get_clock().now().to_msg()
        img = Image()
        img.header.stamp = stamp
        img.header.frame_id = self._frame_id
        img.height = roi.shape[0]
        img.width = roi.shape[1]
        img.encoding = '16UC1'
        img.is_bigendian = 0
        img.step = roi.shape[1] * 2
        img.data = roi.astype('<u2').tobytes()
        self._depth_pub.publish(img)

        # CameraInfo for the cropped ROI (~1 Hz).
        self._info_tick += 1
        if self._info_tick % max(1, int(round(self._fps))) == 0:
            self._info_pub.publish(self._camera_info(stamp))

    def _camera_info(self, stamp):
        ci = CameraInfo()
        ci.header.stamp = stamp
        ci.header.frame_id = self._frame_id
        ci.height = self._h
        ci.width = self._w
        ci.distortion_model = 'plumb_bob'
        ci.d = [0.0] * 5
        # Crop shifts the principal point by the ROI offset.
        cx = KINECT_CX - self._x
        cy = KINECT_CY - self._y
        ci.k = [KINECT_FX, 0.0, cx,
                0.0, KINECT_FY, cy,
                0.0, 0.0, 1.0]
        ci.r = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
        ci.p = [KINECT_FX, 0.0, cx, 0.0,
                0.0, KINECT_FY, cy, 0.0,
                0.0, 0.0, 1.0, 0.0]
        ci.binning_x = 0
        ci.binning_y = 0
        ci.roi.x_offset = self._x
        ci.roi.y_offset = self._y
        ci.roi.height = self._h
        ci.roi.width = self._w
        ci.roi.do_rectify = True
        return ci


def main(args=None):
    rclpy.init(args=args)
    node = KinectDriverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
