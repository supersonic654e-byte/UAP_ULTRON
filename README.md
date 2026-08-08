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
├── 10_architecture/           system · ros · sensor_fusion · safety · diagrams
├── 20_engineering_process/    audit · risk · ADRs · quality gates · changelog
├── 30_data_and_privacy/       collection spec · privacy · data dictionary
├── 40_business/               market analysis
└── 90_reference/              shared BOM · datasheets · CAD
versions/
├── V0.1_Ultron/               retired history
├── V0.2_Ultron/               retired history
├── V0.3_Ultron/               implementation_bible + hardware/firmware/software/tests
├── InsightV1.0_Ultron/        spec + hardware upgrade + deployment plan
└── _future/                   VitalsV2.0 / MedAssistV3.0 roadmap
scripts/                       smoke test + tooling
.github/                       issue/PR templates + CI
```

## Quick facts (V0.3)

- **Architecture:** two-layer (Jetson edge + laptop compute) + Arduino real-time layer.
- **ROS 2 Humble** in Docker; CycloneDDS over Tailscale (see ADR-0001).
- **Safety:** hardware E-stop (<5 ms) → MCU watchdogs → Jetson safety node.
- **Autonomy:** supervised only on V0.3 (Nav2 runs on the laptop).
- **Power:** 3S 2200 mAh → ~15–20 min; missions ≤ 12 min.
- **Data:** privacy-by-design pilot pipeline (Bible §17) — anonymous features, no raw video by default.

## Start here

1. [Project overview](docs/00_project/overview.md)
2. [Roadmap](docs/00_project/roadmap.md)
3. [System architecture](docs/10_architecture/system_architecture.md)
4. [V0.3 implementation Bible](versions/V0.3_Ultron/implementation_bible.md)
5. [Engineering audit (known issues + P0–P3)](docs/20_engineering_process/engineering_audit.md)

## Contributing

- See `.github/` for templates and CI. Quality gates: `docs/20_engineering_process/quality_gates.md`.
- Run `scripts/smoke_test.sh` before every session.

## License

See [LICENSE](LICENSE.md). Code is MIT; documentation is CC-BY-4.0 (see LICENSE).

---

_Team Supersonic · Dhaka, Bangladesh · 2024–present_
