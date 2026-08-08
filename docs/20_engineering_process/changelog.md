# Changelog

Dated log of significant changes. Newest first. Format: `YYYY-MM-DD — what changed (author/PR)`.

## 2026-08-08 — Verified V0.3 software system framework (Sadnan Sajid355)

- `versions/V0.3_Ultron/firmware/` — buildable Arduino Mega 2560 sketch
  (`ultron_firmware/`): full protocol, encoders, two-PWM motors, TX queue,
  power/overcurrent, fault bits + P0 wheel-velocity PID and P1 IMU DLPF +
  gyro zero-offset. Compiles clean with `arduino-cli` (5 % flash, 9 % RAM).
- `versions/V0.3_Ultron/software/jetson/` — ROS 2 `ultron_onboard` package
  (serial/safety/kinect/depth-to-scan/data-logger nodes), Dockerfile,
  compose (host net, mem cap, healthcheck), CycloneDDS config, params, launch.
- `versions/V0.3_Ultron/software/laptop/` — Nav2/EKF/SLAM container
  (nav2_params with B6 0.35 m/s cap + AMCL best-effort QoS, ekf_params B4,
  slam_params), localization mode, RViz2 config, ops scripts.
- `versions/V0.3_Ultron/tests/` — offline unit tests (protocol CRC/frames,
  safety zones, depth->scan) + hardware bench harnesses + procedures/results.
- `versions/V0.3_Ultron/calibration/` — wheel/encoder/battery/IMU tools.
- `versions/V0.3_Ultron/deploy/` — udev, systemd, chrony, build/flash scripts.
- `versions/V0.3_Ultron/data_pilot/` — `feature_extract.py` (anonymous motion
  features), mission index/templates.
- CI: `software-test.yml` (offline tests) + `firmware-build.yml` sketch-path fix.

## 2026-08-08 — V0.3 monorepo restructure (Team_Supersonic)

- Created the UAP_ULTRON monorepo layout (docs/, versions/, .github/).
- Converted the implementation Bible to Markdown
  (`versions/V0.3_Ultron/implementation_bible.md`).
- Split the V0.1/V0.2 history into per-version folders.
- Moved the InsightV1.0 spec and the Vitals/MedAssist roadmap into `versions/`.
- Added Mermaid diagram sources under `docs/10_architecture/diagrams/`.
- Added CI (docs-lint, firmware-build) and issue/PR templates.
- Fixed relative links in copied docs.

## 2026-08-08 — Hardware base + system architecture + sensor fusion (Sadnan Sajid355)

- `versions/V0.3_Ultron/hardware/` — hardware base package (BOM, wiring, power).
- `docs/10_architecture/system_architecture.md` — industrial-grade system
  architecture design notes.
- `docs/10_architecture/sensor_fusion.md` — sensor-fusion build parts.

## 2026-08-08 — Bible v5.0 (V0.3 edition)

- Removed the abandoned optional payload scope from the project history.
- Renamed version identity: `Ultron_V0.3` (builds on Bible v4.2 + r2/r3 fixes).
- Added Section 17 (data collection & logging pilot).
- Applied audit corrections and the data/privacy constraint block.

## 2026-08-05 — Bible v4.2 (+r2/r3)

- B1–B12: right-encoder PCINT fix, IBT-2 two-PWM wiring, CycloneDDS switch,
  TF ownership, E-stop recovery, overcurrent 7 A, serial RX window, 16U2 udev,
  MAKEFLAGS=-j2, chrony, storage architecture + powered hub, Tailscale pin.
- r2: host networking (D2), EN re-enable (D3), RX 1200 µs (D4), firewall (D5),
  restart-latch note (D6).
- r3: Kinect 8 FPS / ROI 320×120, Nano stability hardening.

## 2026-03-18 — Bible v4.0

- Full canonical rewrite: 16 sections, ZRAM/swap, Docker perf, deployment
  modes, troubleshooting.

## 2025 — Bible v1.0–v3.0

- Initial single-machine ROS 2 Humble on Jetson.
- Two-layer architecture, Zenoh/Tailscale (later superseded by ADR-0001).
- Embedded audit: ISR fixes, QoS fix, unified PWM top, HW WDT 8 s, safety node.
