# V0.3 — Test Procedures

Canonical procedure source: [`../implementation_bible.md`](../../implementation_bible.md) §13. These pages are
the runnable summaries; every step maps to a script in `../tests/scripts/` or
a manual check. A benchmark is only "real" once its CSV/JSON is in
`../tests/results/`.

## Hardware tests (robot lifted — always first)

| Test | Procedure | Script / command |
|---|---|---|
| Motor drive + speed clamp | Both wheels forward 0.1 m/s for 2 s; then 0.6 m/s must clamp to 0.45 | `python3 scripts/motor_test.py --port /dev/ultron_arduino` |
| Encoder counts (B1) | Rotate left then right wheel 1 rev by hand → 825 ± 10 each | `python3 scripts/../calibration/scripts/encoder_verify.py --wheel left --revs 1` |
| E-stop (B7) | Wheels spinning → press → stop < 5 ms; release → stays stopped; clear → resumes | `python3 scripts/estop_test.py` |
| IMU | Tilt forward → ax>0; rotate left → gz>0 | `python3 calibration/scripts/imu_offset_calib.py` |
| Battery | Full 3S shows 12.x V ± 0.1 on /battery/state | `python3 calibration/scripts/battery_scale_verify.py --multimeter-v <V>` |
| Overcurrent (B8) | Lock wheels, command 0.3 m/s > 500 ms → fault bit 1, fuse intact | `python3 scripts/overcurrent_test.py` |
| Runtime | Full pack under load → warning 11.1 V after ~15-20 min | `python3 scripts/runtime_test.py --out results/runtime_<date>.csv` |

## Communication tests

- Serial: `minicom -D /dev/ultron_arduino -b 115200` → binary stream ~30 Hz.
- DDS over Tailscale: `tailscale ping <peer>` direct; `ros2 topic list`;
  `ros2 topic echo /odom --once`; `ros2 topic hz /ultron/heartbeat` (~10 Hz).
- TF: `ros2 run tf2_tools view_frames` → map → odom → base_link → laser_link /
  kinect_depth_frame / imu_link. odom→base_link single-sourced by the laptop
  EKF (B4).

## System tests

- Teleop: `teleop_twist_keyboard` (4 directions + /odom).
- Odom twist: command 0.30 m/s → twist ≈ 0.30 ± 10%.
- Safety zone: hand at 0.20 m while commanding 0.3 → /safe_cmd_vel = 0.
- SLAM: drive full area → map builds; `save_map.sh`; AMCL pose tracks.
- Navigation (B6): saved map, Nav2 goal → moves at ≤ 0.35 m/s.

## Failure tests

- Kill WiFi → FAULT_BIT_HEARTBEAT within 500 ms, LED solid, stops.
- Kill Jetson container → Arduino stops motors within 500 ms.
- Kill laptop Nav2 → cmd_vel stops → FAULT_BIT_WATCHDOG, motors stop.
- LiDAR disconnect while moving → safety_node logs "LiDAR timeout — STOP".
- Battery 10.4 V (bench PSU) → FAULT_BIT_BATTERY, motors zero.
- Encoder disconnect while moving → FAULT_BIT_ENCODER within 1 s.

## Offline unit tests (no hardware — run in CI / locally)

```bash
cd tests/scripts && ./run_tests.sh
# or: pytest -q tests/scripts/protocol_test.py \
#            tests/scripts/test_safety_node.py \
#            tests/scripts/test_depth_scan.py
```
