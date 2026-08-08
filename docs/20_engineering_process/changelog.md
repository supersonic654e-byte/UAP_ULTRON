# Changelog

Dated log of significant changes. Newest first. Format: `YYYY-MM-DD — what changed (author/PR)`.

## 2026-08-08 — V0.3 monorepo restructure (Team_Supersonic)

- Created the UAP_ULTRON monorepo layout (docs/, versions/, .github/).
- Converted the implementation Bible to Markdown
  (`versions/V0.3_Ultron/implementation_bible.md`).
- Split the V0.1/V0.2 history into per-version folders.
- Moved the InsightV1.0 spec and the Vitals/MedAssist roadmap into `versions/`.
- Added Mermaid diagram sources under `docs/10_architecture/diagrams/`.

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
