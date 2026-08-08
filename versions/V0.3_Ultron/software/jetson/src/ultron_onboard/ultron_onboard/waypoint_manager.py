#!/usr/bin/env python3
"""waypoint_manager — persistent waypoint storage and ROS interface.

Provides:
  - Service/topic interface for adding/deleting/listing waypoints
  - Persists waypoints to /mnt/ssd/ultron/waypoints.json
  - Publishes waypoint list on /ultron/waypoints/list (latched)
  - Handles navigation requests via /ultron/waypoints/navigate
"""

import json
import os
import threading

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
from std_msgs.msg import String, Empty


class WaypointManager(Node):
    def __init__(self):
        super().__init__('ultron_waypoint_manager')
        self.declare_parameter('storage_path', '/mnt/ssd/ultron/waypoints.json')
        self._path = self.get_parameter('storage_path').value

        # Ensure storage directory exists
        os.makedirs(os.path.dirname(self._path), exist_ok=True)

        # Load existing waypoints
        self._waypoints = self._load()
        self._lock = threading.Lock()

        # Latched publisher for waypoint list
        qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
            durability=DurabilityPolicy.TRANSIENT_LOCAL
        )
        self._list_pub = self.create_publisher(String, '/ultron/waypoints/list', qos)

        # Subscriptions
        rel = QoSProfile(reliability=ReliabilityPolicy.RELIABLE,
                         history=HistoryPolicy.KEEP_LAST, depth=10)
        self.create_subscription(String, '/ultron/waypoints/add',
                                 self._add_cb, rel)
        self.create_subscription(String, '/ultron/waypoints/delete',
                                 self._delete_cb, rel)
        self.create_subscription(String, '/ultron/waypoints/navigate',
                                 self._navigate_cb, rel)
        self.create_subscription(Empty, '/ultron/waypoints/list_request',
                                 self._list_request_cb, rel)

        # Publish initial list
        self._publish_list()
        self.get_logger().info(f'Waypoint manager started with {len(self._waypoints)} waypoints')

    def _load(self):
        try:
            with open(self._path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _save(self):
        with self._lock:
            with open(self._path, 'w') as f:
                json.dump(self._waypoints, f, indent=2)

    def _publish_list(self):
        msg = String()
        msg.data = json.dumps(self._waypoints)
        self._list_pub.publish(msg)

    def _add_cb(self, msg):
        try:
            wp = json.loads(msg.data)
            name = wp.get('name')
            if not name:
                self.get_logger().warn('Waypoint add: missing name')
                return
            with self._lock:
                self._waypoints[name] = wp
                self._save()
            self._publish_list()
            self.get_logger().info(f'Added waypoint: {name}')
        except Exception as e:
            self.get_logger().error(f'Waypoint add failed: {e}')

    def _delete_cb(self, msg):
        try:
            name = msg.data
            with self._lock:
                if name in self._waypoints:
                    del self._waypoints[name]
                    self._save()
                    self._publish_list()
                    self.get_logger().info(f'Deleted waypoint: {name}')
                else:
                    self.get_logger().warn(f'Waypoint not found: {name}')
        except Exception as e:
            self.get_logger().error(f'Waypoint delete failed: {e}')

    def _navigate_cb(self, msg):
        # This is handled by the laptop web server which calls Nav2
        # We just forward to a topic that the laptop can use if needed
        self.get_logger().info(f'Navigate request: {msg.data}')

    def _list_request_cb(self, _):
        self._publish_list()


def main(args=None):
    rclpy.init(args=args)
    node = WaypointManager()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()