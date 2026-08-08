# UAP_ULTRON — Ultron_insightV1.0 Implementation Specification

> First real-world, industry-oriented deployment version of the UAP_ULTRON mother project.
> The transition from the current Ultron_V0.3 is defined in this document (the *target spec* for InsightV1.0, not the V0.3 build). The V0.3 Bible (`../V0.3_Ultron/implementation_bible.md`) contains only Ultron_V0.3 implementation details.
> AI rationale: see [`../../docs/10_architecture/ai_architecture.md`](../../docs/10_architecture/ai_architecture.md).

---

## 1. Mission

Ultron_insightV1.0 converts **hospital movement and environmental signals into research-ready operational insights**, while automating routine patrol and delivery-logistics rounds in a typical Bangladesh hospital (200-bed profile):

- **Environment:** temperature, humidity, CO2, occupancy.
- **Logistics:** delivery/patrol timings, dwell hotspots, audit trail.
- **Human-behaviour intelligence:** anonymous motion features (counts, flow, dwell) — **privacy-aware by design**.
- **Output:** research-ready insights + live **Command Centre** dashboard.

The system stores **anonymous motion features and derived data** rather than identifiable raw video whenever possible. Privacy, data minimization, security, and responsible data handling are part of the architecture, not added later.

---

## 2. Hardware Platform (upgrade from V0.3)

| Component | Specification | Notes |
|---|---|---|
| Compute | **NVIDIA Jetson Orin Nano Super Developer Kit (8 GB)** | JetPack 6.x (Ubuntu 22.04). Hosts Nav2/SLAM/EKF **onboard** — laptop demoted to monitor/data sink. |
| Depth camera | **Intel RealSense D455** | Replaces Kinect 1414; lower power (~4 W), higher quality, USB3. |
| IMU | **BNO085** | Fused quaternion output (on-chip fusion) — replaces MPU6050 raw path. |
| LiDAR | **RPLiDAR A2M12** | 10 Hz, 0.9°, 12 m — improves stop margins and thin-obstacle detection. |
| Motor/encoder bus | **CAN bus + AS5048B encoders (Unit 2)** | 14-bit absolute encoders over CAN replace 825-tick hall encoders. |
| CAN interface | **MCP2515 CAN module + TJA1050 transceiver** | Arduino-side CAN. |
| MCU | **Arduino Nano** | Replaces Mega 2560; runs wheel PID + CAN + safety watchdogs. |
| Storage | **M.2 NVMe 512 GB SSD** | Internal; replaces SD + USB NVMe enclosure. |
| Networking | **Intel AX210 M.2 Wi-Fi module** | 5 GHz, Bluetooth; requires the Orin kernel (5.15+). |
| Enclosure | **Improved/custom enclosure** | Thermal, mounting, serviceability, and sensor layout. |
| Power | **Larger pack + power redesign** | Sized for Orin + D455 + peripherals; hot-swap capability. |
| Additional sensors | **As required** | Environment (temp/humidity/CO2), occupancy; per mission needs. |

---

## 3. Software Architecture (bounded change, no rebuild)

- **Keep:** ROS 2 Humble + Docker (same container strategy); message interfaces and QoS table; layered safety; binary protocol v1 (extended for CAN/BNO085 packets); `/mnt/ssd` layout; TF tree; data-pipeline format (Section 17).
- **Move onboard:** EKF, slam_toolbox, Nav2 — laptop becomes monitor/RViz2 + data sink.
- **Replace:** `serial_node` → `ultron_can_node` (CAN transport, same ROS interface); Kinect driver → `realsense-ros`; `depth_to_scan` consumes `camera_info` (P1 done on V0.3); new IMU packet type for BNO085 fused orientation.
- **Add:** environment-sensor nodes; anonymous motion-feature extraction; cloud/Command-Centre bridge; fleet diagnostics (already stubbed on V0.3).

---

## 4. Data & AI Pipeline (privacy-by-design)

```
SENSORS ─▶ robot edge (Orin) ─▶ derived anonymous features
    │            │                        │
    │            ▼                        ▼
    └── raw depth/video (consent-gated)   hospital database (research-ready)
                   │                        │
                   ▼                        ▼
             operator laptop/         Command Centre
             local gateway            (cloud, remote monitoring)
                   ▼
             "collect → find patterns → predict" loop
             (InsightV1.0 baseline → later VitalsV2.0 / MedAssistV3.0)
```

**Rules:**
- Default: store anonymous motion features and derived data. Do **not** store identifiable raw video unless a documented consent + approval gate is met.
- Data minimization, encryption at rest, defined retention/deletion policy.
- No identifiable names, faces, or metadata without explicit approval.

---

## 5. Deployment Targets

- Onboard autonomy (no laptop dependency) for supervised hospital corridors and service areas.
- Live Command Centre: fleet status, missions, alerts, maintenance, feedback.
- Remote monitoring + cloud data collection for the AI improvement loop.
- Continuous learning infrastructure where technically appropriate.

---

## 6. Transition Checklist (from V0.3)

1. Implement P0/P1 corrections in the V0.3 audit (velocity PID, camera_info refactor, EKF-onboard flag, IMU calibration).
2. Validate the Section 17 data pipeline with ≥10 pilot missions on V0.3.
3. Port the container stack to the Orin Nano Super; verify identical topics.
4. Move EKF/Nav2/SLAM onboard; validate autonomy with the laptop as monitor.
5. Swap sensors per Section 2 table; re-run the full Section 13 test suite.
6. Redo power budget and enclosure; deploy the InsightV1.0 pilot.

---

## 7. Evolution (beyond InsightV1.0)

The platform is designed so future capabilities are added incrementally:
- **Ultron_insightV1.1 / V1.2 …** — additional sensors and features without architectural redesign.
- **Ultron_VitalsV2.0** — patient monitoring (see roadmap doc).
- **Ultron_MedAssistV3.0** — AI diagnosis + medicine (see roadmap doc).
