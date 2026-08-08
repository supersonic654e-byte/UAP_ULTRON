# ROS 2 Architecture

## Stack

| Component | Package | Where |
|---|---|---|
| ROS 2 | Humble Hawksbill (ros-base) | Jetson container |
| RMW | `rmw_cyclonedds_cpp` | both machines |
| Mapping | `ros-humble-slam-toolbox` | laptop |
| Localization | Nav2 AMCL (`ros-humble-navigation2`) | laptop |
| Navigation | Nav2 (DWA) | laptop |
| Fusion | `ros-humble-robot-localization` | laptop (EKF) |
| LiDAR driver | `ros-humble-rplidar-ros` | Jetson |
| Teleop | `ros-humble-teleop-twist-keyboard` | laptop |

## Node graph (V0.3)

On the Jetson (`ultron_onboard` package):

- `rplidar` → `/scan` (best_effort)
- `ultron_kinect` → `/kinect/depth/image_raw` + `/kinect/depth/camera_info`
- `ultron_depth_to_scan` → `/kinect/scan`
- `ultron_safety_node` → `/safe_cmd_vel`, `/ultron/heartbeat`
- `ultron_serial_node` → `/odom`, `/imu/data`, `/battery/state`, `/ultron/fault`
- `ultron_data_logger` → JSONL on SSD (pilot missions)

On the laptop:

- EKF (`robot_localization`) — publishes `odom→base_link`
- `slam_toolbox` / AMCL — publishes `map→odom`
- Nav2 — subscribes `/scan`, publishes `/cmd_vel`
- RViz2 — visualization
- `ros2 bag record` — pilot data

## QoS policy (must stay matched)

| Topic | QoS |
|---|---|
| `/scan`, `/kinect/*` | BEST_EFFORT |
| `/odom`, `/imu/data`, `/cmd_vel`, `/safe_cmd_vel`, `/ultron/*` | RELIABLE |

Nav2 consumers must set `/scan` to best_effort (`obstacle_layer` reliability and
AMCL `sensor_data_qos: 2`) or localization silently fails.

## TF tree

```
map ─▶ odom   (slam_toolbox / AMCL)
odom ─▶ base_link   (EKF — single source, fix B4)
base_link ─▶ laser_link / kinect_depth_frame / imu_link   (static)
```

## Communication transport

CycloneDDS with unicast peers over Tailscale (`ROS_DOMAIN_ID=42`). All
containers use `network_mode: host` (fix D2). See `network` notes in the Bible §7.

## Upgrade hooks

- The EKF container is a launch flag away from moving to the Jetson (P1).
- `depth_to_scan` must consume `camera_info` so the D455 replaces the Kinect
  driver without touching consumers (P1).
- Custom topics are namespaced `/ultron/*` and documented — new nodes follow the
  same convention.
