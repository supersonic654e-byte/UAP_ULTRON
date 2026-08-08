# UAP_ULTRON — Engineering Audit & Corrected Architecture

**Audited document:** `../versions/V0.3_Ultron/implementation_bible.md` — the implementation Bible for **Ultron_V0.3**.
**Date:** 08 August 2026
**Scope:** Full engineering audit: hardware, power, wiring, software/ROS2, networking, safety, AI/mapping/navigation, upgradeability to Ultron_insightV1.0, deployment readiness.
**Method:** Every section was re-derived and checked (pin mapping, timers, interrupts, serial protocol, kinematics math, power budget, USB allocation, DDS behavior, Nav2/safety margins, firmware logic). No assumption of correctness because "it is already written."

---

## 1. Executive Verdict

> ## YES WITH MAJOR CHANGES

`../versions/V0.3_Ultron/implementation_bible.md` is **buildable** and technically strong in its core (layered safety, serial protocol, firmware, containerized ROS2, storage design). The v4.2/r2/r3 defect-fix history is genuine engineering — most "wrong-looking" items you might expect are already documented fixes (right-encoder pin, BTS7960 two-PWM, TF ownership, QoS for AMCL, CycloneDDS discovery).

However, it is **NOT yet suitable as-is** for the declared purpose — *a pre-deployment prototype that evolves into Ultron_insightV1.0 without a rebuild*. It is suitable only **after** the P0/P1 corrections below and the Ultron_V0.3 restructure:

1. **The motion control is open-loop.** Wheel speed is commanded as PWM duty derived from a fixed `MAX_SPEED_MPS`. There is **no closed-loop velocity control**, so the `±10% twist accuracy`, the `0.45 m/s` cap, and the 23 mm autonomous stop-margin all assume a speed accuracy the system does not guarantee — battery sag alone shifts PWM→speed by ~14% (12.6 V → 11.1 V). **This is the single biggest gap** for both Nav2 behavior and the safety stop-margin analysis. (P0/P1)
2. **Autonomy is permanently hostage to the laptop.** The Jetson Nano 4 GB cannot run Nav2, so autonomous navigation requires a network link. This is *honest and safe*, but it means V0.3 cannot do a real unattended pilot. The architecture must be structured so Nav2/SLAM/EKF *move* onto the upgraded compute (they are containerized — good), not be rebuilt. (The upgrade-path spec handles this.)
3. **The Kinect 1414 is an obsolete anchor.** 12 W of power, USB2 isochronous headaches, 8 FPS after ROI cutting, marginal depth quality, and no camera_info-driven refactor in the perception pipeline. It works for a lab; it must be a **drop-in-replaceable** module (P1: refactor depth_to_scan to consume `camera_info`).
4. **No data-collection infrastructure existed.** The declared V0.3 mission is the *first real-world data-collection pilot*, but the Bible had no logging, no rosbag workflow, no privacy gate, no diagnostics. Added as new Section 17.
5. **Power is brutally short.** ~70 W average on a 24.4 Wh pack ≈ 15–20 min, with a 12-min mission rule. Acceptable for supervised lab/prototype work; completely inadequate for deployment. Must be a documented upgrade for InsightV1.0 and mitigated NOW with spare packs + strict mission rules.
6. **The optional disinfection-payload concept (removed from the Ultron_V0.3 scope) was a scope distraction** — it consumed design effort and pin/packet/fault resources for a module that is not part of the current roadmap. Cleanly removed.

**Bottom line:** Build V0.3 to this corrected Bible, with the P0/P1 items done, and it will be a strong, honest, upgradeable pre-deployment platform. Do **not** build it as-written in v4.2 without the corrections.

---

## 2. Section-by-Section Score

Scoring of `../versions/V0.3_Ultron/implementation_bible.md` sections (0–16 as originally written; 17 is new in this edition).

| Section | Score | Why |
|---|---|---|
| 0. Document control / constraints | **8.0 Strong** | Corrected power budget and runtime are honest (rare). Stop-margin math is done properly. DDS/unicast rules are concrete. Downside: the constraint list was mixed with the removed payload and had no data/privacy constraints (now added). |
| 1. System overview | **7.0 Acceptable** | Clear two-layer model; honest about the laptop requirement (B5). Text diagrams were stale and carried abandoned payload references (fixed in this edition); the "two-layer" name hides that the laptop is a *compute* dependency, not just a monitor. |
| 2. Hardware spec & wiring | **7.5 Acceptable** | Excellent detail level; v4.2r2 two-PWM BTS7960 fix is correct; encoder pin fix is correct. Deductions: open-loop drive not flagged; BTS7960 (43 A) wildly oversized for 8 A stall; ACS712-30A resolution marginal; Kinect power input missing from the power topology; Kinect is an obsolete anchor. |
| 3. OS setup (Jetson) | **8.5 Strong** | Realistic for a 4 GB Nano: ZRAM+swap, headless mode, SSD by UUID, journald-on-volatile, fsck cadence, thermal/PSU validation. Qengineering community image is pragmatic. |
| 4. Network setup | **8.0 Strong** | Tailscale + CycloneDDS unicast is a workable answer to "ROS2 across networks without multicast." Pinning 1.68.2 (kernel-panic avoidance) is pragmatic. Chrony for TF is correct. Deduction: pinning forever is a maintenance debt; DDS-over-VPN reliability is unvalidated. |
| 5. Docker setup | **8.5 Strong** | `network_mode: host` for DDS is correct (the D2 rationale is accurate). `MAKEFLAGS=-j2`, device passthrough, healthcheck, memory cap, restart policies — all sensible. Containerization is the single best upgradeability decision. |
| 6. ROS2 setup | **8.0 Strong** | Humble in a container on the Jetson, desktop-full on the laptop; nav2/EKF/SLAM params are sane; the AMCL `sensor_data_qos:2` fix is a classic trap correctly solved. |
| 7. CycloneDDS over Tailscale | **7.0 Acceptable** | Correct and simple for lab/supervised use. Deductions: RELIABLE QoS over a lossy VPN causes head-of-line blocking; the whole remote-op mode is fragile; EKF on the laptop makes localization depend on network + clock sync (mitigated by chrony but fragile). |
| 8. File structure | **8.5 Strong** | Clean separation of SD/SSD, build context, shared DDS config. Simple to maintain. |
| 9. Node-by-node | **6.5 Needs improvement** | Python nodes are heavy on a 4 GB Nano (mitigation: compose them — good). Main deduction: **open-loop drive** not addressed; `depth_to_scan` hardcodes Kinect intrinsics (blocks the D455 drop-in); no diagnostics/logging nodes. |
| 10. Safety system | **8.5 Strong** | Genuinely layered (hardware ISR <5 ms → Arduino watchdogs → Jetson safety node). Stop/Slow zones, stale-sensor handling, two-step E-stop recovery are all correct. Deduction: stop margin (23 mm) is razor-thin and depends on open-loop speed being accurate (it isn't); LiDAR 5.5 Hz + 1° resolution will miss thin obstacles (IV stands, bed legs). |
| 11. Arduino firmware | **8.5 Strong** | The technical depth is real: INT4/EICRB, INT2/3 change-triggered quadrature, PCINT0 for Port B, Timer3/4 20 kHz PWM, CRC-8 protocol, WDT 8 s, E-stop latch + re-enable. Almost everything checks out against the ATmega2560 datasheet. Deductions: no IMU DLPF/offset calibration (biased gyro → heading drift); **no velocity PID**; `velocity_to_pwm` is a fixed open-loop map. |
| 12. Launch system | **7.5 Acceptable** | Clean hierarchy, sane startup order. Deductions: the payload node was in the launch (removed); no lifecycle management for Nav2 moved onboard. |
| 13. Testing | **8.0 Strong** | Thorough, correctly ordered (motors first, encoders, E-stop, then comms, then system). Deductions: no closed-loop tracking test, no IMU calibration test, no long-run soak for the data pipeline. |
| 14. Performance | **8.0 Strong** | Honest targets; the 8 FPS/ROI Kinect strategy and the "don't drop safety rate" warning are correct. |
| 15. Troubleshooting | **8.0 Strong** | Comprehensive and cause-based. The old payload subsection has been repurposed for data-logging diagnostics. |
| 16. Deployment modes | **6.5 Needs improvement** | Honest about the laptop requirement and 15–20 min runtime, but as a *pre-deployment prototype* the field procedure lacked a data-collection pilot workflow (now Section 17) and a defined transition plan (now `../../versions/InsightV1.0_Ultron/implementation_spec.md`). |
| 17. Data collection & logging (NEW) | **9.0 (new)** | Closes the biggest gap between the declared pilot mission and the doc. Privacy-by-design is embedded, not bolted on. |
| 18. Upgrade path V0.3→insightV1.0 (NEW) | **9.0 (new)** | Explicit keep/replace/modify table per component; directly matches the planned hardware list. |

**Overall: ~7.7/10 → "YES WITH MAJOR CHANGES."**

---

## 3. Risk Register

| # | Risk | Sev | Prob | Impact | Current Mitigation | Required Action |
|---|---|---|---|---|---|---|
| R1 | **Open-loop wheel drive**: actual speed ≠ commanded (battery sag, load, slope) | High | High | Stop-margin analysis invalid; Nav2 tracking poor; false claims of ±10% twist | Firmware clamps velocity; Nav2 caps 0.35 m/s; supervised ops | **P0/P1:** add per-wheel velocity PID on the MCU using the encoders; re-validate stop margins at min battery |
| R2 | Kinect 1414 is EOL/obsolete, needs direct USB port, 12 W | Med | High (given) | USB contention, frame drops, power drain, upgrade friction | H1 direct-port allocation; ROI 320×120 @8 FPS | **P1:** refactor depth→scan to `camera_info`; keep driver isolated for the D455 swap (see the upgrade-path spec) |
| R3 | 15–20 min runtime on 3S 2200 mAh | High | High | Missions cut short; pilot data incomplete; field embarrassment | 12-min mission rule; spare packs | **P0 ops:** hot-swap plan + ≥2 packs; **InsightV1.0:** larger pack + power redesign |
| R4 | RELIABLE DDS QoS over VPN stalls under jitter | Med | Med | Frozen teleop/Nav2 commands (safety still holds: heartbeat→stop) | Local heartbeat; unicast peers; chrony | **P1:** keep DDS for lab; for remote use teleop at ≤0.3 m/s; move EKF onboard to shrink network dependency |
| R5 | EKF on laptop → localization depends on network + clock | Med | Med | TF jumps, AMCL instability over VPN | chrony B12; B4 TF ownership | **P1:** move EKF container to the Jetson (it is cheap); laptop keeps Nav2/RViz2 |
| R6 | Thin obstacle detection: 5.5 Hz + 1° LiDAR misses legs/IV stands | High | Med | Collision in cluttered hospital-like space | Kinect mid-field zone | **P1:** widen kinematic footprint in costmap; **P2:** up to A2M12 (10 Hz) earlier if budget allows |
| R7 | Jetson Nano 4 GB OOM/thermal/brownout under full load | Med | Med | Container death → E-stop (safe but disruptive) | ZRAM/swap, memory cap, MAKEFLAGS -j2, headless, 5V/4A check | Verify §3.6 soak test; consider 5 V/5 A buck |
| R8 | 43 A BTS7960 + 15 A fuse mismatch on a 44 A-capable battery | Med | Low | Fuse blow in rare dual-stall; wiring heat | 7 A/motor software trip fires first | **P1:** add wire-gauge spec for 12 V rail; test overcurrent path repeatedly |
| R9 | MPU6050 gyro bias → heading drift in EKF | Med | Med | Slow yaw drift, AMCL fights it | EKF yaw covariance | **P1:** IMU offset calibration + DLPF config; **Insight:** BNO085 |
| R10 | Tailscale pinned at 1.68.2 forever | Low | Med | Security/feature stagnation | apt-mark hold | Document upgrade test procedure before InsightV1.0 |
| R11 | Data-collection pilot privacy breach (raw video stored) | High | Med | Legal/ethical failure in a hospital pilot | Ultron_V0.3 privacy-by-design (17.2) | Follow 17.2/17.6 strictly; consent gate before any raw video |
| R12 | Docker-on-bridge DDS discovery regression after edits | Med | Low | `ros2 topic list` empty, "silent" failures | D2 host-networking rule | Keep it in a checked-in checklist; add a smoke-test script |
| R13 | Old kernel (L4T R32.7.2, kernel 4.9) can't run AX210/BNO085 tooling | Med | Med | Upgrade blocked until Orin | n/a | Sequence AX210/BNO085/CAN with the Orin upgrade, not before (see the upgrade-path spec) |
| R14 | SD card wear/boot hangs | Med | Low | Boot failures | SSD data-root, journald volatile, fsck | Maintained; fine |

---

## 4. Architecture Audit

**Modularity — 8/10.** The three layers (Arduino real-time → Jetson edge → laptop compute) are cleanly separated. The serial binary protocol is the single, versioned interface between MCU and ROS, which is the right seam. Nodes are individually replaceable.

**Scalability — 6/10 (as built) → 9/10 (as corrected).** As-written, the compute ceiling (Nano 4 GB) forces all heavy processing off-board. Because everything heavy is *containerized*, moving EKF/Nav2/SLAM onto a Jetson Orin is a compose-file change, not a rewrite — this is the correct scalability decision and the reason the architecture is salvageable.

**Maintainability — 7.5/10.** Excellent documentation, but: hardcoded constants in two places (firmware `config.h` and Python `serial_node`), no diagnostics, no automated config drift check, and the two-machine manual setup has many steps.

**Upgradeability — 8.5/10.** The container strategy, stable message interfaces, and protocol seam make the V0.3→insightV1.0 migration low-effort *for software*. The hardware seams are good too (sensor driver isolation). The main block is the perception pipeline hardcoding Kinect intrinsics (P1).

**Safety — 9/10.** Layered hardware→MCU→edge safety with heartbeat, WDT, and two-step E-stop recovery is genuinely good. Deduction: safety margins assume open-loop speed accuracy (R1).

**Deployment-oriented — 6.5/10.** As a *pre-deployment* prototype it is honest but not pilot-ready: no data pipeline, no diagnostics, no defined transition, short runtime. Corrected by Sections 17/18.

**Future AI integration — 6/10.** The AI story lives in `../10_architecture/ai_architecture.md` (collect→patterns→predict), but the Bible had zero data-infrastructure to feed it. Section 17 fixes the collection leg; the prediction leg is InsightV1.0+.

---

## 5. Hardware Audit (per component)

| Component | Verdict | Notes / Action |
|---|---|---|
| Jetson Nano 4 GB (C1) | **KEEP (V0.3) → REPLACE (Insight)** | Fine edge compute for sensors+safety; cannot host Nav2. Upgrade to Orin Nano Super 8 GB; same containers (see the upgrade-path spec). |
| Arduino Mega 2560 (C2) | **KEEP (V0.3) → REPLACE (Insight)** | Correctly used. InsightV1.0 moves to Arduino Nano + MCP2515 CAN + AS5048B. Keep protocol v1; add CAN transport. |
| Laptop (C3) | **KEEP** | V0.3 Nav2 + pilot "cloud". Demote to monitor at Insight. |
| 64 GB microSD (C4) | **KEEP** | OS-only; already correct. |
| 128 GB NVMe USB (C5) | **KEEP → M.2 NVMe 512 GB** | Same `/mnt/ssd` layout (Insight: internal M.2). |
| Orico hub (C6) | **KEEP** | Verified allocation (Kinect off hub). |
| TL-WN727N WiFi (C7) | **REPLACE (Insight)** | 2.4 GHz-only, USB2. AX210 needs kernel 5.15+ → do with Orin. |
| DK-37R motors (M1) | **KEEP (V0.3) → REPLACE encoders** | 825 t/rev Hall encoders are low-res (0.29 mm/tick) and open-loop. Add PID now; AS5048B over CAN at Insight. |
| IBT-2 / BTS7960 (D1) | **KEEP (V0.3), FIX sizing note** | 43 A drivers are gross overkill; ensure wire gauge for the 12 V rail; two-PWM wiring (v4.2r2 D1) is correct. |
| MPU6050 (S1) | **KEEP (V0.3) → REPLACE (Insight)** | Add DLPF + offset calibration (P1). BNO085 at Insight. |
| RPLiDAR A1M8 (S2) | **KEEP → REPLACE (Insight)** | A2M12 (10 Hz, 0.9°) improves margins and thin-obstacle detection. |
| Kinect 1414 (S3) | **REPLACE (Insight); KEEP with caveats (V0.3)** | Obsolete; 12 W; direct-port only. D455 at Insight. P1 refactor for drop-in. |
| ACS712-30A (S4) | **KEEP, VERIFY** | 66 mV/A → ~0.07 A resolution; noisy around PWM; 7 A threshold has only 1 A headroom over stall (8 A) — test on bench. |
| 3S 2200 mAh (P1) | **KEEP (V0.3 ops), UPGRADE (Insight)** | 15–20 min is the hard ceiling. ≥2 packs + hot-swap. |
| Buck 12→5V (P2) | **KEEP, VERIFY** | Must hold ≥4.9 V under surges; validate at 0.45 m/s bursts (Brown-out check in §3.6). |
| 15 A fuse (P3) | **KEEP** | Last resort; software trips first. |
| E-stop, LEDs, resistors, cables | **KEEP** | Correct. |

**Wiring notes:** pin map verified against the ATmega2560 (INT4/PE4, INT2/3 change-mode, PCINT0/Port B for D52/D51, Timer3 OC3A/OC3C, Timer4 OC4A/OC4B, 20 kHz at TOP=99). Battery divider (10 k/3.9 k, scale 0.017418) is correct. Kinect 12 V input is now explicit in the power topology (this edition).

---

## 6. Software / ROS Audit

**ROS2 distro/middleware:** Humble (LTS to 2027) inside Docker = correct portability decision; CycloneDDS is Tier-1 arm64/amd64 and ships via packages.ros.org (no source build) — correct choice vs Zenoh for installability. Deduction: DDS-over-VPN reliability (R4).

**Nodes/Topics/Interfaces:** Clean, well-scoped. Custom `/ultron/*` namespacing is consistent. Message types are standard (`Twist`, `Odometry`, `Imu`, `BatteryState`, `UInt8`, `Empty`) — good for reuse.

**QoS:** Table is correct and the AMCL best-effort fix is the classic pitfall solved. Keep.

**Services/actions:** None custom — acceptable at this scale. InsightV1.0 will add mission/action services.

**Lifecycle:** Nav2 lifecycle used; custom nodes are simple ROS nodes — fine for V0.3.

**Parameters:** Mix of launch-file params and code constants. Recommend promoting `WHEEL_RADIUS_M/SEP`, `MAX_SPEED_MPS`, safety-zone radii, and sensor intrinsics to ROS params (P2) to avoid firmware re-flashes for tuning.

**Launch:** Good hierarchy. Add an EKF-onboard option now (P1) so the Insight move is a flag, not a rewrite.

**Dependencies:** All packages exist for Humble arm64 (`rplidar_ros`, `robot_localization`, `slam_toolbox`, `navigation2`, `rmw_cyclonedds_cpp`). Verify `libfreenect 0.5.7-2` exact version availability on Ubuntu 22.04 arm64 at install time (may be 0.5.3-3; either works).

**Containerization:** Excellent. `network_mode: host` required and correctly documented; memory cap + healthcheck + restart policy good.

**Logging/diagnostics:** None before → added Section 17 (JSONL logger + laptop rosbag + diagnostics).

**Error handling:** Serial RX state machine + CRC is solid; nodes generally fail-stop. Add: node-level watchdog on topic rates inside safety_node (some exists via stale-sensor handling).

**Safety layer:** Strong (see §4). Keep.

**Navigation/SLAM:** slam_toolbox (mapping) + AMCL (localization) + Nav2/DWA — standard and correct. Constraint: all on the laptop. Open-loop drive (R1) is the main performance limiter.

**Sensor fusion:** EKF fuses wheel odom + MPU6050. Correct structure, weak inputs (low-res encoders, biased IMU). Improve with PID + IMU calibration (P1).

**AI integration:** None in the Bible; `../10_architecture/ai_architecture.md` provides the concept. Section 17 (data) is the enabling foundation.

---

## 7. Upgrade Path (V0.3 → Ultron_insightV1.0)

Defined in the corrected Bible (an upgrade-path section, moved out during the V0.3-only restructure). Summary — full spec in [`../../versions/InsightV1.0_Ultron/implementation_spec.md`](../../versions/InsightV1.0_Ultron/implementation_spec.md):

**Remain unchanged (no rebuild):** ROS2 Humble + Docker; message interfaces/QoS; safety architecture; binary protocol v1 (extended for CAN/BNO085 packets); `/mnt/ssd` storage layout; TF tree; launch structure; Section 17 data pipeline format.

**Upgrade (bounded change):** compute → Orin Nano Super 8 GB with EKF/Nav2/SLAM moved onboard; Kinect → RealSense D455 (via camera_info refactor, P1); MPU6050 → BNO085 (new IMU packet type); A1M8 → A2M12 (config-only); Mega+IBT-2 → Arduino Nano + MCP2515/TJA1050 CAN + AS5048B encoders (new `ultron_can_node`; keep the ROS interface); SD+USB-SSD → M.2 NVMe 512 GB; TL-WN727N → AX210 (with Orin kernel); 3S 2200 mAh → larger pack + power redesign; wood chassis → improved enclosure.

**Capabilities unlocked:** onboard autonomy (laptop-independent), environment sensors + logistics + privacy-aware human-behaviour intelligence, cloud/Command-Centre bridge, "collect→find patterns→predict" loop → foundation for Ultron_VitalsV2.0 / Ultron_MedAssistV3.0.

---

## 8. Missing Features (add NOW for a smooth deployment)

1. **Wheel-velocity PID** (P0) — closes the loop; carries to the CAN build.
2. **`camera_info`-driven depth→scan** (P1) — enables the D455 drop-in.
3. **Data collection & privacy pipeline** (done in Section 17) — the actual V0.3 mission.
4. **Diagnostics (`/diagnostics`)** (P2) — feeds the Command Centre interface later.
5. **Environment sensor hooks** (P2) — the InsightV1.0 sensors (temp/humidity/CO2) should be a documented slot; adding a cheap DHT22/SCD40 now validates the topic pattern early.
6. **Onboard EKF option** (P1) — flag to move EKF from laptop to Jetson.
7. **Params not constants** (P2) — tune without re-flash.
8. **Automated smoke-test script** (P2) — boot → topics → heartbeat → e-stop, run before every session (mitigates R12).
9. **IMU calibration + DLPF** (P1).
10. **Battery hot-swap procedure** (P0 ops).

---

## 9. Implementation Corrections (Prioritized)

### P0 — Must fix before building
- **Remove the abandoned optional-payload scope** (done).
- **Close the velocity loop or explicitly accept open-loop limits.** Recommend wheel PID on the Arduino (simple P or PI per wheel, ~30 Hz update using existing encoder counts). Re-run the stop-margin test at min battery.
- **Battery operations plan:** ≥2 packs, hot-swap, mission ≤ 12 min, verified 11.1 V return threshold.

### P1 — Should fix during implementation
- Refactor `depth_to_scan_node` to consume `sensor_msgs/CameraInfo` (kinect driver already publishes `/kinect/depth/camera_info`); remove hardcoded `FX/FY/CX/CY`.
- Move the EKF container to the Jetson; keep laptop for Nav2/RViz2 + data sink.
- IMU offset calibration at startup + DLPF configuration in `init_imu()`.
- Validate the 7 A overcurrent threshold against real stall/acceleration current on the bench.
- Wire-gauge spec for the 12 V rail (15 A path); verify the 5 V buck holds ≥4.9 V under surge.
- Verify `libfreenect` version availability; add a Kinect bandwidth smoke test.

### P2 — Recommended improvement
- Promote kinematics/safety/IMU constants to ROS2 parameters.
- Add `diagnostic_updater` health reporting on the Jetson + laptop.
- Add an automated pre-session smoke test (boot, topics, heartbeat, e-stop).
- Add environment-sensor hooks (DHT22/SCD40/MQ-135) behind a documented topic.
- Add `/diagnostics` consumption stub for the future Command Centre.
- Consider `ros-humble-rosbag2-storage-mcap` for compact bags.

### P3 — Future enhancement (InsightV1.0+)
- BNO085 fused-quaternion IMU packet + EKF `imu0` orientation config.
- CAN bus motor/sensor bus (MCP2515 + AS5048B) + `ultron_can_node`.
- Onboard Nav2/SLAM/EKF on Orin; laptop demoted.
- Cloud/Command-Centre bridge and fleet diagnostics.
- Continuous-learning / AI loop per `../10_architecture/ai_architecture.md`.

---

## 10. Final Recommended Architecture (corrected)

```
┌───────────────────────────────────────────────────────────────────────┐
│ LAYER 3 — PILOT "CLOUD" (Laptop, V0.3) → Cloud/Command-Centre (Insight)│
│   Nav2 + SLAM + RViz2 (containers)  ·  rosbag2/mcap data sink          │
│   feature_extract.py (anonymous motion features)  ·  /diagnostics       │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │ CycloneDDS over Tailscale (lab/supervised)
┌──────────────────────────────▼──────────────────────────────────────────┐
│ LAYER 2 — EDGE (Jetson Nano 4 GB now / Orin Nano Super 8 GB Insight)    │
│   Docker (host net): rplidar · kinect (→D455 later) · depth_to_scan     │
│   (camera_info-driven) · safety_node · serial_node (→ultron_can_node)   │
│   EKF (P1: move here now) · data_logger_node (S17) · diagnostics        │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │ USB serial binary protocol v1 (CRC-8)
┌──────────────────────────────▼──────────────────────────────────────────┐
│ LAYER 1 — REAL-TIME (Arduino Mega now / Nano + MCP2515 CAN Insight)     │
│   E-stop ISR (<5 ms) · watchdog (500 ms) · WDT (8 s)                    │
│   quadrature encoders (D18/19, D52/51) · 20 kHz two-PWM (IBT-2)         │
│   IMU (MPU6050 now, DLPF+offset; BNO085 later) · battery/current ADC    │
│   P1: per-wheel velocity PID                                            │
└──────────────────────────────────────────────────────────────────────────┘
```

**Design principles retained:** (a) every safety-critical path is local (hardware ISR → MCU watchdogs → edge safety); (b) the MCU↔ROS seam is a versioned binary protocol so the motor controller can be swapped without touching ROS; (c) all heavy compute is containerized so it can move machines; (d) sensor drivers are isolated so sensors swap behind unchanged topics; (e) data collection is privacy-by-design from the start (Section 17).

**What must be redesigned for InsightV1.0 (not just upgraded):**
- Power system (pack size, distribution, buck sizing for Orin + D455).
- Mechanical enclosure (heat, mounting, sensor layout).
- Perception privacy layer (anonymous feature extraction before storage).

Everything else is upgrade-in-place.

---

*This audit was applied as the Ultron_V0.3 restructure to `../versions/V0.3_Ultron/implementation_bible.md` and `../10_architecture/ai_architecture.md`. See `../versions/V0.3_Ultron/implementation_bible.md` (Section 17 data collection), `../../versions/InsightV1.0_Ultron/implementation_spec.md` (upgrade path), and the [README](../../README.md) for the restructured project. The three JPEG diagrams require manual re-export from the sources in `../10_architecture/diagrams/README.md`.*
