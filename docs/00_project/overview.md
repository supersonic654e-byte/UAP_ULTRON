# UAP_ULTRON — Project Overview

> **Status:** Active development. Current hardware generation: **Ultron_V0.3** (final testing / pre-deployment prototype).

## What this project is

UAP_ULTRON is the mother project for a line of **low-cost autonomous mobile
robots for healthcare**. We are a student research team building the robots
ourselves — chassis, embedded control, ROS 2 software, safety, and the data
pipeline — starting from scratch.

The immediate goal is an indoor mobile robot that:

- navigates hospital-like indoor environments (corridors, rooms, mixed human presence),
- collects **environmental, logistics and privacy-aware motion data**,
- does it at a fraction of the cost of imported hospital robots,
- and is engineered so it can grow into a real deployment version without a rebuild.

## The problem we are aiming at

Bangladesh hospitals operate under heavy constraints:

| Signal | Value (from our market research) |
|---|---|
| Nursing shortage | ~82% (need ~310,500 nurses, have ~56,700) |
| Bed occupancy | ~80% with ~18-day average stay → congestion |
| Hospitals with surveillance / operational data | ~0% |
| Health spending | ~USD 32 per capita |
| Imported hospital robots | USD 100k–200k (not affordable, not serviceable locally) |

There is no local robotics company serving healthcare. That is the gap we are building into.

## What UAP_ULTRON is NOT (yet)

- It is **not** a production product. The current robot (V0.3) is a
  **pre-deployment testing prototype** — the last experimental generation.
- Earlier robots (V0.1, V0.2) were pure learning/lab platforms and are **retired**.

## Version lineage (short)

| Generation | Role | Status |
|---|---|---|
| Ultron_V0.1 (2024) | Lab / learning prototype | Retired |
| Ultron_V0.2 (2025) | Research prototype | Retired |
| **Ultron_V0.3** | Final testing + pre-deployment prototype | **Current** |
| Ultron_insightV1.0 | First real-world deployment version | Planned |
| Ultron_VitalsV2.0 / Ultron_MedAssistV3.0 | Patient monitoring / AI diagnosis | Future |

The canonical naming rules live in [`naming_and_versioning.md`](naming_and_versioning.md).
The full timeline is in [`roadmap.md`](roadmap.md).

## Where to start reading

- Current build: `../versions/V0.3_Ultron/implementation_bible.md`
- Architecture: `../10_architecture/system_architecture.md`
- Audit / known problems: `../20_engineering_process/engineering_audit.md`
- Team process and status: `../20_engineering_process/changelog.md`

## Short engineering identity

- **ROS 2 Humble** (Docker) on a Jetson Nano edge layer + a laptop for Nav2/SLAM.
- **Arduino Mega** real-time layer: E-stop ISR (<5 ms), watchdogs, 20 kHz PWM drive.
- **Safety-first**: hardware E-stop → MCU watchdogs → Jetson safety node.
- **Privacy-by-design** data collection: anonymous motion features, no identifiable video by default.

_Team: Supersonic · Dhaka, Bangladesh_
