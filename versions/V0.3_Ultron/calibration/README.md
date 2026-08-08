# V0.3 — Calibration

Calibration records and procedures. Re-run after any mechanical change.

## Required calibrations (from the Bible)

1. **Wheel geometry** — measure and reflash `WHEEL_RADIUS_M`, `WHEEL_SEP_M`.
2. **Encoder ticks** — verify 825 ±10 per wheel rev (right wheel fix B1).
3. **Battery scale** — confirm `BATTERY_ADC_SCALE = 0.017418`.
4. **TF offsets** — measure sensor positions; update static TFs in the launch.
5. **Kinect intrinsics** — `ros2 run camera_calibration` (record here).
6. **IMU zero-offset** — verify stationary readings at startup (P1: add offsets).

## Record format

```
calibration/
├── wheel_geometry_2026-08-08.md   # measurements + resulting constants
├── tf_offsets_2026-08-08.md
├── camera_intrinsics_*.yaml
└── imu_offset_*.md
```

Rule: reflash after changing constants and record the commit hash alongside.
