#!/usr/bin/env python3
"""serial_node — ROS 2 <-> Arduino bridge over USB serial.

Canonical behavior (Bible Section 9, NODE 4):
  SUB  /safe_cmd_vel      (Twist,  RELIABLE) -> PKT_VELOCITY (0x01)
  SUB  /ultron/heartbeat  (UInt8,  RELIABLE) -> PKT_HEARTBEAT (0x05)
  SUB  /ultron/clear_faults (Empty, RELIABLE) -> PKT_CLEAR_FAULTS (0x07) [B7]
  PUB  /odom              (Odometry, RELIABLE) <- PKT_ENCODER (0x01), ~30 Hz
  PUB  /imu/data          (Imu,     RELIABLE) <- PKT_IMU (0x02)
  PUB  /battery/state     (BatteryState, RELIABLE) <- PKT_BATTERY (0x03)
  PUB  /ultron/fault      (UInt8,   RELIABLE) <- PKT_FAULT (0x04)

v4.2 B4: this node does NOT publish odom->base_link TF — the laptop EKF is
the single publisher of that transform.
"""

import math
import threading
import time

import serial
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu, BatteryState
from geometry_msgs.msg import Twist
from std_msgs.msg import UInt8, Empty

from ultron_onboard import ultron_protocol as proto

_RECONNECT_DELAY_S = 2.0


class SerialNode(Node):
    def __init__(self):
        super().__init__('ultron_serial_node')
        self.declare_parameter('serial_port', '/dev/ultron_arduino')
        self.declare_parameter('serial_baud', 115200)

        self._port = self.get_parameter('serial_port').value
        self._baud = self.get_parameter('serial_baud').value

        rel = QoSProfile(reliability=ReliabilityPolicy.RELIABLE,
                         history=HistoryPolicy.KEEP_LAST, depth=10)

        self.create_subscription(Twist, '/safe_cmd_vel', self.cmd_cb, rel)
        self.create_subscription(UInt8, '/ultron/heartbeat', self.hb_cb, rel)
        self.create_subscription(Empty, '/ultron/clear_faults',
                                 self.clear_cb, rel)          # v4.2 B7

        self._odom_pub = self.create_publisher(Odometry, '/odom', rel)
        self._imu_pub = self.create_publisher(Imu, '/imu/data', rel)
        self._bat_pub = self.create_publisher(BatteryState, '/battery/state', rel)
        self._flt_pub = self.create_publisher(UInt8, '/ultron/fault', rel)

        # v4.2 B4: NO TransformBroadcaster here; EKF owns odom->base_link.
        self._x = self._y = self._theta = 0.0
        self._pl = self._pr = None
        self._last_ms = None

        self._lock = threading.Lock()
        self._running = True
        self._ser = None
        self._parser = proto.FrameParser()

        # Connect in the RX thread so __init__ never blocks on a missing
        # serial device (robot can boot without the Arduino attached).
        threading.Thread(target=self._rx_loop, daemon=True).start()

    # ---- serial lifecycle -------------------------------------------------
    def _connect(self):
        """One connection attempt; returns True on success."""
        try:
            self._ser = serial.Serial(self._port, self._baud, timeout=0.1)
            self.get_logger().info(
                f'Serial connected: {self._port} @ {self._baud}')
            return True
        except serial.SerialException as e:
            self.get_logger().warn(
                f'Serial unavailable ({e}); retrying in '
                f'{_RECONNECT_DELAY_S:.0f}s')
            self._ser = None
            return False

    def _write(self, pkt):
        if self._ser is None:
            return
        try:
            with self._lock:
                self._ser.write(pkt)
        except serial.SerialException as e:
            self.get_logger().error(f'Serial write failed: {e}')

    def _rx_loop(self):
        while self._running:
            if self._ser is None:
                if not self._connect():
                    time.sleep(_RECONNECT_DELAY_S)
                continue
            try:
                b = self._ser.read(1)
                if not b:
                    continue
                frame = self._parser.push(b[0])
                if frame:
                    self._dispatch(*frame)
            except serial.SerialException as e:
                self.get_logger().error(
                    f'Serial read failed: {e}; reconnecting')
                try:
                    self._ser.close()
                except Exception:
                    pass
                self._ser = None
                time.sleep(_RECONNECT_DELAY_S)

    # ---- inbound subscriptions -------------------------------------------
    def cmd_cb(self, msg):
        pkt = proto.velocity_packet(msg.linear.x, msg.angular.z)
        self._write(pkt)

    def hb_cb(self, msg):
        self._write(proto.build_pkt(proto.PKT_HEARTBEAT, bytes([msg.data & 0xFF])))

    def clear_cb(self, msg):               # v4.2 B7
        self._write(proto.build_pkt(proto.PKT_CLEAR_FAULTS, b''))

    # ---- outbound dispatch ------------------------------------------------
    def _dispatch(self, pkt_type, payload):
        now = self.get_clock().now().to_msg()
        if pkt_type == proto.PKT_ENCODER and len(payload) == 12:
            lt, rt, ts = proto.unpack_encoder(payload)
            self._odom(lt, rt, ts, now)
        elif pkt_type == proto.PKT_IMU and len(payload) == 24:
            self._imu(*proto.unpack_imu(payload), stamp=now)
        elif pkt_type == proto.PKT_BATTERY and len(payload) == 4:
            import struct
            v, = struct.unpack('>f', payload)
            m = BatteryState()
            m.header.stamp = now
            m.header.frame_id = 'base_link'
            m.voltage = float(v)
            m.present = True
            self._bat_pub.publish(m)
        elif pkt_type == proto.PKT_FAULT and len(payload) == 1:
            m = UInt8()
            m.data = payload[0]
            self._flt_pub.publish(m)
            self.get_logger().warn(
                f'Fault:0x{m.data:02X} ESTOP={bool(m.data & 1)} '
                f'HB={bool(m.data & 64)}')

    def _odom(self, lt, rt, arduino_ms, stamp):
        # Real inter-packet dt from Arduino ts_ms (encoder ~33 Hz).
        if self._pl is None:
            self._pl = lt
            self._pr = rt
            self._last_ms = arduino_ms
            return
        dt = (arduino_ms - self._last_ms) / 1000.0
        self._last_ms = arduino_ms
        if dt <= 0.0 or dt > 0.5:          # rollover or spurious delta
            self._pl = lt
            self._pr = rt
            return
        dl = (lt - self._pl) * proto.METERS_PER_TICK
        dr = (rt - self._pr) * proto.METERS_PER_TICK
        self._pl = lt
        self._pr = rt
        dc = (dl + dr) / 2.0
        dth = (dr - dl) / proto.WHEEL_SEP_M
        self._x += dc * math.cos(self._theta + dth / 2.0)
        self._y += dc * math.sin(self._theta + dth / 2.0)
        self._theta += dth
        qz = math.sin(self._theta / 2.0)
        qw = math.cos(self._theta / 2.0)
        o = Odometry()
        o.header.stamp = stamp
        o.header.frame_id = 'odom'
        o.child_frame_id = 'base_link'
        o.pose.pose.position.x = self._x
        o.pose.pose.position.y = self._y
        o.pose.pose.orientation.z = qz
        o.pose.pose.orientation.w = qw
        o.twist.twist.linear.x = dc / dt       # real dt (v4.1)
        o.twist.twist.angular.z = dth / dt
        o.pose.covariance[0] = 0.01
        o.pose.covariance[7] = 0.01
        o.pose.covariance[35] = 0.05
        self._odom_pub.publish(o)
        # v4.2 B4: do NOT publish odom->base_link TF here.

    def _imu(self, ax, ay, az, gx, gy, gz, stamp):
        m = Imu()
        m.header.stamp = stamp
        m.header.frame_id = 'imu_link'
        m.linear_acceleration.x = ax
        m.linear_acceleration.y = ay
        m.linear_acceleration.z = az
        m.angular_velocity.x = gx
        m.angular_velocity.y = gy
        m.angular_velocity.z = gz
        m.orientation_covariance[0] = -1
        m.angular_velocity_covariance[0] = 0.01
        m.linear_acceleration_covariance[0] = 0.1
        self._imu_pub.publish(m)

    def destroy_node(self):
        self._running = False
        if self._ser is not None:
            try:
                with self._lock:
                    self._ser.write(proto.build_pkt(proto.PKT_ESTOP, b''))
            except serial.SerialException:
                pass
            try:
                self._ser.close()
            except Exception:
                pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = SerialNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
