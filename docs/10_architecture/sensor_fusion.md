# Sensor Fusion Architecture

> Maintainers: **Sadnan Sajid355** (sensor-fusion build parts).
> Reviewed: 2026-08-08.

## 1. Fusion goal

Estimate the robot pose (x, y, θ) and its uncertainties accurately enough for
SLAM + Nav2, using sensors that are individually weak:

| Sensor | Rate | Weakness | What it contributes |
|---|---|---|---|
| Wheel encoders (825 t/rev) | ~33 Hz | Low resolution, slip, open-loop drive | Distance travelled (odom) |
| MPU6050 IMU | ~33 Hz | Gyro bias, drift | Angular velocity, accel |
| RPLiDAR A1M8 | 5.5 Hz | Slow, 1° resolution | Absolute reference (via SLAM/AMCL) |
| Kinect depth | 8 Hz | Noisy, mid-field only | Mid-field obstacle layer |

## 2. Fusion chain (V0.3)

```
encoders ─▶ odom (serial_node) ─┐
                                ├─▶ EKF (robot_localization) ─▶ odom→base_link TF
IMU ──────▶ /imu/data ──────────┘        (world=odom)
                                map→odom  from slam_toolbox (mapping) / AMCL (localization)
LiDAR ────▶ /scan ──────────────▶ SLAM / AMCL ──▶ map
```

- **EKF** fuses wheel odometry (as `odom0`) and IMU (as `imu0`) in 2D mode.
- The EKF is the **single** publisher of `odom→base_link` (fix B4). `map→odom`
  comes from SLAM or AMCL.
- Localization on the laptop (V0.3) keeps heavy compute off the Nano.

## 3. Sensor-fusion build blocks (for the next generation)

These are the reusable, tested fusion modules we want to carry forward:

1. **Wheel-velocity PID** — closes the loop on each wheel so the EKF input is
   accurate. (P0/P1 on V0.3; becomes CAN + AS5048B on Insight.)
2. **IMU calibration** — gyro/accel offset at startup + DLPF config (P1).
3. **BNO085 fused orientation** — on-chip fusion gives a proper quaternion
   instead of raw accel/gyro (Insight).
4. **EKF-onboard option** — a launch flag to run EKF on the Jetson, removing a
   network hop from localization (P1).
5. **covariance discipline** — every sensor declares its uncertainty; the EKF
   params document the starting values and the tuning procedure.

## 4. Tuning notes (from the Bible §14.2 / §15.4)

- Calibrate `WHEEL_RADIUS_M`, `WHEEL_SEP_M`, `TICKS_PER_REV` first; odom error
  dominates everything else.
- Start EKF covariances: odom0 pose ≈ 0.01 (x/y), 0.05 (yaw); imu0 ang.vel ≈ 0.01.
- If AMCL jumps: check clock sync (chrony) and `/scan` QoS (best_effort).

## 5. What we deliberately do NOT fuse yet

- Raw depth/video into the state estimate (privacy + compute). Depth stays a
  safety-layer input only.
- Global positioning (GPS/GNSS) — indoor platform.
