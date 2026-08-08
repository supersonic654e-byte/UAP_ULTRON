# Mission <MISSION_ID> — Metadata

| Field | Value |
|---|---|
| mission_id | <MISSION_ID> |
| date | YYYY-MM-DD |
| site_id | <site_id> |
| operator_id | <operator_id> |
| mission_type | teleop / supervised_nav2 |
| waypoints | [] |
| start_utc | (chrony-synced) |
| end_utc | |
| mission_result | completed / aborted / interrupted |
| battery_start_v | |
| battery_end_v | |
| retention_days | (per site policy) |
| consent_gate | none / documented (see privacy_policy.md) |
| notes | |

## Artifacts (never commit raw bags to git)

- `checksums.txt` — from `tests/scripts/bag_checksum.py <bag_dir>`
- `features.csv` / `mission_summary.json` — from
  `data_pilot/feature_extract.py` (small, commit these)

## Raw bag

Kept off-repo (laptop "cloud", encrypted at rest). Reference with its DOI /
path here.
