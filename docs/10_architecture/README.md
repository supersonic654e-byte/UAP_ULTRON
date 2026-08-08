# Architecture Docs

Cross-version architecture knowledge (not tied to one robot build).

| Doc | Covers |
|---|---|
| `system_architecture.md` | The three layers, design intent, industrial-grade considerations |
| `ros_architecture.md` | ROS 2 stack, node graph, QoS, TF tree, transport |
| `sensor_fusion.md` | EKF fusion chain, build blocks, tuning |
| `fusion_build_parts.md` | Reusable fusion components (Part 1–6) with interfaces |
| `data_flow.md` | Up/down data paths, bandwidth, latency budget |
| `safety_architecture.md` | Layered safety, watchdogs, E-stop, zones |
| `ai_architecture.md` | collect → find patterns → predict (InsightV1.0+) |
| `diagrams/` | Mermaid sources + rendered PNGs |

> Conventions: shared design lives here; build-specific constants and wiring
> live in `versions/V0.3_Ultron/implementation_bible.md`. If a fact appears in
> both, the implementation Bible is authoritative for V0.3.
