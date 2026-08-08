"""ROS 2 bridge for the web control system (laptop side, rclpy).

Subscribes to the robot's live topics over CycloneDDS and publishes control
commands back. Runs in its own thread so the FastAPI server stays responsive.
All ROS imports are lazy/guarded so the package imports and is unit-testable
without ROS (the server then runs in demo/sim mode).

Topics (matching the V0.3 stack, Bible §9/§7.4):
  SUB /odom, /scan, /kinect/scan, /kinect/depth/image_raw, /map,
      /battery/state, /ultron/fault, /ultron/heartbeat, /ultron/current,
      /safe_cmd_vel
  PUB /cmd_vel, /goal_pose, /ultron/clear_faults
  ACTION /navigate_to_pose (nav2_msgs) — "go to <waypoint>"
"""

import math
import threading
import time

from server import detection, map_render
from server.robot_state import RobotState


class RosBridge:
    """Optional ROS bridge. All ROS access is behind availability checks."""

    def __init__(self, state: RobotState, sim_mode: bool = False):
        self.state = state
        self.sim_mode = sim_mode
        self._thread = None
        self._running = False
        self._rclpy = None
        self._node = None
        self._depth = {"w": 0, "h": 0, "mm": []}
        self._map = None
        self._map_meta = {}
        self._nav_client = None
        self._last_cmd_pub = 0.0
        # sim frames injected by the Simulator (server/simulator.py)
        self._sim_depth = None
        self._sim_map = None
        self._sim_map_meta = {}

    # ---- lifecycle --------------------------------------------------------
    @property
    def available(self):
        return self._rclpy is not None and self._node is not None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._rclpy is not None and self._node is not None:
            try:
                self._node.destroy_node()
            except Exception:
                pass
        try:
            if self._rclpy is not None:
                self._rclpy.shutdown()
        except Exception:
            pass

    # ---- ROS thread -------------------------------------------------------
    def _run(self):
        try:
            import rclpy
            from rclpy.qos import (QoSProfile, ReliabilityPolicy,
                                   HistoryPolicy, DurabilityPolicy)
            self._rclpy = rclpy
            rclpy.init(args=None)
            self._node = rclpy.create_node("ultron_web_bridge")
        except Exception as e:  # no ROS in this environment
            self.state.ros_ready = False
            print(f"[web] ROS bridge unavailable: {e}")
            while self._running:
                time.sleep(1.0)
            return

        best_effort = QoSProfile(reliability=ReliabilityPolicy.BEST_EFFORT,
                                 history=HistoryPolicy.KEEP_LAST, depth=2)
        reliable = QoSProfile(reliability=ReliabilityPolicy.RELIABLE,
                              history=HistoryPolicy.KEEP_LAST, depth=10)
        transient = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)

        from sensor_msgs.msg import LaserScan, Image, BatteryState
        from nav_msgs.msg import Odometry
        from std_msgs.msg import UInt8, Float32
        from geometry_msgs.msg import Twist

        self._node.create_subscription(Odometry, "/odom", self._odom_cb,
                                       reliable)
        self._node.create_subscription(LaserScan, "/scan", self._scan_cb,
                                       best_effort)
        self._node.create_subscription(LaserScan, "/kinect/scan",
                                       self._kinect_cb, best_effort)
        self._node.create_subscription(Image, "/kinect/depth/image_raw",
                                       self._depth_cb, best_effort)
        self._node.create_subscription(BatteryState, "/battery/state",
                                       self._battery_cb, reliable)
        self._node.create_subscription(UInt8, "/ultron/fault",
                                       self._fault_cb, reliable)
        self._node.create_subscription(UInt8, "/ultron/heartbeat",
                                       self._heartbeat_cb, reliable)
        self._node.create_subscription(Float32, "/ultron/current_left",
                                       self._current_left_cb, reliable)
        self._node.create_subscription(Float32, "/ultron/current_right",
                                       self._current_right_cb, reliable)
        self._node.create_subscription(Twist, "/safe_cmd_vel",
                                       self._safe_vel_cb, reliable)

        # /map is TransientLocal from map_server/slam_toolbox.
        try:
            from nav_msgs.msg import OccupancyGrid
            self._node.create_subscription(OccupancyGrid, "/map",
                                           self._map_cb, transient)
        except Exception:
            pass

        from geometry_msgs.msg import PoseStamped
        from std_msgs.msg import Empty
        self._cmd_pub = self._node.create_publisher(Twist, "/cmd_vel", reliable)
        self._goal_pub = self._node.create_publisher(PoseStamped, "/goal_pose",
                                                     reliable)
        self._clear_pub = self._node.create_publisher(Empty,
                                                      "/ultron/clear_faults",
                                                      reliable)
        self._setup_nav_client()

        self.state.ros_ready = True
        print("[web] ROS bridge connected — streaming robot topics")
        while self._running:
            try:
                rclpy.spin_once(self._node, timeout_sec=0.1)
            except Exception as e:
                print(f"[web] spin error: {e}")
                time.sleep(1.0)

    def _setup_nav_client(self):
        try:
            from nav2_msgs.action import NavigateToPose
            self._nav_client = self._node.create_action_client(
                NavigateToPose, "/navigate_to_pose")
        except Exception:
            self._nav_client = None

    # ---- ROS callbacks ----------------------------------------------------
    def _odom_cb(self, msg):
        self.state.update_odom(
            msg.pose.pose.position.x, msg.pose.pose.position.y,
            _yaw(msg.pose.pose.orientation),
            msg.twist.twist.linear.x, msg.twist.twist.angular.z)

    def _scan_cb(self, msg):
        ranges = _downsample(msg.ranges, 120)
        try:
            status = detection.obstacle_status(ranges, msg.angle_min,
                                               msg.angle_increment)
            clusters = detection.detect_clusters(ranges, msg.angle_min,
                                                 msg.angle_increment)
            self.state.update_lidar(status["front_m"], status["left_m"],
                                    status["right_m"], status["front_m"])
            self.state.update_lidar_status(status["state"], status["level"],
                                           status["avoidance"], clusters)
        except Exception:
            pass
        self.state.update_lidar_rate()

    def _kinect_cb(self, msg):
        ranges = _downsample(msg.ranges, 120)
        status = detection.obstacle_status(ranges, msg.angle_min,
                                           msg.angle_increment)
        self.state.update_kinect(status["front_m"], status["front_m"])
        clusters = detection.detect_clusters(ranges, msg.angle_min,
                                             msg.angle_increment)
        self.state.update_kinect_clusters(clusters)

    def _depth_cb(self, msg):
        try:
            if msg.encoding != "16UC1":
                return
            view = memoryview(msg.data).cast("H")
            self._depth = {"w": msg.width, "h": msg.height, "mm": list(view)}
        except Exception:
            pass

    def _map_cb(self, msg):
        try:
            self._map = list(msg.data)
            self._map_meta = {"width": msg.info.width,
                              "height": msg.info.height,
                              "resolution": msg.info.resolution,
                              "origin_x": msg.info.origin.position.x,
                              "origin_y": msg.info.origin.position.y}
        except Exception:
            pass

    def _battery_cb(self, msg):
        self.state.update_battery(msg.voltage, msg.present)

    def _fault_cb(self, msg):
        self.state.update_faults(msg.data)

    def _heartbeat_cb(self, msg):
        self.state.update_heartbeat(msg.data)

    def _current_left_cb(self, msg):
        right = self.state.current["right"]
        self.state.update_current(msg.data, right)

    def _current_right_cb(self, msg):
        left = self.state.current["left"]
        self.state.update_current(left, msg.data)

    def _safe_vel_cb(self, msg):
        self.state.update_safe_vel(msg.linear.x, msg.angular.z)

    # ---- streams (called by web handlers) ---------------------------------
    def depth_png(self, min_m=0.3, max_m=4.0):
        if self._sim_depth:
            d = self._sim_depth
            w, h = d["w"], d["h"]
            row = (h // 2) * w
            row_m = [d["mm"][row + x] / 1000.0 for x in range(w)]
            obstacles, _ = detection.depth_row_obstacles(
                row_m, 574.0527954, 159.5)
            return map_render.render_depth(d["mm"], w, h, min_m, max_m,
                                           obstacles)
        if not self._depth["mm"]:
            return None
        w = self._depth["w"]
        row = (self._depth["h"] // 2) * w
        row_m = [self._depth["mm"][row + x] / 1000.0 for x in range(w)]
        obstacles, _ = detection.depth_row_obstacles(
            row_m, 574.0527954, 159.5)
        return map_render.render_depth(self._depth["mm"], w,
                                       self._depth["h"],
                                       min_m, max_m, obstacles)

    def map_png(self):
        if self._sim_map is not None:
            m = self._sim_map_meta
            robot = (self.state.odom["x"], self.state.odom["y"])
            return map_render.render_map(
                self._sim_map, m["width"], m["height"], m["resolution"],
                m["origin_x"], m["origin_y"], robot, self.state.odom["theta"])
        if self._map is None:
            return None
        m = self._map_meta
        robot = (self.state.odom["x"], self.state.odom["y"]) \
            if self.state.odom else None
        theta = self.state.odom["theta"]
        return map_render.render_map(
            self._map, m["width"], m["height"], m["resolution"],
            m["origin_x"], m["origin_y"], robot, theta)

    def map_meta(self):
        return dict(self._map_meta)

    # ---- command publishing -----------------------------------------------
    def publish_twist(self, vx, wz):
        if self.sim_mode:
            return True
        if not self.available:
            return False
        from geometry_msgs.msg import Twist
        msg = Twist()
        msg.linear.x = float(vx)
        msg.angular.z = float(wz)
        self._cmd_pub.publish(msg)
        return True

    def stop_robot(self):
        if self.sim_mode:
            return True
        if not self.available:
            return False
        from geometry_msgs.msg import Twist
        msg = Twist()
        self._cmd_pub.publish(msg)
        return True

    def clear_faults(self):
        if self.sim_mode:
            return True
        if not self.available:
            return False
        from std_msgs.msg import Empty
        self._clear_pub.publish(Empty())
        return True

    def send_goal(self, x, y, theta):
        """Navigate-to-pose via Nav2 action; falls back to /goal_pose topic."""
        if self.sim_mode:
            return {"ok": True, "via": "simulate"}
        if not self.available:
            return {"ok": False, "reason": "bridge_offline"}
        if self._nav_client is not None:
            try:
                from nav2_msgs.action import NavigateToPose
                goal = NavigateToPose.Goal()
                goal.pose.header.frame_id = "map"
                goal.pose.header.stamp = self._node.get_clock().now().to_msg()
                goal.pose.pose.position.x = float(x)
                goal.pose.pose.position.y = float(y)
                goal.pose.pose.orientation.z = float(math.sin(theta / 2))
                goal.pose.pose.orientation.w = float(math.cos(theta / 2))
                if not self._nav_client.wait_for_server(timeout_sec=5.0):
                    return {"ok": False, "reason": "nav_server_down"}
                future = self._nav_client.send_goal_async(goal)
                future.add_done_callback(self._goal_accept)
                return {"ok": True, "via": "navigate_to_pose"}
            except Exception as e:
                return {"ok": False, "reason": str(e)}
        from geometry_msgs.msg import PoseStamped
        msg = PoseStamped()
        msg.header.frame_id = "map"
        msg.header.stamp = self._node.get_clock().now().to_msg()
        msg.pose.position.x = float(x)
        msg.pose.position.y = float(y)
        msg.pose.orientation.z = float(math.sin(theta / 2))
        msg.pose.pose.orientation.w = float(math.cos(theta / 2))
        self._goal_pub.publish(msg)
        return {"ok": True, "via": "goal_pose"}

    def _goal_accept(self, future):
        try:
            f2 = future.result().get_result_async()
            f2.add_done_callback(self._goal_result)
        except Exception:
            pass

    def _goal_result(self, future):
        try:
            result = future.result()
            status = result.status if hasattr(result, "status") else -1
            print(f"[web] nav goal result status={status}")
        except Exception:
            pass

    def robot_pose_in_map(self):
        """(x, y, theta) of base_link in the map frame (map->odom from
        AMCL/SLAM + odom pose from /odom). We read odom pose directly and let
        the browser place it using the map transform published by Nav2."""
        return (self.state.odom["x"], self.state.odom["y"],
                self.state.odom["theta"])


def _yaw(q):
    import math
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                      1.0 - 2.0 * (q.y ** 2 + q.z ** 2))


def _downsample(ranges, target):
    n = len(ranges)
    if n <= target:
        return list(ranges)
    step = n / target
    out = []
    for i in range(target):
        out.append(float(ranges[int(i * step)]))
    return out