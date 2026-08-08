# Sensor Fusion — Build Parts

> Contributed by **Student Researcher & Technical Expert** (sensor-fusion build parts).

Reusable, buildable fusion components. Each "part" is a self-contained unit with
an interface, so it can be tested alone and composed into the EKF chain (see
`sensor_fusion.md`).

## Part 1 — Wheel odometry (encoder → odom)

- **Input:** left/right tick counters (Arduino, 825 t/rev).
- **Output:** `/odom` twist+pose, real inter-packet `dt` from Arduino `ts_ms`.
- **Notes:** METERS_PER_TICK = π·wheel_diameter/ticks_per_rev. Calibrate
  wheel radius & separation (Bible §13/§14). The host computes the pose; the
  MCU only counts ticks (deterministic, tiny ISR).

## Part 2 — Wheel velocity controller (P0/P1)

- **Input:** commanded wheel speed (m/s) + measured encoder speed.
- **Output:** PWM duty per wheel (two-PWM IBT-2).
- **Why:** open-loop PWM→speed shifts with battery voltage (~14% across the
  pack). A per-wheel PI loop fixes the EKF input and the stop-margin math.
- **Carry-over:** the same controller ports to CAN + AS5048B on InsightV1.0.

## Part 3 — IMU (calibrated gyro/accel)

- **Input:** MPU6050 raw.
- **Output:** `/imu/data` with bias-compensated angular velocity.
- **To do (P1):** startup offset calibration + DLPF configuration; covariance
  tuning. On InsightV1.0, BNO085 gives a fused quaternion instead.

## Part 4 — EKF (robot_localization)

- **Inputs:** `/odom` (odom0), `/imu/data` (imu0).
- **Output:** filtered `odom→base_link` TF (single publisher, fix B4).
- **Params (start):** world=odom; odom0 pose cov ≈ 0.01/0.01/0.05;
  imu0 ang.vel cov ≈ 0.01; `two_d_mode: true`.
- **Option (P1):** a launch flag to run the EKF on the Jetson instead of the
  laptop — removes a network hop from the localization chain.

## Part 5 — SLAM / localization reference

- **Mapping:** `slam_toolbox` (produces map + `map→odom`).
- **Localization:** Nav2 AMCL against saved maps (`sensor_data_qos: 2` for
  best-effort `/scan`).
- **Consistency:** AMCL needs the odom TF; EKF owns it; chrony keeps clocks in
  sync across machines (B12).

## Part 6 — Safety-zone fusion

- **Inputs:** `/scan` (LiDAR), `/kinect/scan` (mid-field).
- **Output:** `/safe_cmd_vel` filtered by STOP/SLOW zones.
- **Priority rule:** LiDAR governs < 1.0 m; Kinect only 1.0–3.0 m. Stale
  sensors degrade defined-ly. See `safety_architecture.md`.

## Composition

```
Part1 ─▶ /odom ─┐
Part3 ─▶ /imu ──┼─▶ Part4 (EKF) ─▶ odom→base_link TF
                │
Part5 ─▶ map→odom TF ─▶ Nav2 ─▶ /cmd_vel ─▶ Part6 ─▶ /safe_cmd_vel
```

## Acceptance

Each part ships with a test in `V0.3_Ultron/tests/` and a tuning record in
`V0.3_Ultron/calibration/`. No part is "done" until both exist.
