# Data Dictionary

Every collected field/artifact, its unit, source, and retention. Add rows as
new sensors arrive. The goal is that a fresh reader can analyze any dataset
without asking the team.

## Telemetry

| Field | Type | Unit | Source | Retention |
|---|---|---|---|---|
| odom.x / odom.y | float | m | wheel encoders (serial_node) | with bag |
| odom.theta | float | rad | wheel encoders | with bag |
| odom.twist.linear.x | float | m/s | wheel encoders (real-dt) | with bag |
| odom.twist.angular.z | float | rad/s | wheel encoders | with bag |
| imu.linear_acceleration | float×3 | m/s² | MPU6050 | with bag |
| imu.angular_velocity | float×3 | rad/s | MPU6050 | with bag |
| battery.voltage | float | V | ADC divider (scale 0.017418) | with bag |
| fault.flags | uint8 | bitmask | Arduino | with bag |
| heartbeat.seq | uint8 | — | safety_node | with bag |

## Perception

| Field | Type | Unit | Source | Retention |
|---|---|---|---|---|
| scan.ranges | float[] | m | RPLiDAR A1M8 | with bag |
| kinect.scan.ranges | float[] | m | Kinect depth → depth_to_scan | with bag |
| motion features (derived) | per zone | count/flow/dwell | feature_extract.py | 30 d default |

## Mission log (JSONL, `/mnt/ssd/ultron/logs/<mission_id>.jsonl`)

| Field | Type | Notes |
|---|---|---|
| ts | float | seconds since mission start |
| phase | string | `idle \| active \| paused \| e-stop \| done` |
| battery_v | float | V |
| faults | uint8 | bitmask snapshot |
| cmd_vel / safe_cmd_vel | float | m/s, rad/s |
| heartbeat_ok | bool | — |

## Dataset metadata

| Field | Notes |
|---|---|
| mission_id | unique per mission |
| date / site_id / operator_id | attribution |
| start_utc / end_utc | chrony-synced |
| waypoints | visited points |
| sensor_manifest | which sensors were live |
| result | success / aborted + reason |
| retention | expiry date |
