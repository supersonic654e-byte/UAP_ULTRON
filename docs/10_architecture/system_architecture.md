# System Architecture

> Maintainers: **Sadnan Sajid355** (industrial-grade system architecture design).
> Reviewed: 2026-08-08.

This document is the architecture-level view of UAP_ULTRON. The implementation
Bible (`versions/V0.3_Ultron/implementation_bible.md`) is the build reference;
this page explains **why** the system is split the way it is, and how it stays
upgradeable across generations.

## 1. Design intent

Ultron_V0.3 is the *last* experimental robot. Everything after it must be a
replacement, not a rebuild. That goal drives three rules:

1. **Stable seams.** The MCU↔ROS boundary is one versioned binary protocol.
   Swap the MCU, keep the ROS side.
2. **Containers for compute.** Heavy components (Nav2, SLAM, EKF) are Docker
   images. They can move machines (laptop → Jetson) without rewriting them.
3. **Sensors behind topics.** A sensor driver owns a topic; the consumer never
   cares which physical sensor produced it (Kinect → D455 later).

## 2. The three layers

```
┌───────────────────────────────────────────────────────────────┐
│ LAYER 3 — PILOT CLOUD (V0.3 laptop)                            │
│   Nav2 · SLAM · EKF · RViz2 · rosbag2 · feature extraction     │
│   (future: hospital server + cloud Command Centre)             │
└───────────────────────────┬───────────────────────────────────┘
                            │ CycloneDDS over Tailscale
┌───────────────────────────▼───────────────────────────────────┐
│ LAYER 2 — EDGE (Jetson Nano 4 GB now, Orin Nano Super later)   │
│   rplidar · kinect · depth_to_scan · safety_node               │
│   serial_node · data_logger_node · diagnostics                 │
└───────────────────────────┬───────────────────────────────────┘
                            │ USB serial protocol v1 (CRC-8)
┌───────────────────────────▼───────────────────────────────────┐
│ LAYER 1 — REAL-TIME (Arduino Mega now, Nano + CAN later)       │
│   E-stop ISR · watchdogs · quadrature encoders · IBT-2 20 kHz  │
│   IMU · battery/current ADC                                    │
└───────────────────────────────────────────────────────────────┘
```

## 3. Why this split

| Concern | Where it lives | Reason |
|---|---|---|
| Safety-critical motion | Layer 1 (MCU) | Hard real-time; survives OS/network failure |
| Sensor acquisition | Layer 2 (Jetson) | USB devices, ROS drivers |
| Safety supervision | Layer 2 (safety_node) | Fuses LiDAR+depth, filters velocity |
| Planning / localization | Layer 3 (laptop) | Compute-heavy; not real-time |
| Data collection | Layers 2+3 | Onboard JSONL + laptop rosbag |

The critical safety path (E-stop → watchdogs → safety node → heartbeat) is
**local** to the robot. The network is an input, not a safety dependency.

## 4. Industrial-grade considerations (this design)

- **Fail-safe default.** Every actuator defaults to OFF; every fault is latched
  until an explicit two-step recovery.
- **Independent layers.** No single point of failure spans all three layers: the
  robot still stops if the laptop dies, if the Jetson dies, or if the MCU hangs.
- **Replaceable modules.** The hardware upgrade matrix (see the insight spec)
  maps each V0.3 component to its InsightV1.0 replacement with an effort grade.
- **Traceability.** Defect fixes are tracked as B1..B12/D1..D6 in the Bible, and
  decisions are logged as ADRs (`20_engineering_process/decisions`).

## 5. Known architectural limits (be honest)

- Nav2 runs on the laptop → no unattended autonomy on V0.3.
- Wheel drive is open-loop PWM (velocity control is a P0/P1 item).
- Kinect is a temporary sensor; the pipeline must stay camera_info-driven.

See `20_engineering_process/engineering_audit.md` for the full list.
