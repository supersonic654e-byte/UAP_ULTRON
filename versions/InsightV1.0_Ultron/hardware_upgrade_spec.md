# InsightV1.0 — Hardware Upgrade Spec

Per-component migration from Ultron_V0.3. **Migration effort** is the honest
cost of the swap; the goal is that everything is LOW/MED and none is a rebuild.

| V0.3 (now) | InsightV1.0 | Effort | Notes |
|---|---|---|---|
| Jetson Nano 4 GB | **Jetson Orin Nano Super 8 GB** | LOW | Same containers; Nav2/SLAM/EKF move onboard |
| Kinect 1414 | **Intel RealSense D455** | LOW/MED | `realsense-ros`; depth_to_scan reads `camera_info` (P1 on V0.3) |
| MPU6050 | **BNO085** | LOW | New IMU packet; EKF uses fused orientation |
| RPLiDAR A1M8 | **RPLiDAR A2M12** | LOW | Driver config; re-derive stop margins (10 Hz) |
| Hall encoders + IBT-2 | **CAN + AS5048B encoders** | MED | Arduino Nano + MCP2515/TJA1050; `ultron_can_node` |
| SD + USB NVMe 128 GB | **M.2 NVMe 512 GB** | LOW | Same `/mnt/ssd` layout |
| TL-WN727N USB WiFi | **Intel AX210 M.2** | LOW | Requires Orin kernel (5.15+); do with the Orin |
| 3S 2200 mAh | **Larger pack + power redesign** | MED | Runtime is the hard ceiling |
| Wood chassis | **Improved enclosure** | MED | Thermal, mounting, serviceability |

## Constraints

- AX210, BNO085, CAN tooling need the Orin kernel — **sequence with the Orin**, not before.
- Depth→scan must be `camera_info`-driven on V0.3 or the D455 swap is a rewrite (P1).
- Wheel velocity PID carries over to the CAN build — do it on V0.3 first (P0/P1).

## Acceptance for the upgrade

The V0.3 test suite (§13) must pass on InsightV1.0 with the same pass criteria,
plus new: onboard-autonomy (no laptop), BNO085 orientation accuracy, CAN
encoder resolution, and the 10 Hz LiDAR stop-margin revalidation.
