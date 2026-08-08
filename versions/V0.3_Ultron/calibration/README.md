# V0.3 — Calibration

Records and procedures. Re-run after any mechanical change.

## Required calibrations (Bible)

1. **Wheel geometry** — `calibration/scripts/wheel_geometry_calib.py`
   (measures actual distance, prints corrected `METERS_PER_TICK` /
   `WHEEL_RADIUS_M`). Reflash `config.h` and re-verify.
2. **Encoder ticks** — `calibration/scripts/encoder_verify.py`
   (expect 825 ± 10 per wheel rev, right wheel fix B1).
3. **Battery scale** — `calibration/scripts/battery_scale_verify.py`
   (confirm `BATTERY_ADC_SCALE = 0.017418` vs multimeter).
4. **TF offsets** — measure sensor positions; update static TFs in
   `software/jetson/launch/jetson_bringup.launch.py`.
5. **Kinect intrinsics** — `ros2 run camera_calibration`
   (see `calibration/scripts/camera_calibration.md`; record YAML here).
6. **IMU zero-offset** — firmware captures gyro bias at boot;
   `calibration/scripts/imu_offset_calib.py` verifies it stays near zero.

## Record format

```
calibration/
├── scripts/                     # runnable tools (python3, pyserial)
└── camera_intrinsics_*.yaml     # camera calibration output (commit)
```

New record files follow `wheel_geometry_2026-08-08.md` style:
measurements + resulting constants + firmware commit hash. Rule: reflash
after changing constants and record the commit hash alongside.
