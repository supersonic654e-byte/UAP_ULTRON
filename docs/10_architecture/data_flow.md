# Data Flow

## Sensors → ROS (upward)

```
Encoders ─▶ Arduino ─▶ serial_node ─▶ /odom ─────────┐
IMU      ─▶ Arduino ─▶ serial_node ─▶ /imu/data ─────┼─▶ Laptop EKF
LiDAR    ─▶ rplidar ─▶ /scan ────────────────────────┼─▶ Laptop Nav2/SLAM
Kinect   ─▶ ultron_kinect ─▶ depth_to_scan ─▶ /kinect/scan ─▶ safety_node
```

## Commands (downward)

```
Laptop Nav2 ─▶ /cmd_vel ─▶ safety_node ─▶ /safe_cmd_vel ─▶ serial_node ─▶ Arduino ─▶ motors
safety_node ─▶ /ultron/heartbeat ─▶ serial_node ─▶ Arduino watchdog
operator    ─▶ /ultron/clear_faults ─▶ serial_node ─▶ Arduino (E-stop release)
```

## Data collection (Section 17)

```
onboard: data_logger_node ─▶ /mnt/ssd/ultron/logs/<mission_id>.jsonl
laptop : ros2 bag record -s mcap ─▶ ~/ultron_data/<mission_id>/
laptop : feature_extract.py ─▶ anonymous motion features (offline)
```

## Bandwidth (remote mode estimate)

| Topic | Rate | Size | Bitrate |
|---|---|---|---|
| /odom | 30 Hz | ~200 B | ~6 KB/s |
| /scan | 5.5 Hz | ~2 KB | ~11 KB/s |
| /kinect/scan | 8 Hz | ~3 KB | ~24 KB/s |
| total | | | ~330 kbps uplink |

Fine for 4G/LTE. The Kinect depth *image* is **not** streamed by default
(privacy + bandwidth) — only the derived scan.

## Latency budget (safety)

Worst-case stop path: LiDAR scan period (~180 ms) + safety loop + serial +
brake ≈ 247–280 ms → at 0.35 m/s ≈ 9.8 cm travel inside the STOP zone (23 mm
margin). This is why autonomous speed is capped at 0.35 m/s.
