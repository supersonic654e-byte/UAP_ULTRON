# Naming & Versioning — Canonical Rules

**Single source of truth for every name in this project.** If two documents
disagree, this file wins and the other one is wrong — fix the other one.

## 1. Version tokens (never deviate)

| Canonical token | Meaning |
|---|---|
| `UAP_ULTRON` | The mother project (repo root). Always uppercase. |
| `Ultron_V0.1` | First laboratory prototype (formerly `Robot_ODA_v1.0`, 2024). |
| `Ultron_V0.2` | Research prototype (formerly `Robot_ODA_v2.0`, 2025). |
| `Ultron_V0.3` | Current build — final testing / pre-deployment prototype. |
| `Ultron_insightV1.0` | First real-world deployment version. |
| `Ultron_VitalsV2.0` | Patient-monitoring generation (future). |
| `Ultron_MedAssistV3.0` | AI diagnosis + medicine generation (future). |

Rules:

- Use the exact token above. `Ultron_V0.3` is never written `V0.3` alone in
  titles, and `Ultron_insightV1.0` is not written `Insight_V1.0` or `V1`.
- Retired versions keep their folder (`versions/V0.1_Ultron/`) as **read-only
  history**. Never update them with current-build facts.
- A "version" is a **robot generation**, not a document revision. Documents
  track their own changes in the changelog, not with `vX.Y` branding in titles.

## 2. Folder naming

- Version folders: `V0.1_Ultron`, `V0.2_Ultron`, `V0.3_Ultron`,
  `InsightV1.0_Ultron` — kept under `versions/`.
- Shared docs under `docs/NN_area/` with numeric sort prefixes
  (`00_project`, `10_architecture`, `20_engineering_process`, …).
- Files: `kebab-case.md`. Code: repo-standard per language.

## 3. Robot identity vs technical identifiers

| Layer | Convention | Example |
|---|---|---|
| Commercial / project identity | `Ultron_V0.3`, `UAP_ULTRON` | — |
| ROS package / node names | `ultron_*` | `ultron_onboard`, `ultron_serial_node` |
| Custom topics | `/ultron/*` | `/ultron/fault`, `/ultron/heartbeat` |
| Device symlinks | `/dev/ultron_*` | `/dev/ultron_arduino`, `/dev/ultron_lidar` |
| Hostname | `ultron-v03` | — |
| Workspace / data paths | `/mnt/ssd/ultron`, `~/ultron_laptop` | — |
| Firmware | `ultron_firmware/` | `config.h`, `robot_oda_firmware.ino` renamed |

Standard ROS topics (`/scan`, `/odom`, `/imu/data`, `/cmd_vel`, `/battery/state`)
keep their canonical names — they are interface contracts with Nav2/SLAM.

## 4. Renaming history (why this file exists)

In early 2026 the project carried several inconsistent names
(`Robot_ODA_v1.0/v2.0`, `robot_odaV4`, and an abandoned optional payload
concept). In the v5.0 restructure:

- `Robot_ODA_v1.0` → `Ultron_V0.1`
- `Robot_ODA_v2.0` → `Ultron_V0.2`
- `robot_odaV4` / current build → `Ultron_V0.3`
- All abandoned-payload references were **removed**, not hidden.

The old names may appear only in *former-name mapping tables* and history
documents, never as an active identity.

## 5. Document versioning

- Every doc gets a `Last updated` line (date + author).
- Substantive changes go into `docs/20_engineering_process/changelog.md`.
- Releases are git tags (`V0.3-m1`, `V0.3-rc1`, `insightV1.0-a1`), never
  "v5.0-style" numbers embedded in content.
