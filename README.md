# UAP_ULTRON

> Low-cost autonomous robots for healthcare. Built by a student research team in
> Dhaka, Bangladesh — robots, embedded control, ROS 2, safety, and data pipeline,
> all from scratch.

**Current build: Ultron_V0.3** — final testing / pre-deployment prototype.
The build reference is the [implementation Bible](versions/V0.3_Ultron/implementation_bible.md).

## Version lineage

| Generation | Role | Status |
|---|---|---|
| Ultron_V0.1 (2024) | Lab / learning prototype | Retired |
| Ultron_V0.2 (2025) | Research prototype | Retired |
| **Ultron_V0.3** | Final testing + pre-deployment prototype | **Active** |
| Ultron_insightV1.0 | — | First real-world deployment version | Planned |
| Ultron_VitalsV2.0 · Ultron_MedAssistV3.0 | — | Patient monitoring · AI diagnosis | Future |

## Repository layout

```
docs/                          cross-version knowledge
├── 00_project/                overview · roadmap · naming · glossary
├── 10_architecture/           system · ros · sensor_fusion · safety · ai · diagrams
├── 20_engineering_process/    audit · risk · ADRs · quality gates · changelog · deployment_guide
├── 30_data_and_privacy/       collection spec · privacy · data dictionary
├── 40_business/               market analysis
└── 90_reference/              shared BOM · datasheets · CAD
versions/
├── V0.1_Ultron/               retired history
├── V0.2_Ultron/               retired history
├── V0.3_Ultron/               implementation_bible + hardware / firmware / software / tests /
│                              calibration / data_pilot / deploy
├── InsightV1.0_Ultron/        spec + hardware upgrade + deployment plan
└── _future/                   VitalsV2.0 / MedAssistV3.0 roadmap
scripts/                       smoke test + tooling
.github/                       issue/PR templates + CI
```

## Component map (Ultron_V0.3)

| Component | Where | What it is |
|---|---|---|
| [Implementation Bible](versions/V0.3_Ultron/implementation_bible.md) | `versions/V0.3_Ultron/` | Canonical build/deploy/ops reference (19 sections) |
| [Firmware](versions/V0.3_Ultron/firmware/README.md) | `firmware/ultron_firmware/` | Arduino Mega 2560 sketch: PID velocity control, encoders, two-PWM motors, IMU, E-stop, watchdogs, protocol |
| [Onboard software](versions/V0.3_Ultron/software/README.md) | `software/jetson/` | ROS 2 `ultron_onboard` package + Docker (serial, safety, kinect, depth→scan, data-logger) |
| [Laptop software](versions/V0.3_Ultron/software/README.md) | `software/laptop/` | EKF + SLAM/AMCL + Nav2 + RViz2 containers, ops scripts |
| [Web control system](versions/V0.3_Ultron/software/web/README.md) | `software/web/` | Admin dashboard (`/admin`) + user control panel (`/user`) — the "live server of the robot" |
| [Tests](versions/V0.3_Ultron/tests/README.md) | `tests/` | 68 offline unit tests + bench harnesses + procedures/results |
| [Calibration](versions/V0.3_Ultron/calibration/README.md) | `calibration/` | Wheel/encoder/battery/IMU/camera calibration tools |
| [Deploy assets](versions/V0.3_Ultron/deploy/README.md) | `deploy/` | udev, systemd, chrony, build/flash/verify scripts |
| [Data pilot](versions/V0.3_Ultron/data_pilot/README.md) | `data_pilot/` | Mission log index + anonymous feature extraction |
| [Deployment guide](docs/20_engineering_process/user_deployment_guide.md) | `docs/20_engineering_process/` | Two-bundle end-user install (Jetson + laptop + firmware) |

## Quick facts (V0.3)

- **Architecture:** two-layer (Jetson edge + laptop compute) + Arduino real-time layer.
- **ROS 2 Humble** in Docker; CycloneDDS over Tailscale (see ADR-0001).
- **Safety:** hardware E-stop (<5 ms) → MCU watchdogs → Jetson safety node.
- **Autonomy:** supervised only on V0.3 (Nav2 runs on the laptop).
- **Web control:** admin dashboard + user control panel (4-digit PIN); admin
  robot-operation only with the 10-character override password.
- **Power:** 3S 2200 mAh → ~15–20 min; missions ≤ 12 min.
- **Data:** privacy-by-design pilot pipeline (Bible §17) — anonymous features, no raw video by default.

## Quickstart

**Build the robot (from scratch):** read the
[Bible](versions/V0.3_Ultron/implementation_bible.md) sections 0–2, then
[firmware](versions/V0.3_Ultron/firmware/README.md) and
[hardware](versions/V0.3_Ultron/hardware/README.md).

**Run the software stack:** follow
[software/README.md](versions/V0.3_Ultron/software/README.md) for the Jetson +
laptop containers, and the [deployment guide](docs/20_engineering_process/user_deployment_guide.md)
for the two-bundle end-user path.

**Control it from the web:** bring up `ultron_web`
([README](versions/V0.3_Ultron/software/web/README.md)) → `/admin` and `/user`.

## Verification & CI

Every push runs:

- **docs-lint** — broken relative links + abandoned-payload tokens.
- **firmware-build** — real `arduino-cli` compile of the Mega 2560 sketch.
- **software-test** — 68 offline tests (protocol, safety zones, depth→scan,
  web auth/store/detection/render/API).

Run locally: `versions/V0.3_Ultron/tests/scripts/run_tests.sh` and
`python -m pytest -q versions/V0.3_Ultron/software/web/tests`.

## Start here

1. [Project overview](docs/00_project/overview.md)
2. [Roadmap](docs/00_project/roadmap.md)
3. [System architecture](docs/10_architecture/system_architecture.md)
4. [V0.3 implementation Bible](versions/V0.3_Ultron/implementation_bible.md)
5. [Engineering audit (known issues + P0–P3)](docs/20_engineering_process/engineering_audit.md)
6. [End-user deployment guide](docs/20_engineering_process/user_deployment_guide.md)

## Contributing

- See `.github/` for templates and CI. Quality gates: `docs/20_engineering_process/quality_gates.md`.
- Run `scripts/smoke_test.sh` before every session.

## License

See [LICENSE](LICENSE.md). Code is MIT; documentation is CC-BY-4.0 (see LICENSE).

## Pre-publication privacy

This project is **pre-publication research**. Before the paper is submitted:

- Contributor identities are withheld — the team is credited only by role
  (**student researcher**, **technical expert**) until publication.
- Keep this repository **private** (Settings → General → Danger Zone →
  Change visibility → Private) so code, data, and findings are not publicly
  attributed before the paper is out.
- Do not quote or cite anything from this repo publicly until the paper is
  accepted or the team lifts this notice.

---

_Team Supersonic — student researcher + technical expert · Dhaka, Bangladesh · 2024–present_
