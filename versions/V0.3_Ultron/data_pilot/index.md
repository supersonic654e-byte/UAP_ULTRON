# V0.3 Pilot — Mission Index

Mission log table. Append one row per completed mission; the full metadata
lives in `missions/<mission_id>/README.md`.

| mission_id | date | site_id | operator_id | result | duration_s | distance_m | features | bag_retained |
|---|---|---|---|---|---|---|---|---|
| MISSION_001 | 2026-08-08 | site_A | op_1 | completed | 420 | 42.1 | yes | until <retention> |

## Rules

- Never commit rosbag/mcap or raw depth/video to git.
- Every mission folder has a `README.md` with metadata per
  [`docs/30_data_and_privacy/data_dictionary.md`](../../../docs/30_data_and_privacy/data_dictionary.md).
- Encryption + retention per
  [`docs/30_data_and_privacy/privacy_policy.md`](../../../docs/30_data_and_privacy/privacy_policy.md).
