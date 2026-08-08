#!/usr/bin/env python3
"""data_logger_node — onboard mission JSONL logger (Bible Section 17.4).

Writes /mnt/ssd/ultron/logs/<mission_id>.jsonl with battery, fault,
heartbeat-health and mission phase events. Does NOT write raw depth/video
(that stays privacy-gated). Disabled unless `enabled:=true`.

Params:
  mission_id (str, required when enabled)
  log_dir    (str, default /mnt/ssd/ultron/logs)
  enabled    (bool, default false)
"""

import json
import os

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from sensor_msgs.msg import BatteryState
from std_msgs.msg import UInt8

_RELIABLE = QoSProfile(
    reliability=ReliabilityPolicy.RELIABLE,
    history=HistoryPolicy.KEEP_LAST, depth=10)


class DataLoggerNode(Node):
    def __init__(self):
        super().__init__('ultron_data_logger')
        self.declare_parameter('mission_id', '')
        self.declare_parameter('log_dir', '/mnt/ssd/ultron/logs')
        self.declare_parameter('enabled', False)

        self._enabled = bool(self.get_parameter('enabled').value)
        self._fh = None
        if not self._enabled:
            self.get_logger().info('Data logger disabled (enabled:=false).')
            return

        mission_id = self.get_parameter('mission_id').value
        if not mission_id:
            self.get_logger().error('mission_id is required when enabled; '
                                    'logger inactive.')
            self._enabled = False
            return

        log_dir = self.get_parameter('log_dir').value
        os.makedirs(log_dir, exist_ok=True)
        self._path = os.path.join(log_dir, f'{mission_id}.jsonl')
        self._fh = open(self._path, 'a', encoding='utf-8')
        self._mission_id = mission_id

        self.create_subscription(BatteryState, '/battery/state',
                                 self._battery_cb, _RELIABLE)
        self.create_subscription(UInt8, '/ultron/fault',
                                 self._fault_cb, _RELIABLE)
        self.create_subscription(UInt8, '/ultron/heartbeat',
                                 self._heartbeat_cb, _RELIABLE)

        self.create_timer(1.0, self._snapshot)
        self._hits = 0
        self._misses = 0
        self._log('mission_start', {'mission_id': mission_id,
                                    'log_dir': log_dir})
        self.get_logger().info(f'Data logger active: {self._path}')

    # ---- helpers ----------------------------------------------------------
    def _ts(self):
        return self.get_clock().now().nanoseconds / 1e9

    def _log(self, event, fields=None):
        if not self._enabled or self._fh.closed:
            return
        row = {'ts': round(self._ts(), 3), 'event': event}
        if fields:
            row.update(fields)
        self._fh.write(json.dumps(row) + '\n')
        self._fh.flush()

    # ---- subscriptions ----------------------------------------------------
    def _battery_cb(self, msg):
        self._log('battery', {'voltage': round(msg.voltage, 3),
                              'present': bool(msg.present)})

    def _fault_cb(self, msg):
        self._log('fault', {'flags': int(msg.data),
                            'flags_hex': f'0x{msg.data:02X}'})

    def _heartbeat_cb(self, msg):
        self._hits += 1

    # ---- periodic snapshot ------------------------------------------------
    def _snapshot(self):
        # Track heartbeat health in 1 s windows: detect gaps.
        self._log('heartbeat_health',
                  {'hb_count_last_s': self._hits,
                   'hb_gap': self._misses > 0})
        self._hits = 0
        self._misses = 0

    def destroy_node(self):
        if self._enabled and self._fh is not None and not self._fh.closed:
            self._log('mission_end', {'mission_id': self._mission_id})
            self._fh.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = DataLoggerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
