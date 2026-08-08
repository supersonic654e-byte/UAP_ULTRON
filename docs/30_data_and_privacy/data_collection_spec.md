# Data Collection Specification (V0.3 Pilot)

## Goal

Prove the full pipeline early: **Collect → Store → (later) Analyze**. Ultron_V0.3
is the first data-collection pilot of the project; the format and privacy model
are meant to survive into the deployment generation unchanged.

## What we collect

| Source | Topic / artifact | Where stored |
|---|---|---|
| Telemetry | `/odom`, `/imu/data`, `/battery/state`, `/ultron/fault`, `/ultron/heartbeat` | laptop rosbag |
| Commands | `/cmd_vel`, `/safe_cmd_vel` | laptop rosbag |
| Perception | `/scan`, `/kinect/scan` (derived) | laptop rosbag |
| Mission log | `data_logger_node` → JSONL (battery, faults, phases, heartbeat health) | `/mnt/ssd/ultron/logs/<mission_id>.jsonl` |
| Derived | `feature_extract.py` → occupancy deltas, flow counts, dwell maps | laptop `~/ultron_data/<mission_id>/` |

Raw depth/video (`/kinect/depth/image_raw`) is **not** retained by default —
privacy-gated only.

## Procedure (each mission)

1. Battery ≥ 11.1 V; mission ≤ 12 min.
2. Laptop: create mission dir, start `ros2 bag record -s mcap` (topics above).
3. Jetson: enable `data_logger_node` with `mission_id`; restart launch.
4. Run the mission (teleop or supervised Nav2). Operator supervises.
5. Stop bag + logger.
6. Run `feature_extract.py`; verify JSONL + bag checksums.
7. Archive under the site retention policy; keep the bag off the robot.
8. Review the run; update the procedure for the next mission.

## Metadata

Every dataset carries: `mission_id`, `date`, `site_id`, `operator_id`,
waypoints, start/end UTC (chrony-synced), mission result, sensor manifest,
retention period.

## Storage & retention

- Encrypted at rest on the laptop (LUKS volume or equivalent) and on the SSD.
- Default retention is short (e.g., 30 days) unless the analysis needs longer;
  expiry is recorded in the dataset metadata.
