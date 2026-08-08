# UAP_ULTRON — Roadmap

> Timeline view. The deep technical details live in each version's own folder;
> this page is the strategic map.

## Now → V0.3 (in progress)

**Goal:** prove the platform and collect the first pilot dataset.

- [x] Two-layer architecture working (edge Jetson + laptop Nav2) — Bible v4.2 baseline
- [x] v4.2r2/r3 defect fixes absorbed (encoder pin, IBT-2 two-PWM, DDS, TF, E-stop recovery)
- [x] Engineering audit + restructure (2026-08) — see `20_engineering_process/engineering_audit.md`
- [x] Data-collection section defined (Bible §17)
- [ ] P0/P1 corrections (wheel velocity control, `camera_info` depth→scan, EKF-onboard option)
- [ ] 10+ pilot data missions (Section 17 procedure)
- [ ] Benchmark suite: odometry, E-stop latency, navigation goal-success, runtime

## Next → Ultron_insightV1.0 (first real-world version)

Planned hardware upgrades (from the insight spec):

- Jetson Orin Nano Super 8 GB (Nav2/SLAM/EKF move onboard)
- Intel RealSense D455 (replaces Kinect 1414)
- CAN bus + AS5048B encoders + Arduino Nano + MCP2515/TJA1050
- BNO085 IMU · RPLiDAR A2M12 · M.2 NVMe 512 GB · Intel AX210 Wi-Fi
- Improved enclosure + power redesign

Capabilities unlocked: onboard autonomy, environment/logistics/privacy-aware
behaviour intelligence, cloud Command Centre, and the data infrastructure for
the generations below.

## Then → Ultron_VitalsV2.0

Patient monitoring: fever, heart rate, SpO2, falls. Incremental add-on to the
InsightV1.0 platform (no redesign).

## Finally → Ultron_MedAssistV3.0

AI diagnosis + medicine: combines Insight + Vitals data to predict outbreak
risk and optimize treatment. Runs on hospital server + cloud.

## Guiding rule

Each generation is an **incremental upgrade of the same platform**. If a change
requires a full architecture rebuild, we stop and question the design — the
whole point of V0.3 is to make that unnecessary.
